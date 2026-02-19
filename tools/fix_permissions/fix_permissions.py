#!/usr/bin/env python3
"""
Fix Permissions — PostgreSQL Permission Fixer
=============================================

Corrige ownership, grants e privilégios padrão em bancos PostgreSQL
de forma declarativa, guiado por um arquivo JSON de operações.

A conexão com o servidor é fornecida por um arquivo de credenciais
em secrets/ (mesmo formato usado pelo migrate_users).

Uso:
    python3 tools/fix_permissions/fix_permissions.py \
        --server  postgresql_destination_config.json \
        --config  fix_permissions.json \
        --database metabase_db \
        --dry-run

    # Modo interativo (pede os arquivos ao executar)
    python3 tools/fix_permissions/fix_permissions.py --dry-run

    # Processar todos os bancos do config
    python3 tools/fix_permissions/fix_permissions.py \
        --server wfdb02_source_config.json \
        --config fix_permissions.json \
        --all --execute

    # Listar configs e servidores disponíveis
    python3 tools/fix_permissions/fix_permissions.py --list-configs
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ psycopg2 não encontrado. Execute: pip install psycopg2-binary")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Caminhos base
# ---------------------------------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parent.parent.parent
SECRETS_DIR = BASE_DIR / "secrets"
TOOLS_DIR   = BASE_DIR / "tools" / "fix_permissions"


def _resolve_path(value: str, fallback_dirs: list) -> Path:
    """Aceita caminho absoluto, relativo ao cwd, nome de arquivo (busca nos fallback_dirs)."""
    p = Path(value)
    if p.is_absolute() or p.exists():
        return p.resolve()
    for d in fallback_dirs:
        candidate = d / p.name
        if candidate.exists():
            return candidate.resolve()
    return p.resolve()


def list_available_files() -> None:
    print(f"\n📁 Servidores disponíveis em '{SECRETS_DIR.relative_to(BASE_DIR)}':\n")
    for p in sorted(SECRETS_DIR.glob("*.json")):
        print(f"   • {p.name}")

    print(f"\n📁 Configs de operações disponíveis em '{TOOLS_DIR.relative_to(BASE_DIR)}':\n")
    for p in sorted(TOOLS_DIR.glob("*.json")):
        print(f"   • {p.name}")
    print()


# ---------------------------------------------------------------------------
# Carregamento de configs
# ---------------------------------------------------------------------------
def load_server_config(path: Path) -> dict:
    if not path.exists():
        print(f"❌ Arquivo de servidor não encontrado: {path}")
        print("   Use --list-configs para ver os disponíveis.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_operations_config(path: Path) -> dict:
    if not path.exists():
        print(f"❌ Arquivo de operações não encontrado: {path}")
        print("   Use --list-configs para ver os disponíveis.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_dsn(server_cfg: dict) -> dict:
    """Monta os parâmetros de conexão a partir dos formatos source ou destiny."""
    # Formato "source" (wfdb02_source_config.json)
    if "possible_users" in server_cfg:
        return dict(
            host=server_cfg["host"],
            port=int(server_cfg["port"]),
            dbname=server_cfg.get("database", "postgres"),
            user=server_cfg["possible_users"][0]["username"],
            password=server_cfg["possible_users"][0]["password"],
            sslmode=server_cfg.get("ssl_mode", "prefer"),
            connect_timeout=10,
        )
    # Formato "destiny" (home016_destiny_config / postgresql_destination_config)
    srv  = server_cfg.get("server", {})
    auth = server_cfg.get("authentication", {})
    conn = server_cfg.get("connection_settings", {})
    return dict(
        host=srv.get("host_ip", srv.get("host", server_cfg.get("host", "localhost"))),
        port=int(srv.get("port", server_cfg.get("port", 5432))),
        dbname="postgres",
        user=auth.get("user", server_cfg.get("user", "postgres")),
        password=auth.get("password", server_cfg.get("password", "")),
        sslmode=srv.get("ssl_mode", server_cfg.get("ssl_mode", "prefer")),
        connect_timeout=conn.get("connection_timeout", 30),
    )


# ---------------------------------------------------------------------------
# Executor de SQL
# ---------------------------------------------------------------------------
def run_sql(conn, sql: str, params=None, dry_run: bool = False) -> bool:
    if dry_run:
        preview = sql.replace("\n", " ").strip()[:110]
        print(f"   [DRY-RUN] {preview}")
        return True
    try:
        cur = conn.cursor()
        cur.execute(sql, params) if params else cur.execute(sql)
        cur.close()
        return True
    except Exception as e:
        print(f"   ❌ Erro SQL: {e}")
        print(f"      SQL: {sql.strip()[:120]}")
        return False


# ---------------------------------------------------------------------------
# Operações
# ---------------------------------------------------------------------------
def op_transfer_ownership(conn, op: dict, dry_run: bool) -> int:
    target   = op["target"]          # tables | sequences | views
    from_usr = op.get("from_user", "")
    to_usr   = op["to_user"]

    queries = {
        "tables":    ("SELECT tablename     FROM pg_tables    WHERE schemaname='public'"
                      + (" AND tableowner=%s"    if from_usr else ""),
                      "ALTER TABLE    public.{obj} OWNER TO {to}"),
        "sequences": ("SELECT sequencename  FROM pg_sequences WHERE schemaname='public'"
                      + (" AND sequenceowner=%s" if from_usr else ""),
                      "ALTER SEQUENCE public.{obj} OWNER TO {to}"),
        "views":     ("SELECT viewname      FROM pg_views     WHERE schemaname='public'",
                      "ALTER VIEW     public.{obj} OWNER TO {to}"),
    }

    if target not in queries:
        print(f"   ⚠️  Tipo desconhecido para transfer_ownership: {target}")
        return 0

    list_sql, alter_tpl = queries[target]
    cur = conn.cursor()
    cur.execute(list_sql, (from_usr,) if from_usr and target != "views" else ())
    objects = [row[0] for row in cur.fetchall()]
    cur.close()

    count = 0
    for obj in objects:
        sql = alter_tpl.format(obj=obj, to=to_usr) + ";"
        if run_sql(conn, sql, dry_run=dry_run):
            count += 1

    print(f"   ✅ transfer_ownership({target}): {count} objeto(s) → {to_usr}")
    return count


def op_grant_privileges(conn, op: dict, dry_run: bool) -> bool:
    privs  = ", ".join(op["privileges"])
    target = op["target"]
    user   = op["user"]

    if target == "database":
        sql = f'GRANT {privs} ON DATABASE "{op["database"]}" TO "{user}";'
    elif target == "schema":
        sql = f'GRANT {privs} ON SCHEMA {op["schema"]} TO "{user}";'
    elif target == "all_tables":
        sql = f'GRANT {privs} ON ALL TABLES IN SCHEMA {op["schema"]} TO "{user}";'
    elif target == "all_sequences":
        sql = f'GRANT {privs} ON ALL SEQUENCES IN SCHEMA {op["schema"]} TO "{user}";'
    else:
        print(f"   ⚠️  Alvo desconhecido para grant_privileges: {target}")
        return False

    ok = run_sql(conn, sql, dry_run=dry_run)
    if ok and not dry_run:
        print(f"   ✅ GRANT {privs} ON {target} TO {user}")
    return ok


def op_set_default_privileges(conn, op: dict, dry_run: bool) -> bool:
    privs  = ", ".join(op["privileges"])
    target = op["target"].upper()
    schema = op["schema"]
    user   = op["user"]

    sql = (f'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} '
           f'GRANT {privs} ON {target} TO "{user}";')
    ok = run_sql(conn, sql, dry_run=dry_run)
    if ok and not dry_run:
        print(f"   ✅ DEFAULT PRIVILEGES {privs} ON {target} TO {user}")
    return ok


# ---------------------------------------------------------------------------
# Processamento de um banco
# ---------------------------------------------------------------------------
def process_database(db_cfg: dict, dsn_base: dict, dry_run: bool, verbose: bool) -> bool:
    db_name = db_cfg["name"]
    owner   = db_cfg.get("owner", "")
    ops     = db_cfg.get("operations", [])

    print(f"\n{'='*70}")
    print(f"🗄️  {db_name}  —  {db_cfg.get('description', '')}")
    if owner:
        print(f"   Owner esperado : {owner}")
    print(f"   Operações      : {len(ops)}")
    print(f"   Modo           : {'DRY-RUN' if dry_run else 'EXECUÇÃO'}")
    print(f"{'='*70}")

    dsn = {**dsn_base, "dbname": db_name}
    try:
        conn = psycopg2.connect(**dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print(f"   🔌 Conectado a '{db_name}'")
    except Exception as e:
        print(f"   ❌ Não foi possível conectar ao banco '{db_name}': {e}")
        return False

    # Verificar owner existe
    if owner:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (owner,))
        if not cur.fetchone():
            print(f"   ⚠️  Usuário '{owner}' não existe — operações podem falhar")
        else:
            print(f"   ✅ Usuário '{owner}' confirmado")
        cur.close()

    success = errors = 0
    for idx, op in enumerate(ops, 1):
        op_type = op.get("type", "?")
        if verbose:
            print(f"\n   [{idx}/{len(ops)}] {op_type}")

        if op_type == "transfer_ownership":
            ok = op_transfer_ownership(conn, op, dry_run) >= 0
        elif op_type == "grant_privileges":
            ok = op_grant_privileges(conn, op, dry_run)
        elif op_type == "set_default_privileges":
            ok = op_set_default_privileges(conn, op, dry_run)
        else:
            print(f"   ⚠️  Operação desconhecida: {op_type}")
            ok = False

        success += ok
        errors  += not ok

    # Verificação final
    if not dry_run:
        print(f"\n   🔍 Estado atual de '{db_name}':")
        cur = conn.cursor()

        cur.execute("""
            SELECT tableowner, COUNT(*) AS n
            FROM pg_tables WHERE schemaname = 'public'
            GROUP BY tableowner ORDER BY n DESC
        """)
        rows = cur.fetchall()
        if rows:
            for row_owner, count in rows:
                mark = "✅" if row_owner == owner else "•"
                print(f"      {mark} {count} tabela(s) com owner: {row_owner}")
        else:
            print("      (sem tabelas em public)")

        if owner:
            cur.execute("""
                SELECT COUNT(DISTINCT table_name)
                FROM information_schema.table_privileges
                WHERE table_schema = 'public' AND grantee = %s
            """, (owner,))
            priv_count = cur.fetchone()[0]
            mark = "✅" if priv_count > 0 else "⚠️ "
            print(f"      {mark} {owner} tem privilégios em {priv_count} tabela(s)")

        cur.close()

    conn.close()
    print(f"\n   📊 {success}/{len(ops)} operações OK | {errors} erros")
    return errors == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Fix Permissions — corrige ownership e grants em bancos PostgreSQL",
    )
    parser.add_argument("--server",   metavar="ARQUIVO",
                        help="JSON de credenciais do servidor (nome em secrets/ ou caminho)")
    parser.add_argument("--config",   metavar="ARQUIVO",
                        help="JSON de operações (nome em tools/fix_permissions/ ou caminho)")
    parser.add_argument("--database", metavar="NOME",
                        help="Banco específico a processar")
    parser.add_argument("--all",      action="store_true",
                        help="Processar todos os bancos definidos no config")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Simula sem aplicar alterações")
    parser.add_argument("--execute",  action="store_true",
                        help="Aplica as alterações de fato")
    parser.add_argument("--verbose",  action="store_true",
                        help="Log detalhado de cada operação")
    parser.add_argument("--list-configs", action="store_true",
                        help="Lista arquivos disponíveis em secrets/ e tools/fix_permissions/")
    args = parser.parse_args()

    if args.list_configs:
        list_available_files()
        sys.exit(0)

    if args.execute and args.dry_run:
        parser.error("Use --execute OU --dry-run, não ambos.")

    dry_run = not args.execute   # padrão seguro: dry-run quando --execute omitido

    # ---- Solicitar interativamente se ausente ----
    if not args.server or not args.config:
        list_available_files()
    if not args.server:
        args.server = input("🔵 Nome/caminho do JSON do SERVIDOR  : ").strip()
    if not args.config:
        args.config = input("🟢 Nome/caminho do JSON de OPERAÇÕES : ").strip()
    if not args.database and not args.all:
        resp = input("📦 Banco específico (ou Enter para todos) : ").strip()
        if resp:
            args.database = resp
        else:
            args.all = True

    server_path = _resolve_path(args.server, [SECRETS_DIR])
    config_path = _resolve_path(args.config, [TOOLS_DIR, SECRETS_DIR])

    print("=" * 70)
    print("🔧 Fix Permissions — PostgreSQL Permission Fixer")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📂 Servidor  : {server_path.name}")
    print(f"📂 Operações : {config_path.name}")
    print(f"{'🧪 DRY-RUN ATIVO — nenhuma alteração será feita' if dry_run else '🔴 MODO REAL — alterações serão aplicadas'}")
    print("=" * 70)

    server_cfg = load_server_config(server_path)
    ops_cfg    = load_operations_config(config_path)
    dsn_base   = build_dsn(server_cfg)

    print("\n🔌 Testando conexão com o servidor…")
    try:
        test = psycopg2.connect(**dsn_base)
        test.close()
        print("   ✅ Conectado")
    except Exception as e:
        print(f"   ❌ Falha: {e}")
        sys.exit(1)

    databases = ops_cfg.get("databases", [])
    if not databases:
        print("❌ Nenhum banco definido no arquivo de operações.")
        sys.exit(1)

    # Selecionar bancos a processar
    if args.all:
        targets = databases
    elif args.database:
        targets = [db for db in databases if db["name"] == args.database]
        if not targets:
            names = [db["name"] for db in databases]
            print(f"❌ Banco '{args.database}' não encontrado. Disponíveis: {', '.join(names)}")
            sys.exit(1)
    else:
        print("\n📦 Bancos disponíveis no config:")
        for i, db in enumerate(databases, 1):
            print(f"   [{i}] {db['name']}  —  {db.get('description', '')}")
        choice = input("\nEscolha o número (ou Enter para todos): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(databases):
            targets = [databases[int(choice) - 1]]
        else:
            targets = databases

    ok_count = 0
    for db_cfg in targets:
        if process_database(db_cfg, dsn_base, dry_run, args.verbose):
            ok_count += 1

    print("\n" + "=" * 70)
    print(f"{'🧪 Dry-run concluído' if dry_run else '✅ Execução concluída'}"
          f"  —  {ok_count}/{len(targets)} banco(s) sem erros")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
