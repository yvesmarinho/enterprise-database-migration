#!/usr/bin/env python3
"""
Teste de Verificação de Dependências
====================================

Script para testar a funcionalidade de verificação de dependências
antes de excluir usuários PostgreSQL.

Uso:
    python3 test_user_dependencies.py
"""

import json
import sys
from pathlib import Path

# Simular a verificação de dependências
def simulate_dependency_check():
    """Simula o processo de verificação de dependências."""

    print("🔍 Teste de Verificação de Dependências de Usuários")
    print("=" * 55)

    # Simular diferentes cenários de usuários
    test_users = [
        {
            'name': 'prometheus',
            'dependencies': {
                'has_dependencies': True,
                'owned_databases': ['monitoring_db'],
                'owned_schemas': ['prometheus_schema'],
                'owned_tables': ['public.metrics', 'public.alerts', 'public.targets']
            }
        },
        {
            'name': 'enterprise_user',
            'dependencies': {
                'has_dependencies': False,
                'owned_databases': [],
                'owned_schemas': [],
                'owned_tables': []
            }
        },
        {
            'name': 'test_user',
            'dependencies': {
                'has_dependencies': False,
                'owned_databases': [],
                'owned_schemas': [],
                'owned_tables': []
            }
        },
        {
            'name': 'app_owner',
            'dependencies': {
                'has_dependencies': True,
                'owned_databases': ['app_production', 'app_staging'],
                'owned_schemas': ['app_schema'],
                'owned_tables': ['app_schema.users', 'app_schema.orders', 'app_schema.products']
            }
        }
    ]

    print("\n📋 Simulando verificação de dependências:")
    print("-" * 50)

    for user_data in test_users:
        user = user_data['name']
        deps = user_data['dependencies']

        print(f"\n👤 Usuário: {user}")

        if deps['has_dependencies']:
            print(f"   ⚠️ POSSUI DEPENDÊNCIAS - seria PULADO")
            if deps['owned_databases']:
                print(f"   📁 Bancos proprietários: {deps['owned_databases']}")
            if deps['owned_schemas']:
                print(f"   📂 Schemas proprietários: {deps['owned_schemas']}")
            if deps['owned_tables']:
                tables_preview = deps['owned_tables'][:3]
                more = "..." if len(deps['owned_tables']) > 3 else ""
                print(f"   📋 Tabelas proprietárias: {tables_preview}{more}")
            print(f"   🚫 Ação: PULAR usuário (evitar erro)")
        else:
            print(f"   ✅ SEM DEPENDÊNCIAS - seria APAGADO")
            print(f"   🗑️ Ação: Deletar usuário com segurança")

    print("\n" + "=" * 55)
    print("📊 Resultado da Simulação:")

    total_users = len(test_users)
    users_with_deps = sum(1 for u in test_users if u['dependencies']['has_dependencies'])
    users_safe_to_delete = total_users - users_with_deps

    print(f"   • Total de usuários: {total_users}")
    print(f"   • Com dependências (pulados): {users_with_deps}")
    print(f"   • Seguros para deletar: {users_safe_to_delete}")

    print("\n💡 Benefícios da verificação:")
    print("   • Evita erros do tipo 'cannot be dropped because some objects depend on it'")
    print("   • Informa claramente quais usuários foram pulados e por quê")
    print("   • Permite limpeza parcial sem interromper o processo")
    print("   • Relatório detalhado de ações tomadas")

def show_sql_queries():
    """Mostra as queries SQL usadas para verificar dependências."""

    print("\n🔍 Queries SQL para Verificação de Dependências")
    print("=" * 50)

    queries = [
        ("Bancos de propriedade do usuário", """
SELECT datname
FROM pg_database d
JOIN pg_authid a ON d.datdba = a.oid
WHERE a.rolname = 'username'
AND datname NOT IN ('template0', 'template1')
        """),

        ("Schemas de propriedade do usuário (CATÁLOGO DIRETO)", """
SELECT nspname
FROM pg_namespace n
JOIN pg_authid a ON n.nspowner = a.oid
WHERE a.rolname = 'username'
AND nspname NOT LIKE 'pg_%'
AND nspname NOT IN ('information_schema')
        """),

        ("Tabelas de propriedade do usuário (CATÁLOGO DIRETO)", """
SELECT n.nspname, c.relname
FROM pg_class c
JOIN pg_namespace n ON c.relnamespace = n.oid
JOIN pg_authid a ON c.relowner = a.oid
WHERE a.rolname = 'username'
AND c.relkind IN ('r', 't')
AND n.nspname NOT LIKE 'pg_%'
AND n.nspname NOT IN ('information_schema')
LIMIT 10
        """)
    ]

    for description, query in queries:
        print(f"\n📝 {description}:")
        print(query.strip())

if __name__ == "__main__":
    simulate_dependency_check()
    show_sql_queries()
    print(f"\n{'='*55}")
    print("✅ Teste de verificação de dependências concluído!")
    print("🚀 Execute 'python3 cleanup_database.py --dry-run' para testar com dados reais")
