#!/usr/bin/env python3
"""
FASE 2: GERADOR DE SCRIPTS SQL
Baseado no JSON extraído, gera scripts SQL precisos usando template
"""

import json
import os
from datetime import datetime
from pathlib import Path


class SQLScriptGenerator:
    def __init__(self, json_file):
        self.json_file = json_file
        self.data = None
        self.output_dir = "generated_scripts"

    def load_extracted_data(self):
        """Carrega dados extraídos do JSON."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            print(f"✅ JSON carregado: {self.json_file}")
            summary = self.data['summary']
            print(f"   👥 {summary['total_users']} usuários")
            print(f"   🏗️ {summary['total_databases']} bases")
            print(f"   🔐 {summary['total_grants']} grants")

            return True

        except Exception as e:
            print(f"❌ Erro carregando JSON: {e}")
            return False

    def create_output_directory(self):
        """Cria diretório de saída."""
        Path(self.output_dir).mkdir(exist_ok=True)
        print(f"📁 Diretório de saída: {self.output_dir}/")

    def generate_users_script(self):
        """Gera script de criação de usuários."""
        print("\n👥 GERANDO SCRIPT DE USUÁRIOS...")

        script_lines = [
            "-- =====================================================",
            "-- SCRIPT DE CRIAÇÃO DE USUÁRIOS",
            f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Fonte: {self.data['source_server']}",
            f"-- Total: {len(self.data['users'])} usuários",
            "-- =====================================================",
            "",
            "-- Criação de usuários (sem transação - DDL commands)",
            ""
        ]

        for user in self.data['users']:
            rolname = user['rolname']

            # Comentário do usuário
            script_lines.append(f"-- Usuário: {rolname}")

            # Comando CREATE ROLE
            create_role = f"CREATE ROLE \"{rolname}\""

            # Adicionar atributos
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

            if attributes:
                create_role += f" WITH {' '.join(attributes)}"

            # Connection limit
            if user['rolconnlimit'] != -1:
                create_role += f" CONNECTION LIMIT {user['rolconnlimit']}"

            # Password (se existir)
            if user['rolpassword']:
                create_role += f" PASSWORD '{user['rolpassword']}'"

            # Valid until (se existir)
            if user['rolvaliduntil']:
                create_role += f" VALID UNTIL '{user['rolvaliduntil']}'"

            create_role += ";"
            script_lines.append(create_role)
            script_lines.append("")

        script_lines.extend([
            "-- Scripts de usuários concluídos",
            "",
            f"-- {len(self.data['users'])} usuários processados"
        ])

        # Salvar script
        script_file = f"{self.output_dir}/01_create_users.sql"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))

        print(f"   ✅ Script salvo: {script_file}")
        return script_file

    def generate_databases_script(self):
        """Gera script de criação de bases de dados."""
        print("\n🏗️ GERANDO SCRIPT DE BASES DE DADOS...")

        script_lines = [
            "-- =====================================================",
            "-- SCRIPT DE CRIAÇÃO DE BASES DE DADOS",
            f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Fonte: {self.data['source_server']}",
            f"-- Total: {self.data['summary']['user_databases']} bases de usuário",
            "-- =====================================================",
            "",
            "-- Criação de bases (sem transação - CREATE DATABASE)",
            ""
        ]

        # Filtrar apenas bases de usuário
        user_databases = [db for db in self.data['databases'] if not db['is_system']]

        for db in user_databases:
            datname = db['datname']
            owner = db['owner']

            script_lines.extend([
                f"-- Base: {datname} (Owner: {owner}, Tamanho: {db['size_mb']} MB)",
                f"-- DROP DATABASE IF EXISTS \"{datname}\";",
                "",
                f"CREATE DATABASE \"{datname}\"",
                "    WITH",
                f"    OWNER = postgres",
                f"    ENCODING = 'UTF8'",
                f"    LC_COLLATE = 'pt_BR.UTF-8'",  # Usar locale do servidor
                f"    LC_CTYPE = 'pt_BR.UTF-8'",    # Usar locale do servidor
                "    TABLESPACE = pg_default",
                "    TEMPLATE = template0",           # Usar template0 para evitar conflito
                f"    CONNECTION LIMIT = {db['datconnlimit']}",
                "    IS_TEMPLATE = False;",
                ""
            ])

        script_lines.extend([
            "-- Scripts de bases concluídos",
            "",
            f"-- {len(user_databases)} bases de dados processadas"
        ])

        # Salvar script
        script_file = f"{self.output_dir}/02_create_databases.sql"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))

        print(f"   ✅ Script salvo: {script_file}")
        return script_file

    def generate_grants_script(self):
        """Gera script de aplicação de grants."""
        print("\n🔐 GERANDO SCRIPT DE GRANTS...")

        script_lines = [
            "-- =====================================================",
            "-- SCRIPT DE APLICAÇÃO DE GRANTS",
            f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Fonte: {self.data['source_server']}",
            f"-- Total: {self.data['summary']['total_grants']} grants",
            "-- =====================================================",
            "",
            "-- IMPORTANTE: Executar APÓS criação de usuários e bases",
            "",
            "-- Aplicação de grants (autocommit)",
            ""
        ]

        grants_count = 0

        for db_name, db_grants in self.data['grants'].items():
            # Pular bases do sistema
            db_info = next((db for db in self.data['databases'] if db['datname'] == db_name), None)
            if db_info and db_info['is_system']:
                continue

            script_lines.extend([
                f"-- =====================================================",
                f"-- GRANTS PARA BASE: {db_name}",
                f"-- =====================================================",
                ""
            ])

            # Aplicar grants específicos
            for grant in db_grants:
                grantee = grant['grantee']
                privileges = grant['privileges']

                # Pular usuários do sistema e root
                if grantee in ['postgres', 'migration_user', 'root']:
                    continue

                # Limpar aspas duplas já existentes no grantee
                clean_grantee = grantee.strip('"')

                # Gerar comando GRANT
                for privilege in privileges:
                    if clean_grantee == 'public':
                        grant_cmd = f"GRANT {privilege} ON DATABASE \"{db_name}\" TO public;"
                    else:
                        grant_cmd = f"GRANT {privilege} ON DATABASE \"{db_name}\" TO \"{clean_grantee}\";"

                    script_lines.append(grant_cmd)
                    grants_count += 1

            script_lines.append("")

        script_lines.extend([
            "-- Scripts de grants concluídos",
            "",
            f"-- {grants_count} grants processados"
        ])

        # Salvar script
        script_file = f"{self.output_dir}/03_apply_grants.sql"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))

        print(f"   ✅ Script salvo: {script_file}")
        return script_file

    def generate_master_script(self):
        """Gera script master que executa tudo em ordem."""
        print("\n📜 GERANDO SCRIPT MASTER...")

        script_lines = [
            "-- =====================================================",
            "-- SCRIPT MASTER DE MIGRAÇÃO POSTGRESQL",
            f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Fonte: {self.data['source_server']}",
            "-- Destino: wfdb02.vya.digital:5432",
            "-- =====================================================",
            "",
            "-- INSTRUÇÕES:",
            "-- 1. Executar como usuário postgres",
            "-- 2. Conectar ao servidor de destino",
            "-- 3. Executar os scripts na ordem abaixo",
            "",
            "-- ORDEM DE EXECUÇÃO:",
            "\\i 01_create_users.sql",
            "\\i 02_create_databases.sql",
            "\\i 03_apply_grants.sql",
            "",
            "-- VERIFICAÇÃO FINAL:",
            "SELECT 'Migração concluída!' AS status;",
            "",
            f"-- Resumo: {self.data['summary']['total_users']} usuários, "
            f"{self.data['summary']['user_databases']} bases, "
            f"{self.data['summary']['total_grants']} grants"
        ]

        # Salvar script
        script_file = f"{self.output_dir}/00_master_migration.sql"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))

        print(f"   ✅ Script master salvo: {script_file}")
        return script_file

    def generate_validation_script(self):
        """Gera script de validação pós-migração."""
        print("\n🔍 GERANDO SCRIPT DE VALIDAÇÃO...")

        script_lines = [
            "-- =====================================================",
            "-- SCRIPT DE VALIDAÇÃO PÓS-MIGRAÇÃO",
            f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-- =====================================================",
            "",
            "-- Verificar usuários criados",
            "SELECT 'USUÁRIOS CRIADOS' AS categoria, count(*) AS total",
            "FROM pg_roles",
            "WHERE rolname NOT LIKE 'pg_%' AND rolname != 'postgres';",
            "",
            "-- Verificar bases criadas",
            "SELECT 'BASES CRIADAS' AS categoria, count(*) AS total",
            "FROM pg_database",
            "WHERE datname NOT IN ('postgres', 'template0', 'template1');",
            "",
            "-- Verificar grants aplicados",
            "SELECT 'GRANTS APLICADOS' AS categoria, count(*) AS total",
            "FROM (",
            "    SELECT DISTINCT d.datname, grantee::regrole::text",
            "    FROM pg_database d,",
            "         aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))",
            "    WHERE d.datname NOT IN ('postgres', 'template0', 'template1')",
            ") AS grants;",
            ""
        ]

        # Adicionar verificações específicas para bases importantes
        important_dbs = ['app_workforce', 'botpress_db', 'n8n_db']

        script_lines.append("-- Verificações específicas de grants:")
        for db_name in important_dbs:
            if db_name in self.data['grants']:
                script_lines.extend([
                    f"",
                    f"SELECT '{db_name}' AS database,",
                    "       grantee::regrole::text AS user,",
                    "       privilege_type AS privilege",
                    "FROM pg_database d,",
                    "     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))",
                    f"WHERE d.datname = '{db_name}'",
                    "ORDER BY grantee, privilege_type;"
                ])

        # Salvar script
        script_file = f"{self.output_dir}/04_validate_migration.sql"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))

        print(f"   ✅ Script de validação salvo: {script_file}")
        return script_file

    def run_generation(self):
        """Executa geração completa de scripts."""
        print("🚀 INICIANDO GERAÇÃO DE SCRIPTS SQL")
        print("=" * 50)

        if not self.load_extracted_data():
            return False

        self.create_output_directory()

        # Gerar todos os scripts
        scripts_generated = []
        scripts_generated.append(self.generate_master_script())
        scripts_generated.append(self.generate_users_script())
        scripts_generated.append(self.generate_databases_script())
        scripts_generated.append(self.generate_grants_script())
        scripts_generated.append(self.generate_validation_script())

        print(f"\n✅ GERAÇÃO CONCLUÍDA!")
        print(f"📁 {len(scripts_generated)} scripts gerados em {self.output_dir}/")

        # Listar arquivos gerados
        for script in scripts_generated:
            file_size = os.path.getsize(script)
            print(f"   📄 {os.path.basename(script)} ({file_size:,} bytes)")

        return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "extracted_data_20251006_114724.json"

    generator = SQLScriptGenerator(json_file)
    success = generator.run_generation()

    if success:
        print(f"\n🎯 PRÓXIMO PASSO: Executar scripts em {generator.output_dir}/")
        print(f"   1. 📋 Revisar scripts gerados")
        print(f"   2. 🔌 Conectar ao wfdb02")
        print(f"   3. 🚀 Executar 00_master_migration.sql")
    else:
        print(f"\n❌ Falha na geração de scripts")
