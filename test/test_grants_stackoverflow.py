#!/usr/bin/env python3
"""
Testador de Grants Usando Query Completa do StackOverflow
Análise definitiva de onde estão os grants reais
"""

import json

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


def load_configs():
    """Carrega configurações."""
    try:
        with open('secrets/postgresql_source_config.json', 'r') as f:
            source_config = json.load(f)

        with open('secrets/postgresql_destination_config.json', 'r') as f:
            dest_config = json.load(f)

        source_url = get_sqlalchemy_url(source_config, database='postgres')
        dest_url = get_sqlalchemy_url(dest_config, database='postgres')

        source_engine = create_engine(source_url)
        dest_engine = create_engine(dest_url)

        return source_engine, dest_engine

    except Exception as e:
        print(f"❌ Erro: {e}")
        return None, None


def get_complete_user_privileges(engine, username, server_name):
    """Executa query completa do StackOverflow para um usuário específico."""

    # Query completa do StackOverflow adaptada
    query = text("""
        -- Cluster permissions not "on" anything else
        SELECT
          'cluster' AS on,
          NULL AS name,
          unnest(
            CASE WHEN rolcanlogin THEN ARRAY['LOGIN'] ELSE ARRAY[]::text[] END
            || CASE WHEN rolsuper THEN ARRAY['SUPERUSER'] ELSE ARRAY[]::text[] END
            || CASE WHEN rolcreaterole THEN ARRAY['CREATE ROLE'] ELSE ARRAY[]::text[] END
            || CASE WHEN rolcreatedb THEN ARRAY['CREATE DATABASE'] ELSE ARRAY[]::text[] END
          ) AS privilege_type
        FROM pg_roles
        WHERE rolname = :username

        UNION ALL

        -- Direct role memberships
        SELECT 'role' AS on, groups.rolname AS name, 'MEMBER' AS privilege_type
        FROM pg_auth_members mg
        INNER JOIN pg_roles groups ON groups.oid = mg.roleid
        INNER JOIN pg_roles members ON members.oid = mg.member
        WHERE members.rolname = :username

        -- Database ownership
        UNION ALL
        SELECT 'database' AS on, quote_ident(datname) AS name, 'OWNER' AS privilege_type
        FROM pg_database d
        WHERE d.datdba = :username::regrole

        UNION ALL

        -- Database privileges
        SELECT 'database' AS on, quote_ident(datname) AS name, privilege_type
        FROM pg_database d
        CROSS JOIN aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
        WHERE grantee = :username::regrole

        UNION ALL

        -- Schema ownership
        SELECT 'schema' AS on, n.oid::regnamespace::text AS name, 'OWNER' AS privilege_type
        FROM pg_namespace n
        WHERE n.nspowner = :username::regrole

        UNION ALL

        -- Schema privileges
        SELECT 'schema' AS on, n.oid::regnamespace::text AS name, privilege_type
        FROM pg_namespace n
        CROSS JOIN aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner)))
        WHERE grantee = :username::regrole

        ORDER BY on, name, privilege_type
    """)

    try:
        with engine.connect() as conn:
            print(f"🔍 {server_name} - Privilégios para '{username}':")
            result = conn.execute(query, {"username": username})

            privileges = []
            for row in result:
                privilege = {
                    'object_type': row[0],
                    'object_name': row[1],
                    'privilege_type': row[2]
                }
                privileges.append(privilege)

                # Formatação limpa
                obj_name = row[1] if row[1] else "N/A"
                print(f"   {row[0].upper():<12} {obj_name:<25} {row[2]}")

            return privileges

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return []


def test_database_privileges_methods(engine, server_name):
    """Testa diferentes métodos de buscar privilégios de banco."""

    print(f"\n📊 {server_name} - MÉTODOS DE BUSCA DE GRANTS:")
    print("=" * 60)

    # Método 1: Consulta direta de datacl
    print("\n🔹 MÉTODO 1: Consulta direta datacl")
    try:
        with engine.connect() as conn:
            query1 = text("""
                SELECT
                    datname,
                    datacl,
                    r.rolname as owner
                FROM pg_database d
                JOIN pg_roles r ON d.datdba = r.oid
                WHERE datname IN ('ai_process_db', 'app_workforce', 'botpress_db')
                ORDER BY datname
            """)

            result = conn.execute(query1)
            for row in result:
                print(f"   {row.datname}: datacl={row.datacl}, owner={row.owner}")
    except Exception as e:
        print(f"   ❌ Erro método 1: {e}")

    # Método 2: Usando aclexplode
    print("\n🔹 MÉTODO 2: Usando aclexplode")
    try:
        with engine.connect() as conn:
            query2 = text("""
                SELECT
                    d.datname,
                    grantee::regrole::text as grantee,
                    privilege_type,
                    is_grantable
                FROM pg_database d,
                     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                WHERE d.datname IN ('ai_process_db', 'app_workforce', 'botpress_db')
                ORDER BY d.datname, grantee, privilege_type
            """)

            result = conn.execute(query2)
            for row in result:
                grantable = " (WITH GRANT OPTION)" if row.is_grantable else ""
                print(f"   {row.datname}: {row.grantee} -> {row.privilege_type}{grantable}")
    except Exception as e:
        print(f"   ❌ Erro método 2: {e}")

    # Método 3: Usando has_database_privilege
    print("\n🔹 MÉTODO 3: Verificação funcional has_database_privilege")
    try:
        with engine.connect() as conn:
            # Primeiro buscar usuários
            users_query = text("""
                SELECT rolname FROM pg_roles
                WHERE rolcanlogin = true
                AND rolname NOT LIKE 'pg_%'
                AND rolname NOT IN ('postgres', 'migration_user')
                ORDER BY rolname
                LIMIT 5
            """)

            users_result = conn.execute(users_query)
            users = [row.rolname for row in users_result]

            databases = ['ai_process_db', 'app_workforce', 'botpress_db']

            for db in databases:
                print(f"   📁 {db}:")
                for user in users:
                    try:
                        priv_query = text("""
                            SELECT
                                has_database_privilege(:user, :database, 'CONNECT') as connect,
                                has_database_privilege(:user, :database, 'CREATE') as create,
                                has_database_privilege(:user, :database, 'TEMPORARY') as temporary
                        """)

                        priv_result = conn.execute(priv_query, {"user": user, "database": db})
                        priv_row = priv_result.fetchone()

                        privileges = []
                        if priv_row.connect: privileges.append("CONNECT")
                        if priv_row.create: privileges.append("CREATE")
                        if priv_row.temporary: privileges.append("TEMPORARY")

                        if privileges:
                            print(f"      {user}: {', '.join(privileges)}")

                    except Exception as e:
                        print(f"      {user}: ERRO - {e}")

    except Exception as e:
        print(f"   ❌ Erro método 3: {e}")


def main():
    """Função principal com análise completa."""
    print("🔍 ANÁLISE COMPLETA DE GRANTS - Query StackOverflow")
    print("=" * 60)

    # Carregar engines
    source_engine, dest_engine = load_configs()
    if not source_engine or not dest_engine:
        return

    # Testar usuários específicos
    test_users = ['ai_process', 'app_workforce', 'botpress', 'chatwoot', 'dify']

    print("📋 TESTANDO USUÁRIOS ESPECÍFICOS:")
    print("=" * 60)

    for username in test_users:
        print(f"\n👤 USUÁRIO: {username}")
        print("-" * 40)

        print("📤 ORIGEM:")
        source_privs = get_complete_user_privileges(source_engine, username, "ORIGEM")

        print("\n📥 DESTINO:")
        dest_privs = get_complete_user_privileges(dest_engine, username, "DESTINO")

        # Comparação rápida
        source_dbs = [p for p in source_privs if p['object_type'] == 'database']
        dest_dbs = [p for p in dest_privs if p['object_type'] == 'database']

        print(f"\n📊 COMPARAÇÃO:")
        print(f"   Origem: {len(source_dbs)} privilégios de banco")
        print(f"   Destino: {len(dest_dbs)} privilégios de banco")

    # Testar métodos diferentes
    test_database_privileges_methods(source_engine, "ORIGEM")
    test_database_privileges_methods(dest_engine, "DESTINO")


if __name__ == "__main__":
    main()
