#!/usr/bin/env python3
"""
Script para verificar permissões do Metabase (READ-ONLY)
Não modifica nenhum dado, apenas verifica o estado atual
"""

import json

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def main():
    # Carregar credenciais
    with open('secrets/postgresql_destination_config.json', 'r') as f:
        config = json.load(f)

    conn_params = {
        'host': config['server']['host'],
        'port': config['server']['port'],
        'database': 'metabase_db',
        'user': config['authentication']['user'],
        'password': config['authentication']['password']
    }

    print("=" * 80)
    print("VERIFICAÇÃO DE PERMISSÕES METABASE (READ-ONLY)")
    print("=" * 80)
    print()

    conn = psycopg2.connect(**conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # 1. Verificar usuário metabase_user
    print("1. VERIFICANDO USUÁRIO METABASE_USER:")
    print("-" * 80)
    cur.execute("""
        SELECT
            usename,
            usesuper,
            usecreatedb,
            usebypassrls
        FROM pg_user
        WHERE usename = 'metabase_user';
    """)
    user_info = cur.fetchone()
    if user_info:
        print(f"✓ Usuário existe: {user_info[0]}")
        print(f"  - Superuser: {'Sim' if user_info[1] else 'Não'}")
        print(f"  - CreateDB: {'Sim' if user_info[2] else 'Não'}")
        print(f"  - Bypass RLS: {'Sim' if user_info[3] else 'Não'}")
    else:
        print("✗ Usuário metabase_user NÃO EXISTE")
    print()

    # 2. Verificar ownership das tabelas
    print("2. OWNERSHIP DAS TABELAS:")
    print("-" * 80)
    cur.execute("""
        SELECT
            tablename,
            tableowner
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    tables = cur.fetchall()

    owners_count = {}
    for table_name, owner in tables:
        owners_count[owner] = owners_count.get(owner, 0) + 1
        if len(tables) <= 30:  # Mostrar todas se forem poucas
            print(f"  {table_name:50} → {owner}")

    print()
    print("Resumo de Owners:")
    for owner, count in sorted(owners_count.items()):
        print(f"  {owner}: {count} tabelas")
    print(f"\nTotal de tabelas: {len(tables)}")
    print()

    # 3. Verificar privilégios do metabase_user
    print("3. PRIVILÉGIOS DO METABASE_USER NAS TABELAS:")
    print("-" * 80)
    cur.execute("""
        SELECT
            table_name,
            string_agg(privilege_type, ', ' ORDER BY privilege_type) as privileges
        FROM information_schema.table_privileges
        WHERE grantee = 'metabase_user'
        AND table_schema = 'public'
        GROUP BY table_name
        ORDER BY table_name;
    """)
    privileges = cur.fetchall()

    if privileges:
        if len(privileges) <= 20:
            for table_name, privs in privileges:
                print(f"  {table_name:50} → {privs}")
        else:
            print(f"  Total de tabelas com privilégios: {len(privileges)}")
            print("  Primeiras 10 tabelas:")
            for table_name, privs in privileges[:10]:
                print(f"    {table_name:50} → {privs}")
    else:
        print("  ✗ NENHUM PRIVILÉGIO ENCONTRADO para metabase_user")
    print()

    # 4. Verificar tabela databasechangelog
    print("4. TABELA DATABASECHANGELOG (Liquibase):")
    print("-" * 80)
    cur.execute("""
        SELECT
            tableowner
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename = 'databasechangelog';
    """)
    changelog_owner = cur.fetchone()
    if changelog_owner:
        print(f"  Owner: {changelog_owner[0]}")

        cur.execute("SELECT COUNT(*) FROM databasechangelog;")
        migration_count = cur.fetchone()[0]
        print(f"  Total de migrações: {migration_count}")

        cur.execute("""
            SELECT filename, COUNT(*) as count
            FROM databasechangelog
            GROUP BY filename
            ORDER BY filename DESC
            LIMIT 5;
        """)
        recent_files = cur.fetchall()
        print("\n  Últimos arquivos de migração:")
        for filename, count in recent_files:
            print(f"    {filename}: {count} migrações")
    else:
        print("  ✗ Tabela databasechangelog não encontrada")
    print()

    # 5. Verificar tabela auth_identity
    print("5. TABELA AUTH_IDENTITY:")
    print("-" * 80)
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'auth_identity'
        );
    """)
    table_exists = cur.fetchone()[0]

    if table_exists:
        cur.execute("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'auth_identity'
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()

        print("  Estrutura da tabela:")
        for col_name, data_type, max_len, nullable in columns:
            len_info = f"({max_len})" if max_len else ""
            null_info = "NULL" if nullable == 'YES' else "NOT NULL"
            print(f"    {col_name:20} {data_type}{len_info:15} {null_info}")

        cur.execute("SELECT COUNT(*) FROM auth_identity;")
        count = cur.fetchone()[0]
        print(f"\n  Total de registros: {count}")
    else:
        print("  ✗ Tabela auth_identity não encontrada")
    print()

    # 6. Verificar algumas tabelas críticas do Metabase
    print("6. TABELAS CRÍTICAS DO METABASE:")
    print("-" * 80)
    critical_tables = [
        'core_user',
        'metabase_database',
        'metabase_table',
        'report_card',
        'report_dashboard',
        'permissions',
        'permissions_group'
    ]

    for table_name in critical_tables:
        cur.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
            );
        """)
        exists = cur.fetchone()[0]

        if exists:
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cur.fetchone()[0]

            cur.execute(f"""
                SELECT tableowner
                FROM pg_tables
                WHERE tablename = '{table_name}';
            """)
            owner = cur.fetchone()[0]

            status = "✓" if count > 0 or table_name in [
                'permissions', 'permissions_group'] else "⚠"
            print(
                f"  {status} {table_name:30} Owner: {owner:20} Registros: {count}")
        else:
            print(f"  ✗ {table_name:30} NÃO EXISTE")
    print()

    # 7. Verificar privilégios na database
    print("7. PRIVILÉGIOS DO METABASE_USER NA DATABASE:")
    print("-" * 80)
    cur.execute("""
        SELECT
            datname,
            has_database_privilege('metabase_user', datname, 'CONNECT') as can_connect,
            has_database_privilege('metabase_user', datname, 'CREATE') as can_create,
            has_database_privilege('metabase_user', datname, 'TEMP') as can_temp
        FROM pg_database
        WHERE datname = 'metabase_db';
    """)
    db_privs = cur.fetchone()
    if db_privs:
        print(f"  Database: {db_privs[0]}")
        print(f"  - CONNECT: {'Sim' if db_privs[1] else 'Não'}")
        print(f"  - CREATE: {'Sim' if db_privs[2] else 'Não'}")
        print(f"  - TEMP: {'Sim' if db_privs[3] else 'Não'}")
    print()

    cur.close()
    conn.close()

    print("=" * 80)
    print("VERIFICAÇÃO CONCLUÍDA (nenhuma alteração foi feita)")
    print("=" * 80)


if __name__ == '__main__':
    main()
