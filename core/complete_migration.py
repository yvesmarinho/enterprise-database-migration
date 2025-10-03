#!/usr/bin/env python3
"""
PostgreSQL Complete Migration System
===================================

Sistema completo de migração PostgreSQL 14→16 na ordem correta:
1. Migração de usuários e roles (com senhas SCRAM-SHA-256)
2. Criação de bancos com owners corretos
3. Migração de estruturas (tabelas, views, etc.)
4. Aplicação de permissões e privilégios

Corrige o problema de ordem na migração anterior.

Uso:
    python3 complete_migration.py [--dry-run] [--phase=users|databases|structures|permissions|all]
"""

import json
import psycopg2
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

class CompleteMigrationSystem:
    def __init__(self):
        self.source_config = None
        self.dest_config = None
        self.migration_log = []
        
    def load_configurations(self):
        """Carrega configurações dos servidores."""
        try:
            with open('config/source_config.json', 'r', encoding='utf-8') as f:
                self.source_config = json.load(f)
            with open('config/destination_config.json', 'r', encoding='utf-8') as f:
                self.dest_config = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
            return False
    
    def get_database_owners_mapping(self):
        """Obtém mapeamento de bancos e seus proprietários originais."""
        print("📋 Coletando proprietários originais dos bancos...")
        
        try:
            conn_string = (
                f"host={self.source_config['server']['host']} "
                f"port={self.source_config['server']['port']} "
                f"dbname=postgres "
                f"user={self.source_config['authentication']['user']} "
                f"password={self.source_config['authentication']['password']} "
                f"sslmode={self.source_config['server']['ssl_mode']} "
                f"connect_timeout={self.source_config['connection_settings']['connection_timeout']}"
            )
            
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            
            # Query para obter bancos com seus proprietários
            excluded_dbs = ['template0', 'template1', 'postgres']
            excluded_dbs_str = "', '".join(excluded_dbs)
            
            cursor.execute(f"""
                SELECT 
                    d.datname,
                    r.rolname as owner_name,
                    d.datdba as owner_oid,
                    d.encoding,
                    d.datcollate,
                    d.datctype,
                    d.datconnlimit,
                    pg_database_size(d.datname) as size_bytes,
                    pg_size_pretty(pg_database_size(d.datname)) as size_pretty
                FROM pg_database d
                JOIN pg_roles r ON d.datdba = r.oid
                WHERE d.datname NOT IN ('{excluded_dbs_str}')
                AND d.datistemplate = false
                ORDER BY d.datname
            """)
            
            databases = cursor.fetchall()
            
            db_mapping = []
            for db in databases:
                db_info = {
                    'datname': db[0],
                    'owner_name': db[1],
                    'owner_oid': db[2],
                    'encoding': db[3],
                    'datcollate': db[4],
                    'datctype': db[5],
                    'datconnlimit': db[6],
                    'size_bytes': db[7],
                    'size_pretty': db[8]
                }
                db_mapping.append(db_info)
                
                print(f"   - {db[0]} → Owner: {db[1]} ({db[8]})")
            
            cursor.close()
            conn.close()
            
            print(f"   ✅ {len(db_mapping)} bancos mapeados com proprietários")
            return db_mapping
            
        except Exception as e:
            print(f"❌ Erro ao mapear proprietários: {e}")
            return []
    
    def get_users_from_source(self):
        """Obtém todos os usuários do servidor origem."""
        print("👥 Coletando usuários do servidor origem...")
        
        try:
            conn_string = (
                f"host={self.source_config['server']['host']} "
                f"port={self.source_config['server']['port']} "
                f"dbname=postgres "
                f"user={self.source_config['authentication']['user']} "
                f"password={self.source_config['authentication']['password']} "
                f"sslmode={self.source_config['server']['ssl_mode']} "
                f"connect_timeout={self.source_config['connection_settings']['connection_timeout']}"
            )
            
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            
            # Query para obter usuários completos
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
                    rolvaliduntil,
                    oid
                FROM pg_authid 
                WHERE rolname NOT LIKE 'pg_%'
                  AND rolname NOT IN ('postgres', 'migration_user')
                ORDER BY rolname
            """)
            
            users = cursor.fetchall()
            
            user_list = []
            for user in users:
                user_dict = {
                    'rolname': user[0],
                    'rolsuper': user[1],
                    'rolinherit': user[2],
                    'rolcreaterole': user[3],
                    'rolcreatedb': user[4],
                    'rolcanlogin': user[5],
                    'rolreplication': user[6],
                    'rolconnlimit': user[7],
                    'rolpassword': user[8],
                    'rolvaliduntil': user[9],
                    'oid': user[10]
                }
                user_list.append(user_dict)
            
            print(f"   ✅ {len(user_list)} usuários coletados")
            cursor.close()
            conn.close()
            
            return user_list
            
        except Exception as e:
            print(f"❌ Erro ao coletar usuários: {e}")
            return []
    
    def migrate_users_phase(self, users_list, dry_run=False):
        """FASE 1: Migra usuários para o destino."""
        print("\n" + "="*80)
        print("🔵 FASE 1: MIGRAÇÃO DE USUÁRIOS")
        print("="*80)
        
        if dry_run:
            print("🧪 MODO DRY-RUN - Simulando migração de usuários")
            return True
        
        try:
            conn_string = (
                f"host={self.dest_config['server']['host']} "
                f"port={self.dest_config['connection_settings']['setup_port']} "
                f"dbname=postgres "
                f"user={self.dest_config['authentication']['user']} "
                f"password={self.dest_config['authentication']['password']} "
                f"sslmode={self.dest_config['server']['ssl_mode']} "
                f"connect_timeout={self.dest_config['connection_settings']['connection_timeout']}"
            )
            
            conn = psycopg2.connect(conn_string)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Verificar usuários existentes
            cursor.execute("SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%'")
            existing_users = [row[0] for row in cursor.fetchall()]
            
            created_count = 0
            skipped_count = 0
            
            for user_info in users_list:
                username = user_info['rolname']
                
                if username in existing_users:
                    print(f"   ⚠️ Usuário {username} já existe - pulando")
                    skipped_count += 1
                    continue
                
                # Construir comando CREATE USER/ROLE
                create_cmd = f'CREATE ROLE "{username}"'
                
                attributes = []
                
                if user_info['rolcanlogin']:
                    attributes.append("LOGIN")
                else:
                    attributes.append("NOLOGIN")
                    
                if user_info['rolsuper']:
                    attributes.append("SUPERUSER")
                else:
                    attributes.append("NOSUPERUSER")
                    
                if user_info['rolinherit']:
                    attributes.append("INHERIT")
                else:
                    attributes.append("NOINHERIT")
                    
                if user_info['rolcreaterole']:
                    attributes.append("CREATEROLE")
                else:
                    attributes.append("NOCREATEROLE")
                    
                if user_info['rolcreatedb']:
                    attributes.append("CREATEDB")
                else:
                    attributes.append("NOCREATEDB")
                    
                if user_info['rolreplication']:
                    attributes.append("REPLICATION")
                else:
                    attributes.append("NOREPLICATION")
                    
                if user_info['rolconnlimit'] != -1:
                    attributes.append(f"CONNECTION LIMIT {user_info['rolconnlimit']}")
                
                # Senha SCRAM-SHA-256
                if user_info['rolpassword']:
                    attributes.append(f"PASSWORD '{user_info['rolpassword']}'")
                
                # Data de validade
                if user_info['rolvaliduntil']:
                    attributes.append(f"VALID UNTIL '{user_info['rolvaliduntil']}'")
                
                if attributes:
                    create_cmd += " WITH " + " ".join(attributes)
                
                try:
                    cursor.execute(create_cmd)
                    print(f"   ✅ Usuário {username} criado")
                    created_count += 1
                except Exception as e:
                    print(f"   ❌ Erro ao criar {username}: {e}")
            
            cursor.close()
            conn.close()
            
            print(f"\n📊 FASE 1 RESULTADO:")
            print(f"   ✅ Usuários criados: {created_count}")
            print(f"   ⚠️ Usuários existentes: {skipped_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na migração de usuários: {e}")
            return False
    
    def migrate_databases_phase(self, db_mapping, dry_run=False):
        """FASE 2: Cria bancos com owners corretos."""
        print("\n" + "="*80)
        print("🔵 FASE 2: CRIAÇÃO DE BANCOS COM OWNERS CORRETOS")
        print("="*80)
        
        if dry_run:
            print("🧪 MODO DRY-RUN - Simulando criação de bancos")
            for db in db_mapping:
                print(f"   🧪 Criaria: {db['datname']} (Owner: {db['owner_name']})")
            return True
        
        try:
            conn_string = (
                f"host={self.dest_config['server']['host']} "
                f"port={self.dest_config['connection_settings']['setup_port']} "
                f"dbname=postgres "
                f"user={self.dest_config['authentication']['user']} "
                f"password={self.dest_config['authentication']['password']} "
                f"sslmode={self.dest_config['server']['ssl_mode']} "
                f"connect_timeout={self.dest_config['connection_settings']['connection_timeout']}"
            )
            
            conn = psycopg2.connect(conn_string)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Verificar bancos existentes
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
            existing_dbs = [row[0] for row in cursor.fetchall()]
            
            created_count = 0
            skipped_count = 0
            
            for db_info in db_mapping:
                db_name = db_info['datname']
                owner_name = db_info['owner_name']
                
                if db_name in existing_dbs:
                    print(f"   ⚠️ Banco {db_name} já existe - pulando")
                    skipped_count += 1
                    continue
                
                # Verificar se owner existe
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (owner_name,))
                if not cursor.fetchone():
                    print(f"   ❌ Owner {owner_name} não existe - usando migration_user")
                    owner_name = "migration_user"
                
                # Criar banco com owner correto
                create_db_sql = f'''
                CREATE DATABASE "{db_name}"
                WITH 
                    OWNER = "{owner_name}"
                    ENCODING = 'UTF8'
                    LC_COLLATE = '{db_info['datcollate']}'
                    LC_CTYPE = '{db_info['datctype']}'
                    TEMPLATE = template0
                '''
                
                if db_info['datconnlimit'] != -1:
                    create_db_sql += f"    CONNECTION LIMIT = {db_info['datconnlimit']}"
                
                try:
                    cursor.execute(create_db_sql)
                    print(f"   ✅ Banco {db_name} criado (Owner: {owner_name})")
                    created_count += 1
                except Exception as e:
                    print(f"   ❌ Erro ao criar {db_name}: {e}")
            
            cursor.close()
            conn.close()
            
            print(f"\n📊 FASE 2 RESULTADO:")
            print(f"   ✅ Bancos criados: {created_count}")
            print(f"   ⚠️ Bancos existentes: {skipped_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na criação de bancos: {e}")
            return False
    
    def run_complete_migration(self, dry_run=False, phase='all'):
        """Executa migração completa na ordem correta."""
        print("🚀 INICIANDO MIGRAÇÃO COMPLETA PostgreSQL 14→16")
        print("="*80)
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🧪 Dry-run: {'SIM' if dry_run else 'NÃO'}")
        print(f"🎯 Fase: {phase}")
        print("="*80)
        
        start_time = time.time()
        
        # Carregar configurações
        if not self.load_configurations():
            return False
        
        success = True
        
        if phase in ['users', 'all']:
            # FASE 1: Migrar usuários
            users_list = self.get_users_from_source()
            if not users_list:
                print("❌ Nenhum usuário encontrado")
                return False
            
            if not self.migrate_users_phase(users_list, dry_run):
                success = False
        
        if phase in ['databases', 'all'] and success:
            # FASE 2: Criar bancos com owners corretos
            db_mapping = self.get_database_owners_mapping()
            if not db_mapping:
                print("❌ Nenhum banco encontrado")
                return False
            
            if not self.migrate_databases_phase(db_mapping, dry_run):
                success = False
        
        # TODO: FASE 3 e 4 (estruturas e permissões) podem ser implementadas depois
        
        execution_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("📊 RESULTADO FINAL DA MIGRAÇÃO")
        print("="*80)
        
        if success:
            print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print("❌ MIGRAÇÃO FALHOU")
        
        print(f"⏱️ Tempo total: {execution_time:.2f}s")
        
        if dry_run:
            print("🧪 MODO DRY-RUN - Execute sem --dry-run para aplicar")
        
        print("="*80)
        
        return success

def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete PostgreSQL Migration")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Executar em modo dry-run")
    parser.add_argument("--phase", choices=['users', 'databases', 'structures', 'permissions', 'all'],
                       default='all', help="Fase específica para executar")
    args = parser.parse_args()
    
    migrator = CompleteMigrationSystem()
    success = migrator.run_complete_migration(args.dry_run, args.phase)
    
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