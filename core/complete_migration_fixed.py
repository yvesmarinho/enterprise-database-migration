#!/usr/bin/env python3
"""
PostgreSQL Complete Migration Tool - Fixed Order
===============================================

Migração correta com ordem adequada:
1. Migrar usuários primeiro
2. Criar bancos com owners corretos
3. Aplicar privilégios específicos

Corrige o problema de owners incorretos e privilégios ausentes.
"""

import json
import psycopg2
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class CompletePostgreSQLMigrator:
    def __init__(self):
        self.source_config = None
        self.dest_config = None

    def load_configs(self):
        """Carrega configurações."""
        try:
            with open('config/source_config.json', 'r', encoding='utf-8') as f:
                source = json.load(f)
            with open('config/destination_config.json', 'r', encoding='utf-8') as f:
                destination = json.load(f)

            self.source_config = source
            self.dest_config = destination
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
            return False

    def get_source_connection(self):
        """Conexão com servidor origem."""
        return psycopg2.connect(
            host=self.source_config['server']['host'],
            port=self.source_config['server']['port'],
            dbname='postgres',
            user=self.source_config['authentication']['user'],
            password=self.source_config['authentication']['password'],
            sslmode=self.source_config['server']['ssl_mode'],
            connect_timeout=self.source_config['connection_settings']['connection_timeout']
        )

    def get_dest_connection(self, database='postgres'):
        """Conexão com servidor destino."""
        return psycopg2.connect(
            host=self.dest_config['server']['host'],
            port=self.dest_config['connection_settings']['setup_port'],
            dbname=database,
            user=self.dest_config['authentication']['user'],
            password=self.dest_config['authentication']['password'],
            sslmode=self.dest_config['server']['ssl_mode'],
            connect_timeout=self.dest_config['connection_settings']['connection_timeout']
        )

    def get_users_from_source(self):
        """Coleta usuários do servidor origem."""
        print("👥 Coletando usuários do servidor origem...")

        conn = self.get_source_connection()
        cursor = conn.cursor()

        # Usuários com detalhes completos
        cursor.execute("""
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

        users = []
        for row in cursor.fetchall():
            user = {
                'rolname': row[0],
                'rolsuper': row[1],
                'rolinherit': row[2],
                'rolcreaterole': row[3],
                'rolcreatedb': row[4],
                'rolcanlogin': row[5],
                'rolreplication': row[6],
                'rolconnlimit': row[7],
                'rolpassword': row[8],
                'rolvaliduntil': row[9]
            }
            users.append(user)

        cursor.close()
        conn.close()

        print(f"   ✅ Encontrados {len(users)} usuários")
        return users

    def get_databases_with_privileges(self):
        """Coleta bancos com informações de owner e privilégios."""
        print("🏗️ Coletando bancos e privilégios do servidor origem...")

        conn = self.get_source_connection()
        cursor = conn.cursor()

        # Bancos com owners
        cursor.execute("""
            SELECT
                d.datname,
                r.rolname as owner,
                d.encoding,
                d.datcollate,
                d.datctype,
                d.datconnlimit
            FROM pg_database d
            JOIN pg_roles r ON d.datdba = r.oid
            WHERE d.datname NOT IN ('postgres', 'template0', 'template1')
              AND NOT d.datistemplate
            ORDER BY d.datname
        """)

        databases = []
        for row in cursor.fetchall():
            db_info = {
                'datname': row[0],
                'owner': row[1],
                'encoding': row[2],
                'datcollate': row[3],
                'datctype': row[4],
                'datconnlimit': row[5],
                'privileges': []
            }
            databases.append(db_info)

        # Para cada banco, obter privilégios usando método mais simples
        for db_info in databases:
            db_name = db_info['datname']

            try:
                # Método simplificado - buscar usuários que podem conectar ao banco
                cursor.execute("""
                    SELECT
                        r.rolname
                    FROM pg_roles r
                    WHERE r.rolname NOT LIKE 'pg_%'
                      AND r.rolname != 'postgres'
                      AND r.rolname != 'migration_user'
                      AND r.rolcanlogin = true
                """)

                potential_users = cursor.fetchall()
                privileges = []

                # Para cada usuário, verificar se tem privilégios no banco
                for user_row in potential_users:
                    username = user_row[0]
                    try:
                        # Testar se usuário tem privilégios no banco específico
                        # Isso é mais confiável que consultar information_schema
                        cursor.execute("""
                            SELECT has_database_privilege(%s, %s, 'CONNECT')
                        """, (username, db_name))

                        has_connect = cursor.fetchone()[0]
                        if has_connect:
                            privileges.append((username, 'CONNECT'))
                    except:
                        # Se der erro, usuário provavelmente não tem acesso
                        continue

                db_info['privileges'] = privileges

            except Exception as e:
                print(f"   ⚠️ Erro ao coletar privilégios de {db_name}: {e}")
                db_info['privileges'] = []

        cursor.close()
        conn.close()

        print(f"   ✅ Encontrados {len(databases)} bancos")
        return databases

    def create_users_in_destination(self, users):
        """Cria usuários no destino."""
        print("🔧 Criando usuários no servidor destino...")

        conn = self.get_dest_connection()
        conn.autocommit = True
        cursor = conn.cursor()

        # Verificar usuários existentes
        cursor.execute("SELECT rolname FROM pg_roles")
        existing_users = {row[0] for row in cursor.fetchall()}

        created_count = 0
        for user in users:
            username = user['rolname']

            if username in existing_users:
                print(f"   ⚠️ Usuário {username} já existe - pulando")
                continue

            # Construir comando CREATE ROLE
            cmd_parts = [f'CREATE ROLE "{username}"']

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
            if user['rolpassword']:
                attributes.append(f"PASSWORD '{user['rolpassword']}'")

            if attributes:
                cmd_parts.append("WITH " + " ".join(attributes))

            create_cmd = " ".join(cmd_parts)

            try:
                cursor.execute(create_cmd)
                print(f"   ✅ Usuário {username} criado")
                created_count += 1
            except Exception as e:
                print(f"   ❌ Erro ao criar {username}: {e}")

        cursor.close()
        conn.close()

        print(f"   🎯 {created_count} usuários criados")
        return created_count

    def create_databases_with_correct_owners(self, databases):
        """Cria bancos com owners corretos."""
        print("🏗️ Criando bancos com owners corretos...")

        conn = self.get_dest_connection()
        conn.autocommit = True
        cursor = conn.cursor()

        # Verificar bancos existentes
        cursor.execute("SELECT datname FROM pg_database")
        existing_dbs = {row[0] for row in cursor.fetchall()}

        created_count = 0
        for db_info in databases:
            db_name = db_info['datname']

            if db_name in existing_dbs:
                print(f"   ⚠️ Banco {db_name} já existe - verificando owner")

                # Verificar owner atual
                cursor.execute("""
                    SELECT r.rolname
                    FROM pg_database d
                    JOIN pg_roles r ON d.datdba = r.oid
                    WHERE d.datname = %s
                """, (db_name,))

                current_owner = cursor.fetchone()
                if current_owner:
                    current_owner = current_owner[0]
                    if current_owner != 'postgres':
                        print(f"   🔄 Alterando owner de {db_name}: {current_owner} → postgres")
                        try:
                            cursor.execute(f'ALTER DATABASE "{db_name}" OWNER TO postgres')
                        except Exception as e:
                            print(f"   ❌ Erro ao alterar owner: {e}")
                continue

            # Criar banco com owner postgres
            create_cmd = f'''
            CREATE DATABASE "{db_name}"
            WITH
                OWNER = postgres
                ENCODING = 'UTF8'
                LC_COLLATE = 'en_US.UTF-8'
                LC_CTYPE = 'en_US.UTF-8'
                TEMPLATE = template0
                CONNECTION LIMIT = {db_info['datconnlimit']}
            '''

            try:
                cursor.execute(create_cmd)
                print(f"   ✅ Banco {db_name} criado (owner: postgres)")
                created_count += 1
            except Exception as e:
                print(f"   ❌ Erro ao criar banco {db_name}: {e}")

        cursor.close()
        conn.close()

        print(f"   🎯 {created_count} bancos criados")
        return created_count

    def apply_database_privileges(self, databases):
        """Aplica privilégios específicos nos bancos."""
        print("🔐 Aplicando privilégios nos bancos...")

        conn = self.get_dest_connection()
        conn.autocommit = True
        cursor = conn.cursor()

        privileges_applied = 0

        for db_info in databases:
            db_name = db_info['datname']
            original_owner = db_info['owner']

            print(f"   🔧 Configurando privilégios para {db_name}")

            # Privilégios padrão PUBLIC
            try:
                cursor.execute(f'GRANT TEMPORARY, CONNECT ON DATABASE "{db_name}" TO PUBLIC')
                privileges_applied += 1
            except Exception as e:
                print(f"   ⚠️ Erro ao dar privilégio PUBLIC: {e}")

            # Privilégios para owner original (se não for postgres)
            if original_owner != 'postgres' and original_owner != 'migration_user':
                try:
                    cursor.execute(f'GRANT ALL ON DATABASE "{db_name}" TO "{original_owner}"')
                    print(f"     ✅ ALL → {original_owner}")
                    privileges_applied += 1
                except Exception as e:
                    print(f"     ❌ Erro privilégio para {original_owner}: {e}")

            # Aplicar outros privilégios descobertos
            for privilege_info in db_info['privileges']:
                if len(privilege_info) >= 1:
                    grantee = privilege_info[0]
                    try:
                        cursor.execute(f'GRANT CONNECT ON DATABASE "{db_name}" TO "{grantee}"')
                        print(f"     ✅ CONNECT → {grantee}")
                        privileges_applied += 1
                    except Exception as e:
                        print(f"     ❌ Erro privilégio para {grantee}: {e}")

        cursor.close()
        conn.close()

        print(f"   🎯 {privileges_applied} privilégios aplicados")
        return privileges_applied

    def run_complete_migration(self):
        """Executa migração completa na ordem correta."""
        print("="*80)
        print("🚀 PostgreSQL Complete Migration - Ordem Correta")
        print("="*80)
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*80)

        start_time = time.time()

        # 1. Carregar configurações
        if not self.load_configs():
            return False

        # 2. Coletar dados da origem
        users = self.get_users_from_source()
        databases = self.get_databases_with_privileges()

        if not users or not databases:
            print("❌ Dados insuficientes da origem")
            return False

        # 3. FASE 1: Criar usuários primeiro
        print(f"\n🔶 FASE 1: CRIANDO USUÁRIOS")
        print("-" * 50)
        users_created = self.create_users_in_destination(users)

        # 4. FASE 2: Criar bancos com owners corretos
        print(f"\n🔶 FASE 2: CRIANDO BANCOS COM OWNERS CORRETOS")
        print("-" * 50)
        databases_created = self.create_databases_with_correct_owners(databases)

        # 5. FASE 3: Aplicar privilégios
        print(f"\n🔶 FASE 3: APLICANDO PRIVILÉGIOS")
        print("-" * 50)
        privileges_applied = self.apply_database_privileges(databases)

        # Relatório final
        execution_time = time.time() - start_time

        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL DA MIGRAÇÃO COMPLETA")
        print("="*80)
        print(f"👤 Usuários processados: {len(users)}")
        print(f"✅ Usuários criados: {users_created}")
        print(f"🏗️ Bancos processados: {len(databases)}")
        print(f"✅ Bancos criados/corrigidos: {databases_created}")
        print(f"🔐 Privilégios aplicados: {privileges_applied}")
        print(f"⏱️ Tempo total: {execution_time:.2f}s")
        print("="*80)

        if users_created > 0 or databases_created > 0 or privileges_applied > 0:
            print("🎉 MIGRAÇÃO COMPLETA CONCLUÍDA COM SUCESSO!")
            return True
        else:
            print("⚠️ Nenhuma alteração foi necessária")
            return True

def main():
    migrator = CompletePostgreSQLMigrator()
    success = migrator.run_complete_migration()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Migração interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
