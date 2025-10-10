#!/usr/bin/env python3
"""
TESTE DIRETO DA APLICAÇÃO DE GRANTS
Simular exatamente o que o sistema faz na migração
"""

import json

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


def test_grant_application():
    """Testa aplicação direta de grants."""

    # Carregar destino
    with open('secrets/postgresql_destination_config.json', 'r') as f:
        dest_config = json.load(f)

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    dest_engine = create_engine(dest_url)

    print("🔧 TESTE DIRETO DE APLICAÇÃO DE GRANTS")
    print("=" * 50)

    # Testar grants específicos que deveriam existir
    test_grants = [
        {'db': 'app_workforce', 'user': 'app_workforce_user', 'privileges': ['ALL']},
        {'db': 'botpress_db', 'user': 'botpress_user', 'privileges': ['ALL']},
        {'db': 'ai_process_db', 'user': 'ai_process_user', 'privileges': ['ALL']}  # Este deve falhar
    ]

    print("🎯 GRANTS QUE DEVERIAM ESTAR APLICADOS:")
    for grant in test_grants:
        print(f"   • {grant['db']} -> {grant['user']}: {', '.join(grant['privileges'])}")

    print("\n🔍 VERIFICANDO STATUS ATUAL NO DESTINO:")

    with dest_engine.connect() as conn:
        # 1. Verificar usuários existentes
        print("\n👥 USUÁRIOS EXISTENTES:")
        users_query = text("SELECT rolname FROM pg_roles WHERE rolcanlogin = true ORDER BY rolname")
        result = conn.execute(users_query)
        existing_users = [row.rolname for row in result]

        for user in existing_users:
            if user not in ['postgres', 'migration_user']:
                print(f"   ✅ {user}")

        # 2. Verificar grants específicos usando aclexplode
        print("\n🔒 GRANTS ATUAIS (aclexplode):")
        for grant in test_grants:
            db_name = grant['db']
            expected_user = grant['user']

            grants_query = text("""
                SELECT
                    grantee::regrole::text as grantee,
                    privilege_type,
                    is_grantable
                FROM pg_database d,
                     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                WHERE d.datname = :db_name
                AND grantee::regrole::text = :expected_user
                ORDER BY privilege_type
            """)

            try:
                grants_result = conn.execute(grants_query, {
                    "db_name": db_name,
                    "expected_user": expected_user
                })

                user_grants = list(grants_result)

                print(f"   📁 {db_name} -> {expected_user}:")
                if user_grants:
                    for grant_row in user_grants:
                        grantable = " (WITH GRANT OPTION)" if grant_row.is_grantable else ""
                        print(f"      ✅ {grant_row.privilege_type}{grantable}")
                else:
                    print(f"      ❌ SEM GRANTS EXPLÍCITOS")

            except Exception as e:
                print(f"   ❌ Erro verificando {db_name}: {e}")

        # 3. Verificar privileges funcionais
        print("\n🛠️ PRIVILÉGIOS FUNCIONAIS (has_database_privilege):")
        for grant in test_grants:
            db_name = grant['db']
            expected_user = grant['user']

            # Verificar se usuário existe primeiro
            if expected_user not in existing_users:
                print(f"   ⚠️ {db_name} -> {expected_user}: USUÁRIO NÃO EXISTE")
                continue

            try:
                functional_query = text("""
                    SELECT
                        has_database_privilege(:user, :database, 'CONNECT') as connect,
                        has_database_privilege(:user, :database, 'CREATE') as create,
                        has_database_privilege(:user, :database, 'TEMPORARY') as temporary
                """)

                func_result = conn.execute(functional_query, {
                    "user": expected_user,
                    "database": db_name
                })

                func_row = func_result.fetchone()

                privileges = []
                if func_row.connect: privileges.append("CONNECT")
                if func_row.create: privileges.append("CREATE")
                if func_row.temporary: privileges.append("TEMPORARY")

                print(f"   📁 {db_name} -> {expected_user}: {', '.join(privileges) if privileges else 'NENHUM'}")

            except Exception as e:
                print(f"   ❌ Erro funcional {db_name}: {e}")

    print("\n💡 ANÁLISE:")
    print("   • Se grants explícitos estão ausentes MAS privilégios funcionais existem:")
    print("   • Então o problema está na APLICAÇÃO de grants explícitos")
    print("   • Usuários estão herdando privilégios por DEFAULT/PUBLIC")
    print("   • Sistema precisa aplicar GRANT explícito para cada usuário")


def test_manual_grant():
    """Testa aplicação manual de um grant."""

    with open('secrets/postgresql_destination_config.json', 'r') as f:
        dest_config = json.load(f)

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    dest_engine = create_engine(dest_url)

    print("\n" + "="*50)
    print("🧪 TESTE MANUAL DE GRANT")
    print("="*50)

    # Testar aplicação manual
    test_db = 'app_workforce'
    test_user = 'app_workforce_user'

    with dest_engine.connect() as conn:
        conn = conn.execution_options(autocommit=True)

        # Verificar estado antes
        print("📋 ANTES do grant manual:")
        before_query = text("""
            SELECT count(*) as explicit_grants
            FROM pg_database d, aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
            WHERE d.datname = :db_name AND grantee::regrole::text = :user_name
        """)

        before_result = conn.execute(before_query, {"db_name": test_db, "user_name": test_user})
        before_count = before_result.fetchone().explicit_grants
        print(f"   Grants explícitos antes: {before_count}")

        # Aplicar grant manual
        try:
            grant_query = text(f'GRANT ALL ON DATABASE "{test_db}" TO "{test_user}"')
            conn.execute(grant_query)
            print(f"   ✅ Executado: GRANT ALL ON DATABASE {test_db} TO {test_user}")

            # Verificar estado depois
            after_result = conn.execute(before_query, {"db_name": test_db, "user_name": test_user})
            after_count = after_result.fetchone().explicit_grants
            print(f"   Grants explícitos depois: {after_count}")

            if after_count > before_count:
                print("   🎯 GRANT MANUAL FUNCIONOU!")
            else:
                print("   ❌ Grant manual não teve efeito")

        except Exception as e:
            print(f"   ❌ Erro no grant manual: {e}")


if __name__ == "__main__":
    test_grant_application()
    test_manual_grant()
