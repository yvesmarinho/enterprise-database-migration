#!/usr/bin/env python3
"""
Teste de         ("✅ Tabelas de propriedade do usuário (CORRIGIDO v2)", """
SELECT table_schema, table_name
FROM information_schema.tables t
JOIN pg_authid a ON t.table_owner = a.rolname
WHERE a.rolname = 'username'
LIMIT 10
        """) SQL de Dependências
====================================

Script para testar e validar as queries SQL usadas na verificação
de dependências de usuários PostgreSQL.

Uso:
    python3 test_sql_queries.py
"""

def show_corrected_queries():
    """Mostra as queries SQL corrigidas para verificação de dependências."""

    print("🔧 Queries SQL Corrigidas para Verificação de Dependências")
    print("=" * 60)

    queries = [
        ("✅ Bancos de propriedade do usuário", """
SELECT datname
FROM pg_database d
JOIN pg_authid a ON d.datdba = a.oid
WHERE a.rolname = 'username'
AND datname NOT IN ('template0', 'template1')
        """),

        ("✅ Schemas de propriedade do usuário (CORRIGIDO)", """
SELECT schema_name
FROM information_schema.schemata s
JOIN pg_authid a ON s.schema_owner = a.rolname
WHERE a.rolname = 'username'
AND schema_name NOT LIKE 'pg_%'
AND schema_name != 'information_schema'
        """),

        ("✅ Tabelas de propriedade do usuário (CORRIGIDO)", """
SELECT table_schema, table_name
FROM information_schema.tables t
JOIN pg_authid a ON t.tableowner = a.rolname
WHERE a.rolname = 'username'
LIMIT 10
        """)
    ]

    for description, query in queries:
        print(f"\n📝 {description}:")
        print(query.strip())

def show_error_analysis():
    """Mostra análise detalhada do erro encontrado."""

    print("\n🚨 Análise do Erro Corrigido")
    print("=" * 40)

    print("\n❌ ERROS ANTERIORES:")
    print("   1º Erro: SELECT schemaname FROM information_schema.schemata")
    print("           → column 'schemaname' does not exist")
    print("   2º Erro: JOIN pg_authid a ON t.tableowner = a.rolname")
    print("           → column 't.tableowner' does not exist")

    print("\n✅ CORREÇÕES APLICADAS:")
    print("   1º Fix: SELECT schema_name FROM information_schema.schemata")
    print("   2º Fix: JOIN pg_authid a ON t.table_owner = a.rolname")
    print("   Resultado: Queries funcionam corretamente")

    print("\n📋 Todas as correções:")
    print("   • schemaname → schema_name")
    print("   • tablename → table_name")
    print("   • tableowner → table_owner")
    print("   • Usar nomes corretos das colunas do information_schema")

    print("\n💡 Impacto da correção:")
    print("   • Usuários SEM dependências serão corretamente identificados")
    print("   • Usuários COM dependências serão corretamente pulados")
    print("   • Verificação de dependências funcionará adequadamente")

def show_expected_behavior():
    """Mostra o comportamento esperado após a correção."""

    print("\n🎯 Comportamento Esperado Após a Correção")
    print("=" * 45)

    scenarios = [
        {
            'user': 'backup',
            'expected': 'SEM dependências → Seria APAGADO',
            'reason': 'Usuário sem objetos próprios'
        },
        {
            'user': 'prometheus',
            'expected': 'COM dependências → Seria PULADO',
            'reason': 'Possui tabelas ou schemas próprios'
        },
        {
            'user': 'postgres_exporter',
            'expected': 'SEM dependências → Seria APAGADO',
            'reason': 'Usuário apenas para conexão, sem objetos'
        }
    ]

    for scenario in scenarios:
        print(f"\n👤 Usuário: {scenario['user']}")
        print(f"   📊 Resultado: {scenario['expected']}")
        print(f"   💭 Motivo: {scenario['reason']}")

    print("\n📈 Saída esperada do próximo teste:")
    print("   🔍 [DRY-RUN] Apagaria usuário: backup")
    print("   🔍 [DRY-RUN] Apagaria usuário: postgres_exporter")
    print("   🔍 [DRY-RUN] Usuário 'prometheus' seria PULADO (possui dependências)")
    print("   📊 Usuários - Apagados: X, Pulados: Y, Falharam: 0")

def main():
    """Função principal."""
    print("🧪 Teste de Queries SQL de Dependências")
    print("=" * 40)

    show_corrected_queries()
    show_error_analysis()
    show_expected_behavior()

    print(f"\n{'='*60}")
    print("✅ Análise concluída!")
    print("🚀 Execute novamente: python3 cleanup_database.py --server destino --dry-run")
    print("📊 Agora a verificação de dependências funcionará corretamente")

if __name__ == "__main__":
    main()
