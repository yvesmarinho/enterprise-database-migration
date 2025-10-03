#!/usr/bin/env python3
"""
PostgreSQL Complete Migration Tool - SQLAlchemy Version
======================================================

Versão profissional usando SQLAlchemy para:
- Melhor abstração de banco
- Connection pooling automático
- Transações robustas
- Metadata reflection
- Escape automático de SQL

Dependências:
    pip install sqlalchemy psycopg2-binary
"""

import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine

class SQLAlchemyPostgreSQLMigrator:
    def __init__(self):
        self.source_engine: Optional[Engine] = None
        self.dest_engine: Optional[Engine] = None
        self.source_config = None
        self.dest_config = None

    def load_configs(self):
        """Carrega configurações."""
        try:
            with open('config/source_config.json', 'r', encoding='utf-8') as f:
                self.source_config = json.load(f)
            with open('config/destination_config.json', 'r', encoding='utf-8') as f:
                self.dest_config = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
            return False

    def create_engines(self):
        """Cria engines SQLAlchemy para origem e destino."""
        try:
            # Engine para servidor origem
            source_url = (
                f"postgresql://"
                f"{self.source_config['authentication']['user']}:"
                f"{self.source_config['authentication']['password']}@"
                f"{self.source_config['server']['host']}:"
                f"{self.source_config['server']['port']}/"
                f"postgres"
                f"?sslmode={self.source_config['server']['ssl_mode']}"
            )

            self.source_engine = create_engine(
                source_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                echo=False  # Set True for SQL debugging
            )

            # Engine para servidor destino
            dest_url = (
                f"postgresql://"
                f"{self.dest_config['authentication']['user']}:"
                f"{self.dest_config['authentication']['password']}@"
                f"{self.dest_config['server']['host']}:"
                f"{self.dest_config['connection_settings']['setup_port']}/"
                f"postgres"
                f"?sslmode={self.dest_config['server']['ssl_mode']}"
            )

            self.dest_engine = create_engine(
                dest_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                echo=False
            )

            # Testar conexões
            with self.source_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("   ✅ Conexão origem OK")

            with self.dest_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("   ✅ Conexão destino OK")

            return True

        except Exception as e:
            print(f"❌ Erro ao criar engines: {e}")
            return False

    def get_users_from_source(self) -> List[Dict]:
        """Coleta usuários usando SQLAlchemy."""
        print("👥 Coletando usuários do servidor origem...")

        query = text("""
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
              AND rolname NOT IN ('postgres', 'migration_user')
            ORDER BY rolname
        """)

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(query)
                users = []

                for row in result:
                    user = {
                        'rolname': row.rolname,
                        'rolsuper': row.rolsuper,
                        'rolinherit': row.rolinherit,
                        'rolcreaterole': row.rolcreaterole,
                        'rolcreatedb': row.rolcreatedb,
                        'rolcanlogin': row.rolcanlogin,
                        'rolreplication': row.rolreplication,
                        'rolconnlimit': row.rolconnlimit,
                        'rolpassword': row.rolpassword,
                        'rolvaliduntil': row.rolvaliduntil
                    }
                    users.append(user)

                print(f"   ✅ Encontrados {len(users)} usuários")
                return users

        except SQLAlchemyError as e:
            print(f"❌ Erro SQLAlchemy ao coletar usuários: {e}")
            return []

    def get_databases_with_owners(self) -> List[Dict]:
        """Coleta bancos com owners usando SQLAlchemy."""
        print("🏗️ Coletando bancos e owners do servidor origem...")

        query = text("""
            SELECT
                d.datname,
                r.rolname as owner,
                d.encoding,
                d.datcollate,
                d.datctype,
                d.datconnlimit,
                pg_database_size(d.datname) as size_bytes
            FROM pg_database d
            JOIN pg_roles r ON d.datdba = r.oid
            WHERE d.datname NOT IN ('postgres', 'template0', 'template1')
              AND NOT d.datistemplate
            ORDER BY d.datname
        """)

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(query)
                databases = []

                for row in result:
                    db_info = {
                        'datname': row.datname,
                        'owner': row.owner,
                        'encoding': row.encoding,
                        'datcollate': row.datcollate,
                        'datctype': row.datctype,
                        'datconnlimit': row.datconnlimit,
                        'size_bytes': row.size_bytes
                    }
                    databases.append(db_info)

                print(f"   ✅ Encontrados {len(databases)} bancos")
                return databases

        except SQLAlchemyError as e:
            print(f"❌ Erro SQLAlchemy ao coletar bancos: {e}")
            return []

    def get_database_privileges(self, db_name: str) -> List[Dict]:
        """Coleta privilégios específicos de um banco."""
        privileges = []

        # Query para privilégios de database usando SQLAlchemy
        privilege_query = text("""
            SELECT
                r.rolname,
                CASE
                    WHEN has_database_privilege(r.rolname, :db_name, 'CONNECT') THEN 'CONNECT'
                    ELSE NULL
                END as connect_priv,
                CASE
                    WHEN has_database_privilege(r.rolname, :db_name, 'CREATE') THEN 'CREATE'
                    ELSE NULL
                END as create_priv,
                CASE
                    WHEN has_database_privilege(r.rolname, :db_name, 'TEMPORARY') THEN 'TEMPORARY'
                    ELSE NULL
                END as temp_priv
            FROM pg_roles r
            WHERE r.rolname NOT LIKE 'pg_%'
              AND r.rolname NOT IN ('postgres', 'migration_user')
              AND r.rolcanlogin = true
              AND (
                  has_database_privilege(r.rolname, :db_name, 'CONNECT') OR
                  has_database_privilege(r.rolname, :db_name, 'CREATE') OR
                  has_database_privilege(r.rolname, :db_name, 'TEMPORARY')
              )
        """)

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(privilege_query, {"db_name": db_name})

                for row in result:
                    user_privs = {
                        'username': row.rolname,
                        'privileges': []
                    }

                    if row.connect_priv:
                        user_privs['privileges'].append('CONNECT')
                    if row.create_priv:
                        user_privs['privileges'].append('CREATE')
                    if row.temp_priv:
                        user_privs['privileges'].append('TEMPORARY')

                    if user_privs['privileges']:
                        privileges.append(user_privs)

        except SQLAlchemyError as e:
            print(f"   ⚠️ Erro ao coletar privilégios de {db_name}: {e}")

        return privileges

    def create_users_in_destination(self, users: List[Dict]) -> int:
        """Cria usuários no destino usando SQLAlchemy."""
        print("🔧 Criando usuários no servidor destino...")

        # Verificar usuários existentes
        existing_query = text("SELECT rolname FROM pg_roles")

        try:
            with self.dest_engine.connect() as conn:
                result = conn.execute(existing_query)
                existing_users = {row.rolname for row in result}

                created_count = 0

                for user in users:
                    username = user['rolname']

                    if username in existing_users:
                        print(f"   ⚠️ Usuário {username} já existe - pulando")
                        continue

                    # Construir comando CREATE ROLE com parâmetros seguros
                    attributes = []
                    if user['rolcanlogin']:
                        attributes.append("LOGIN")
                    if user['rolsuper']:
                        attributes.append("SUPERUSER")
                    if user['rolinherit']:
                        attributes.append("INHERIT")
                    if user['rolcreaterole']:
                        attributes.append("CREATEROLE")
                    if user['rolcreatedb']:
                        attributes.append("CREATEDB")
                    if user['rolreplication']:
                        attributes.append("REPLICATION")
                    if user['rolconnlimit'] != -1:
                        attributes.append(f"CONNECTION LIMIT {user['rolconnlimit']}")

                    attrs_str = " ".join(attributes)

                    # Usar transação para CREATE ROLE
                    with conn.begin():
                        if user['rolpassword']:
                            # Com senha
                            create_query = text(f"""
                                CREATE ROLE "{username}"
                                WITH {attrs_str}
                                PASSWORD :password
                            """)
                            conn.execute(create_query, {"password": user['rolpassword']})
                        else:
                            # Sem senha
                            create_query = text(f'CREATE ROLE "{username}" WITH {attrs_str}')
                            conn.execute(create_query)

                        print(f"   ✅ Usuário {username} criado")
                        created_count += 1

                print(f"   🎯 {created_count} usuários criados")
                return created_count

        except SQLAlchemyError as e:
            print(f"❌ Erro SQLAlchemy ao criar usuários: {e}")
            return 0

    def create_databases_with_postgres_owner(self, databases: List[Dict]) -> int:
        """Cria bancos com owner postgres usando SQLAlchemy."""
        print("🏗️ Criando bancos com owner postgres...")

        # Verificar bancos existentes
        existing_query = text("SELECT datname FROM pg_database")

        try:
            with self.dest_engine.connect() as conn:
                result = conn.execute(existing_query)
                existing_dbs = {row.datname for row in result}

                created_count = 0

                for db_info in databases:
                    db_name = db_info['datname']

                    if db_name in existing_dbs:
                        print(f"   ⚠️ Banco {db_name} já existe - verificando owner")

                        # Verificar e corrigir owner
                        owner_query = text("""
                            SELECT r.rolname
                            FROM pg_database d
                            JOIN pg_roles r ON d.datdba = r.oid
                            WHERE d.datname = :db_name
                        """)

                        owner_result = conn.execute(owner_query, {"db_name": db_name})
                        current_owner_row = owner_result.fetchone()

                        if current_owner_row and current_owner_row.rolname != 'postgres':
                            print(f"   🔄 Alterando owner: {current_owner_row.rolname} → postgres")
                            alter_query = text(f'ALTER DATABASE "{db_name}" OWNER TO postgres')
                            conn.execute(alter_query)
                        continue

                    # Criar banco com owner postgres
                    # SQLAlchemy requires autocommit for CREATE DATABASE
                    conn.execute(text("COMMIT"))  # End any transaction

                    create_query = text(f"""
                        CREATE DATABASE "{db_name}"
                        WITH
                            OWNER = postgres
                            ENCODING = 'UTF8'
                            LC_COLLATE = 'en_US.UTF-8'
                            LC_CTYPE = 'en_US.UTF-8'
                            TEMPLATE = template0
                            CONNECTION LIMIT = :conn_limit
                    """)

                    conn.execute(create_query, {"conn_limit": db_info['datconnlimit']})
                    print(f"   ✅ Banco {db_name} criado (owner: postgres)")
                    created_count += 1

                print(f"   🎯 {created_count} bancos criados/corrigidos")
                return created_count

        except SQLAlchemyError as e:
            print(f"❌ Erro SQLAlchemy ao criar bancos: {e}")
            return 0

    def apply_database_privileges(self, databases: List[Dict]) -> int:
        """Aplica privilégios usando SQLAlchemy."""
        print("🔐 Aplicando privilégios nos bancos...")

        privileges_applied = 0

        try:
            with self.dest_engine.connect() as conn:
                for db_info in databases:
                    db_name = db_info['datname']
                    original_owner = db_info['owner']

                    print(f"   🔧 Configurando privilégios para {db_name}")

                    # Privilégios padrão PUBLIC
                    public_query = text(f'GRANT TEMPORARY, CONNECT ON DATABASE "{db_name}" TO PUBLIC')
                    conn.execute(public_query)
                    privileges_applied += 1

                    # Privilégios para owner original
                    if original_owner != 'postgres' and original_owner != 'migration_user':
                        owner_query = text(f'GRANT ALL ON DATABASE "{db_name}" TO "{original_owner}"')
                        try:
                            conn.execute(owner_query)
                            print(f"     ✅ ALL → {original_owner}")
                            privileges_applied += 1
                        except SQLAlchemyError as e:
                            print(f"     ❌ Erro privilégio {original_owner}: {e}")

                    # Coletar e aplicar privilégios específicos
                    db_privileges = self.get_database_privileges(db_name)
                    for priv_info in db_privileges:
                        username = priv_info['username']
                        for privilege in priv_info['privileges']:
                            try:
                                priv_query = text(f'GRANT {privilege} ON DATABASE "{db_name}" TO "{username}"')
                                conn.execute(priv_query)
                                print(f"     ✅ {privilege} → {username}")
                                privileges_applied += 1
                            except SQLAlchemyError as e:
                                print(f"     ❌ Erro {privilege} para {username}: {e}")

                print(f"   🎯 {privileges_applied} privilégios aplicados")
                return privileges_applied

        except SQLAlchemyError as e:
            print(f"❌ Erro SQLAlchemy ao aplicar privilégios: {e}")
            return 0

    def run_complete_migration(self) -> bool:
        """Executa migração completa usando SQLAlchemy."""
        print("="*80)
        print("🚀 PostgreSQL Migration - SQLAlchemy Professional")
        print("="*80)
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("🔧 Engine: SQLAlchemy + psycopg2")
        print("="*80)

        start_time = time.time()

        try:
            # 1. Configurações e engines
            if not self.load_configs():
                return False

            print("🔌 Criando connections engines...")
            if not self.create_engines():
                return False

            # 2. Coletar dados da origem
            users = self.get_users_from_source()
            databases = self.get_databases_with_owners()

            if not users or not databases:
                print("❌ Dados insuficientes da origem")
                return False

            # 3. FASE 1: Criar usuários primeiro
            print(f"\n🔶 FASE 1: CRIANDO USUÁRIOS")
            print("-" * 50)
            users_created = self.create_users_in_destination(users)

            # 4. FASE 2: Criar bancos com owners corretos
            print(f"\n🔶 FASE 2: CRIANDO BANCOS (owner=postgres)")
            print("-" * 50)
            databases_created = self.create_databases_with_postgres_owner(databases)

            # 5. FASE 3: Aplicar privilégios
            print(f"\n🔶 FASE 3: APLICANDO PRIVILÉGIOS")
            print("-" * 50)
            privileges_applied = self.apply_database_privileges(databases)

            # Relatório final
            execution_time = time.time() - start_time

            print("\n" + "="*80)
            print("📊 RELATÓRIO FINAL - SQLALCHEMY MIGRATION")
            print("="*80)
            print(f"👤 Usuários encontrados: {len(users)}")
            print(f"✅ Usuários criados: {users_created}")
            print(f"🏗️ Bancos encontrados: {len(databases)}")
            print(f"✅ Bancos criados/corrigidos: {databases_created}")
            print(f"🔐 Privilégios aplicados: {privileges_applied}")
            print(f"⏱️ Tempo total: {execution_time:.2f}s")
            print(f"🔧 Engine: SQLAlchemy (connection pooling)")
            print("="*80)

            if users_created > 0 or databases_created > 0 or privileges_applied > 0:
                print("🎉 MIGRAÇÃO SQLALCHEMY CONCLUÍDA COM SUCESSO!")
                return True
            else:
                print("⚠️ Sistema já estava configurado corretamente")
                return True

        except Exception as e:
            print(f"❌ Erro fatal na migração SQLAlchemy: {e}")
            return False

        finally:
            # Cleanup engines
            if self.source_engine:
                self.source_engine.dispose()
            if self.dest_engine:
                self.dest_engine.dispose()

def main():
    migrator = SQLAlchemyPostgreSQLMigrator()
    success = migrator.run_complete_migration()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Migração SQLAlchemy interrompida")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal SQLAlchemy: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
