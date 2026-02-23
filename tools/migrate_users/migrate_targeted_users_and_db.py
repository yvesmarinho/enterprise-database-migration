#!/usr/bin/env python3
"""
Targeted User & Database Migration
===================================

Copia do servidor **source** (wfdb02 / 82.197.64.145) para o servidor
**destiny** (home016 / 127.0.0.1) os seguintes itens:

Usuários:
  - migration_user
  - backup
  - journey*  (journey_system, journey_typebot, journeydb_user, journeytypebot, …)
  - yves_marinho
  - vanderson_andrade

Banco de dados:
  - app_workforce  (criação + grants originais)

Uso:
    python3 scripts/migrate_targeted_users_and_db.py \
        --source secrets/wfdb02_source_config.json \
        --destiny secrets/home016_destiny_config.json \
        [--dry-run] [--verbose]

    # Listar configs disponíveis em secrets/
    python3 scripts/migrate_targeted_users_and_db.py --list-configs
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ psycopg2 não encontrado. Execute: pip install psycopg2-binary")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Caminhos base
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = SCRIPT_DIR / "migration_settings.json"
SECRETS_DIR = BASE_DIR / "secrets"


def load_migration_settings() -> dict:
    """Carrega migration_settings.json do diretório do script, se existir."""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def list_available_configs() -> None:
    """Imprime os arquivos .json disponíveis em secrets/."""
    print(
        f"\n📁 Configs disponíveis em '{SECRETS_DIR.relative_to(BASE_DIR)}':\n")
    jsons = sorted(SECRETS_DIR.glob("*.json"))
    if jsons:
        for p in jsons:
            print(f"   • {p.name}")
    else:
        print("   (nenhum arquivo .json encontrado)")
    print()


# ---------------------------------------------------------------------------
# Filtro de usuários alvo
# ---------------------------------------------------------------------------
TARGET_USERS_EXACT = {
    "migration_user",
    "backup",
    "yves_marinho",
    "vanderson_andrade",
}

TARGET_USERS_PREFIX = ("journey",)   # journeytypebot, journey_system, etc.

TARGET_DATABASE = "app_workforce"


def is_target_user(rolname: str) -> bool:
    if rolname in TARGET_USERS_EXACT:
        return True
    return rolname.startswith(TARGET_USERS_PREFIX)


# ---------------------------------------------------------------------------
# Helpers de conexão
# ---------------------------------------------------------------------------
def _source_dsn(cfg: dict) -> dict:
    return dict(
        host=cfg["host"],
        port=int(cfg["port"]),
        dbname=cfg.get("database", "postgres"),
        user=cfg["possible_users"][0]["username"],
        password=cfg["possible_users"][0]["password"],
        sslmode=cfg.get("ssl_mode", "prefer"),
        connect_timeout=10,
    )


def _dest_dsn(cfg: dict) -> dict:
    srv = cfg["server"]
    auth = cfg["authentication"]
    conn = cfg.get("connection_settings", {})
    return dict(
        host=srv.get("host_ip", srv["host"]),
        port=int(srv["port"]),
        dbname="postgres",
        user=auth["user"],
        password=auth["password"],
        sslmode=srv.get("ssl_mode", "disable"),
        connect_timeout=conn.get("connection_timeout", 30),
    )


def load_configs(source_path: Path, destiny_path: Path):
    """Carrega os dois arquivos de configuração JSON."""
    for label, path in (("source", source_path), ("destiny", destiny_path)):
        if not path.exists():
            print(f"❌ Arquivo {label} não encontrado: {path}")
            print("   Use --list-configs para ver os disponíveis.")
            sys.exit(1)

    with open(source_path, encoding="utf-8") as f:
        source = json.load(f)
    with open(destiny_path, encoding="utf-8") as f:
        destiny = json.load(f)
    return source, destiny


# ---------------------------------------------------------------------------
# Coleta de dados na origem
# ---------------------------------------------------------------------------
def get_target_users_from_source(conn, verbose=False) -> list[dict]:
    """Extrai somente os usuários alvo do pg_authid."""
    cur = conn.cursor()
    cur.execute("""
        SELECT
            rolname,
            rolsuper,
            rolinherit,
            rolcreaterole,
            rolcreatedb,
            rolcanlogin,
            rolreplication,
            rolconnlimit,
            rolpassword,
            rolvaliduntil
        FROM pg_authid
        WHERE rolname NOT LIKE 'pg_%'
        ORDER BY rolname
    """)

    users = []
    for row in cur.fetchall():
        rolname = row[0]
        if not is_target_user(rolname):
            if verbose:
                print(f"   ⏭  Ignorando: {rolname}")
            continue
        users.append({
            "rolname":        row[0],
            "rolsuper":       row[1],
            "rolinherit":     row[2],
            "rolcreaterole":  row[3],
            "rolcreatedb":    row[4],
            "rolcanlogin":    row[5],
            "rolreplication": row[6],
            "rolconnlimit":   row[7],
            "rolpassword":    row[8],
            "rolvaliduntil":  row[9],
        })
    cur.close()
    return users


def get_app_workforce_grants(conn) -> list[dict]:
    """Extrai grants do banco app_workforce na origem."""
    cur = conn.cursor()
    cur.execute("""
        SELECT
            grantee::regrole::text AS grantee,
            privilege_type
        FROM pg_database d,
             aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
        WHERE d.datname = %s
        ORDER BY grantee, privilege_type
    """, (TARGET_DATABASE,))
    grants = [{"grantee": row[0], "privilege": row[1]}
              for row in cur.fetchall()]
    cur.close()
    return grants


def database_exists_in_source(conn) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s",
                (TARGET_DATABASE,))
    exists = cur.fetchone() is not None
    cur.close()
    return exists


# ---------------------------------------------------------------------------
# Criação no destino
# ---------------------------------------------------------------------------
def get_existing_roles(conn) -> set:
    cur = conn.cursor()
    cur.execute("SELECT rolname FROM pg_roles")
    roles = {row[0] for row in cur.fetchall()}
    cur.close()
    return roles


def create_user_in_dest(conn, user: dict, dry_run: bool) -> bool:
    username = user["rolname"]
    attrs = []

    if user["rolcanlogin"]:
        attrs.append("LOGIN")
    else:
        attrs.append("NOLOGIN")

    if user["rolsuper"]:
        attrs.append("SUPERUSER")
    else:
        attrs.append("NOSUPERUSER")

    if user["rolinherit"]:
        attrs.append("INHERIT")
    else:
        attrs.append("NOINHERIT")

    if user["rolcreaterole"]:
        attrs.append("CREATEROLE")
    else:
        attrs.append("NOCREATEROLE")

    if user["rolcreatedb"]:
        attrs.append("CREATEDB")
    else:
        attrs.append("NOCREATEDB")

    if user["rolreplication"]:
        attrs.append("REPLICATION")
    else:
        attrs.append("NOREPLICATION")

    if user["rolconnlimit"] is not None and user["rolconnlimit"] >= 0:
        attrs.append(f"CONNECTION LIMIT {user['rolconnlimit']}")

    if user["rolvaliduntil"]:
        attrs.append(f"VALID UNTIL '{user['rolvaliduntil']}'")

    attrs_str = " ".join(attrs)

    if user["rolpassword"]:
        cmd = f'CREATE ROLE "{username}" WITH {attrs_str} PASSWORD \'{user["rolpassword"]}\''
    else:
        cmd = f'CREATE ROLE "{username}" WITH {attrs_str}'

    if dry_run:
        print(f"   [DRY-RUN] {cmd[:120]}…")
        return True

    try:
        cur = conn.cursor()
        cur.execute(cmd)
        conn.commit()
        cur.close()
        return True
    except psycopg2.errors.DuplicateObject:
        conn.rollback()
        print(f"   ⚠️  Usuário {username} já existe — ignorado")
        return True
    except Exception as e:
        conn.rollback()
        print(f"   ❌ Erro ao criar {username}: {e}")
        return False


def create_app_workforce_db(conn, dry_run: bool) -> bool:
    cmd = f"""
CREATE DATABASE "{TARGET_DATABASE}"
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TABLESPACE = pg_default
    TEMPLATE = template0
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False
""".strip()

    if dry_run:
        print(f"   [DRY-RUN] {cmd[:120]}…")
        return True

    # CREATE DATABASE não funciona dentro de transação
    old_isolation = conn.isolation_level
    conn.set_isolation_level(0)
    try:
        cur = conn.cursor()
        cur.execute(cmd)
        cur.close()
        print(f"   ✅ Banco '{TARGET_DATABASE}' criado")
        return True
    except psycopg2.errors.DuplicateDatabase:
        print(f"   ⚠️  Banco '{TARGET_DATABASE}' já existe — ignorado")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao criar banco '{TARGET_DATABASE}': {e}")
        return False
    finally:
        conn.set_isolation_level(old_isolation)


def apply_grants(conn, grants: list[dict], dry_run: bool) -> int:
    applied = 0
    # PUBLIC e postgres são ruídos — filtrar se desejado
    # "-" = PUBLIC no aclexplode (OID 0)
    SKIP_GRANTEES = {"PUBLIC", "postgres", "-"}

    for grant in grants:
        grantee = grant["grantee"]
        privilege = grant["privilege"]

        if grantee in SKIP_GRANTEES:
            continue

        cmd = f'GRANT {privilege} ON DATABASE "{TARGET_DATABASE}" TO "{grantee}"'

        if dry_run:
            print(f"   [DRY-RUN] {cmd}")
            applied += 1
            continue

        try:
            cur = conn.cursor()
            cur.execute(cmd)
            conn.commit()
            cur.close()
            print(f"   ✅ GRANT {privilege} ON {TARGET_DATABASE} TO {grantee}")
            applied += 1
        except Exception as e:
            conn.rollback()
            print(f"   ❌ Erro grant {grantee}/{privilege}: {e}")

    return applied


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _resolve_config_path(value: str) -> Path:
    """Aceita caminho absoluto, relativo ao cwd, ou só o nome do arquivo (busca em secrets/)."""
    p = Path(value)
    if p.is_absolute() or p.exists():
        return p.resolve()
    # Tenta resolver relativo ao BASE_DIR
    candidate = BASE_DIR / value
    if candidate.exists():
        return candidate.resolve()
    # Tenta só o nome dentro de secrets/
    candidate = SECRETS_DIR / p.name
    if candidate.exists():
        return candidate.resolve()
    return p.resolve()   # deixa falhar com mensagem clara em load_configs


def main():
    parser = argparse.ArgumentParser(
        description="Migra usuários selecionados e banco app_workforce (source → destiny)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Defaults de --source e --destiny são lidos automaticamente de\n"
            f"  {SETTINGS_FILE}\n"
            "quando os argumentos não são informados na linha de comando."
        ),
    )
    parser.add_argument(
        "--source", metavar="ARQUIVO",
        help=(
            "JSON de configuração do servidor ORIGEM "
            "(nome em secrets/ ou caminho completo). "
            "Se omitido, usa o valor em migration_settings.json → source.file"
        ),
    )
    parser.add_argument(
        "--destiny", metavar="ARQUIVO",
        help=(
            "JSON de configuração do servidor DESTINO "
            "(nome em secrets/ ou caminho completo). "
            "Se omitido, usa o valor em migration_settings.json → destiny.file"
        ),
    )
    parser.add_argument(
        "--settings", metavar="ARQUIVO",
        default=str(SETTINGS_FILE),
        help=(
            f"Arquivo JSON com configurações padrão do script "
            f"(padrão: migration_settings.json no mesmo diretório)"
        ),
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula sem aplicar alterações")
    parser.add_argument("--verbose", action="store_true",
                        help="Exibe usuários ignorados")
    parser.add_argument("--list-configs", action="store_true",
                        help="Lista arquivos .json disponíveis em secrets/ e sai")
    args = parser.parse_args()

    if args.list_configs:
        list_available_configs()
        sys.exit(0)

    # ---- Carregar defaults do migration_settings.json (ou --settings) ----
    settings_path = Path(args.settings)
    if settings_path.exists():
        with open(settings_path, encoding="utf-8") as f:
            settings = json.load(f)
    else:
        settings = {}
    cfg_dir = settings.get("configs_dir", "secrets/")
    default_source = settings.get("source", {}).get("file", "")
    default_destiny = settings.get("destiny", {}).get("file", "")

    # ---- Solicitar interativamente se não fornecido ----
    if not args.source:
        if default_source:
            print(
                f"   📄 Usando origem  do settings: {cfg_dir}{default_source}")
            args.source = cfg_dir + default_source
        else:
            list_available_configs()
            args.source = input("🔵 Nome/caminho do JSON de ORIGEM  : ").strip()
    if not args.destiny:
        if default_destiny:
            print(
                f"   📄 Usando destino do settings: {cfg_dir}{default_destiny}")
            args.destiny = cfg_dir + default_destiny
        else:
            args.destiny = input(
                "🟢 Nome/caminho do JSON de DESTINO : ").strip()

    source_path = _resolve_config_path(args.source)
    destiny_path = _resolve_config_path(args.destiny)

    print("=" * 70)
    print("🚀 Targeted User & Database Migration")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📂 ORIGEM  : {source_path.name}")
    print(f"📂 DESTINO : {destiny_path.name}")
    print(f"{'🧪 DRY-RUN ATIVO — nenhuma alteração será feita' if args.dry_run else '🔴 MODO REAL — alterações serão aplicadas'}")
    print("=" * 70)

    # Carregar configs
    source_cfg, dest_cfg = load_configs(source_path, destiny_path)

    # ----- Conexão origem -----
    src_label = source_cfg.get("host", source_path.name)
    print(f"\n🔌 Conectando no servidor ORIGEM ({src_label})…")
    try:
        src_conn = psycopg2.connect(**_source_dsn(source_cfg))
        src_conn.autocommit = False
        print("   ✅ Conectado")
    except Exception as e:
        print(f"   ❌ Falha: {e}")
        sys.exit(1)

    # ----- Conexão destino -----
    dst_label = dest_cfg.get("server", {}).get("host", destiny_path.name)
    print(f"🔌 Conectando no servidor DESTINO ({dst_label})…")
    try:
        dst_conn = psycopg2.connect(**_dest_dsn(dest_cfg))
        dst_conn.autocommit = False
        print("   ✅ Conectado")
    except Exception as e:
        print(f"   ❌ Falha: {e}")
        src_conn.close()
        sys.exit(1)

    # =========================================================
    # FASE 1 — Usuários
    # =========================================================
    print("\n" + "=" * 70)
    print("👥 FASE 1: USUÁRIOS")
    print("=" * 70)

    users = get_target_users_from_source(src_conn, args.verbose)
    print(f"   → {len(users)} usuário(s) alvo encontrados na origem:")
    for u in users:
        print(f"      • {u['rolname']}")

    existing = get_existing_roles(dst_conn)
    created = skipped = errors = 0

    for user in users:
        rolname = user["rolname"]
        if rolname in existing:
            print(f"   ⚠️  {rolname} já existe no destino — ignorado")
            skipped += 1
            continue
        print(f"   🔄 Criando {rolname}…")
        if create_user_in_dest(dst_conn, user, args.dry_run):
            if not args.dry_run:
                print(f"   ✅ {rolname} criado")
            created += 1
        else:
            errors += 1

    print(
        f"\n   📊 Usuários: {created} criados | {skipped} ignorados | {errors} erros")

    # =========================================================
    # FASE 2 — Banco app_workforce
    # =========================================================
    print("\n" + "=" * 70)
    print(f"🗄️  FASE 2: BANCO DE DADOS '{TARGET_DATABASE}'")
    print("=" * 70)

    if not database_exists_in_source(src_conn):
        print(
            f"   ❌ Banco '{TARGET_DATABASE}' não encontrado na origem! Abortando fase 2.")
    else:
        # Criar banco
        print(f"   🔄 Criando banco '{TARGET_DATABASE}' no destino…")
        create_app_workforce_db(dst_conn, args.dry_run)

        # Coletar e aplicar grants
        grants = get_app_workforce_grants(src_conn)
        print(
            f"\n   📋 {len(grants)} grant(s) encontrados na origem para '{TARGET_DATABASE}':")
        for g in grants:
            print(f"      • {g['privilege']} → {g['grantee']}")

        print(f"\n   🔄 Aplicando grants…")
        applied = apply_grants(dst_conn, grants, args.dry_run)
        print(f"\n   📊 Grants: {applied} aplicados")

    # =========================================================
    # VERIFICAÇÃO FINAL — estado atual no destino
    # =========================================================
    print("\n" + "=" * 70)
    print("🔍 VERIFICAÇÃO FINAL: ESTADO NO SERVIDOR DESTINO")
    print("=" * 70)

    cur = dst_conn.cursor()

    # --- Usuários alvo presentes no destino ---
    print("\n👥 Usuários alvo no destino:")
    cur.execute("""
        SELECT
            rolname,
            rolsuper,
            rolcreatedb,
            rolcreaterole,
            rolcanlogin,
            rolreplication
        FROM pg_roles
        WHERE rolname NOT LIKE 'pg_%%'
        ORDER BY rolname
    """)
    all_roles = {row[0]: row for row in cur.fetchall()}
    found = 0
    for rolname in sorted(all_roles):
        if not is_target_user(rolname):
            continue
        r = all_roles[rolname]
        flags = []
        if r[1]:
            flags.append("SUPERUSER")
        if r[2]:
            flags.append("CREATEDB")
        if r[3]:
            flags.append("CREATEROLE")
        if r[4]:
            flags.append("LOGIN")
        if r[5]:
            flags.append("REPLICATION")
        flag_str = ", ".join(flags) if flags else "NOLOGIN"
        print(f"   ✅ {rolname:<25} [{flag_str}]")
        found += 1
    if not found:
        print("   ⚠️  Nenhum usuário alvo encontrado no destino")

    # --- Banco app_workforce ---
    print(f"\n🗄️  Banco '{TARGET_DATABASE}' no destino:")
    cur.execute(
        "SELECT datname, pg_encoding_to_char(encoding), datcollate, pg_size_pretty(pg_database_size(datname)) "
        "FROM pg_database WHERE datname = %s",
        (TARGET_DATABASE,)
    )
    row = cur.fetchone()
    if row:
        print(f"   ✅ {row[0]}")
        print(f"      Encoding  : {row[1]}")
        print(f"      Collation : {row[2]}")
        print(f"      Tamanho   : {row[3]}")
    else:
        print(f"   ⚠️  Banco '{TARGET_DATABASE}' não encontrado no destino")

    # --- Grants do banco no destino ---
    print(f"\n🔑 Grants de '{TARGET_DATABASE}' no destino:")
    cur.execute("""
        SELECT
            grantee::regrole::text AS grantee,
            privilege_type
        FROM pg_database d,
             aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
        WHERE d.datname = %s
          AND grantee != 0
        ORDER BY grantee, privilege_type
    """, (TARGET_DATABASE,))
    grants_dest = cur.fetchall()
    SKIP = {"-", "postgres"}
    filtered = [(g, p) for g, p in grants_dest if g not in SKIP]
    if filtered:
        for grantee, privilege in filtered:
            print(f"   • {privilege:<12} → {grantee}")
    else:
        print("   (nenhum grant explícito além dos padrões)")

    cur.close()

    # =========================================================
    # Encerrar
    # =========================================================
    src_conn.close()
    dst_conn.close()

    print("\n" + "=" * 70)
    print("✅ Migração concluída" if not args.dry_run else "🧪 Dry-run concluído")
    print("=" * 70)


if __name__ == "__main__":
    main()
