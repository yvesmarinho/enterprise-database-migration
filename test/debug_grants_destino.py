#!/usr/bin/env python3
"""
Diagnóstico de Grants no Destino
Investiga por que o destino retorna 0 grants
"""

import json

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


def main():
    """Diagnóstico do problema de grants no destino."""
    print("🔍 DIAGNÓSTICO DE GRANTS NO DESTINO")
    print("=" * 50)

    # Carregar config do destino
    with open('secrets/postgresql_destination_config.json', 'r') as f:
        dest_config = json.load(f)

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    engine = create_engine(dest_url)

    print("✅ Conectado ao destino")

    # Teste 1: Verificar se base existe
    db_name = 'ai_process_db'
    print(f"\n🔍 TESTE 1: Verificando se {db_name} existe...")

    with engine.connect() as conn:
        # Verificar se database existe
        db_check = text("SELECT datname FROM pg_database WHERE datname = :db")
        result = conn.execute(db_check, {"db": db_name})
        exists = result.fetchone()

        if exists:
            print(f"   ✅ Database {db_name} existe")
        else:
            print(f"   ❌ Database {db_name} NÃO existe")
            return

    # Teste 2: Verificar datacl diretamente
    print(f"\n🔍 TESTE 2: Verificando datacl diretamente...")

    with engine.connect() as conn:
        datacl_query = text("""
            SELECT datname, datacl::text as datacl_text,
                   CASE WHEN datacl IS NULL THEN 'NULL' ELSE 'HAS_DATA' END as status
            FROM pg_database
            WHERE datname = :db
        """)
        result = conn.execute(datacl_query, {"db": db_name})
        row = result.fetchone()

        if row:
            print(f"   📋 Database: {row.datname}")
            print(f"   📊 Status datacl: {row.status}")
            if row.datacl_text:
                print(f"   📝 datacl: {row.datacl_text}")
            else:
                print(f"   ⚠️ datacl é NULL")

    # Teste 3: Verificar owner
    print(f"\n🔍 TESTE 3: Verificando owner do database...")

    with engine.connect() as conn:
        owner_query = text("""
            SELECT d.datname, r.rolname as owner
            FROM pg_database d
            JOIN pg_roles r ON d.datdba = r.oid
            WHERE d.datname = :db
        """)
        result = conn.execute(owner_query, {"db": db_name})
        row = result.fetchone()

        if row:
            print(f"   👤 Owner atual: {row.owner}")

    # Teste 4: Tentar query completa sem filtros
    print(f"\n🔍 TESTE 4: Query completa sem filtros...")

    with engine.connect() as conn:
        full_query = text("""
            SELECT
                d.datname as database_name,
                split_part(aclitem::text, '=', 1) as grantee,
                split_part(split_part(aclitem::text, '=', 2), '/', 1) as privileges,
                aclitem::text as raw_acl
            FROM pg_database d, unnest(COALESCE(d.datacl, ARRAY[]::aclitem[])) as aclitem
            WHERE d.datname = :db_name
        """)

        result = conn.execute(full_query, {"db_name": db_name})
        rows = list(result)

        print(f"   📊 Resultados encontrados: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"      {i+1}. {row.grantee} -> {row.privileges} (raw: {row.raw_acl})")

    # Teste 5: Verificar se há ACLs em outras bases
    print(f"\n🔍 TESTE 5: Verificando ACLs em outras bases...")

    with engine.connect() as conn:
        other_query = text("""
            SELECT datname,
                   CASE WHEN datacl IS NULL THEN 'NULL' ELSE 'HAS_ACLS' END as acl_status,
                   array_length(datacl, 1) as acl_count
            FROM pg_database
            WHERE datname IN ('app_workforce', 'botpress_db', 'chatwoot_db')
            ORDER BY datname
        """)

        result = conn.execute(other_query)
        rows = list(result)

        print(f"   📊 Status de outras bases:")
        for row in rows:
            count = row.acl_count if row.acl_count else 0
            print(f"      • {row.datname}: {row.acl_status} ({count} ACLs)")


if __name__ == "__main__":
    main()
