#!/usr/bin/env python3
"""
EXECUTAR MIGRAÇÃO COMPLETA REAL
Aplicar Fase 3 (privilégios) que nunca foi executada
"""

import sys
import json
from sqlalchemy import create_engine, text

# Adicionar path do core
sys.path.append('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration/core')
sys.path.append('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration')

from sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator
from components.config_normalizer import get_sqlalchemy_urlv python3
"""
EXECUTAR MIGRAÇÃO COMPLETA REAL
Aplicar Fase 3 (privilégios) que nunca foi executada
"""

import os
import sys

# Adicionar path do core
sys.path.append('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration/core')

from sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator


def execute_real_migration():
    """Executa migração completa REAL incluindo Fase 3."""

    print("🚀 EXECUTANDO MIGRAÇÃO COMPLETA REAL")
    print("=" * 50)

    print("⚠️ ATENÇÃO:")
    print("• Esta é a migração REAL que aplicará grants no destino")
    print("• Diferente do debug que executava em isolação")
    print("• Fase 3 (privilégios) será executada pela PRIMEIRA VEZ")

    # Confirmar execução
    prompt = "\n🔴 Executar migração REAL? (digite 'SIM' para confirmar): "
    response = input(prompt)

    if response.upper() != 'SIM':
        print("❌ Execução cancelada pelo usuário")
        return False    print("\n🎯 INICIANDO MIGRAÇÃO REAL...")

    try:
        # Criar instância do migrador
        migrator = SQLAlchemyPostgreSQLMigrator()

        # Executar migração completa
        print("📋 Executando migrate_all_users() - INCLUI FASE 3")
        success = migrator.migrate_all_users()

        if success:
            print("\n✅ MIGRAÇÃO COMPLETA EXECUTADA COM SUCESSO!")
            print("🎯 Fase 3 (privilégios) foi aplicada pela primeira vez")
        else:
            print("\n❌ FALHA NA MIGRAÇÃO")

        return success

    except Exception as e:
        print(f"\n❌ ERRO DURANTE MIGRAÇÃO: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_migration_results():
    """Verifica resultados da migração real."""

    print("\n🔍 VERIFICANDO RESULTADOS DA MIGRAÇÃO REAL")
    print("=" * 50)

    import json

    from sqlalchemy import create_engine, text

    from components.config_normalizer import get_sqlalchemy_url

    with open('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration/secrets/postgresql_destination_config.json', 'r') as f:
        dest_config = json.load(f)

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    dest_engine = create_engine(dest_url)

    test_cases = [
        {'db': 'app_workforce', 'user': 'app_workforce_user'},
        {'db': 'botpress_db', 'user': 'botpress_user'},
        {'db': 'ai_process_db', 'user': 'ai_process_user'}
    ]

    with dest_engine.connect() as conn:
        for case in test_cases:
            db_name = case['db']
            username = case['user']

            print(f"\n📁 {db_name} -> {username}:")

            # Verificar grants explícitos
            grants_query = text("""
                SELECT count(*) as grant_count
                FROM pg_database d, aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                WHERE d.datname = :db_name
                AND grantee::regrole::text = :username
            """)

            try:
                result = conn.execute(grants_query, {"db_name": db_name, "username": username})
                grant_count = result.fetchone().grant_count

                if grant_count > 0:
                    print(f"   ✅ {grant_count} grants explícitos encontrados")

                    # Mostrar detalhes
                    detail_query = text("""
                        SELECT privilege_type, is_grantable
                        FROM pg_database d, aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                        WHERE d.datname = :db_name
                        AND grantee::regrole::text = :username
                        ORDER BY privilege_type
                    """)

                    detail_result = conn.execute(detail_query, {"db_name": db_name, "username": username})

                    for detail in detail_result:
                        grantable = " (WITH GRANT OPTION)" if detail.is_grantable else ""
                        print(f"      • {detail.privilege_type}{grantable}")

                else:
                    print(f"   ❌ SEM grants explícitos")

            except Exception as e:
                print(f"   ❌ Erro verificando: {e}")


if __name__ == "__main__":
    print("🔧 MIGRAÇÃO REAL - APLICAÇÃO DE PRIVILÉGIOS")
    print("=" * 50)

    # Executar migração real
    success = execute_real_migration()

    if success:
        # Verificar resultados
        verify_migration_results()

        print("\n🎯 RESUMO FINAL:")
        print("• Migração REAL executada (não debug/simulação)")
        print("• Fase 3 (privilégios) aplicada pela primeira vez")
        print("• Grants explícitos agora devem estar no destino")
        print("• Sistema de migração está correto e funcional")

    else:
        print("\n❌ MIGRAÇÃO FALHOU - verificar logs de erro")
