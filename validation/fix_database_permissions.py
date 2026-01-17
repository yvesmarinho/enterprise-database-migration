#!/usr/bin/env python3
"""
Fix Database Permissions - PostgreSQL 18 wfdb02
Analisa e corrige permissões de um banco de dados específico.

Este script:
1. Solicita o nome do banco de dados (ou lê de arquivo JSON)
2. Identifica os usuários e tipos de permissão
3. Analisa permissões atuais
4. Corrige problemas de permissões automaticamente
5. Gera relatório detalhado

Tipos de permissão:
- admin: Todas as permissões + GRANT OPTION
- user: Todas as permissões CRUD (SELECT, INSERT, UPDATE, DELETE)
- readonly: Apenas SELECT

Exemplo de uso:
  python3 fix_database_permissions.py
  python3 fix_database_permissions.py --config permissions_config.json
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

# ============================================================================
# CONFIGURAÇÃO E CREDENCIAIS
# ============================================================================

COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "magenta": "\033[95m",
}


def colorize(text: str, color: str) -> str:
    """Adiciona cor ao texto"""
    return f"{COLORS[color]}{text}{COLORS['reset']}"


def load_permissions_config(config_file: str) -> Dict[str, Any]:
    """Carrega configuração de permissões de um arquivo JSON

    Formato esperado:
    {
        "database": "nome_do_banco",
        "users": [
            {
                "username": "user1",
                "permission_type": "admin|user|readonly",
                "description": "opcional"
            }
        ]
    }
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Validar estrutura
        if 'database' not in config:
            raise ValueError("Campo 'database' obrigatório no JSON")
        if 'users' not in config or not isinstance(config['users'], list):
            raise ValueError("Campo 'users' deve ser uma lista")

        # Validar cada usuário
        valid_types = ['admin', 'user', 'readonly']
        for user in config['users']:
            if 'username' not in user:
                raise ValueError(
                    "Campo 'username' obrigatório para cada usuário")
            if 'permission_type' not in user:
                raise ValueError(
                    f"Campo 'permission_type' obrigatório para usuário {user['username']}")
            if user['permission_type'] not in valid_types:
                raise ValueError(
                    f"permission_type '{user['permission_type']}' inválido. "
                    f"Use: {', '.join(valid_types)}"
                )

        print(
            f"{colorize('[✓]', 'green')} Configuração carregada: {config_file}")
        print(f"  Database: {colorize(config['database'], 'cyan')}")
        print(f"  Usuários: {colorize(str(len(config['users'])), 'cyan')}")

        return config

    except FileNotFoundError:
        print(
            f"{colorize('[✗]', 'red')} Arquivo não encontrado: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{colorize('[✗]', 'red')} Erro ao parsear JSON: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"{colorize('[✗]', 'red')} Configuração inválida: {e}")
        sys.exit(1)


def load_admin_credentials() -> Dict[str, Any]:
    """Carrega credenciais do migration_user (admin)"""
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
        }
    except Exception as e:
        raise ValueError(f"Erro ao ler credenciais de admin: {e}")


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class UserPermissions:
    """Permissões de um usuário"""
    username: str
    exists: bool
    can_login: bool
    is_superuser: bool
    connect_privilege: bool
    usage_on_schema: bool
    tables_with_select: int
    tables_with_insert: int
    tables_with_update: int
    tables_with_delete: int
    total_tables: int
    missing_permissions: List[str]


@dataclass
class DatabaseInfo:
    """Informações do banco de dados"""
    name: str
    exists: bool
    owner: str
    encoding: str
    tablespace: str
    size: str
    total_tables: int
    total_schemas: int


@dataclass
class PermissionFix:
    """Registro de correção aplicada"""
    username: str
    action: str
    sql_command: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class AnalysisReport:
    """Relatório completo da análise"""
    timestamp: str
    database_name: str
    database_info: Optional[DatabaseInfo]
    expected_users: List[str]
    user_permissions: Dict[str, UserPermissions]
    fixes_applied: List[PermissionFix]
    summary: str


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

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
    creds: Dict[str, str], database: str = "postgres"
) -> str:
    """Constrói string de conexão PostgreSQL"""
    return (
        f"postgresql://{creds['user']}:{creds['password']}"
        f"@{creds['host']}:{creds['port']}/{database}"
    )


# ============================================================================
# FUNÇÕES DE ANÁLISE
# ============================================================================

def check_database_exists(session: Session, db_name: str) -> bool:
    """Verifica se banco de dados existe"""
    try:
        result = session.execute(
            text("SELECT datname FROM pg_database WHERE datname = :db"),
            {"db": db_name}
        )
        return result.scalar() is not None
    except Exception as e:
        print(f"{colorize('[ERROR]', 'red')} Erro ao verificar banco: {e}")
        return False


def get_database_info(session: Session, db_name: str) -> Optional[DatabaseInfo]:
    """Obtém informações detalhadas do banco de dados"""
    try:
        result = session.execute(text("""
            SELECT
                d.datname as name,
                pg_get_userbyid(d.datdba) as owner,
                pg_encoding_to_char(d.encoding) as encoding,
                t.spcname as tablespace,
                pg_size_pretty(pg_database_size(d.datname)) as size
            FROM pg_database d
            LEFT JOIN pg_tablespace t ON d.dattablespace = t.oid
            WHERE d.datname = :db
        """), {"db": db_name})

        row = result.fetchone()
        if row:
            return DatabaseInfo(
                name=row[0],
                exists=True,
                owner=row[1],
                encoding=row[2],
                tablespace=row[3] or "pg_default",
                size=row[4],
                total_tables=0,  # Será preenchido depois
                total_schemas=0  # Será preenchido depois
            )
        return None
    except Exception as e:
        print(f"{colorize('[ERROR]', 'red')} Erro ao obter info do banco: {e}")
        return None


def check_user_exists(session: Session, username: str) -> bool:
    """Verifica se usuário existe"""
    try:
        result = session.execute(
            text("SELECT rolname FROM pg_roles WHERE rolname = :user"),
            {"user": username}
        )
        return result.scalar() is not None
    except Exception as e:
        print(f"{colorize('[ERROR]', 'red')} Erro ao verificar usuário: {e}")
        return False


def get_user_basic_info(session: Session, username: str) -> Dict[str, Any]:
    """Obtém informações básicas do usuário"""
    try:
        result = session.execute(text("""
            SELECT
                rolname,
                rolcanlogin,
                rolsuper
            FROM pg_roles
            WHERE rolname = :user
        """), {"user": username})

        row = result.fetchone()
        if row:
            return {
                "exists": True,
                "can_login": row[1],
                "is_superuser": row[2],
            }
        return {"exists": False, "can_login": False, "is_superuser": False}
    except Exception as e:
        print(
            f"{colorize('[ERROR]', 'red')} Erro ao obter info do usuário: {e}")
        return {"exists": False, "can_login": False, "is_superuser": False}


def check_connect_privilege(
    session: Session, username: str, db_name: str
) -> bool:
    """Verifica se usuário tem privilégio CONNECT no banco"""
    try:
        result = session.execute(text("""
            SELECT has_database_privilege(:user, :db, 'CONNECT')
        """), {"user": username, "db": db_name})
        return result.scalar() or False
    except Exception as e:
        print(f"{colorize('[ERROR]', 'red')} Erro ao verificar CONNECT: {e}")
        return False


def check_schema_usage(
    session: Session, username: str, schema: str = "public"
) -> bool:
    """Verifica se usuário tem USAGE no schema"""
    try:
        result = session.execute(text("""
            SELECT has_schema_privilege(:user, :schema, 'USAGE')
        """), {"user": username, "schema": schema})
        return result.scalar() or False
    except Exception as e:
        print(f"{colorize('[ERROR]', 'red')} Erro ao verificar USAGE: {e}")
        return False


def count_table_permissions(
    session: Session, username: str, db_name: str, permission: str
) -> int:
    """Conta quantas tabelas o usuário tem determinada permissão

    IMPORTANTE: session deve estar conectada ao banco de dados correto (db_name)
    """
    try:
        # Contar permissões iterando pelas tabelas ao invés de usar subquery
        result = session.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tableowner != 'postgres'
            ORDER BY tablename
        """))

        tables = [row[0] for row in result.fetchall()]
        count = 0

        for table in tables:
            try:
                has_perm = session.execute(text("""
                    SELECT has_table_privilege(:user, :table_ref, :perm)
                """), {
                    "user": username,
                    "table_ref": f"public.{table}",
                    "perm": permission.upper()
                }).scalar()

                if has_perm:
                    count += 1
            except Exception as e:
                # Ignorar erros em tabelas específicas e continuar
                continue

        return count
    except Exception as e:
        print(f"{colorize('[ERROR]', 'red')} Erro ao contar permissões: {e}")
        return 0


def get_total_tables(session: Session, db_name: str) -> int:
    """Obtém total de tabelas no schema public (excluindo apenas tabelas de sistema pg_*)"""
    try:
        result = session.execute(text("""
            SELECT COUNT(*)
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename NOT LIKE 'pg_%'
        """))
        return result.scalar() or 0
    except Exception as e:
        print(f"{colorize('[ERROR]', 'red')} Erro ao contar tabelas: {e}")
        return 0


def analyze_user_permissions(
    session: Session, username: str, db_name: str, total_tables: int,
    permission_type: Optional[str] = None
) -> UserPermissions:
    """Analisa permissões completas de um usuário

    IMPORTANTE: session deve estar conectada ao banco de dados correto (db_name)
    para que has_table_privilege funcione corretamente.

    Args:
        permission_type: Tipo explícito de permissão ('admin', 'user', 'readonly').
                        Se None, será detectado pelo nome do usuário.
    """

    basic_info = get_user_basic_info(session, username)

    if not basic_info["exists"]:
        return UserPermissions(
            username=username,
            exists=False,
            can_login=False,
            is_superuser=False,
            connect_privilege=False,
            usage_on_schema=False,
            tables_with_select=0,
            tables_with_insert=0,
            tables_with_update=0,
            tables_with_delete=0,
            total_tables=total_tables,
            missing_permissions=["USER_NOT_EXISTS"],
        )

    connect_priv = check_connect_privilege(session, username, db_name)
    usage_priv = check_schema_usage(session, username, "public")

    # Contar permissões por tipo
    select_count = count_table_permissions(
        session, username, db_name, "SELECT")
    insert_count = count_table_permissions(
        session, username, db_name, "INSERT")
    update_count = count_table_permissions(
        session, username, db_name, "UPDATE")
    delete_count = count_table_permissions(
        session, username, db_name, "DELETE")

    # Identificar permissões faltando
    missing = []
    if not connect_priv:
        missing.append("CONNECT")
    if not usage_priv:
        missing.append("USAGE_ON_SCHEMA")

    # Determinar tipo de usuário (usar explícito se fornecido, senão detectar por nome)
    if permission_type:
        is_readonly = permission_type == "readonly"
        is_admin = permission_type == "admin"
    else:
        is_readonly = username.endswith("_readonly") or username.endswith(
            "_viewer") or "readonly" in username.lower() or "viewer" in username.lower()
        is_admin = username.endswith("_admin") or "admin" in username.lower()

    if is_readonly:
        # Usuário readonly precisa apenas SELECT
        if select_count < total_tables:
            missing.append("SELECT_ON_TABLES")
    else:
        # Usuário normal precisa todas as permissões
        if select_count < total_tables:
            missing.append("SELECT_ON_TABLES")
        if insert_count < total_tables:
            missing.append("INSERT_ON_TABLES")
        if update_count < total_tables:
            missing.append("UPDATE_ON_TABLES")
        if delete_count < total_tables:
            missing.append("DELETE_ON_TABLES")
        if delete_count < total_tables:
            missing.append("DELETE_ON_TABLES")

    return UserPermissions(
        username=username,
        exists=True,
        can_login=basic_info["can_login"],
        is_superuser=basic_info["is_superuser"],
        connect_privilege=connect_priv,
        usage_on_schema=usage_priv,
        tables_with_select=select_count,
        tables_with_insert=insert_count,
        tables_with_update=update_count,
        tables_with_delete=delete_count,
        total_tables=total_tables,
        missing_permissions=missing,
    )


# ============================================================================
# FUNÇÕES DE CORREÇÃO
# ============================================================================

def create_user_if_not_exists(
    session: Session, username: str, password: str = None
) -> PermissionFix:
    """Cria usuário se não existir"""

    if password is None:
        # Gerar senha temporária
        import secrets
        password = secrets.token_urlsafe(16)

    sql = f"CREATE USER {username} WITH PASSWORD '{password}' LOGIN"

    try:
        session.execute(text(sql))
        session.commit()

        print(
            f"{colorize('[✓]', 'green')} Usuário {username} criado com sucesso")
        print(f"    Senha temporária: {colorize(password, 'yellow')}")
        print(f"    {colorize('IMPORTANTE: Salve esta senha!', 'red')}")

        return PermissionFix(
            username=username,
            action="CREATE_USER",
            sql_command=sql.replace(password, "***"),
            success=True,
        )
    except Exception as e:
        session.rollback()
        print(f"{colorize('[✗]', 'red')} Erro ao criar usuário: {e}")
        return PermissionFix(
            username=username,
            action="CREATE_USER",
            sql_command=sql.replace(password, "***"),
            success=False,
            error_message=str(e),
        )


def grant_connect_privilege(
    session: Session, username: str, db_name: str
) -> PermissionFix:
    """Concede privilégio CONNECT no banco"""

    sql = f"GRANT CONNECT ON DATABASE {db_name} TO {username}"

    try:
        session.execute(text(sql))
        session.commit()
        print(f"{colorize('[✓]', 'green')} CONNECT concedido para {username}")

        return PermissionFix(
            username=username,
            action="GRANT_CONNECT",
            sql_command=sql,
            success=True,
        )
    except Exception as e:
        session.rollback()
        print(f"{colorize('[✗]', 'red')} Erro ao conceder CONNECT: {e}")
        return PermissionFix(
            username=username,
            action="GRANT_CONNECT",
            sql_command=sql,
            success=False,
            error_message=str(e),
        )


def grant_schema_usage(
    session: Session, username: str, schema: str = "public"
) -> PermissionFix:
    """Concede USAGE no schema"""

    sql = f"GRANT USAGE ON SCHEMA {schema} TO {username}"

    try:
        session.execute(text(sql))
        session.commit()
        print(
            f"{colorize('[✓]', 'green')} USAGE no schema concedido para {username}")

        return PermissionFix(
            username=username,
            action="GRANT_USAGE",
            sql_command=sql,
            success=True,
        )
    except Exception as e:
        session.rollback()
        print(f"{colorize('[✗]', 'red')} Erro ao conceder USAGE: {e}")
        return PermissionFix(
            username=username,
            action="GRANT_USAGE",
            sql_command=sql,
            success=False,
            error_message=str(e),
        )


def grant_table_permissions(
    session: Session, username: str, permissions: List[str], schema: str = "public"
) -> PermissionFix:
    """Concede permissões em todas as tabelas"""

    perms_str = ", ".join(permissions)
    sql = f"GRANT {perms_str} ON ALL TABLES IN SCHEMA {schema} TO {username}"

    try:
        session.execute(text(sql))
        session.commit()
        print(
            f"{colorize('[✓]', 'green')} {perms_str} concedido para {username}")

        return PermissionFix(
            username=username,
            action=f"GRANT_{perms_str}",
            sql_command=sql,
            success=True,
        )
    except Exception as e:
        session.rollback()
        print(f"{colorize('[✗]', 'red')} Erro ao conceder {perms_str}: {e}")
        return PermissionFix(
            username=username,
            action=f"GRANT_{perms_str}",
            sql_command=sql,
            success=False,
            error_message=str(e),
        )


def grant_default_privileges(
    session: Session, username: str, permissions: List[str], schema: str = "public"
) -> PermissionFix:
    """Concede privilégios padrão para futuras tabelas"""

    perms_str = ", ".join(permissions)
    sql = f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT {perms_str} ON TABLES TO {username}"

    try:
        session.execute(text(sql))
        session.commit()
        print(
            f"{colorize('[✓]', 'green')} Privilégios padrão configurados para {username}")

        return PermissionFix(
            username=username,
            action=f"ALTER_DEFAULT_PRIVILEGES_{perms_str}",
            sql_command=sql,
            success=True,
        )
    except Exception as e:
        session.rollback()
        print(
            f"{colorize('[✗]', 'red')} Erro ao configurar privilégios padrão: {e}")
        return PermissionFix(
            username=username,
            action=f"ALTER_DEFAULT_PRIVILEGES_{perms_str}",
            sql_command=sql,
            success=False,
            error_message=str(e),
        )


def grant_admin_privileges(
    session: Session, username: str, db_name: str, schema: str = "public"
) -> List[PermissionFix]:
    """Concede permissões administrativas completas (ALL PRIVILEGES com GRANT OPTION)"""

    fixes = []

    # 1. ALL PRIVILEGES em todas as tabelas com GRANT OPTION
    sql_tables = f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema} TO {username} WITH GRANT OPTION"
    try:
        session.execute(text(sql_tables))
        session.commit()
        print(
            f"{colorize('[✓]', 'green')} ALL PRIVILEGES em tabelas concedido para {username} (com GRANT OPTION)")
        fixes.append(PermissionFix(
            username=username,
            action="GRANT_ALL_TABLES_WITH_GRANT_OPTION",
            sql_command=sql_tables,
            success=True,
        ))
    except Exception as e:
        session.rollback()
        print(f"{colorize('[✗]', 'red')} Erro ao conceder ALL em tabelas: {e}")
        fixes.append(PermissionFix(
            username=username,
            action="GRANT_ALL_TABLES_WITH_GRANT_OPTION",
            sql_command=sql_tables,
            success=False,
            error_message=str(e),
        ))

    # 2. ALL PRIVILEGES em sequences com GRANT OPTION
    sql_sequences = f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {schema} TO {username} WITH GRANT OPTION"
    try:
        session.execute(text(sql_sequences))
        session.commit()
        print(
            f"{colorize('[✓]', 'green')} ALL PRIVILEGES em sequences concedido para {username}")
        fixes.append(PermissionFix(
            username=username,
            action="GRANT_ALL_SEQUENCES_WITH_GRANT_OPTION",
            sql_command=sql_sequences,
            success=True,
        ))
    except Exception as e:
        session.rollback()
        print(
            f"{colorize('[✗]', 'red')} Erro ao conceder ALL em sequences: {e}")
        fixes.append(PermissionFix(
            username=username,
            action="GRANT_ALL_SEQUENCES_WITH_GRANT_OPTION",
            sql_command=sql_sequences,
            success=False,
            error_message=str(e),
        ))

    # 3. ALL PRIVILEGES em functions com GRANT OPTION
    sql_functions = f"GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA {schema} TO {username} WITH GRANT OPTION"
    try:
        session.execute(text(sql_functions))
        session.commit()
        print(
            f"{colorize('[✓]', 'green')} ALL PRIVILEGES em functions concedido para {username}")
        fixes.append(PermissionFix(
            username=username,
            action="GRANT_ALL_FUNCTIONS_WITH_GRANT_OPTION",
            sql_command=sql_functions,
            success=True,
        ))
    except Exception as e:
        session.rollback()
        print(
            f"{colorize('[✗]', 'red')} Erro ao conceder ALL em functions: {e}")
        fixes.append(PermissionFix(
            username=username,
            action="GRANT_ALL_FUNCTIONS_WITH_GRANT_OPTION",
            sql_command=sql_functions,
            success=False,
            error_message=str(e),
        ))

    # 4. CREATE no schema
    sql_create_schema = f"GRANT CREATE ON SCHEMA {schema} TO {username}"
    try:
        session.execute(text(sql_create_schema))
        session.commit()
        print(
            f"{colorize('[✓]', 'green')} CREATE no schema concedido para {username}")
        fixes.append(PermissionFix(
            username=username,
            action="GRANT_CREATE_ON_SCHEMA",
            sql_command=sql_create_schema,
            success=True,
        ))
    except Exception as e:
        session.rollback()
        print(
            f"{colorize('[✗]', 'red')} Erro ao conceder CREATE no schema: {e}")
        fixes.append(PermissionFix(
            username=username,
            action="GRANT_CREATE_ON_SCHEMA",
            sql_command=sql_create_schema,
            success=False,
            error_message=str(e),
        ))

    # 5. ALTER DEFAULT PRIVILEGES com GRANT OPTION
    sql_default = f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT ALL PRIVILEGES ON TABLES TO {username} WITH GRANT OPTION"
    try:
        session.execute(text(sql_default))
        session.commit()
        print(
            f"{colorize('[✓]', 'green')} Privilégios padrão administrativos configurados para {username}")
        fixes.append(PermissionFix(
            username=username,
            action="ALTER_DEFAULT_PRIVILEGES_ALL_WITH_GRANT_OPTION",
            sql_command=sql_default,
            success=True,
        ))
    except Exception as e:
        session.rollback()
        print(
            f"{colorize('[✗]', 'red')} Erro ao configurar privilégios padrão: {e}")
        fixes.append(PermissionFix(
            username=username,
            action="ALTER_DEFAULT_PRIVILEGES_ALL_WITH_GRANT_OPTION",
            sql_command=sql_default,
            success=False,
            error_message=str(e),
        ))

    return fixes


def fix_user_permissions(
    session: Session,
    username: str,
    db_name: str,
    permissions: UserPermissions,
    auto_fix: bool = True,
) -> List[PermissionFix]:
    """Corrige permissões de um usuário"""

    fixes = []

    if not permissions.exists:
        print(f"\n{colorize('⚠', 'yellow')} Usuário {username} não existe")
        if auto_fix:
            fix = create_user_if_not_exists(session, username)
            fixes.append(fix)
            if not fix.success:
                return fixes
        else:
            print(
                f"  Execute: CREATE USER {username} WITH PASSWORD '...' LOGIN")
            return fixes

    # Corrigir CONNECT
    if "CONNECT" in permissions.missing_permissions:
        print(f"\n{colorize('⚠', 'yellow')} Falta privilégio CONNECT")
        if auto_fix:
            fixes.append(grant_connect_privilege(session, username, db_name))
        else:
            print(
                f"  Execute: GRANT CONNECT ON DATABASE {db_name} TO {username}")

    # Corrigir USAGE
    if "USAGE_ON_SCHEMA" in permissions.missing_permissions:
        print(f"\n{colorize('⚠', 'yellow')} Falta privilégio USAGE no schema")
        if auto_fix:
            fixes.append(grant_schema_usage(session, username))
        else:
            print(f"  Execute: GRANT USAGE ON SCHEMA public TO {username}")

    # Determinar permissões de tabela necessárias
    # Usuários admin precisam de permissões totais com GRANT OPTION
    is_admin = username.endswith("_admin") or "admin" in username.lower()
    # Usuários readonly/viewer precisam apenas SELECT
    is_readonly = username.endswith("_readonly") or username.endswith(
        "_viewer") or "readonly" in username.lower() or "viewer" in username.lower()

    if is_admin:
        # Usuário admin precisa de ALL PRIVILEGES com GRANT OPTION
        print(
            f"\n{colorize('⚠', 'yellow')} Aplicando permissões administrativas completas")
        if auto_fix:
            admin_fixes = grant_admin_privileges(session, username, db_name)
            fixes.extend(admin_fixes)
        else:
            print(f"  Execute os seguintes comandos:")
            print(
                f"    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {username} WITH GRANT OPTION;")
            print(
                f"    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {username} WITH GRANT OPTION;")
            print(
                f"    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {username} WITH GRANT OPTION;")
            print(f"    GRANT CREATE ON SCHEMA public TO {username};")
            print(
                f"    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO {username} WITH GRANT OPTION;")
    elif is_readonly:
        # Usuário readonly precisa apenas SELECT
        if "SELECT_ON_TABLES" in permissions.missing_permissions:
            print(f"\n{colorize('⚠', 'yellow')} Falta SELECT em tabelas")
            if auto_fix:
                fixes.append(grant_table_permissions(
                    session, username, ["SELECT"]))
                fixes.append(grant_default_privileges(
                    session, username, ["SELECT"]))
            else:
                print(
                    f"  Execute: GRANT SELECT ON ALL TABLES IN SCHEMA public TO {username}")
    else:
        # Usuário normal precisa todas as permissões
        missing_perms = []
        if "SELECT_ON_TABLES" in permissions.missing_permissions:
            missing_perms.append("SELECT")
        if "INSERT_ON_TABLES" in permissions.missing_permissions:
            missing_perms.append("INSERT")
        if "UPDATE_ON_TABLES" in permissions.missing_permissions:
            missing_perms.append("UPDATE")
        if "DELETE_ON_TABLES" in permissions.missing_permissions:
            missing_perms.append("DELETE")

        if missing_perms:
            print(
                f"\n{colorize('⚠', 'yellow')} Falta permissões: {', '.join(missing_perms)}")
            if auto_fix:
                fixes.append(grant_table_permissions(
                    session, username, missing_perms))
                fixes.append(grant_default_privileges(
                    session, username, missing_perms))
            else:
                perms_str = ", ".join(missing_perms)
                print(
                    f"  Execute: GRANT {perms_str} ON ALL TABLES IN SCHEMA public TO {username}")

    return fixes


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def analyze_and_fix_database(
    db_name: str, auto_fix: bool = True, create_users: bool = False,
    custom_users: List[str] = None, user_types: Dict[str, str] = None
) -> AnalysisReport:
    """Analisa e corrige permissões de um banco de dados

    Args:
        user_types: Dicionário mapeando username -> permission_type ('admin', 'user', 'readonly')
    """

    print_header(f"ANÁLISE E CORREÇÃO DE PERMISSÕES - {db_name}")

    report = AnalysisReport(
        timestamp=datetime.now().isoformat(),
        database_name=db_name,
        database_info=None,
        expected_users=[],
        user_permissions={},
        fixes_applied=[],
        summary="",
    )

    try:
        # Carregar credenciais admin
        admin_creds = load_admin_credentials()

        # Conectar ao postgres como admin
        print_section("1. Conectando ao PostgreSQL")
        conn_str = build_connection_string(admin_creds, "postgres")
        engine = create_engine(
            conn_str,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )

        with Session(engine) as session:
            print(
                f"{colorize('[✓]', 'green')} Conectado como {admin_creds['user']}")

            # Verificar se banco existe
            print_section(f"2. Verificando banco de dados '{db_name}'")

            if not check_database_exists(session, db_name):
                print(
                    f"{colorize('[✗]', 'red')} Banco de dados '{db_name}' não existe!")
                report.summary = f"Banco de dados '{db_name}' não encontrado"
                return report

            db_info = get_database_info(session, db_name)
            if db_info:
                print(f"{colorize('[✓]', 'green')} Banco encontrado")
                print(f"  Owner: {colorize(db_info.owner, 'cyan')}")
                print(f"  Encoding: {colorize(db_info.encoding, 'cyan')}")
                print(f"  Tablespace: {colorize(db_info.tablespace, 'cyan')}")
                print(f"  Tamanho: {colorize(db_info.size, 'yellow')}")

                # Contar tabelas
                total_tables = get_total_tables(session, db_name)
                db_info.total_tables = total_tables
                print(
                    f"  Tabelas (public): {colorize(str(total_tables), 'cyan')}")

                report.database_info = db_info
            else:
                print(
                    f"{colorize('[✗]', 'red')} Erro ao obter informações do banco")
                report.summary = "Erro ao obter informações do banco"
                return report

            # Identificar usuários esperados
            print_section("3. Identificando usuários esperados")

            if custom_users:
                expected_users = custom_users
            else:
                expected_users = [
                    f"{db_name}_user",
                    f"{db_name}_readonly",
                ]
            report.expected_users = expected_users

            for user in expected_users:
                exists = check_user_exists(session, user)
                status = colorize(
                    "✓", "green") if exists else colorize("✗", "red")
                print(f"  {status} {user}")

            # Analisar permissões de cada usuário
            print_section("4. Analisando permissões dos usuários")

        # Reconectar ao banco de dados correto para análise de permissões
        conn_str_db = build_connection_string(admin_creds, db_name)
        engine_db = create_engine(
            conn_str_db,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10},
        )

        with Session(engine_db) as session_db:
            for username in expected_users:
                print(f"\n{colorize(f'Analisando: {username}', 'cyan')}")

                # Obter permission_type do dict se fornecido
                perm_type = user_types.get(username) if user_types else None

                perms = analyze_user_permissions(
                    session_db, username, db_name, total_tables, perm_type
                )
                report.user_permissions[username] = perms

                if not perms.exists:
                    print(f"  {colorize('[✗]', 'red')} Usuário não existe")
                else:
                    print(f"  {colorize('[✓]', 'green')} Usuário existe")
                    print(
                        f"    Can Login: {colorize(str(perms.can_login), 'cyan')}")
                    print(
                        f"    CONNECT: {colorize(str(perms.connect_privilege), 'green' if perms.connect_privilege else 'red')}")
                    print(
                        f"    USAGE: {colorize(str(perms.usage_on_schema), 'green' if perms.usage_on_schema else 'red')}")
                    print(f"    SELECT: {colorize(f'{perms.tables_with_select}/{total_tables}',
                          'green' if perms.tables_with_select == total_tables else 'yellow')}")

                    # Identificar tipo de usuário (usar perm_type se fornecido)
                    if perm_type:
                        is_admin = perm_type == "admin"
                        is_readonly = perm_type == "readonly"
                    else:
                        is_admin = username.endswith(
                            "_admin") or "admin" in username.lower()
                        is_readonly = username.endswith("_readonly") or username.endswith(
                            "_viewer") or "readonly" in username.lower() or "viewer" in username.lower()

                    # Mostrar permissões adicionais apenas para usuários não-readonly
                    if not is_readonly:
                        print(f"    INSERT: {colorize(f'{perms.tables_with_insert}/{total_tables}',
                              'green' if perms.tables_with_insert == total_tables else 'yellow')}")
                        print(f"    UPDATE: {colorize(f'{perms.tables_with_update}/{total_tables}',
                              'green' if perms.tables_with_update == total_tables else 'yellow')}")
                        print(f"    DELETE: {colorize(f'{perms.tables_with_delete}/{total_tables}',
                              'green' if perms.tables_with_delete == total_tables else 'yellow')}")

                    # Indicar tipo de usuário
                    if is_admin:
                        print(
                            f"    {colorize('Tipo: ADMIN (permissões totais esperadas)', 'magenta')}")
                    elif is_readonly:
                        print(
                            f"    {colorize('Tipo: READONLY/VIEWER (apenas SELECT)', 'cyan')}")
                    else:
                        print(
                            f"    {colorize('Tipo: USUÁRIO NORMAL (CRUD completo)', 'cyan')}")

                if perms.missing_permissions:
                    print(
                        f"  {colorize('Problemas:', 'red')} {', '.join(perms.missing_permissions)}")

        # Aplicar correções (conectar novamente ao banco correto)
        with Session(engine_db) as session_db:
            # Aplicar correções
            if auto_fix:
                print_section("5. Aplicando correções")

                for username in expected_users:
                    perms = report.user_permissions[username]

                    if perms.missing_permissions:
                        print(
                            f"\n{colorize(f'Corrigindo: {username}', 'yellow')}")

                        # Se usuário não existe e create_users=False, pular
                        if not perms.exists and not create_users:
                            print(
                                f"  {colorize('[SKIP]', 'yellow')} Criação de usuário desabilitada")
                            continue

                        fixes = fix_user_permissions(
                            session_db, username, db_name, perms, auto_fix=True
                        )
                        report.fixes_applied.extend(fixes)
                    else:
                        print(
                            f"\n{colorize(f'✓ {username}', 'green')} - Sem problemas")

            else:
                print_section("5. Recomendações (modo somente leitura)")
                print(f"{colorize('Execute as correções manualmente:', 'yellow')}")

                for username in expected_users:
                    perms = report.user_permissions[username]
                    if perms.missing_permissions:
                        print(f"\n{colorize(f'{username}:', 'cyan')}")
                        fix_user_permissions(
                            session_db, username, db_name, perms, auto_fix=False
                        )

        # Resumo
        total_fixes = len(report.fixes_applied)
        successful_fixes = sum(
            1 for f in report.fixes_applied if f.success)
        failed_fixes = total_fixes - successful_fixes

        report.summary = (
            f"Análise concluída. {total_fixes} correções aplicadas "
            f"({successful_fixes} sucesso, {failed_fixes} falhas)"
        )

    except OperationalError as e:
        print(f"{colorize('[✗ ERRO DE CONEXÃO]', 'red')}")
        print(f"Detalhes: {str(e)}")
        report.summary = f"Falha ao conectar: {str(e)}"

    except Exception as e:
        print(f"{colorize('[✗ ERRO]', 'red')}")
        print(f"Detalhes: {str(e)}")
        report.summary = f"Erro: {str(e)}"

    return report


def export_report(report: AnalysisReport, output_dir: str = "reports"):
    """Exporta relatório em JSON"""

    Path(output_dir).mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/fix_permissions_{report.database_name}_{timestamp}.json"

    # Converter dataclasses para dict
    data = {
        "timestamp": report.timestamp,
        "database_name": report.database_name,
        "database_info": asdict(report.database_info) if report.database_info else None,
        "expected_users": report.expected_users,
        "user_permissions": {
            k: asdict(v) for k, v in report.user_permissions.items()
        },
        "fixes_applied": [asdict(f) for f in report.fixes_applied],
        "summary": report.summary,
    }

    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n{colorize('[✓]', 'green')} Relatório exportado: {filename}")
        return filename
    except Exception as e:
        print(f"\n{colorize('[✗]', 'red')} Erro ao exportar: {e}")
        return None


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Função principal"""

    # Parsear argumentos de linha de comando
    parser = argparse.ArgumentParser(
        description='Analisa e corrige permissões de banco de dados PostgreSQL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  Modo interativo:
    python3 fix_database_permissions.py

  Com arquivo de configuração JSON:
    python3 fix_database_permissions.py --config permissions_config.json

  Com auto-fix:
    python3 fix_database_permissions.py --config permissions_config.json --auto-fix

  Com criação de usuários:
    python3 fix_database_permissions.py --config permissions_config.json --auto-fix --create-users
        """
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Arquivo JSON com configuração de permissões (database + users)'
    )
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='Aplicar correções automaticamente sem perguntar'
    )
    parser.add_argument(
        '--create-users',
        action='store_true',
        help='Criar usuários automaticamente se não existirem (requer --auto-fix)'
    )

    args = parser.parse_args()

    print_header("FIX DATABASE PERMISSIONS - PostgreSQL 18 wfdb02")

    # Modo configuração JSON
    if args.config:
        config = load_permissions_config(args.config)
        db_name = config['database']

        # Construir lista de usuários customizados com informação de tipo
        custom_users = [user['username'] for user in config['users']]

        # Construir dicionário de user_types
        user_types = {user['username']: user['permission_type']
                      for user in config['users']}

        # Aplicar auto-fix e create-users se especificados
        auto_fix = args.auto_fix
        create_users = args.create_users if args.auto_fix else False

        print(f"\n{colorize('Configuração carregada:', 'green')}")
        print(f"  Banco: {colorize(db_name, 'cyan')}")
        print(f"  Usuários: {colorize(str(len(custom_users)), 'cyan')}")
        for user_config in config['users']:
            perm_type = user_config['permission_type']
            username = user_config['username']
            color = 'magenta' if perm_type == 'admin' else 'green' if perm_type == 'user' else 'cyan'
            print(
                f"    {colorize('•', color)} {username} ({colorize(perm_type, color)})")

        print(
            f"\n  Auto-fix: {colorize('SIM' if auto_fix else 'NÃO', 'green' if auto_fix else 'yellow')}")
        print(
            f"  Criar usuários: {colorize('SIM' if create_users else 'NÃO', 'green' if create_users else 'yellow')}")

    # Modo interativo
    else:
        # Solicitar nome do banco
        print(f"{colorize('Digite o nome do banco de dados:', 'cyan')}")
        db_name = input("> ").strip()

        if not db_name:
            print(f"{colorize('[✗]', 'red')} Nome do banco é obrigatório!")
            sys.exit(1)

        # Sugerir usuários baseado no nome do banco
        suggested_users = [
            f"{db_name}_admin",
            f"{db_name}_user",
            f"{db_name}_readonly",
        ]

        print(
            f"\n{colorize('Usuários sugeridos para o banco', 'yellow')} {colorize(db_name, 'cyan')}:")
        print(
            f"  {colorize('•', 'magenta')} {suggested_users[0]} {colorize('(admin - permissões totais)', 'magenta')}")
        print(
            f"  {colorize('•', 'green')} {suggested_users[1]} {colorize('(user - CRUD completo)', 'green')}")
        print(
            f"  {colorize('•', 'cyan')} {suggested_users[2]} {colorize('(readonly - apenas SELECT)', 'cyan')}")

        # Solicitar usuários a analisar
        print(f"\n{colorize('Digite os nomes dos usuários a analisar:', 'cyan')}")
        print(
            f"{colorize('(Separados por vírgula para múltiplos usuários)', 'yellow')}")
        print(f"{colorize('(Enter para usar os usuários sugeridos)', 'yellow')}")
        users_input = input("> ").strip()

        if users_input:
            custom_users = [u.strip()
                            for u in users_input.split(",") if u.strip()]
            print(
                f"\n{colorize(f'Usuários selecionados: {len(custom_users)}', 'green')}")
            for u in custom_users:
                print(f"  - {colorize(u, 'cyan')}")
        else:
            custom_users = None
            print(f"\n{colorize('Usando usuários sugeridos', 'green')}")

        # No modo interativo, não temos user_types explícitos
        user_types = None

        # Perguntar sobre auto-fix
        print(f"\n{colorize('Aplicar correções automaticamente? (s/n):', 'cyan')}")
        auto_fix_input = input("> ").strip().lower()
        auto_fix = auto_fix_input in ["s", "sim", "y", "yes"]

        # Perguntar sobre criação de usuários
        create_users = False
        if auto_fix:
            print(
                f"\n{colorize('Criar usuários se não existirem? (s/n):', 'cyan')}")
            create_users_input = input("> ").strip().lower()
            create_users = create_users_input in ["s", "sim", "y", "yes"]

    # Executar análise e correção
    report = analyze_and_fix_database(
        db_name, auto_fix, create_users, custom_users, user_types)

    # Exportar relatório
    export_report(report)

    # Sumário final
    print_header("SUMÁRIO")
    print(f"Banco: {colorize(report.database_name, 'cyan')}")
    print(f"Status: {colorize(report.summary, 'yellow')}")

    if report.fixes_applied:
        successful = sum(1 for f in report.fixes_applied if f.success)
        failed = len(report.fixes_applied) - successful

        print(
            f"\nCorreções aplicadas: {colorize(str(len(report.fixes_applied)), 'cyan')}")
        print(f"  Sucesso: {colorize(str(successful), 'green')}")
        if failed > 0:
            print(f"  Falhas: {colorize(str(failed), 'red')}")

    print()


if __name__ == "__main__":
    main()
