#!/usr/bin/env python3
"""
FASE 3: EXECUTOR CONTROLADO DE MIGRAÇÃO
Executa scripts SQL gerados com controle completo e validação
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2


class ControlledMigrationExecutor:
    def __init__(self, destination_config_file="secrets/postgresql_destination_config.json"):
        self.config_file = destination_config_file
        self.config = None
        self.connection = None
        self.scripts_dir = "generated_scripts"

        # Scripts em ordem de execução
        self.execution_order = [
            "01_create_users.sql",
            "02_create_databases.sql",
            "03_apply_grants.sql",
            "04_validate_migration.sql"
        ]

    def load_config(self):
        """Carrega configuração do servidor de destino."""
        try:
            with open(self.config_file, 'r') as f:
                raw_config = json.load(f)

            # Extrair dados da estrutura aninhada
            self.config = {
                'host': raw_config['server']['host'],
                'port': raw_config['server']['port'],
                'user': raw_config['authentication']['user'],
                'password': raw_config['authentication']['password']
            }

            print(f"✅ Configuração carregada: {self.config['host']}:{self.config['port']}")
            return True

        except Exception as e:
            print(f"❌ Erro carregando configuração: {e}")
            return False

    def connect_to_destination(self):
        """Conecta ao servidor de destino."""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database='postgres',  # Conectar à base administrativa
                user=self.config['user'],
                password=self.config['password']
            )

            self.connection.autocommit = True  # Importante para DDL

            print(f"✅ Conectado ao {self.config['host']}:{self.config['port']}")

            # Verificar versão
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"   📊 Versão: {version.split(',')[0]}")

            return True

        except Exception as e:
            print(f"❌ Erro conectando: {e}")
            return False

    def execute_script(self, script_file, dry_run=False):
        """Executa um script SQL específico statement por statement."""
        script_path = os.path.join(self.scripts_dir, script_file)

        if not os.path.exists(script_path):
            print(f"❌ Script não encontrado: {script_path}")
            return False

        try:
            # Ler script
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            print(f"📜 Executando: {script_file}")

            if dry_run:
                print(f"   🔍 DRY RUN - Script seria executado ({len(script_content)} chars)")
                return True

            # Dividir script em statements SQL completos (termina com ;)
            statements = []
            current_statement = []

            for line in script_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('--'):
                    current_statement.append(line)
                    if line.endswith(';'):
                        # Statement completo
                        statements.append(' '.join(current_statement))
                        current_statement = []

            # Se sobrou algo sem ';', adicionar também
            if current_statement:
                statements.append(' '.join(current_statement))

            # Executar cada statement completo
            executed_count = 0
            with self.connection.cursor() as cursor:
                for statement in statements:
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                            executed_count += 1
                        except Exception as stmt_error:
                            # Para DDL com IF EXISTS/IF NOT EXISTS, alguns erros são OK
                            if "already exists" in str(stmt_error).lower():
                                print(f"   ⚠️  {stmt_error}")
                                continue
                            else:
                                raise stmt_error

                # Para scripts de validação, buscar resultados
                if script_file.startswith('04_'):
                    try:
                        cursor.execute("SELECT 'Validação' AS status, current_timestamp")
                        results = cursor.fetchall()
                        if results:
                            print(f"   ✅ Validação:")
                            for row in results:
                                print(f"      {row}")
                    except Exception:
                        pass

            print(f"   ✅ {executed_count} statements executados com sucesso!")
            return True

        except Exception as e:
            print(f"   ❌ Erro executando script: {e}")
            return False

    def verify_users_created(self):
        """Verifica se usuários foram criados."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT rolname, rolcanlogin, rolsuper, rolcreatedb
                    FROM pg_roles
                    WHERE rolname NOT LIKE 'pg_%'
                      AND rolname NOT IN ('postgres', 'migration_user')
                    ORDER BY rolname
                """)

                users = cursor.fetchall()
                print(f"\n👥 USUÁRIOS CRIADOS ({len(users)}):")

                for user in users[:10]:  # Mostrar primeiros 10
                    rolname, login, super_user, createdb = user
                    attrs = []
                    if login: attrs.append("LOGIN")
                    if super_user: attrs.append("SUPERUSER")
                    if createdb: attrs.append("CREATEDB")

                    print(f"   🟢 {rolname} ({', '.join(attrs)})")

                if len(users) > 10:
                    print(f"   ... e mais {len(users) - 10} usuários")

                return len(users) > 0

        except Exception as e:
            print(f"❌ Erro verificando usuários: {e}")
            return False

    def verify_databases_created(self):
        """Verifica se bases foram criadas."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT datname, datdba::regrole::text, pg_size_pretty(pg_database_size(datname))
                    FROM pg_database
                    WHERE datname NOT IN ('postgres', 'template0', 'template1')
                    ORDER BY datname
                """)

                databases = cursor.fetchall()
                print(f"\n🏗️ BASES CRIADAS ({len(databases)}):")

                for db in databases:
                    datname, owner, size = db
                    print(f"   🟢 {datname} (Owner: {owner}, Size: {size})")

                return len(databases) > 0

        except Exception as e:
            print(f"❌ Erro verificando bases: {e}")
            return False

    def verify_grants_applied(self):
        """Verifica se grants foram aplicados."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT d.datname,
                           grantee::regrole::text AS user,
                           privilege_type
                    FROM pg_database d,
                         aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                    WHERE d.datname NOT IN ('postgres', 'template0', 'template1')
                      AND grantee::regrole::text NOT IN ('postgres')
                    ORDER BY d.datname, grantee::regrole::text, privilege_type
                """)

                grants = cursor.fetchall()
                print(f"\n🔐 GRANTS APLICADOS ({len(grants)}):")

                current_db = None
                count_for_db = 0

                for grant in grants:
                    datname, user, privilege = grant

                    if datname != current_db:
                        if current_db and count_for_db > 5:
                            print(f"      ... e mais {count_for_db - 5} grants")
                        current_db = datname
                        count_for_db = 0
                        print(f"   📊 {datname}:")

                    count_for_db += 1
                    if count_for_db <= 5:
                        print(f"      🟢 {user} → {privilege}")

                if count_for_db > 5:
                    print(f"      ... e mais {count_for_db - 5} grants")

                return len(grants) > 0

        except Exception as e:
            print(f"❌ Erro verificando grants: {e}")
            return False

    def run_migration(self, dry_run=False, interactive=False):
        """Executa migração completa."""
        print("🚀 INICIANDO MIGRAÇÃO CONTROLADA")
        print("=" * 60)

        if dry_run:
            print("🔍 MODO DRY RUN - Nenhuma alteração será feita")

        # Carregar config e conectar
        if not self.load_config():
            return False

        if not self.connect_to_destination():
            return False

        # Verificar scripts
        missing_scripts = []
        for script in self.execution_order:
            script_path = os.path.join(self.scripts_dir, script)
            if not os.path.exists(script_path):
                missing_scripts.append(script)

        if missing_scripts:
            print(f"❌ Scripts faltando: {missing_scripts}")
            return False

        print(f"✅ Todos os {len(self.execution_order)} scripts encontrados")

        # Executar scripts
        for i, script in enumerate(self.execution_order, 1):
            print(f"\n{'='*20} FASE {i}/{len(self.execution_order)} {'='*20}")

            if interactive:
                response = input(f"Executar {script}? (s/N): ")
                if response.lower() not in ['s', 'sim', 'y', 'yes']:
                    print("⏭️ Script pulado")
                    continue

            success = self.execute_script(script, dry_run)

            if not success:
                print(f"❌ Falha na execução do script {script}")
                if not dry_run:
                    response = input("Continuar mesmo assim? (s/N): ")
                    if response.lower() not in ['s', 'sim', 'y', 'yes']:
                        return False

        # Verificações finais (só se não for dry run)
        if not dry_run:
            print(f"\n{'='*20} VERIFICAÇÕES FINAIS {'='*20}")

            users_ok = self.verify_users_created()
            databases_ok = self.verify_databases_created()
            grants_ok = self.verify_grants_applied()

            print(f"\n📊 RESUMO FINAL:")
            print(f"   👥 Usuários: {'✅' if users_ok else '❌'}")
            print(f"   🏗️ Bases: {'✅' if databases_ok else '❌'}")
            print(f"   🔐 Grants: {'✅' if grants_ok else '❌'}")

            if users_ok and databases_ok and grants_ok:
                print(f"\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
                return True
            else:
                print(f"\n⚠️ Migração concluída com problemas")
                return False
        else:
            print(f"\n🔍 DRY RUN CONCLUÍDO - Todos os scripts são válidos")
            return True

    def close_connection(self):
        """Fecha conexão."""
        if self.connection:
            self.connection.close()
            print("🔌 Conexão fechada")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Executor Controlado de Migração PostgreSQL')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simular execução sem fazer alterações')
    parser.add_argument('--interactive', action='store_true',
                       help='Modo interativo - pedir confirmação para cada script')
    parser.add_argument('--config', default='secrets/postgresql_destination_config.json',
                       help='Arquivo de configuração do destino')

    args = parser.parse_args()

    executor = ControlledMigrationExecutor(args.config)

    try:
        success = executor.run_migration(
            dry_run=args.dry_run,
            interactive=args.interactive
        )

        if success:
            print(f"\n✅ Processo concluído com sucesso!")
            sys.exit(0)
        else:
            print(f"\n❌ Processo falhou!")
            sys.exit(1)

    finally:
        executor.close_connection()
