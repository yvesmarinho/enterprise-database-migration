#!/usr/bin/env python3
"""
DEBUG ESPECÍFICO DO apply_database_privileges
Simular exatamente o que acontece na função
"""

import json

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


def debug_apply_database_privileges():
    """Debug específico da função apply_database_privileges."""

    # Carregar engines
    with open('secrets/postgresql_source_config.json', 'r') as f:
        source_config = json.load(f)
    with open('secrets/postgresql_destination_config.json', 'r') as f:
        dest_config = json.load(f)

    source_url = get_sqlalchemy_url(source_config, database='postgres')
    dest_url = get_sqlalchemy_url(dest_config, database='postgres')

    source_engine = create_engine(source_url)
    dest_engine = create_engine(dest_url)

    print("🔍 DEBUG APPLY_DATABASE_PRIVILEGES")
    print("=" * 50)

    # Simular exatamente o que a função faz
    databases = [
        {'datname': 'app_workforce', 'owner': 'root'},
        {'datname': 'botpress_db', 'owner': 'root'}
    ]

    def get_existing_users():
        """Simula get_existing_users da função."""
        with dest_engine.connect() as conn:
            result = conn.execute(text("SELECT rolname FROM pg_roles"))
            users = {row.rolname for row in result}
            return users

    def get_database_privileges_debug(db_name: str):
        """Simula get_database_privileges da função."""
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

        privileges = []

        try:
            with source_engine.connect() as conn:
                result = conn.execute(acl_query, {"db_name": db_name})

                for row in result:
                    grantee = row.grantee if row.grantee else 'public'
                    priv_codes = row.privileges or ''

                    # Ignorar usuários do sistema
                    if grantee in ['postgres', 'migration_user']:
                        continue

                    # Converter códigos
                    db_privileges = []
                    if 'C' in priv_codes:
                        db_privileges.append('CONNECT')
                    if 'T' in priv_codes:
                        db_privileges.append('TEMPORARY')
                    if 'c' in priv_codes:
                        db_privileges.append('CREATE')

                    if priv_codes == 'CTc':
                        db_privileges = ['ALL']

                    if db_privileges:
                        privileges.append({
                            'username': grantee,
                            'privileges': db_privileges
                        })

        except Exception as e:
            print(f"   ❌ Erro get_database_privileges: {e}")

        return privileges

    def apply_privilege_safely_debug(db_name: str, privilege: str, username: str) -> bool:
        """Simula apply_privilege_safely com debug."""
        print(f"      🔧 TENTANDO: GRANT {privilege} ON DATABASE {db_name} TO {username}")

        try:
            with dest_engine.connect() as conn:
                conn = conn.execution_options(autocommit=True)

                if username == "public":
                    grant_query = text(f'GRANT {privilege} ON DATABASE "{db_name}" TO public')
                else:
                    grant_query = text(f'GRANT {privilege} ON DATABASE "{db_name}" TO "{username}"')

                print(f"      📝 SQL: {grant_query}")
                conn.execute(grant_query)
                print(f"      ✅ SUCESSO!")
                return True

        except Exception as e:
            print(f"      ❌ ERRO: {e}")
            return False

    # Executar debug
    existing_users = get_existing_users()
    print(f"👥 Usuários existentes: {len(existing_users)}")

    privileges_applied = 0

    for db_info in databases:
        db_name = db_info['datname']
        original_owner = db_info['owner']

        print(f"\n🔧 Processando {db_name} (owner: {original_owner})")

        # 1. Privilégios PUBLIC (como no sistema)
        print("   📋 1. Aplicando privilégios PUBLIC:")
        if apply_privilege_safely_debug(db_name, "CONNECT", "public"):
            privileges_applied += 1
        if apply_privilege_safely_debug(db_name, "TEMPORARY", "public"):
            privileges_applied += 1

        # 2. Owner original (como no sistema)
        print("   📋 2. Privilégios para owner original:")
        if original_owner != 'postgres' and original_owner != 'migration_user':
            if original_owner in existing_users:
                if apply_privilege_safely_debug(db_name, "ALL", original_owner):
                    print(f"      ✅ ALL → {original_owner}")
                    privileges_applied += 1
            else:
                print(f"      ⚠️ Usuário {original_owner} não existe")

        # 3. Privilégios específicos da origem (AQUI PODE ESTAR O PROBLEMA)
        print("   📋 3. Privilégios específicos da origem:")
        try:
            db_privileges = get_database_privileges_debug(db_name)
            print(f"      📊 Coletados {len(db_privileges)} privilégios:")

            for i, priv_info in enumerate(db_privileges, 1):
                username = priv_info['username']
                privileges = priv_info['privileges']

                print(f"      {i}. {username}: {', '.join(privileges)}")

                # Verificar se usuário existe
                if username not in existing_users:
                    print(f"         ⚠️ Usuário {username} não existe - PULANDO")
                    continue

                # Aplicar cada privilégio
                for privilege in privileges:
                    print(f"         🎯 Aplicando {privilege} para {username}")
                    if apply_privilege_safely_debug(db_name, privilege, username):
                        print(f"         ✅ {privilege} → {username}")
                        privileges_applied += 1
                    else:
                        print(f"         ❌ FALHOU: {privilege} → {username}")

        except Exception as e:
            print(f"      ❌ Erro ao processar privilégios específicos: {e}")

    print(f"\n📊 TOTAL DE PRIVILÉGIOS APLICADOS: {privileges_applied}")


if __name__ == "__main__":
    debug_apply_database_privileges()
