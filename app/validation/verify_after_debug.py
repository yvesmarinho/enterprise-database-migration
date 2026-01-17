#!/usr/bin/env python3
"""
VERIFICAÇÃO IMEDIATA APÓS DEBUG
Confirmar se grants foram realmente aplicados
"""

import json

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


def verify_grants_after_debug():
    """Verifica grants imediatamente após o debug."""

    with open('secrets/postgresql_destination_config.json', 'r') as f:
        dest_config = json.load(f)

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    dest_engine = create_engine(dest_url)

    print("🔍 VERIFICAÇÃO IMEDIATA APÓS DEBUG")
    print("=" * 50)

    databases_to_check = ['app_workforce', 'botpress_db']
    expected_users = ['app_workforce_user', 'botpress_user']

    with dest_engine.connect() as conn:
        for db_name in databases_to_check:
            print(f"\n📁 {db_name}:")

            # Verificar grants explícitos usando aclexplode
            grants_query = text("""
                SELECT
                    grantee::regrole::text as grantee,
                    privilege_type,
                    is_grantable
                FROM pg_database d,
                     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                WHERE d.datname = :db_name
                ORDER BY grantee, privilege_type
            """)

            try:
                result = conn.execute(grants_query, {"db_name": db_name})
                grants = list(result)

                print(f"   📊 Total de grants explícitos: {len(grants)}")

                # Mostrar todos os grants
                current_grantee = None
                for grant in grants:
                    if grant.grantee != current_grantee:
                        current_grantee = grant.grantee
                        print(f"   👤 {current_grantee}:")

                    grantable = " (WITH GRANT OPTION)" if grant.is_grantable else ""
                    print(f"      • {grant.privilege_type}{grantable}")

                # Verificar usuários específicos esperados
                for expected_user in expected_users:
                    user_grants = [g for g in grants if g.grantee == expected_user]

                    if user_grants:
                        privileges = [g.privilege_type for g in user_grants]
                        print(f"   ✅ {expected_user}: {', '.join(privileges)}")
                    else:
                        print(f"   ❌ {expected_user}: SEM GRANTS")

            except Exception as e:
                print(f"   ❌ Erro verificando {db_name}: {e}")


def check_migration_logs():
    """Verifica logs da migração para entender o que aconteceu."""

    print(f"\n📋 VERIFICANDO LOGS DE MIGRAÇÃO:")
    print("=" * 40)

    import glob
    import os

    # Buscar logs recentes
    log_pattern = "core/reports/migration_*.log"
    log_files = glob.glob(log_pattern)

    if log_files:
        # Pegar o log mais recente
        latest_log = max(log_files, key=os.path.getmtime)
        print(f"📄 Log mais recente: {latest_log}")

        try:
            with open(latest_log, 'r') as f:
                lines = f.readlines()

            # Procurar por linhas relacionadas a grants
            print("🔍 Linhas relacionadas a privilégios:")
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['privilege', 'grant', 'fase 3', 'aplicando']):
                    print(f"   {i+1}: {line.strip()}")

        except Exception as e:
            print(f"❌ Erro lendo log: {e}")
    else:
        print("⚠️ Nenhum log encontrado")


def check_last_migration_execution():
    """Verifica quando foi a última execução de migração."""

    print(f"\n🕐 ÚLTIMA EXECUÇÃO DE MIGRAÇÃO:")
    print("=" * 35)

    with open('secrets/postgresql_destination_config.json', 'r') as f:
        dest_config = json.load(f)

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    dest_engine = create_engine(dest_url)

    with dest_engine.connect() as conn:
        # Verificar se existe alguma tabela de controle de migração
        try:
            migration_query = text("""
                SELECT
                    schemaname,
                    tablename
                FROM pg_tables
                WHERE tablename LIKE '%migration%'
                   OR tablename LIKE '%log%'
                ORDER BY schemaname, tablename
            """)

            result = conn.execute(migration_query)
            tables = list(result)

            if tables:
                print("📋 Tabelas relacionadas a migração:")
                for table in tables:
                    print(f"   • {table.schemaname}.{table.tablename}")
            else:
                print("⚠️ Nenhuma tabela de controle encontrada")

        except Exception as e:
            print(f"❌ Erro verificando tabelas: {e}")


if __name__ == "__main__":
    verify_grants_after_debug()
    check_migration_logs()
    check_last_migration_execution()
