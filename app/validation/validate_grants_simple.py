#!/usr/bin/env python3
"""
Script Simplificado de Validação de Grants
Usa a mesma lógica do sistema principal de migração
"""

import json
from datetime import datetime

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


def load_configs():
    """Carrega configurações e cria engines."""
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


def get_database_privileges(engine, db_name):
    """Usa a mesma query do sistema principal."""
    query = text("""
        SELECT
            datname,
            CASE
                WHEN datacl IS NULL THEN 'public=CTc'
                ELSE unnest(datacl)::text
            END AS acl_entry
        FROM pg_database
        WHERE datname = :db_name
    """)

    privileges = []
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"db_name": db_name})

            for row in result:
                acl = row.acl_entry
                if '=' in acl:
                    parts = acl.split('=')
                    grantee = parts[0] if parts[0] else 'public'
                    priv_codes = parts[1].split('/')[0] if len(parts) > 1 else ''

                    # Decodificar privilégios
                    decoded_privs = decode_privileges(priv_codes)

                    privileges.append({
                        'grantee': grantee,
                        'privileges': decoded_privs,
                        'raw': acl
                    })

        return privileges

    except Exception as e:
        print(f"   ❌ Erro ao consultar {db_name}: {e}")
        return []


def decode_privileges(codes):
    """Decodifica códigos de privilégio PostgreSQL."""
    if not codes:
        return []

    # Se tem CTc, é ALL
    if 'CTc' in codes:
        return ['ALL']

    # Mapear códigos individuais
    priv_map = {
        'c': 'CONNECT', 'C': 'CREATE', 'T': 'TEMPORARY',
        'a': 'INSERT', 'r': 'SELECT', 'w': 'UPDATE',
        'd': 'DELETE', 'D': 'TRUNCATE'
    }

    privileges = []
    for code in codes:
        if code in priv_map:
            privileges.append(priv_map[code])

    return privileges if privileges else ['CONNECT']


def main():
    """Função principal simplificada."""
    print("🔍 VALIDAÇÃO SIMPLIFICADA DE GRANTS")
    print("=" * 50)

    # Carregar engines
    source_engine, dest_engine = load_configs()
    if not source_engine or not dest_engine:
        return

    print("✅ Engines criadas com sucesso")

    # Top 10 bases de dados
    databases = [
        'ai_process_db', 'app_workforce', 'botpress_db',
        'botpress_db_dev', 'chatwoot002_db', 'chatwoot003_db',
        'chatwoot004_db', 'chatwoot_db', 'dify_db', 'dw_chatwoot_db'
    ]

    print(f"📋 Validando {len(databases)} bases de dados")

    results = []
    for db_name in databases:
        print(f"\n📊 {db_name}:")

        # Coletar privilégios origem
        source_privs = get_database_privileges(source_engine, db_name)
        print(f"   📤 Origem: {len(source_privs)} grants")

        # Coletar privilégios destino
        dest_privs = get_database_privileges(dest_engine, db_name)
        print(f"   📥 Destino: {len(dest_privs)} grants")

        # Comparar simples
        if len(source_privs) == len(dest_privs):
            print("   ✅ Contagem igual")
            status = "OK"
        else:
            print(f"   ⚠️ Diferença: {len(source_privs)} vs {len(dest_privs)}")
            status = "DIFF"

        results.append({
            'database': db_name,
            'source_count': len(source_privs),
            'dest_count': len(dest_privs),
            'status': status
        })

    # Relatório final
    print(f"\n📋 RESUMO FINAL:")
    ok_count = len([r for r in results if r['status'] == 'OK'])
    print(f"✅ Bases OK: {ok_count}/{len(results)}")
    print(f"⚠️ Bases com diferenças: {len(results) - ok_count}")

    # Salvar resultado
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"core/reports/grants_validation_simple_{timestamp}.json"

    try:
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Resultado salvo: {report_file}")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")


if __name__ == "__main__":
    main()
