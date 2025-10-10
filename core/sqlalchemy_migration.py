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
from typing import Any, Dict, List, Optional

from sqlalchemy import MetaData, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


class SQLAlchemyPostgreSQLMigrator:
    def __init__(self):
        self.source_engine: Optional[Engine] = None
        self.dest_engine: Optional[Engine] = None
        self.source_config = None
        self.dest_config = None

    def load_configs(self):
        """Carrega configurações usando o sistema centralizado."""
        try:
            from components.config_manager import get_db_config_path

            source_config_path = get_db_config_path('postgresql_source_config')
            dest_config_path = get_db_config_path('postgresql_destination_config')

            with open(source_config_path, 'r', encoding='utf-8') as f:
                self.source_config = json.load(f)
            with open(dest_config_path, 'r', encoding='utf-8') as f:
                self.dest_config = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
            return False

    def create_engines(self):
        """Cria engines SQLAlchemy para origem e destino."""
        try:
            from components.config_normalizer import get_sqlalchemy_url

            # Engine para servidor origem
            source_url = get_sqlalchemy_url(self.source_config)

            self.source_engine = create_engine(
                source_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                echo=False  # Set True for SQL debugging
            )

            # Engine para servidor destino
            dest_url = get_sqlalchemy_url(self.dest_config)

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

    def get_protected_items(self) -> tuple:
        """Carrega listas de proteção dos arquivos de configuração."""
        try:
            protected_users = set()
            protected_databases = set()

            # Carregar proteções da origem
            if self.source_config and 'cleanup_protection' in self.source_config:
                protected_users.update(self.source_config['cleanup_protection'].get('protected_users', []))
                protected_databases.update(self.source_config['cleanup_protection'].get('protected_databases', []))

            # Carregar proteções do destino (mais importantes)
            if self.dest_config and 'cleanup_protection' in self.dest_config:
                protected_users.update(self.dest_config['cleanup_protection'].get('protected_users', []))
                protected_databases.update(self.dest_config['cleanup_protection'].get('protected_databases', []))

            print(f"   🛡️ Usuários protegidos: {len(protected_users)} ({', '.join(sorted(protected_users))})")
            print(f"   🛡️ Bancos protegidos: {len(protected_databases)} ({', '.join(sorted(protected_databases))})")

            return protected_users, protected_databases

        except Exception as e:
            print(f"❌ Erro ao carregar proteções: {e}")
            return set(), set()

    def filter_protected_users(self, users: List[Dict]) -> List[Dict]:
        """Remove usuários protegidos da lista de migração."""
        protected_users, _ = self.get_protected_items()

        filtered_users = []
        skipped_count = 0

        for user in users:
            username = user['rolname']
            if username in protected_users:
                print(f"   🛡️ Usuário {username} está protegido - pulando migração")
                skipped_count += 1
            else:
                filtered_users.append(user)

        print(f"   📊 Usuários filtrados: {len(filtered_users)} (pulados: {skipped_count})")
        return filtered_users

    def filter_protected_databases(self, databases: List[Dict]) -> List[Dict]:
        """Remove bancos protegidos da lista de migração."""
        _, protected_databases = self.get_protected_items()

        filtered_databases = []
        skipped_count = 0

        for db in databases:
            db_name = db['datname']
            if db_name in protected_databases:
                print(f"   🛡️ Banco {db_name} está protegido - pulando migração")
                skipped_count += 1
            else:
                filtered_databases.append(db)

        print(f"   📊 Bancos filtrados: {len(filtered_databases)} (pulados: {skipped_count})")
        return filtered_databases

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

        # Primeiro, vamos ver todos os bancos para debug
        debug_query = text("""
            SELECT d.datname, d.datistemplate, r.rolname as owner
            FROM pg_database d
            JOIN pg_roles r ON d.datdba = r.oid
            ORDER BY d.datname
        """)

        # Query principal mais robusta e inclusiva
        main_query = text("""
            SELECT
                d.datname,
                r.rolname as owner,
                d.encoding,
                d.datcollate,
                d.datctype,
                d.datconnlimit,
                CASE
                    WHEN has_database_privilege(d.datname, 'CONNECT') THEN
                        pg_database_size(d.datname)
                    ELSE 0
                END as size_bytes,
                d.datistemplate,
                has_database_privilege(d.datname, 'CONNECT') as can_connect
            FROM pg_database d
            JOIN pg_roles r ON d.datdba = r.oid
            WHERE d.datallowconn = true
            ORDER BY d.datname
        """)

        try:
            with self.source_engine.connect() as conn:
                # Debug: mostrar todos os bancos primeiro
                print("   🔍 Verificando todos os bancos disponíveis:")
                debug_result = conn.execute(debug_query)
                all_databases = []
                for row in debug_result:
                    all_databases.append(row)
                    template_status = " (template)" if row.datistemplate else ""
                    print(f"      - {row.datname} (owner: {row.owner}){template_status}")

                print(f"   📊 Total de bancos encontrados: {len(all_databases)}")

                # Agora executar query principal
                result = conn.execute(main_query)
                databases = []

                for row in result:
                    # Incluir todos os bancos encontrados (não apenas templates)
                    db_info = {
                        'datname': row.datname,
                        'owner': row.owner,
                        'encoding': row.encoding,
                        'datcollate': row.datcollate,
                        'datctype': row.datctype,
                        'datconnlimit': row.datconnlimit,
                        'size_bytes': row.size_bytes,
                        'is_template': row.datistemplate,
                        'can_connect': row.can_connect
                    }
                    databases.append(db_info)

                # Separar bancos do sistema dos bancos de usuário
                user_databases = [db for db in databases if db['datname'] not in ['postgres'] and not db['is_template']]
                system_databases = [db for db in databases if db['datname'] in ['postgres'] or db['is_template']]

                print(f"   ✅ Encontrados {len(databases)} bancos total")
                print(f"      ├─ 👤 Bancos de usuário: {len(user_databases)}")
                print(f"      └─ ⚙️ Bancos do sistema: {len(system_databases)}")

                if user_databases:
                    print("   📋 Bancos de usuário encontrados:")
                    for db in user_databases:
                        size_mb = db['size_bytes'] / (1024 * 1024) if db['size_bytes'] > 0 else 0
                        print(f"      - {db['datname']} ({size_mb:.2f} MB, owner: {db['owner']})")

                # Retornar todos os bancos (sistema + usuário) para análise completa
                return databases

        except SQLAlchemyError as e:
            print(f"❌ Erro SQLAlchemy ao coletar bancos: {e}")
            return []

    def get_database_privileges(self, db_name: str) -> List[Dict]:
        """Coleta privilégios de um banco usando a abordagem do pgAdmin - queries ACL simples."""
        privileges = []

        # Query similar ao pgAdmin para buscar ACLs de banco
        acl_query = text("""
            SELECT
                d.datname as deftype,
                CASE WHEN aclitem IS NULL THEN 'datacl' ELSE 'datacl' END as deftype,
                split_part(aclitem::text, '=', 1) as grantee,
                split_part(split_part(aclitem::text, '=', 2), '/', 2) as grantor,
                split_part(split_part(aclitem::text, '=', 2), '/', 1) as privileges
            FROM pg_database d, unnest(COALESCE(d.datacl, ARRAY[]::aclitem[])) as aclitem
            WHERE d.datname = :db_name
              AND d.datname NOT LIKE 'template%'

            UNION ALL

            -- Adicionar owner se não tem ACL explícita
            SELECT
                d.datname as deftype,
                'datacl' as deftype,
                r.rolname as grantee,
                r.rolname as grantor,
                'CTc' as privileges
            FROM pg_database d
            JOIN pg_roles r ON d.datdba = r.oid
            WHERE d.datname = :db_name
              AND d.datname NOT LIKE 'template%'
              AND (d.datacl IS NULL OR NOT EXISTS (
                  SELECT 1 FROM unnest(d.datacl) as acl
                  WHERE split_part(acl::text, '=', 1) = r.rolname
              ))
        """)

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(acl_query, {"db_name": db_name})

                print(f"     🔍 DEBUG: Coletando ACLs para {db_name}...")

                # Processar resultados como o pgAdmin faz
                for row in result:
                    grantee = row.grantee if row.grantee else 'public'
                    priv_codes = row.privileges or ''

                    # Ignorar usuários do sistema
                    if grantee in ['postgres', 'migration_user']:
                        continue

                    # Converter códigos de privilégio para nomes (baseado no pgAdmin)
                    db_privileges = []
                    if 'C' in priv_codes:  # CONNECT
                        db_privileges.append('CONNECT')
                    if 'T' in priv_codes:  # TEMPORARY
                        db_privileges.append('TEMPORARY')
                    if 'c' in priv_codes:  # CREATE
                        db_privileges.append('CREATE')

                    # Se tem todos os códigos principais, é ALL
                    if priv_codes == 'CTc':
                        db_privileges = ['ALL']

                    if db_privileges:
                        privileges.append({
                            'username': grantee,
                            'privileges': db_privileges
                        })
                        print(f"     🔍 DEBUG: {grantee} tem {', '.join(db_privileges)} no banco {db_name}")

                print(f"     📊 Total de privilégios coletados para {db_name}: {len(privileges)}")

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

                # Obter listas de proteção
                protected_users, _ = self.get_protected_items()

                for user in users:
                    username = user['rolname']

                    # Verificação adicional de proteção
                    if username in protected_users:
                        print(f"   🛡️ Usuário {username} está protegido - pulando criação")
                        continue

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

                    # Executar CREATE ROLE com commit explícito
                    try:
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

                        # CRÍTICO: Commit explícito para persistir usuário
                        conn.commit()

                        # Verificação imediata de criação
                        verify_query = text(
                            "SELECT rolname FROM pg_roles WHERE rolname = :username"
                        )
                        verify_result = conn.execute(
                            verify_query, {"username": username}
                        )
                        if verify_result.fetchone():
                            print(f"   ✅ Usuário {username} criado e verificado")
                            created_count += 1
                        else:
                            print(f"   ❌ Usuário {username} não persistido")

                    except Exception as e:
                        print(f"   ❌ Erro ao criar {username}: {e}")

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

                # Obter listas de proteção
                _, protected_databases = self.get_protected_items()

                for db_info in databases:
                    db_name = db_info['datname']

                    # Verificação adicional de proteção para bancos existentes
                    if db_name in protected_databases:
                        print(f"   🛡️ Banco {db_name} está protegido - pulando alteração de owner")
                        continue

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
                            created_count += 1
                        else:
                            print(f"   ✅ Owner já é postgres - OK")
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
        """Aplica privilégios usando estratégia de comando individual para evitar transações abortadas."""
        print("🔐 Aplicando privilégios nos bancos...")

        privileges_applied = 0

        def get_existing_users():
            """Busca usuários existentes sempre atualizado (não usa cache)."""
            try:
                if not self.dest_engine:
                    return set()
                with self.dest_engine.connect() as conn:
                    result = conn.execute(text("SELECT rolname FROM pg_roles"))
                    users = {row.rolname for row in result}
                    return users
            except Exception as e:
                print(f"     ❌ Erro ao buscar usuários: {e}")
                return set()

        def apply_privilege_safely(db_name: str, privilege: str, username: str) -> bool:
            """Aplica um privilégio em conexão isolada."""
            try:
                if not self.dest_engine:
                    return False
                with self.dest_engine.connect() as conn:
                    conn = conn.execution_options(autocommit=True)
                    # Usar aspas apenas para identificadores que precisam
                    if username == "public":
                        grant_query = text(f'GRANT {privilege} ON DATABASE "{db_name}" TO public')
                    else:
                        grant_query = text(f'GRANT {privilege} ON DATABASE "{db_name}" TO "{username}"')
                    conn.execute(grant_query)
                    return True
            except Exception as e:
                print(f"     ❌ Erro {privilege} para {username}: {e}")
                return False

        try:
            # Buscar usuários existentes (sempre atualizado)
            existing_users = get_existing_users()

            for db_info in databases:
                db_name = db_info['datname']
                original_owner = db_info['owner']

                print(f"   🔧 Configurando privilégios para {db_name}")

                # Atualizar lista de usuários para cada banco
                existing_users = get_existing_users()

                # Privilégios padrão PUBLIC (aplicar separadamente)
                if apply_privilege_safely(db_name, "CONNECT", "public"):
                    privileges_applied += 1
                if apply_privilege_safely(db_name, "TEMPORARY", "public"):
                    privileges_applied += 1

                # Privilégios para owner original
                if original_owner != 'postgres' and original_owner != 'migration_user':
                    if original_owner in existing_users:
                        if apply_privilege_safely(db_name, "ALL", original_owner):
                            print(f"     ✅ ALL → {original_owner}")
                            privileges_applied += 1
                    else:
                        print(f"     ⚠️ Usuário {original_owner} não existe - pulando privilégios")

                # Coletar e aplicar privilégios específicos da origem
                try:
                    db_privileges = self.get_database_privileges(db_name)
                    skipped_users = 0

                    for priv_info in db_privileges:
                        username = priv_info['username']

                        # Verificar se usuário existe (silenciosamente ignorar se não existe)
                        if username not in existing_users:
                            skipped_users += 1
                            continue

                        for privilege in priv_info['privileges']:
                            if apply_privilege_safely(db_name, privilege, username):
                                print(f"     ✅ {privilege} → {username}")
                                privileges_applied += 1

                    if skipped_users > 0:
                        print(f"     ℹ️ {skipped_users} usuários inexistentes ignorados")

                except Exception as e:
                    print(f"     ⚠️ Erro ao coletar privilégios específicos para {db_name}: {e}")

            print(f"   🎯 {privileges_applied} privilégios aplicados")
            return privileges_applied

        except Exception as e:
            print(f"❌ Erro ao aplicar privilégios: {e}")
            return 0

    def migrate_all_users(self) -> bool:
        """Método para migração completa: usuários, bancos e permissões (usado pelo orquestrador)."""
        print("� Executando migração completa: usuários, bancos e permissões...")

        try:
            # 1. Carregar configurações e criar engines
            if not self.load_configs():
                print("❌ Falha ao carregar configurações")
                return False

            print("🔌 Criando connection engines...")
            if not self.create_engines():
                print("❌ Falha ao criar engines de conexão")
                return False

            # 2. Coletar dados da origem
            print("\n📊 Coletando dados da origem...")
            users = self.get_users_from_source()
            databases = self.get_databases_with_owners()

            # 2.1 Aplicar proteções de segurança
            print("\n🛡️ Aplicando filtros de proteção...")
            if users:
                users = self.filter_protected_users(users)
                if not users:
                    print("⚠️ Todos os usuários foram filtrados por proteção")
            else:
                print("⚠️ Nenhum usuário encontrado na origem")
                users = []

            if databases:
                databases = self.filter_protected_databases(databases)
                if not databases:
                    print("⚠️ Todos os bancos foram filtrados por proteção")
            else:
                print("⚠️ Nenhum banco encontrado na origem")
                databases = []

            # 3. FASE 1: Criar usuários primeiro
            print(f"\n🔶 FASE 1: CRIANDO USUÁRIOS")
            print("-" * 50)
            users_created = 0
            if users:
                users_created = self.create_users_in_destination(users)
                print(f"✅ {users_created} usuários criados")
            else:
                print("⚠️ Nenhum usuário para criar")

            # 4. FASE 2: Criar bancos com owners corretos
            print(f"\n🔶 FASE 2: CRIANDO BANCOS DE DADOS")
            print("-" * 50)
            databases_created = 0
            if databases:
                databases_created = self.create_databases_with_postgres_owner(databases)
                print(f"✅ {databases_created} bancos criados")
            else:
                print("⚠️ Nenhum banco para criar")

            # 5. FASE 3: Aplicar privilégios
            print(f"\n🔶 FASE 3: APLICANDO PRIVILÉGIOS")
            print("-" * 50)
            privileges_applied = 0
            if databases:
                privileges_applied = self.apply_database_privileges(databases)
                print(f"✅ {privileges_applied} privilégios aplicados")
            else:
                print("⚠️ Nenhum privilégio para aplicar")

            # Relatório final
            print(f"\n📊 RESUMO DA MIGRAÇÃO COMPLETA:")
            print(f"   👥 Usuários criados: {users_created}")
            print(f"   🏗️ Bancos criados: {databases_created}")
            print(f"   🔐 Privilégios aplicados: {privileges_applied}")

            return True

        except Exception as e:
            print(f"❌ Erro na migração completa: {e}")
            import traceback
            traceback.print_exc()
            return False

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
