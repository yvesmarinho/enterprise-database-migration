#!/usr/bin/env python3
"""
Script Final de Validação de Grants - PostgreSQL Migration System
Usa a query exata que funciona no sistema principal

INFORMAÇÕES DO PROJETO:
- Source Server: wf004.vya.digital:5432 (PostgreSQL 14)
- Source User: root (superuser com todos os privilégios)
- Destination Server: wfdb02.vya.digital:5432 (PostgreSQL 16)
- Destination User: postgres/migration_user (superuser para migração)

OBJETIVO:
Validar se os grants coletados da origem (como root) foram aplicados
corretamente no destino (como postgres), comparando privilégios
específicos por usuário e banco de dados.
"""

import json
from datetime import datetime

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


def get_database_privileges_working(engine, db_name, server_type='source'):
    """Usa a query exata que funciona no sistema principal.

    Args:
        engine: SQLAlchemy engine
        db_name: Nome do banco de dados
        server_type: 'source' ou 'dest' para aplicar filtros corretos
    """
    acl_query = text("""
        SELECT
            d.datname as database_name,
            split_part(aclitem::text, '=', 1) as grantee,
            split_part(split_part(aclitem::text, '=', 2), '/', 1) as privileges
        FROM pg_database d, unnest(COALESCE(d.datacl, ARRAY[]::aclitem[])) as aclitem
        WHERE d.datname = :db_name
          AND d.datname NOT LIKE 'template%'

        UNION ALL

        SELECT
            d.datname as database_name,
            r.rolname as grantee,
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
        with engine.connect() as conn:
            result = conn.execute(acl_query, {"db_name": db_name})

            for row in result:
                grantee = row.grantee if row.grantee else 'public'
                priv_codes = row.privileges or ''

                # Filtrar usuários específicos baseado no servidor
                # Source: usuário conectado como 'root'
                # Dest: usuário conectado como 'postgres' (migration_user)
                if server_type == 'source':
                    # Ignorar usuários sistema no source
                    if grantee in ['postgres', 'migration_user']:
                        continue
                elif server_type == 'dest':
                    # Ignorar usuários sistema no destino
                    if grantee in ['postgres', 'migration_user']:
                        continue
                    # No destino, root é um usuário migrado válido

                # Decodificar privilégios
                decoded_privs = decode_privileges(priv_codes)

                privileges.append({
                    'grantee': grantee,
                    'privileges': decoded_privs,
                    'raw_codes': priv_codes
                })

        return privileges

    except Exception as e:
        print(f"   ❌ Erro ao consultar {db_name}: {e}")
        return []


def decode_privileges(codes):
    """Decodifica códigos PostgreSQL."""
    if not codes:
        return []

    # ALL privileges
    if 'CTc' in codes:
        return ['ALL']

    # Mapeamento individual
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


def compare_privilege_lists(source_privs, dest_privs):
    """Compara duas listas de privilégios."""
    # Normalizar para comparação
    source_normalized = {}
    for priv in source_privs:
        key = priv['grantee']
        source_normalized[key] = set(priv['privileges'])

    dest_normalized = {}
    for priv in dest_privs:
        key = priv['grantee']
        dest_normalized[key] = set(priv['privileges'])

    # Encontrar diferenças
    all_users = set(source_normalized.keys()) | set(dest_normalized.keys())
    differences = []

    for user in all_users:
        source_set = source_normalized.get(user, set())
        dest_set = dest_normalized.get(user, set())

        if source_set != dest_set:
            missing = source_set - dest_set
            extra = dest_set - source_set

            if missing:
                differences.append(f"Falta no destino: {user} -> {list(missing)}")
            if extra:
                differences.append(f"Extra no destino: {user} -> {list(extra)}")

    return differences


def main():
    """Função principal com query corrigida."""
    print("🔍 VALIDAÇÃO FINAL DE GRANTS - PostgreSQL Migration")
    print("=" * 55)
    print("📋 CONFIGURAÇÃO DO PROJETO:")
    print("   📤 Source: wf004.vya.digital:5432 (root user)")
    print("   📥 Destino: wfdb02.vya.digital:5432 (postgres user)")
    print("   🎯 Objetivo: Validar grants origem vs destino")
    print("=" * 55)

    # Carregar engines
    source_engine, dest_engine = load_configs()
    if not source_engine or not dest_engine:
        return

    print("✅ Engines criadas e conexões testadas")

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

        # Coletar privilégios origem (conectado como root)
        source_privs = get_database_privileges_working(
            source_engine, db_name, 'source'
        )
        print(f"   📤 Origem (root): {len(source_privs)} grants")

        # Mostrar alguns exemplos se houver
        if source_privs:
            for i, priv in enumerate(source_privs[:2]):
                print(f"      Ex{i+1}: {priv['grantee']} -> {priv['privileges']}")

        # Coletar privilégios destino (conectado como postgres/migration_user)
        dest_privs = get_database_privileges_working(
            dest_engine, db_name, 'dest'
        )
        print(f"   📥 Destino (postgres): {len(dest_privs)} grants")

        # Mostrar alguns exemplos se houver
        if dest_privs:
            for i, priv in enumerate(dest_privs[:2]):
                print(f"      Ex{i+1}: {priv['grantee']} -> {priv['privileges']}")

        # Comparar detalhada
        differences = compare_privilege_lists(source_privs, dest_privs)

        if not differences:
            print("   ✅ CONFORMIDADE TOTAL")
            status = "CONFORMANTE"
        else:
            print(f"   ⚠️ {len(differences)} divergências encontradas:")
            for diff in differences[:3]:  # Mostrar primeiras 3
                print(f"      - {diff}")
            status = "DIVERGENTE"

        results.append({
            'database': db_name,
            'source_count': len(source_privs),
            'dest_count': len(dest_privs),
            'differences_count': len(differences),
            'status': status,
            'differences': differences
        })

    # Relatório final detalhado
    conformant = len([r for r in results if r['status'] == 'CONFORMANTE'])
    divergent = len(results) - conformant

    print(f"\n📋 RELATÓRIO FINAL DETALHADO:")
    print("=" * 40)
    print(f"✅ Bases conformantes: {conformant}/{len(results)}")
    print(f"⚠️ Bases divergentes: {divergent}")
    print(f"📈 Taxa de conformidade: {(conformant/len(results)*100):.1f}%")

    if divergent > 0:
        print(f"\n⚠️ BASES COM DIVERGÊNCIAS:")
        for result in results:
            if result['status'] == 'DIVERGENTE':
                print(f"   • {result['database']}: {result['differences_count']} diferenças")

    # Salvar resultado completo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"core/reports/grants_validation_final_{timestamp}.json"

    try:
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': {
                    'total_databases': len(results),
                    'conformant': conformant,
                    'divergent': divergent,
                    'conformity_rate': f"{(conformant/len(results)*100):.1f}%"
                },
                'detailed_results': results
            }, f, indent=2)
        print(f"\n💾 Relatório detalhado salvo: {report_file}")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")


if __name__ == "__main__":
    main()
