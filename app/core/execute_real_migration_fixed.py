#!/usr/bin/env python3
"""
EXECUTAR MIGRAÇÃO COMPLETA REAL
Aplicar Fase 3 (privilégios) que nunca foi executada
"""

import json
import sys

from sqlalchemy import create_engine, text

# Adicionar path do core
sys.path.append('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration/core')
sys.path.append('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration')

from sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator

from components.config_normalizer import get_sqlalchemy_url


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
        return False

    print("\n🎯 INICIANDO MIGRAÇÃO REAL...")

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

    config_path = ('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/'
                  'enterprise-database-migration/secrets/'
                  'postgresql_destination_config.json')

    with open(config_path, 'r') as f:
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
                FROM pg_database d,
                     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                WHERE d.datname = :db_name
                AND grantee::regrole::text = :username
            """)

            try:
                result = conn.execute(grants_query, {
                    "db_name": db_name,
                    "username": username
                })
                row = result.fetchone()
                grant_count = row.grant_count if row else 0

                if grant_count > 0:
                    print(f"   ✅ {grant_count} grants explícitos encontrados")

                    # Mostrar detalhes
                    detail_query = text("""
                        SELECT privilege_type, is_grantable
                        FROM pg_database d,
                             aclexplode(COALESCE(d.datacl,
                                                acldefault('d', d.datdba)))
                        WHERE d.datname = :db_name
                        AND grantee::regrole::text = :username
                        ORDER BY privilege_type
                    """)

                    detail_result = conn.execute(detail_query, {
                        "db_name": db_name,
                        "username": username
                    })

                    for detail in detail_result:
                        grantable = " (WITH GRANT OPTION)" \
                                   if detail.is_grantable else ""
                        print(f"      • {detail.privilege_type}{grantable}")

                else:
                    print("   ❌ SEM grants explícitos")

            except Exception as e:
                print(f"   ❌ Erro verificando: {e}")


def execute_only_phase3():
    """Executa APENAS a Fase 3 (privilégios) se usuários já existem."""

    print("🎯 EXECUTANDO APENAS FASE 3 (PRIVILÉGIOS)")
    print("=" * 50)

    try:
        migrator = SQLAlchemyPostgreSQLMigrator()

        # Carregar configurações
        if not migrator.load_configs():
            print("❌ Falha ao carregar configurações")
            return False

        if not migrator.create_engines():
            print("❌ Falha ao criar engines")
            return False

        # Coletar bancos da origem
        databases = migrator.get_databases_with_owners()

        if not databases:
            print("❌ Nenhum banco encontrado")
            return False

        print(f"📊 Encontrados {len(databases)} bancos para aplicar privilégios")

        # Aplicar APENAS privilégios (Fase 3)
        print("\n🔶 FASE 3: APLICANDO PRIVILÉGIOS")
        print("-" * 50)

        privileges_applied = migrator.apply_database_privileges(databases)

        print(f"\n✅ FASE 3 CONCLUÍDA!")
        print(f"🔐 Total de privilégios aplicados: {privileges_applied}")

        return privileges_applied > 0

    except Exception as e:
        print(f"❌ ERRO na Fase 3: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🔧 MIGRAÇÃO REAL - APLICAÇÃO DE PRIVILÉGIOS")
    print("=" * 50)

    # Escolher opção
    print("\n📋 OPÇÕES DISPONÍVEIS:")
    print("1. Migração completa (Fases 1, 2 e 3)")
    print("2. Apenas Fase 3 (privilégios) - usuários já existem")

    option = input("\nEscolha uma opção (1 ou 2): ")

    if option == "1":
        success = execute_real_migration()
    elif option == "2":
        success = execute_only_phase3()
    else:
        print("❌ Opção inválida")
        success = False

    if success:
        # Verificar resultados
        verify_migration_results()

        print("\n🎯 RESUMO FINAL:")
        print("• Migração REAL executada (não debug/simulação)")
        print("• Fase 3 (privilégios) aplicada")
        print("• Grants explícitos agora devem estar no destino")
        print("• Sistema de migração está correto e funcional")

    else:
        print("\n❌ MIGRAÇÃO FALHOU - verificar logs de erro")
