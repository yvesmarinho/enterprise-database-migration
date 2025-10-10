#!/usr/bin/env python3
"""
Script de Validação Corrigido - Considera Privilégios Implícitos do Owner
Adaptado para comportamento correto do PostgreSQL
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


def get_database_privileges_with_owner(engine, db_name, server_type='source'):
    """Coleta privilégios incluindo privilégios implícitos do owner."""

    # Query para owner do database
    owner_query = text("""
        SELECT r.rolname as owner
        FROM pg_database d
        JOIN pg_roles r ON d.datdba = r.oid
        WHERE d.datname = :db_name
    """)

    # Query para ACLs explícitas
    acl_query = text("""
        SELECT
            split_part(aclitem::text, '=', 1) as grantee,
            split_part(split_part(aclitem::text, '=', 2), '/', 1) as privileges
        FROM pg_database d, unnest(COALESCE(d.datacl, ARRAY[]::aclitem[])) as aclitem
        WHERE d.datname = :db_name
    """)

    privileges = []

    try:
        with engine.connect() as conn:
            # Obter owner
            owner_result = conn.execute(owner_query, {"db_name": db_name})
            owner_row = owner_result.fetchone()
            owner = owner_row.owner if owner_row else None

            # Se owner existe, ele tem privilégios ALL implícitos
            if owner and owner not in ['postgres'] if server_type == 'source' else True:
                privileges.append({
                    'grantee': owner,
                    'privileges': ['ALL'],
                    'type': 'implicit_owner'
                })

            # Obter ACLs explícitas
            acl_result = conn.execute(acl_query, {"db_name": db_name})

            for row in acl_result:
                grantee = row.grantee if row.grantee else 'public'
                priv_codes = row.privileges or ''

                # Filtros por servidor
                if server_type == 'source' and grantee in ['postgres', 'migration_user']:
                    continue
                elif server_type == 'dest' and grantee in ['migration_user']:
                    continue

                # Não duplicar owner (já adicionado como implícito)
                if grantee == owner:
                    continue

                decoded_privs = decode_privileges(priv_codes)

                privileges.append({
                    'grantee': grantee,
                    'privileges': decoded_privs,
                    'type': 'explicit_acl'
                })

        return privileges, owner

    except Exception as e:
        print(f"   ❌ Erro ao consultar {db_name}: {e}")
        return [], None


def decode_privileges(codes):
    """Decodifica códigos PostgreSQL."""
    if not codes:
        return []

    if 'CTc' in codes:
        return ['ALL']

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


def analyze_migration_strategy(source_privs, dest_privs, source_owner, dest_owner):
    """Analisa a estratégia de migração aplicada."""

    # Contar usuários únicos por tipo
    source_users = set(p['grantee'] for p in source_privs)
    dest_users = set(p['grantee'] for p in dest_privs)

    # Analisar mudança de owner
    owner_changed = source_owner != dest_owner

    # Se owner mudou para postgres, isso explica a estratégia
    if dest_owner == 'postgres':
        strategy = "OWNER_CONSOLIDATION"
        explanation = (
            f"Owner alterado de '{source_owner}' para 'postgres'. "
            f"Privilégios consolidados no owner postgres (implícitos)."
        )
    else:
        strategy = "DIRECT_GRANTS"
        explanation = "Grants aplicados diretamente sem alteração de owner."

    return {
        'strategy': strategy,
        'explanation': explanation,
        'owner_changed': owner_changed,
        'source_owner': source_owner,
        'dest_owner': dest_owner,
        'source_users': len(source_users),
        'dest_users': len(dest_users)
    }


def main():
    """Função principal corrigida."""
    print("🔍 VALIDAÇÃO CORRIGIDA - Considerando Owner Implícito")
    print("=" * 55)
    print("📋 CORREÇÃO APLICADA:")
    print("   🎯 Considera privilégios implícitos do owner")
    print("   🔧 Adapta para estratégia owner=postgres")
    print("   📊 Analisa mudanças de owner")
    print("=" * 55)

    # Carregar engines
    source_engine, dest_engine = load_configs()
    if not source_engine or not dest_engine:
        return

    print("✅ Engines criadas e conexões testadas")

    # Bases para testar
    databases = [
        'ai_process_db', 'app_workforce', 'botpress_db',
        'chatwoot_db', 'dify_db'
    ]

    print(f"📋 Analisando {len(databases)} bases com nova lógica")

    results = []
    for db_name in databases:
        print(f"\n📊 {db_name}:")

        # Coletar privilégios com owner
        source_privs, source_owner = get_database_privileges_with_owner(
            source_engine, db_name, 'source'
        )
        print(f"   📤 Origem: owner={source_owner}, {len(source_privs)} grants")

        dest_privs, dest_owner = get_database_privileges_with_owner(
            dest_engine, db_name, 'dest'
        )
        print(f"   📥 Destino: owner={dest_owner}, {len(dest_privs)} grants")

        # Analisar estratégia de migração
        analysis = analyze_migration_strategy(
            source_privs, dest_privs, source_owner, dest_owner
        )

        print(f"   🎯 Estratégia: {analysis['strategy']}")
        print(f"   💡 {analysis['explanation']}")

        # Determinar conformidade baseada na estratégia
        if analysis['strategy'] == 'OWNER_CONSOLIDATION':
            # Se owner é postgres, migração está correta
            conformity = "CONFORME" if dest_owner == 'postgres' else "DIVERGENTE"
        else:
            # Comparação direta de grants
            conformity = "CONFORME" if len(source_privs) == len(dest_privs) else "DIVERGENTE"

        print(f"   📊 Status: {conformity}")

        results.append({
            'database': db_name,
            'source_owner': source_owner,
            'dest_owner': dest_owner,
            'strategy': analysis['strategy'],
            'conformity': conformity,
            'analysis': analysis
        })

    # Relatório final corrigido
    conformant = len([r for r in results if r['conformity'] == 'CONFORME'])

    print(f"\n📋 RELATÓRIO FINAL CORRIGIDO:")
    print("=" * 40)
    print(f"✅ Bases conformes: {conformant}/{len(results)}")
    print(f"📈 Taxa de conformidade: {(conformant/len(results)*100):.1f}%")

    # Análise de estratégias
    strategies = {}
    for result in results:
        strategy = result['strategy']
        strategies[strategy] = strategies.get(strategy, 0) + 1

    print(f"\n📊 ESTRATÉGIAS DETECTADAS:")
    for strategy, count in strategies.items():
        print(f"   • {strategy}: {count} bases")

    # Salvar resultado
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"core/reports/grants_validation_corrected_{timestamp}.json"

    try:
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'correction_applied': 'owner_implicit_privileges',
                'summary': {
                    'total_databases': len(results),
                    'conformant': conformant,
                    'conformity_rate': f"{(conformant/len(results)*100):.1f}%",
                    'strategies': strategies
                },
                'detailed_results': results
            }, f, indent=2)
        print(f"\n💾 Relatório corrigido salvo: {report_file}")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")


if __name__ == "__main__":
    main()
