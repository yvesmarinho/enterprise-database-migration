#!/usr/bin/env python3
"""
Diagnóstico de Permissões - PostgreSQL 18 wfdb02
Analisa permissões de usuários em bancos de dados PostgreSQL.

Possíveis causas de problemas:
1. Falta de permissão em schema (USAGE)
2. Tablespace com permissões restritivas
3. Permissões de tabela não herdadas corretamente
4. Problemas com roles/group memberships
5. Configurações de default_transaction_isolation ou similar
"""

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

# ============================================================================
# CARREGAMENTO DE CONFIGURAÇÃO
# ============================================================================


def load_admin_credentials() -> Dict[str, Any]:
    """Carrega credenciais do migration_user do arquivo de config"""
    config_file = Path(__file__).parent.parent / "secrets" / \
        "postgresql_destination_config.json"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {config_file}"
        )

    try:
        with open(config_file, "r") as f:
            config = json.load(f)

        auth = config.get("authentication", {})
        server = config.get("server", {})

        return {
            "user": auth.get("user", "migration_user"),
            "password": auth.get("password"),
            "host": server.get("host", "wfdb02.vya.digital"),
            "port": server.get("port", 5432),
            "database": "postgres"
        }
    except Exception as e:
        raise ValueError(f"Erro ao ler credenciais de migration_user: {e}")


def load_destination_config() -> Dict[str, Any]:
    """Carrega config do servidor destino"""
    config_file = Path(__file__).parent.parent / "secrets" / \
        "postgresql_destination_config.json"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {config_file}"
        )

    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        raise ValueError(f"Erro ao ler configuração: {e}")


# Carregar credenciais admin
try:
    ADMIN_CREDENTIALS = load_admin_credentials()
except Exception as e:
    print(f"ERRO ao carregar credenciais do admin: {e}")
    exit(1)

COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
}

# ============================================================================
# DATACLASSES PARA RESULTADOS
# ============================================================================


@dataclass
class PermissionIssue:
    """Representa um problema encontrado"""
    severity: str  # "CRITICAL", "WARNING", "INFO"
    category: str  # "SCHEMA", "TABLE", "TABLESPACE", "ROLE", "DEFAULT"
    description: str
    affected_item: str
    recommendation: str


@dataclass
class DiagnosisResult:
    """Resultado completo do diagnóstico"""
    timestamp: str
    user: str
    database: str
    server: str
    connected: bool
    role_info: Dict[str, Any]
    schema_permissions: Dict[str, Any]
    table_permissions: Dict[str, Any]
    tablespace_info: Dict[str, Any]
    issues: List[PermissionIssue]
    summary: str


# ============================================================================
# FUNÇÕES DE DIAGNÓSTICO
# ============================================================================

def colorize(text: str, color: str) -> str:
    """Adiciona cor ao texto"""
    return f"{COLORS[color]}{text}{COLORS['reset']}"


def print_header(title: str):
    """Imprime header formatado"""
    print(f"\n{colorize('=' * 80, 'cyan')}")
    print(f"{colorize(title, 'bold')}")
    print(f"{colorize('=' * 80, 'cyan')}\n")


def print_section(title: str):
    """Imprime seção formatada"""
    print(f"\n{colorize(f'➜ {title}', 'blue')}")
    print(f"{colorize('-' * 60, 'blue')}\n")


def build_connection_string(
    creds: Dict[str, str], database: str = None
) -> str:
    """Constrói string de conexão PostgreSQL"""
    db = database or creds.get("database", "postgres")
    return (
        f"postgresql://{creds['user']}:{creds['password']}"
        f"@{creds['host']}:{creds['port']}/{db}"
    )


def check_user_exists(session: Session, username: str) -> bool:
    """Verifica se usuário existe no PostgreSQL"""
    try:
        result = session.execute(
            text("SELECT usename FROM pg_user WHERE usename = :user"),
            {"user": username}
        )
        return result.scalar() is not None
    except Exception as e:
        print(
            f"{colorize('[ERROR]', 'red')} Não conseguiu verificar se usuário existe: {e}")
        return False


def get_role_info(session: Session, username: str) -> Dict[str, Any]:
    """Obtém informações da role do usuário"""
    try:
        # PostgreSQL 18: usar pg_roles ao invés de pg_user (mais compatível)
        result = session.execute(text("""
            SELECT
                rolname as username,
                rolsuper as is_superuser,
                rolcreatedb as can_create_db,
                rolcanlogin as can_login,
                rolinherit as inherits_permissions,
                oid as role_oid
            FROM pg_roles
            WHERE rolname = :user
        """), {"user": username})

        row = result.fetchone()
        if row:
            return {
                "username": row[0],
                "is_superuser": row[1],
                "can_create_db": row[2],
                "can_login": row[3],
                "inherits_permissions": row[4],
                "role_oid": row[5],
            }
        return {}
    except Exception as e:
        msg = f"Erro ao obter info da role: {e}"
        print(f"{colorize('[ERROR]', 'red')} {msg}")
        try:
            session.rollback()  # Recuperar de transaction abort
        except Exception:
            pass
        return {}


def get_role_memberships(
    session: Session, username: str
) -> List[Dict[str, Any]]:
    """Obtém memberships da role do usuário"""
    try:
        # Usar pg_roles ao invés de pg_authid (evita privilege denied)
        result = session.execute(text("""
            SELECT
                m.rolname as member_of,
                a.admin_option
            FROM pg_auth_members a
            JOIN pg_roles m ON m.oid = a.roleid
            JOIN pg_roles r ON r.oid = a.member
            WHERE r.rolname = :user
            ORDER BY m.rolname
        """), {"user": username})

        memberships = []
        for row in result.fetchall():
            memberships.append({
                "member_of": row[0],
                "admin_option": row[1],
            })
        return memberships
    except Exception as e:
        msg = f"Erro ao obter memberships: {e}"
        print(f"{colorize('[ERROR]', 'red')} {msg}")
        try:
            session.rollback()
        except Exception:
            pass
        return []


def get_schema_permissions(session: Session, username: str) -> Dict[str, Any]:
    """Analisa permissões em schemas"""
    try:
        result = session.execute(text("""
            SELECT
                n.nspname as schema_name,
                pg_catalog.array_to_string(
                    ARRAY(
                        SELECT (CASE WHEN aclitem::text LIKE '%' || :user || '%' THEN aclitem::text ELSE NULL END)
                        FROM (SELECT unnest(nspacl) as aclitem) AS a
                    ),
                    ', '
                ) as user_privileges,
                n.nspacl as all_privileges
            FROM pg_catalog.pg_namespace n
            ORDER BY n.nspname
        """), {"user": username})

        schemas = {}
        for row in result.fetchall():
            schema_name = row[0]
            user_privs = row[1]
            all_privs = row[2]

            schemas[schema_name] = {
                "has_privileges": user_privs is not None and user_privs != "",
                "user_privileges": user_privs or "NENHUMA",
                "all_privileges": str(all_privs) if all_privs else "NULL",
            }

        return schemas
    except Exception as e:
        print(
            f"{colorize('[ERROR]', 'red')} Erro ao obter permissões de schema: {e}")
        try:
            session.rollback()
        except Exception:
            pass
        return {}


def check_schema_usage(
    session: Session, username: str, schema: str = "public"
) -> bool:
    """Tenta fazer USAGE em um schema"""
    try:
        session.execute(text(f"SET search_path TO {schema}"))
        session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(
            f"{colorize('[WARNING]', 'yellow')} Não conseguiu fazer USAGE em schema '{schema}': {e}")
        try:
            session.rollback()
        except Exception:
            pass
        return False


def get_table_permissions(
    session: Session, username: str, schema: str = "public"
) -> Dict[str, Dict]:
    """Obtém permissões em tabelas de um schema"""
    try:
        result = session.execute(text("""
            SELECT
                t.tablename as table_name,
                CASE
                    WHEN pg_catalog.has_table_privilege(:user, :schema_name || '.' || t.tablename, 'SELECT')
                    THEN 'SELECT'
                    ELSE 'NO SELECT'
                END as select_perm,
                CASE
                    WHEN pg_catalog.has_table_privilege(:user, :schema_name || '.' || t.tablename, 'INSERT')
                    THEN 'INSERT'
                    ELSE 'NO INSERT'
                END as insert_perm,
                CASE
                    WHEN pg_catalog.has_table_privilege(:user, :schema_name || '.' || t.tablename, 'UPDATE')
                    THEN 'UPDATE'
                    ELSE 'NO UPDATE'
                END as update_perm,
                CASE
                    WHEN pg_catalog.has_table_privilege(:user, :schema_name || '.' || t.tablename, 'DELETE')
                    THEN 'DELETE'
                    ELSE 'NO DELETE'
                END as delete_perm
            FROM pg_tables t
            WHERE t.schemaname = :schema_name
            ORDER BY t.tablename
        """), {
            "user": username,
            "schema_name": schema
        })

        tables = {}
        for row in result.fetchall():
            table_name = row[0]
            tables[table_name] = {
                "select": "SELECT" in row[1],
                "insert": "INSERT" in row[2],
                "update": "UPDATE" in row[3],
                "delete": "DELETE" in row[4],
            }

        return tables
    except Exception as e:
        print(
            f"{colorize('[ERROR]', 'red')} Erro ao obter permissões de tabelas: {e}")
        try:
            session.rollback()
        except Exception:
            pass
        return {}


def get_tablespace_info(session: Session) -> Dict[str, Any]:
    """Obtém informações sobre tablespaces"""
    try:
        result = session.execute(text("""
            SELECT
                spcname as tablespace_name,
                pg_get_userbyid(spcowner) as owner,
                spcacl as acl
            FROM pg_tablespace
            ORDER BY spcname
        """))

        tablespaces = {}
        for row in result.fetchall():
            name = row[0]
            tablespaces[name] = {
                "owner": row[1],
                "acl": str(row[2]) if row[2] else "NULL",
            }

        return tablespaces
    except Exception as e:
        print(
            f"{colorize('[ERROR]', 'red')} Erro ao obter info de tablespaces: {e}")
        try:
            session.rollback()
        except Exception:
            pass
        return {}


def get_database_default_tablespace(
    session: Session, db_name: str
) -> Optional[str]:
    """Obtém tablespace padrão de um banco de dados"""
    try:
        result = session.execute(text("""
            SELECT spcname
            FROM pg_database
            JOIN pg_tablespace ON pg_database.dattablespace = pg_tablespace.oid
            WHERE datname = :db
        """), {"db": db_name})

        return result.scalar()
    except Exception as e:
        print(
            f"{colorize('[ERROR]', 'red')} Erro ao obter tablespace do BD: {e}")
        try:
            session.rollback()
        except Exception:
            pass
        return None


def analyze_issues(  # noqa: C901
    role_info: Dict[str, Any],
    schema_permissions: Dict[str, Any],
    table_permissions: Dict[str, Any],
    tablespace_info: Dict[str, Any],
    username: str = "target_user",
) -> List[PermissionIssue]:
    """Analisa e identifica problemas de permissão"""

    issues = []

    # Verificar se usuário existe e é não-superuser
    if not role_info:
        issues.append(PermissionIssue(
            severity="CRITICAL",
            category="ROLE",
            description=f"Usuário {username} não encontrado no PostgreSQL",
            affected_item=username,
            recommendation=f"Criar o usuário: CREATE USER {username} WITH PASSWORD '...'"
        ))
        return issues

    # Verificar permissão em schema public
    public_schema_perms = schema_permissions.get("public", {})
    if not public_schema_perms.get("has_privileges", False):
        issues.append(PermissionIssue(
            severity="CRITICAL",
            category="SCHEMA",
            description="Usuário não tem permissão USAGE no schema 'public'",
            affected_item="public schema",
            recommendation=f"Executar: GRANT USAGE ON SCHEMA public TO {username}"
        ))

    # Verificar se há tabelas mas sem permissão SELECT
    tables = table_permissions.get("public", {})
    if tables:
        no_select_tables = [
            t for t, perms in tables.items() if not perms.get("select")]
        if no_select_tables:
            issues.append(PermissionIssue(
                severity="CRITICAL",
                category="TABLE",
                description=f"Usuário não tem SELECT em {len(no_select_tables)} tabelas do schema public",
                affected_item=", ".join(
                    no_select_tables[:5]) + ("..." if len(no_select_tables) > 5 else ""),
                recommendation=f"Executar: GRANT SELECT ON ALL TABLES IN SCHEMA public TO {username}"
            ))

    # Verificar tablespaces
    for ts_name, ts_info in tablespace_info.items():
        if ts_name != "pg_default" and ts_name != "pg_global":
            if ts_info["acl"] == "NULL" or "=" not in ts_info["acl"]:
                issues.append(PermissionIssue(
                    severity="WARNING",
                    category="TABLESPACE",
                    description=f"Tablespace '{ts_name}' pode ter ACLs restritivas",
                    affected_item=ts_name,
                    recommendation=(
                        f"Verificar: SELECT * FROM pg_tablespace "
                        f"WHERE spcname = '{ts_name}'"
                    )
                ))

    return issues


def run_diagnostic(  # noqa: C901
    username: str,
    database_name: str = "postgres",
    test_databases: List[str] = None,
) -> DiagnosisResult:
    """Executa diagnóstico completo - usa usuário admin para análise

    Args:
        username: Nome do usuário a ser analisado
        database_name: Nome do banco para análise inicial (padrão: postgres)
        test_databases: Lista de bancos para testar conexão do usuário
    """

    print_header(f"DIAGNÓSTICO DE PERMISSÕES - {username}")
    print(f"Usuário alvo: {colorize(username, 'yellow')}")
    print(f"Banco principal: {colorize(database_name, 'yellow')}")
    print(f"Analisador: {colorize(ADMIN_CREDENTIALS['user'], 'cyan')}")
    host = ADMIN_CREDENTIALS['host']
    print(f"Host: {colorize(host, 'yellow')}\n")

    if test_databases is None:
        test_databases = []

    result = DiagnosisResult(
        timestamp=datetime.now().isoformat(),
        user=username,
        database=database_name,
        server=ADMIN_CREDENTIALS['host'],
        connected=False,
        role_info={},
        schema_permissions={},
        table_permissions={},
        tablespace_info={},
        issues=[],
        summary=""
    )

    # Conectar como admin
    print_section("1. Conectando ao PostgreSQL (usuário admin)")

    try:
        # Usar ADMIN_CREDENTIALS para análise
        conn_str = build_connection_string(ADMIN_CREDENTIALS)
        print(
            f"Conectando como: {colorize(ADMIN_CREDENTIALS['user'], 'cyan')}")

        engine = create_engine(
            conn_str,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )

        with Session(engine) as session:
            result.connected = True
            print(
                f"{colorize('[✓]', 'green')} Conectado como {ADMIN_CREDENTIALS['user']}")

            # Verificar se usuário existe
            print_section(f"2. Verificando Role do Usuário ({username})")

            role_info = get_role_info(session, username)
            result.role_info = role_info

            if role_info:
                print(f"Username: {colorize(role_info['username'], 'cyan')}")
                print(
                    f"Superuser: {colorize(str(role_info['is_superuser']), 'yellow' if role_info['is_superuser'] else 'green')}")
                print(
                    f"Can Create DB: {colorize(str(role_info['can_create_db']), 'cyan')}")
                print(
                    f"Can Login: {colorize(str(role_info['can_login']), 'cyan')}")
                print(
                    f"Inherits Permissions: {colorize(str(role_info['inherits_permissions']), 'cyan')}")
                print(
                    f"Role OID: {colorize(str(role_info['role_oid']), 'cyan')}")

                # Memberships
                print_section("2.1 Memberships da Role")
                memberships = get_role_memberships(session, username)
                if memberships:
                    for mem in memberships:
                        print(
                            f"  └─ {colorize(mem['member_of'], 'cyan')} (admin: {mem['admin_option']})")
                else:
                    print(f"{colorize('(nenhum membership encontrado)', 'yellow')}")
            else:
                print(
                    f"{colorize('[✗]', 'red')} Usuário {username} não encontrado!")

            # Permissões em Schemas
            print_section("3. Permissões em Schemas")

            schema_perms = get_schema_permissions(session, username)
            result.schema_permissions = schema_perms

            for schema, perms in sorted(schema_perms.items()):
                status = colorize(
                    "✓", "green") if perms["has_privileges"] else colorize("✗", "red")
                print(f"{status} {schema:30} → {perms['user_privileges']}")

            # Permissões em Tabelas
            print_section("4. Permissões em Tabelas (schema 'public')")

            # Primeiro verificar se consegue fazer USAGE no schema
            can_use_schema = check_schema_usage(session, username, "public")

            if can_use_schema:
                table_perms = get_table_permissions(
                    session, username, "public")
                result.table_permissions = {"public": table_perms}

                if table_perms:
                    print(
                        f"Total de tabelas: {colorize(str(len(table_perms)), 'cyan')}\n")

                    select_ok = sum(
                        1 for p in table_perms.values() if p.get("select"))
                    print(f"  Tabelas com SELECT: {colorize(f'{select_ok}/{len(table_perms)}',
                          'green' if select_ok == len(table_perms) else 'yellow')}")

                    # Listar tabelas sem SELECT
                    no_select = [t for t, p in table_perms.items()
                                 if not p.get("select")]
                    if no_select:
                        print(f"\n{colorize('  Tabelas SEM SELECT:', 'red')}")
                        for table in no_select[:10]:
                            print(f"    └─ {table}")
                        if len(no_select) > 10:
                            extra = len(no_select) - 10
                            print(f"    └─ ... e mais {extra}")
                else:
                    print(f"{colorize('(nenhuma tabela encontrada)', 'yellow')}")
            else:
                print(
                    f"{colorize('[✗]', 'red')} Não conseguiu fazer USAGE no schema public")
                print(f"    Isso impede visualização das tabelas")

            # Informações de Tablespaces
            print_section("5. Informações de Tablespaces")

            tablespaces = get_tablespace_info(session)
            result.tablespace_info = tablespaces

            for ts_name, ts_info in sorted(tablespaces.items()):
                print(f"  {colorize(ts_name, 'cyan')}")
                print(f"    Owner: {ts_info['owner']}")
                print(f"    ACL: {ts_info['acl']}")

            # Default tablespace da database
            default_ts = get_database_default_tablespace(
                session, database_name)
            print(
                f"\n  Default Tablespace da DB: {colorize(default_ts or 'pg_default', 'yellow')}")

            # Analisar problemas
            print_section("6. Análise de Problemas")

            issues = analyze_issues(
                role_info,
                schema_perms,
                {"public": table_perms} if can_use_schema else {},
                tablespaces,
                username
            )
            result.issues = issues

            if issues:
                print(
                    f"Encontrados {colorize(str(len(issues)), 'red')} problemas:\n")

                for i, issue in enumerate(issues, 1):
                    severity_color = {
                        "CRITICAL": "red",
                        "WARNING": "yellow",
                        "INFO": "cyan"
                    }.get(issue.severity, "cyan")

                    print(
                        f"{i}. [{colorize(issue.severity, severity_color)}] {issue.category}")
                    print(f"   Descrição: {issue.description}")
                    print(f"   Afetado: {issue.affected_item}")
                    print(
                        f"   Recomendação: {colorize(issue.recommendation, 'green')}\n")
            else:
                msg = "Nenhum problema encontrado!"
                print(f"{colorize(f'✓ {msg}', 'green')}")

            # Sumarizando
            result.summary = (
                f"Diagnóstico completo com {len(issues)} "
                f"problema(s) identificado(s)"
            )

            # Testar conexão do usuário em bancos específicos
            if test_databases:
                for idx, test_db in enumerate(test_databases, start=7):
                    print_section(
                        f"{idx}. Testando {username} no banco {test_db}")
                    test_database_connection(username, test_db)

    except OperationalError as e:
        result.connected = False
        print(f"{colorize('[✗ ERRO DE CONEXÃO]', 'red')}")
        print(f"Detalhes: {str(e)}")
        result.summary = f"Falha ao conectar: {str(e)}"
        return result

    except Exception as e:
        print(f"{colorize('[✗ ERRO GERAL]', 'red')}")
        print(f"Detalhes: {str(e)}")
        result.summary = f"Erro durante diagnóstico: {str(e)}"
        return result

    return result


def test_database_connection(username: str, database_name: str):
    """Testa conexão de um usuário a um banco específico"""
    try:
        # Construir credenciais para teste (sem senha, apenas para verificar acesso)
        print(f"Conectando como {colorize(username, 'yellow')} "
              f"ao banco {colorize(database_name, 'cyan')}\n")

        # Nota: Este teste requer que o usuário tenha credenciais configuradas
        # ou usa o admin para verificar as permissões
        conn_str = build_connection_string(ADMIN_CREDENTIALS, database_name)

        test_engine = create_engine(
            conn_str,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )

        with Session(test_engine) as test_session:
            # Verificar se usuário tem CONNECT no banco
            has_connect = test_session.execute(text("""
                SELECT has_database_privilege(:user, :db, 'CONNECT')
            """), {"user": username, "db": database_name}).scalar()

            if not has_connect:
                print(
                    f"{colorize('[✗]', 'red')} Usuário não tem CONNECT no banco")
                return

            print(f"{colorize('[✓]', 'green')} Usuário tem CONNECT no banco")

            # Listar tabelas do schema public
            list_tables_query = text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
                LIMIT 5
            """)

            try:
                test_result = test_session.execute(list_tables_query)
                tables = test_result.fetchall()

                if tables:
                    print(
                        f"{colorize('[✓]', 'green')} Conseguiu listar tabelas!")
                    print(f"  Primeiras 5 tabelas:")
                    for table in tables:
                        # Verificar permissão SELECT
                        has_select = test_session.execute(text("""
                            SELECT has_table_privilege(:user, :schema || '.' || :table, 'SELECT')
                        """), {"user": username, "schema": "public", "table": table[0]}).scalar()

                        status = colorize(
                            "✓", "green") if has_select else colorize("✗", "red")
                        print(f"    {status} {colorize(table[0], 'cyan')}")
                else:
                    print(
                        f"{colorize('[!]', 'yellow')} Nenhuma tabela encontrada")

            except Exception as e:
                print(f"{colorize('[✗]', 'red')} Erro ao listar tabelas")
                print(f"  Detalhes: {str(e)}")

    except Exception as e:
        print(
            f"{colorize('[✗]', 'red')} Erro ao conectar ao banco {database_name}")
        print(f"  Detalhes: {str(e)}")


def export_results(
    result: DiagnosisResult, filename: Optional[str] = None
):
    """Exporta resultados em JSON"""

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diagnosis_{result.user}_{timestamp}.json"

    filepath = f"reports/{filename}"

    # Converter issues para dict
    issues_dict = [asdict(issue) for issue in result.issues]

    data = {
        "timestamp": result.timestamp,
        "user": result.user,
        "database": result.database,
        "server": result.server,
        "connected": result.connected,
        "role_info": result.role_info,
        "schema_permissions": result.schema_permissions,
        "table_permissions": result.table_permissions,
        "tablespace_info": result.tablespace_info,
        "issues": issues_dict,
        "summary": result.summary,
    }

    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(
            f"\n{colorize('[✓]', 'green')} Resultados exportados para: {filepath}")
        return filepath
    except Exception as e:
        print(f"\n{colorize('[✗]', 'red')} Erro ao exportar: {e}")
        return None


# ============================================================================
# RECOMENDAÇÕES SQL
# ============================================================================

def print_sql_recommendations(
    issues: List[PermissionIssue], username: str = "target_user"
):
    """Imprime comandos SQL recomendados

    Args:
        issues: Lista de problemas encontrados
        username: Nome do usuário para o qual gerar recomendações
    """

    sql_commands = []

    for issue in issues:
        if "SCHEMA" in issue.category:
            sql_commands.append("-- Conceder USAGE no schema")
            sql_commands.append(
                f"GRANT USAGE ON SCHEMA public TO {username};")

        if "TABLE" in issue.category:
            sql_commands.append("-- Conceder SELECT em tabelas")
            sql_commands.append(
                f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {username};")
            sql_commands.append("-- Para futuras tabelas")
            sql_commands.append(
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {username};")

    if sql_commands:
        next_section = 7 + len(issues)
        print_section(f"{next_section}. Comandos SQL Recomendados")
        print("Execute os seguintes comandos como superuser (postgres):\n")

        for cmd in sql_commands:
            print(colorize(cmd, "cyan"))

        print(
            f"\nNota: Execute em um terminal conectado como {colorize('postgres', 'yellow')}")


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def suggest_users_from_database(database_name: str) -> List[str]:
    """Sugere possíveis usuários baseado no nome do banco de dados

    Padrão: <database_name>_user, <database_name>_readonly
    """
    base_name = database_name.replace("_db", "").replace("-", "_")
    return [
        f"{base_name}_user",
        f"{base_name}_readonly",
    ]


def get_all_database_users() -> List[str]:
    """Lista todos os usuários não-superuser do PostgreSQL"""
    try:
        conn_str = build_connection_string(ADMIN_CREDENTIALS)
        engine = create_engine(
            conn_str,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )

        with Session(engine) as session:
            result = session.execute(text("""
                SELECT rolname
                FROM pg_roles
                WHERE rolcanlogin = true
                AND rolsuper = false
                AND rolname NOT IN ('postgres', 'replication')
                ORDER BY rolname
            """))

            users = [row[0] for row in result.fetchall()]
            return users
    except Exception as e:
        print(
            f"{colorize('[WARN]', 'yellow')} Não foi possível listar usuários: {e}")
        return []


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Função principal interativa"""

    print_header("DIAGNÓSTICO DE PERMISSÕES - PostgreSQL")

    # Solicitar nome do(s) usuário(s)
    print(f"{colorize('Digite o(s) nome(s) do(s) usuário(s) a analisar:', 'cyan')}")
    print(f"{colorize('(Separados por vírgula para múltiplos usuários)', 'yellow')}")
    print(f"{colorize('Exemplos:', 'yellow')}")
    print(f"  - metabase_user")
    print(f"  - metabase_user, metabase_readonly")
    print(f"  - journey_user, journey_readonly, analytics_user")
    usernames_input = input("> ").strip()

    if not usernames_input:
        print(f"{colorize('[✗]', 'red')} Nome do usuário é obrigatório!")
        sys.exit(1)

    # Processar múltiplos usuários
    usernames = [u.strip() for u in usernames_input.split(",") if u.strip()]

    print(f"\n{colorize(f'Usuários a analisar: {len(usernames)}', 'green')}")
    for u in usernames:
        print(f"  - {colorize(u, 'cyan')}")

    # Solicitar nome do banco (opcional)
    print(
        f"\n{colorize('Digite o nome do banco principal (Enter para postgres):', 'cyan')}")
    database = input("> ").strip() or "postgres"

    # Perguntar sobre bancos adicionais para teste
    print(
        f"\n{colorize('Deseja testar acesso a bancos específicos? (s/n):', 'cyan')}")
    test_dbs_input = input("> ").strip().lower()

    test_databases = []
    if test_dbs_input in ["s", "sim", "y", "yes"]:
        print(
            f"{colorize('Digite os nomes dos bancos separados por vírgula:', 'cyan')}")
        dbs_input = input("> ").strip()
        if dbs_input:
            test_databases = [db.strip()
                              for db in dbs_input.split(",") if db.strip()]

    # Executar diagnóstico para cada usuário
    all_results = []
    for idx, username in enumerate(usernames, 1):
        print(f"\n{colorize('=' * 80, 'magenta')}")
        print(
            f"{colorize(f'ANALISANDO USUÁRIO {idx}/{len(usernames)}: {username}', 'bold')}")
        print(f"{colorize('=' * 80, 'magenta')}")

        result = run_diagnostic(username, database, test_databases)
        all_results.append(result)

        # Imprimir recomendações SQL
        if result.issues:
            print_sql_recommendations(result.issues, username)

        # Exportar resultados individuais
        filepath = export_results(result)

    # Sumário final consolidado
    print_header("DIAGNÓSTICO CONSOLIDADO - TODOS OS USUÁRIOS")
    print(f"Banco principal: {colorize(database, 'cyan')}")
    print(
        f"Total de usuários analisados: {colorize(str(len(all_results)), 'yellow')}\n")

    for result in all_results:
        status_color = 'green' if len(result.issues) == 0 else (
            'yellow' if len(result.issues) <= 3 else 'red')
        print(
            f"  {colorize('●', status_color)} {colorize(result.user, 'cyan'):30} → {result.summary}")
    print(
        f"Conectado: {colorize(str(result.connected), 'green' if result.connected else 'red')}")
    if filepath:
        print(f"Resultados: {colorize(filepath, 'yellow')}\n")


if __name__ == "__main__":
    main()
