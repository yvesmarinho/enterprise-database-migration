#!/usr/bin/env python3
"""
INVESTIGAÇÃO IMEDIATA DA CONTRADIÇÃO
Verificar por que grants aplicados não aparecem
"""

import json

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


def investigate_grant_contradiction():
    """Investiga por que grants não aparecem após aplicação."""

    print("🕵️ INVESTIGAÇÃO DA CONTRADIÇÃO DE GRANTS")
    print("=" * 50)

    config_path = ('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/'
                  'enterprise-database-migration/secrets/'
                  'postgresql_destination_config.json')

    with open(config_path, 'r') as f:
        dest_config = json.load(f)

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    dest_engine = create_engine(dest_url)

    # Usuários testados
    test_users = ['app_workforce_user', 'botpress_user', 'ai_process_user']
    test_databases = ['app_workforce', 'botpress_db', 'ai_process_db']

    with dest_engine.connect() as conn:

        # 1. VERIFICAR SE USUÁRIOS EXISTEM
        print("👥 1. VERIFICANDO EXISTÊNCIA DOS USUÁRIOS:")
        print("-" * 40)

        for user in test_users:
            user_query = text("""
                SELECT rolname, rolcanlogin, oid
                FROM pg_roles
                WHERE rolname = :username
            """)

            result = conn.execute(user_query, {"username": user})
            user_row = result.fetchone()

            if user_row:
                print(f"   ✅ {user}: EXISTS (oid={user_row.oid}, login={user_row.rolcanlogin})")
            else:
                print(f"   ❌ {user}: NÃO EXISTE!")

        # 2. VERIFICAR TODOS OS GRANTS ATUAIS
        print(f"\n📊 2. GRANTS ATUAIS NOS BANCOS DE TESTE:")
        print("-" * 45)

        for db_name in test_databases:
            print(f"\n📁 {db_name}:")

            # Todos os grants do banco
            all_grants_query = text("""
                SELECT
                    grantee::regrole::text as grantee,
                    privilege_type,
                    is_grantable
                FROM pg_database d,
                     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                WHERE d.datname = :db_name
                ORDER BY grantee, privilege_type
            """)

            result = conn.execute(all_grants_query, {"db_name": db_name})
            grants = list(result)

            if grants:
                current_grantee = None
                for grant in grants:
                    if grant.grantee != current_grantee:
                        current_grantee = grant.grantee
                        print(f"   👤 {current_grantee}:")

                    grantable = " (GRANTABLE)" if grant.is_grantable else ""
                    print(f"      • {grant.privilege_type}{grantable}")
            else:
                print("   ⚠️ SEM GRANTS EXPLÍCITOS")

        # 3. VERIFICAR OWNER DOS BANCOS
        print(f"\n🏠 3. OWNERS DOS BANCOS:")
        print("-" * 25)

        for db_name in test_databases:
            owner_query = text("""
                SELECT r.rolname as owner, d.datname
                FROM pg_database d
                JOIN pg_roles r ON d.datdba = r.oid
                WHERE d.datname = :db_name
            """)

            result = conn.execute(owner_query, {"db_name": db_name})
            owner_row = result.fetchone()

            if owner_row:
                print(f"   📁 {owner_row.datname}: owner = {owner_row.owner}")

        # 4. VERIFICAR PRIVILEGES FUNCIONAIS
        print(f"\n🛠️ 4. PRIVILÉGIOS FUNCIONAIS (has_database_privilege):")
        print("-" * 55)

        for db_name in test_databases:
            print(f"\n📁 {db_name}:")

            for user in test_users:
                # Verificar se usuário existe primeiro
                user_check = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :user"), {"user": user})
                if not user_check.fetchone():
                    print(f"   ⚠️ {user}: USUÁRIO NÃO EXISTE")
                    continue

                try:
                    priv_query = text("""
                        SELECT
                            has_database_privilege(:user, :database, 'CONNECT') as connect,
                            has_database_privilege(:user, :database, 'CREATE') as create,
                            has_database_privilege(:user, :database, 'TEMPORARY') as temporary
                    """)

                    priv_result = conn.execute(priv_query, {"user": user, "database": db_name})
                    priv_row = priv_result.fetchone()

                    privileges = []
                    if priv_row.connect: privileges.append("CONNECT")
                    if priv_row.create: privileges.append("CREATE")
                    if priv_row.temporary: privileges.append("TEMPORARY")

                    if privileges:
                        print(f"   ✅ {user}: {', '.join(privileges)}")
                    else:
                        print(f"   ❌ {user}: SEM PRIVILÉGIOS")

                except Exception as e:
                    print(f"   ❌ {user}: ERRO - {e}")


def test_manual_grant_verification():
    """Testa aplicação manual e verificação imediata."""

    print(f"\n🧪 TESTE DE GRANT MANUAL E VERIFICAÇÃO")
    print("=" * 45)

    config_path = ('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/'
                  'enterprise-database-migration/secrets/'
                  'postgresql_destination_config.json')

    with open(config_path, 'r') as f:
        dest_config = json.load(f)

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    dest_engine = create_engine(dest_url)

    test_db = 'app_workforce'
    test_user = 'app_workforce_user'

    with dest_engine.connect() as conn:
        conn = conn.execution_options(autocommit=True)

        # Verificar se usuário existe
        user_check = conn.execute(text("SELECT rolname FROM pg_roles WHERE rolname = :user"), {"user": test_user})
        if not user_check.fetchone():
            print(f"❌ PROBLEMA: Usuário {test_user} NÃO EXISTE!")
            print("   Este é o motivo dos grants não aparecerem!")
            return

        print(f"✅ Usuário {test_user} existe")

        # Estado antes
        print("\n📋 Estado ANTES do grant manual:")
        before_query = text("""
            SELECT count(*) as count
            FROM pg_database d, aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
            WHERE d.datname = :db_name AND grantee::regrole::text = :user_name
        """)

        before_result = conn.execute(before_query, {"db_name": test_db, "user_name": test_user})
        before_count = before_result.fetchone().count
        print(f"   Grants antes: {before_count}")

        # Aplicar grant
        try:
            grant_query = text(f'GRANT ALL ON DATABASE "{test_db}" TO "{test_user}"')
            conn.execute(grant_query)
            print(f"✅ Grant aplicado: GRANT ALL ON DATABASE {test_db} TO {test_user}")
        except Exception as e:
            print(f"❌ Erro aplicando grant: {e}")
            return

        # Estado depois
        after_result = conn.execute(before_query, {"db_name": test_db, "user_name": test_user})
        after_count = after_result.fetchone().count
        print(f"   Grants depois: {after_count}")

        if after_count > before_count:
            print("🎯 GRANT MANUAL FUNCIONOU - grants persistem!")
        else:
            print("❌ Grant não persistiu - problema grave!")


if __name__ == "__main__":
    investigate_grant_contradiction()
    test_manual_grant_verification()
