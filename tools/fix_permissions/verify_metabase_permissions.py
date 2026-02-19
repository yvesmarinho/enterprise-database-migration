#!/usr/bin/env python3
"""
Script universal para verificar permissões PostgreSQL (READ-ONLY)
Não modifica nenhum dado, apenas verifica o estado atual

Características:
- Suporta parâmetros CLI ou arquivo de configuração JSON
- Verifica permissões de usuários específicos
- Analisa ownership de tabelas e schemas
- Lista privilégios detalhados
- Identifica tabelas críticas

Autor: Sistema de Migração Enterprise
Data: 28/01/2026
Python: 3.11+
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError


class PostgreSQLPermissionVerifier:
    """Verificador de permissões PostgreSQL (somente leitura)."""

    def __init__(self, host: str, port: int, database: str, admin_user: str, admin_password: str):
        """
        Inicializa o verificador.

        Args:
            host: Hostname do servidor PostgreSQL
            port: Porta do servidor
            database: Nome da database a verificar
            admin_user: Usuário com permissão de leitura
            admin_password: Senha do usuário
        """
        self.host = host
        self.port = port
        self.database = database
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.engine: Optional[Engine] = None

    def connect(self) -> bool:
        """Conecta ao servidor PostgreSQL."""
        try:
            conn_str = (
                f"postgresql://{self.admin_user}:{self.admin_password}"
                f"@{self.host}:{self.port}/{self.database}"
            )

            self.engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 30}
            )

            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Conectado ao PostgreSQL: {version[:50]}...")
                print(f"   Database: {self.database}")
                print()

            return True

        except (OperationalError, SQLAlchemyError) as e:
            print(f"❌ Erro ao conectar: {e}")
            return False

    def verify_user_exists(self, username: str) -> bool:
        """Verifica se um usuário existe."""
        query = text("""
            SELECT
                usename,
                usesuper,
                usecreatedb,
                usebypassrls
            FROM pg_user
            WHERE usename = :username
        """)

        print(f"1. VERIFICANDO USUÁRIO: {username}")
        print("-" * 80)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {"username": username})
                user_info = result.fetchone()

                if user_info:
                    print(f"✓ Usuário existe: {user_info[0]}")
                    print(f"  - Superuser: {'Sim' if user_info[1] else 'Não'}")
                    print(f"  - CreateDB: {'Sim' if user_info[2] else 'Não'}")
                    print(
                        f"  - Bypass RLS: {'Sim' if user_info[3] else 'Não'}")
                    print()
                    return True
                else:
                    print(f"✗ Usuário '{username}' NÃO EXISTE")
                    print()
                    return False

        except SQLAlchemyError as e:
            print(f"❌ Erro ao verificar usuário: {e}")
            print()
            return False

    def check_table_ownership(self, schema: str = 'public') -> Dict[str, int]:
        """Verifica ownership das tabelas."""
        query = text("""
            SELECT
                tablename,
                tableowner
            FROM pg_tables
            WHERE schemaname = :schema
            ORDER BY tablename
        """)

        print(f"2. OWNERSHIP DAS TABELAS (schema: {schema}):")
        print("-" * 80)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {"schema": schema})
                tables = result.fetchall()

                if not tables:
                    print(
                        f"  ⚠️  Nenhuma tabela encontrada no schema '{schema}'")
                    print()
                    return {}

                owners_count = {}
                for table_name, owner in tables:
                    owners_count[owner] = owners_count.get(owner, 0) + 1
                    if len(tables) <= 30:
                        print(f"  {table_name:50} → {owner}")

                print()
                print("Resumo de Owners:")
                for owner, count in sorted(owners_count.items()):
                    print(f"  {owner}: {count} tabelas")
                print(f"\nTotal de tabelas: {len(tables)}")
                print()

                return owners_count

        except SQLAlchemyError as e:
            print(f"❌ Erro ao verificar ownership: {e}")
            print()
            return {}

    def check_user_privileges(self, username: str, schema: str = 'public') -> List[tuple]:
        """Verifica privilégios de um usuário nas tabelas."""
        query = text("""
            SELECT
                table_name,
                string_agg(privilege_type, ', ' ORDER BY privilege_type) as privileges
            FROM information_schema.table_privileges
            WHERE grantee = :username
            AND table_schema = :schema
            GROUP BY table_name
            ORDER BY table_name
        """)

        print(
            f"3. PRIVILÉGIOS DO USUÁRIO '{username}' NAS TABELAS (schema: {schema}):")
        print("-" * 80)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    query, {"username": username, "schema": schema})
                privileges = result.fetchall()

                if privileges:
                    if len(privileges) <= 20:
                        for table_name, privs in privileges:
                            print(f"  {table_name:50} → {privs}")
                    else:
                        print(
                            f"  Total de tabelas com privilégios: {len(privileges)}")
                        print("  Primeiras 10 tabelas:")
                        for table_name, privs in privileges[:10]:
                            print(f"    {table_name:50} → {privs}")
                else:
                    print(
                        f"  ✗ NENHUM PRIVILÉGIO ENCONTRADO para '{username}' no schema '{schema}'")

                print()
                return privileges

        except SQLAlchemyError as e:
            print(f"❌ Erro ao verificar privilégios: {e}")
            print()
            return []

    def check_database_privileges(self, username: str) -> Dict[str, bool]:
        """Verifica privilégios do usuário na database."""
        query = text("""
            SELECT
                datname,
                has_database_privilege(:username, datname, 'CONNECT') as can_connect,
                has_database_privilege(:username, datname, 'CREATE') as can_create,
                has_database_privilege(:username, datname, 'TEMP') as can_temp
            FROM pg_database
            WHERE datname = :database
        """)

        print(f"4. PRIVILÉGIOS DO USUÁRIO '{username}' NA DATABASE:")
        print("-" * 80)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"username": username, "database": self.database}
                )
                db_privs = result.fetchone()

                if db_privs:
                    print(f"  Database: {db_privs[0]}")
                    print(
                        f"  - CONNECT: {'✓ Sim' if db_privs[1] else '✗ Não'}")
                    print(f"  - CREATE: {'✓ Sim' if db_privs[2] else '✗ Não'}")
                    print(f"  - TEMP: {'✓ Sim' if db_privs[3] else '✗ Não'}")

                    privs = {
                        'connect': db_privs[1],
                        'create': db_privs[2],
                        'temp': db_privs[3]
                    }
                else:
                    print(f"  ✗ Não foi possível verificar privilégios")
                    privs = {}

                print()
                return privs

        except SQLAlchemyError as e:
            print(f"❌ Erro ao verificar privilégios na database: {e}")
            print()
            return {}

    def check_schema_privileges(self, username: str, schema: str = 'public') -> Dict[str, bool]:
        """Verifica privilégios do usuário no schema."""
        query = text("""
            SELECT
                nspname,
                has_schema_privilege(:username, nspname, 'USAGE') as can_usage,
                has_schema_privilege(:username, nspname, 'CREATE') as can_create
            FROM pg_namespace
            WHERE nspname = :schema
        """)

        print(f"5. PRIVILÉGIOS DO USUÁRIO '{username}' NO SCHEMA '{schema}':")
        print("-" * 80)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {"username": username, "schema": schema}
                )
                schema_privs = result.fetchone()

                if schema_privs:
                    print(f"  Schema: {schema_privs[0]}")
                    print(
                        f"  - USAGE: {'✓ Sim' if schema_privs[1] else '✗ Não'}")
                    print(
                        f"  - CREATE: {'✓ Sim' if schema_privs[2] else '✗ Não'}")

                    privs = {
                        'usage': schema_privs[1],
                        'create': schema_privs[2]
                    }
                else:
                    print(f"  ✗ Não foi possível verificar privilégios no schema")
                    privs = {}

                print()
                return privs

        except SQLAlchemyError as e:
            print(f"❌ Erro ao verificar privilégios no schema: {e}")
            print()
            return {}

    def list_all_schemas(self) -> List[str]:
        """Lista todos os schemas da database."""
        query = text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)

        print("6. SCHEMAS DISPONÍVEIS:")
        print("-" * 80)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                schemas = [row[0] for row in result]

                if schemas:
                    for schema in schemas:
                        print(f"  • {schema}")
                else:
                    print("  ⚠️  Nenhum schema encontrado")

                print(f"\nTotal: {len(schemas)} schemas")
                print()
                return schemas

        except SQLAlchemyError as e:
            print(f"❌ Erro ao listar schemas: {e}")
            print()
            return []

    def check_critical_tables(self, critical_tables: List[str], schema: str = 'public'):
        """Verifica existência e detalhes de tabelas críticas."""
        print(f"7. TABELAS CRÍTICAS (schema: {schema}):")
        print("-" * 80)

        for table_name in critical_tables:
            query_exists = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = :schema
                    AND table_name = :table_name
                )
            """)

            try:
                with self.engine.connect() as conn:
                    result = conn.execute(
                        query_exists,
                        {"schema": schema, "table_name": table_name}
                    )
                    exists = result.scalar()

                    if exists:
                        # Conta registros
                        count_query = text(
                            f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
                        count = conn.execute(count_query).scalar()

                        # Pega owner
                        owner_query = text("""
                            SELECT tableowner
                            FROM pg_tables
                            WHERE schemaname = :schema
                            AND tablename = :table_name
                        """)
                        owner = conn.execute(
                            owner_query,
                            {"schema": schema, "table_name": table_name}
                        ).scalar()

                        status = "✓" if count > 0 else "⚠"
                        print(
                            f"  {status} {table_name:35} Owner: {owner:20} Registros: {count}")
                    else:
                        print(f"  ✗ {table_name:35} NÃO EXISTE")

            except SQLAlchemyError as e:
                print(f"  ✗ {table_name:35} ERRO: {str(e)[:50]}")

        print()

    def generate_summary(self, username: str, schema: str = 'public'):
        """Gera resumo da verificação."""
        print("=" * 80)
        print("RESUMO DA VERIFICAÇÃO")
        print("=" * 80)
        print()
        print(f"📊 Configuração:")
        print(f"  • Servidor: {self.host}:{self.port}")
        print(f"  • Database: {self.database}")
        print(f"  • Schema: {schema}")
        print(f"  • Usuário verificado: {username}")
        print()
        print("✅ Nenhuma alteração foi feita (modo READ-ONLY)")
        print()

    def close(self):
        """Fecha a conexão."""
        if self.engine:
            self.engine.dispose()


def load_config_file(config_path: str) -> Optional[Dict]:
    """Carrega arquivo de configuração JSON."""
    try:
        path = Path(config_path)
        if not path.exists():
            print(f"⚠️  Arquivo de configuração não encontrado: {config_path}")
            return None

        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"✅ Configuração carregada de: {config_path}")
            return config

    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        return None


def extract_connection_info(config: Dict) -> Optional[Dict]:
    """Extrai informações de conexão do arquivo postgresql_destination_config.json."""
    try:
        server = config.get('server', {})
        auth = config.get('authentication', {})

        return {
            'host': server.get('host'),
            'port': server.get('port', 5432),
            'user': auth.get('user'),
            'password': auth.get('password')
        }

    except Exception as e:
        print(f"❌ Erro ao extrair informações de conexão: {e}")
        return None


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Verifica permissões de usuários PostgreSQL (READ-ONLY)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Modo padrão - Usa configuração de secrets/postgresql_destination_config.json
  python fix_permissions/verify_metabase_permissions.py \\
    --database metabase_db \\
    --username metabase_user

  # Especificar arquivo de configuração customizado
  python fix_permissions/verify_metabase_permissions.py \\
    --config secrets/postgresql_destination_config.json \\
    --database app_workforce \\
    --username workforce_user

  # Modo manual (sem arquivo de configuração)
  python fix_permissions/verify_metabase_permissions.py \\
    --host wfdb02.vya.digital \\
    --port 5432 \\
    --admin-user migration_user \\
    --admin-password senha_admin \\
    --database kutt \\
    --username kutt_user

  # Verificar múltiplas tabelas críticas
  python fix_permissions/verify_metabase_permissions.py \\
    --database metabase_db \\
    --username metabase_user \\
    --critical-tables core_user,metabase_database,report_card

  # Verificar schema customizado
  python fix_permissions/verify_metabase_permissions.py \\
    --database app_workforce \\
    --username workforce_user \\
    --schema dados

Verificações Realizadas:
  1. Existência do usuário e suas características
  2. Ownership das tabelas no schema
  3. Privilégios do usuário nas tabelas
  4. Privilégios do usuário na database
  5. Privilégios do usuário no schema
  6. Lista de todos os schemas disponíveis
  7. Verificação de tabelas críticas (se especificadas)

⚠️ IMPORTANTE:
  - Este script é READ-ONLY - não faz alterações
  - Use para auditoria de segurança e troubleshooting
  - Requer permissões de leitura no sistema do PostgreSQL
        """
    )

    parser.add_argument(
        '--config',
        default='secrets/postgresql_destination_config.json',
        help='Arquivo de configuração JSON (padrão: secrets/postgresql_destination_config.json)'
    )
    parser.add_argument('--host', help='Host do servidor PostgreSQL')
    parser.add_argument('--port', type=int, default=5432,
                        help='Porta do servidor (padrão: 5432)')
    parser.add_argument('--admin-user',
                        help='Usuário para conectar (com permissões de leitura)')
    parser.add_argument('--admin-password', help='Senha do usuário de conexão')
    parser.add_argument('--database', required=True,
                        help='Nome da database a verificar')
    parser.add_argument('--username', required=True,
                        help='Nome do usuário cujas permissões serão verificadas')
    parser.add_argument('--schema', default='public',
                        help='Schema a verificar (padrão: public)')
    parser.add_argument('--critical-tables',
                        help='Lista de tabelas críticas separadas por vírgula')
    parser.add_argument('--list-schemas', action='store_true',
                        help='Listar todos os schemas disponíveis')

    args = parser.parse_args()

    # Carrega configuração
    conn_info = None
    config_file = None

    if Path(args.config).exists():
        config_file = load_config_file(args.config)
        if config_file:
            conn_info = extract_connection_info(config_file)

    # Determina credenciais de conexão
    if conn_info:
        host = args.host or conn_info['host']
        port = args.port if args.port != 5432 else conn_info.get('port', 5432)
        admin_user = args.admin_user or conn_info['user']
        admin_password = args.admin_password or conn_info['password']
    else:
        if not all([args.host, args.admin_user, args.admin_password]):
            print("❌ Erro: Sem arquivo de configuração válido, é necessário informar:")
            print("   --host, --admin-user e --admin-password")
            sys.exit(1)
        host = args.host
        port = args.port
        admin_user = args.admin_user
        admin_password = args.admin_password

    print("=" * 80)
    print(f"VERIFICAÇÃO DE PERMISSÕES POSTGRESQL - {args.database.upper()}")
    print("=" * 80)
    print()

    # Cria verificador
    verifier = PostgreSQLPermissionVerifier(
        host=host,
        port=port,
        database=args.database,
        admin_user=admin_user,
        admin_password=admin_password
    )

    # Conecta
    if not verifier.connect():
        print("❌ Falha ao conectar ao servidor")
        sys.exit(1)

    # Executa verificações
    verifier.verify_user_exists(args.username)
    verifier.check_table_ownership(args.schema)
    verifier.check_user_privileges(args.username, args.schema)
    verifier.check_database_privileges(args.username)
    verifier.check_schema_privileges(args.username, args.schema)

    if args.list_schemas:
        verifier.list_all_schemas()

    # Verifica tabelas críticas se especificadas
    if args.critical_tables:
        critical_list = [t.strip()
                         for t in args.critical_tables.split(',') if t.strip()]
        if critical_list:
            verifier.check_critical_tables(critical_list, args.schema)

    # Gera resumo
    verifier.generate_summary(args.username, args.schema)

    # Fecha conexão
    verifier.close()

    print("=" * 80)
    print("✅ VERIFICAÇÃO CONCLUÍDA")
    print("=" * 80)


if __name__ == '__main__':
    main()
