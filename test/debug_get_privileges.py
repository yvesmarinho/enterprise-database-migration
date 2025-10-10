#!/usr/bin/env python3
"""
Teste Específico do get_database_privileges
Descobrir por que não está coletando grants específicos
"""

import json

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


def test_get_database_privileges(db_name='app_workforce'):
    """Testa especificamente a função get_database_privileges."""

    # Carregar config
    with open('secrets/postgresql_source_config.json', 'r') as f:
        source_config = json.load(f)

    source_url = get_sqlalchemy_url(source_config, database='postgres')
    source_engine = create_engine(source_url)

    print(f"🔍 TESTANDO get_database_privileges para '{db_name}'")
    print("=" * 60)

    # Query EXATA do sistema atual
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

        -- Adicionar owner se não tem ACL explícita
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

    try:
        with source_engine.connect() as conn:
            result = conn.execute(acl_query, {"db_name": db_name})

            print("📋 RESULTADOS BRUTOS DA QUERY:")
            rows = list(result)
            for i, row in enumerate(rows, 1):
                print(f"   {i}. grantee='{row.grantee}', privileges='{row.privileges}', grantor='{row.grantor}'")

            print(f"\n📊 Total de linhas: {len(rows)}")

            # Simular processamento do sistema
            print("\n🔄 PROCESSAMENTO DO SISTEMA:")
            privileges = []

            for row in rows:
                grantee = row.grantee if row.grantee else 'public'
                priv_codes = row.privileges or ''

                print(f"   Processando: grantee='{grantee}', priv_codes='{priv_codes}'")

                # Ignorar usuários do sistema (AQUI PODE ESTAR O PROBLEMA!)
                if grantee in ['postgres', 'migration_user']:
                    print(f"   ❌ IGNORADO: {grantee} está na lista de sistema")
                    continue

                # Se grantee vazio, vira 'public'
                if grantee == '':
                    grantee = 'public'
                    print(f"   🔄 Convertido para 'public'")

                # Converter códigos de privilégio
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
                    print(f"   ✅ ADICIONADO: {grantee} -> {', '.join(db_privileges)}")
                else:
                    print(f"   ⚠️ SEM PRIVILÉGIOS: {grantee}")

            print(f"\n📊 RESULTADO FINAL: {len(privileges)} privilégios coletados")
            for priv in privileges:
                print(f"   • {priv['username']}: {', '.join(priv['privileges'])}")

            # Testar com bancos específicos conhecidos
            print(f"\n🔍 COMPARANDO COM RESULTADO ESPERADO:")
            print("   Esperado (do resultado anterior):")
            print("   • app_workforce_user -> CONNECT, CREATE, TEMPORARY")
            print("   • testemigracao -> CONNECT, CREATE, TEMPORARY")

            return privileges

    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


def test_multiple_databases():
    """Testa múltiplos bancos para comparação."""
    databases = ['app_workforce', 'botpress_db', 'ai_process_db']

    for db_name in databases:
        print(f"\n" + "="*60)
        privileges = test_get_database_privileges(db_name)
        print()


if __name__ == "__main__":
    test_multiple_databases()
