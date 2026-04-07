#!/usr/bin/env python3
"""
Database Expert Agent - Demonstração Completa

Este script demonstra todas as capacidades do Database Expert Agent.

Uso:
    python examples/expert_agent_demo.py
"""

import json
import logging
import sys
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents import DatabaseExpertAgent
from app.agents.database_expert_agent import DatabaseType, AnalysisLevel


def print_header(title: str):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_agent_initialization():
    """Demonstra inicialização do agente."""
    print_header("1. Inicialização do Database Expert Agent")
    
    # Criar agente
    agent = DatabaseExpertAgent(log_level=logging.INFO)
    
    print(f"\n✅ Agent criado com sucesso!")
    print(f"📌 Version: {agent.version}")
    print(f"📊 Capabilities:")
    for db, available in agent.capabilities.items():
        status = "✅ Disponível" if available else "❌ Não disponível"
        print(f"   - {db.upper()}: {status}")
    
    return agent


def demo_knowledge_base(agent: DatabaseExpertAgent):
    """Demonstra base de conhecimento."""
    print_header("2. Base de Conhecimento")
    
    kb = agent.knowledge_base
    
    print("\n📚 Conteúdo da base de conhecimento:")
    print(f"   - Type mappings (MySQL→PostgreSQL): {len(kb['mysql_to_postgresql']['type_mappings'])}")
    print(f"   - Function mappings: {len(kb['mysql_to_postgresql']['function_mappings'])}")
    print(f"   - Known incompatibilities: {len(kb['mysql_to_postgresql']['incompatibilities'])}")
    print(f"   - PostgreSQL best practices: {len(kb['postgresql_best_practices'])}")
    print(f"   - MySQL best practices: {len(kb['mysql_best_practices'])}")
    print(f"   - Common migration pitfalls: {len(kb['common_migration_pitfalls'])}")
    
    # Mostrar alguns exemplos
    print("\n📋 Exemplos de mapeamentos de tipos:")
    for mysql_type, pg_type in list(kb['mysql_to_postgresql']['type_mappings'].items())[:5]:
        print(f"   {mysql_type:20} → {pg_type}")
    
    print("\n📋 Exemplos de mapeamentos de funções:")
    for mysql_func, pg_func in list(kb['mysql_to_postgresql']['function_mappings'].items())[:5]:
        print(f"   {mysql_func:20} → {pg_func}")
    
    print("\n⚠️ Top 3 Incompatibilidades:")
    for i, issue in enumerate(kb['mysql_to_postgresql']['incompatibilities'][:3], 1):
        print(f"\n   {i}. {issue['feature']} (severity: {issue['severity']})")
        print(f"      MySQL: {issue['mysql']}")
        print(f"      PostgreSQL: {issue['postgresql']}")
        print(f"      Solução: {issue['solution']}")


def demo_mysql_analysis_simulation(agent: DatabaseExpertAgent):
    """Simula análise de banco MySQL (sem conexão real)."""
    print_header("3. Análise de Banco MySQL (Simulação)")
    
    print("\n📊 Exemplo de análise MySQL:")
    print("   Database: perfexcrm")
    print("   Type: MySQL 8.0.35")
    print("   Size: 245.67 MB")
    print("   Tables: 89")
    print("   Encoding: utf8mb4")
    print("   Collation: utf8mb4_unicode_ci")
    
    print("\n✅ Recomendações (simuladas):")
    for rec in agent.knowledge_base['mysql_best_practices'][:5]:
        print(f"   • {rec}")


def demo_postgresql_analysis_simulation(agent: DatabaseExpertAgent):
    """Simula análise de banco PostgreSQL (sem conexão real)."""
    print_header("4. Análise de Banco PostgreSQL (Simulação)")
    
    print("\n📊 Exemplo de análise PostgreSQL:")
    print("   Database: production_db")
    print("   Type: PostgreSQL 14.10")
    print("   Size: 1024.50 MB")
    print("   Tables: 42")
    print("   Encoding: UTF8")
    print("   Collation: en_US.UTF-8")
    
    print("\n✅ Recomendações (simuladas):")
    for rec in agent.knowledge_base['postgresql_best_practices'][:5]:
        print(f"   • {rec}")


def demo_query_optimization(agent: DatabaseExpertAgent):
    """Demonstra otimização de queries."""
    print_header("5. Otimização de Queries")
    
    # Query problemática
    query = """
SELECT * FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN products p ON o.product_id = p.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE u.status = 'active' OR u.email LIKE '%@gmail.com'
ORDER BY u.created_at DESC
"""
    
    print("\n📝 Query original:")
    print(query)
    
    # Analisar query
    analysis = agent.optimize_query(
        query=query,
        db_type=DatabaseType.POSTGRESQL
    )
    
    print("\n🔍 Análise:")
    print(f"\n⚠️ Issues encontrados: {len(analysis['issues'])}")
    for issue in analysis['issues']:
        print(f"\n   • {issue['type']} (severity: {issue['severity']})")
        print(f"     {issue['description']}")
        print(f"     Impact: {issue['impact']}")
    
    print(f"\n💡 Sugestões ({len(analysis['suggestions'])}):")
    for suggestion in analysis['suggestions']:
        print(f"   • {suggestion}")


def demo_migration_planning_simulation(agent: DatabaseExpertAgent):
    """Simula planejamento de migração."""
    print_header("6. Planejamento de Migração MySQL → PostgreSQL")
    
    print("\n📋 Cenário:")
    print("   Source: MySQL 8.0 - perfexcrm")
    print("   Target: PostgreSQL 14")
    print("   Size: 500 MB")
    print("   Tables: 50")
    
    # Simular dados de análise
    from dataclasses import dataclass
    from datetime import datetime
    
    # Criar estrutura simulada
    print("\n🔄 Gerando estratégia de migração...")
    
    print("\n✅ Estratégia gerada:")
    print("   Nome: MySQL to PostgreSQL Migration")
    print("   Complexidade: medium")
    print("   Duração estimada: 4-6 horas")
    
    print("\n📋 Passos principais:")
    steps = [
        "1. Backup completo do banco MySQL de origem",
        "2. Análise e validação da estrutura de dados",
        "3. Conversão de tipos de dados MySQL → PostgreSQL",
        "4. Tratamento de AUTO_INCREMENT → SERIAL/IDENTITY",
        "5. Conversão de funções e expressões SQL",
        "6. Migração de dados em lotes (batches)",
        "7. Validação de integridade referencial",
        "8. Teste de queries críticas"
    ]
    for step in steps:
        print(f"   {step}")
    
    print("\n⚠️ Riscos identificados:")
    risks = agent.knowledge_base['common_migration_pitfalls'][:5]
    for risk in risks:
        print(f"   • {risk}")
    
    print("\n🔧 Issues de compatibilidade:")
    issues = agent.knowledge_base['mysql_to_postgresql']['incompatibilities'][:3]
    for issue in issues:
        print(f"\n   • {issue['feature']} (severity: {issue['severity']})")
        print(f"     MySQL: {issue['mysql']}")
        print(f"     PostgreSQL: {issue['postgresql']}")


def demo_export_knowledge_base(agent: DatabaseExpertAgent):
    """Demonstra exportação da base de conhecimento."""
    print_header("7. Exportação da Base de Conhecimento")
    
    output_file = Path("knowledge_base_export.json")
    
    print(f"\n📤 Exportando base de conhecimento para {output_file}...")
    agent.export_knowledge_base(output_file)
    
    # Ler e mostrar estatísticas
    with open(output_file, 'r') as f:
        kb_data = json.load(f)
    
    print(f"\n✅ Exportação concluída!")
    print(f"   Arquivo: {output_file}")
    print(f"   Tamanho: {output_file.stat().st_size / 1024:.2f} KB")
    print(f"   Seções: {len(kb_data)}")


def demo_compatibility_check(agent: DatabaseExpertAgent):
    """Demonstra verificação de compatibilidade."""
    print_header("8. Verificação de Compatibilidade MySQL → PostgreSQL")
    
    print("\n🔍 Verificando incompatibilidades conhecidas...")
    
    incompatibilities = agent.knowledge_base['mysql_to_postgresql']['incompatibilities']
    
    print(f"\n📊 Total de incompatibilidades: {len(incompatibilities)}")
    
    # Agrupar por severidade
    by_severity = {}
    for issue in incompatibilities:
        severity = issue['severity']
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(issue)
    
    print("\n📈 Por severidade:")
    for severity in ['high', 'medium', 'low']:
        count = len(by_severity.get(severity, []))
        print(f"   {severity.upper():10} : {count} issues")
    
    print("\n⚠️ Issues críticos (high severity):")
    for issue in by_severity.get('high', []):
        print(f"\n   • {issue['feature']}")
        print(f"     MySQL: {issue['mysql']}")
        print(f"     PostgreSQL: {issue['postgresql']}")
        print(f"     💡 Solução: {issue['solution']}")


def main():
    """Função principal."""
    print("\n" + "=" * 70)
    print("  🤖 DATABASE EXPERT AGENT - DEMONSTRAÇÃO COMPLETA")
    print("=" * 70)
    print("\n  Agente especializado em MySQL e PostgreSQL")
    print("  Version: 1.0.0")
    print("  Autor: Vya.Digital")
    print("=" * 70)
    
    try:
        # 1. Inicialização
        agent = demo_agent_initialization()
        
        # 2. Base de Conhecimento
        demo_knowledge_base(agent)
        
        # 3. Análise MySQL (simulação)
        demo_mysql_analysis_simulation(agent)
        
        # 4. Análise PostgreSQL (simulação)
        demo_postgresql_analysis_simulation(agent)
        
        # 5. Otimização de Queries
        demo_query_optimization(agent)
        
        # 6. Planejamento de Migração
        demo_migration_planning_simulation(agent)
        
        # 7. Verificação de Compatibilidade
        demo_compatibility_check(agent)
        
        # 8. Exportação
        demo_export_knowledge_base(agent)
        
        # Finalização
        print_header("✅ Demonstração Concluída")
        print("\n📚 Para mais informações, consulte:")
        print("   - docs/DATABASE_EXPERT_AGENT.md")
        print("   - app/agents/database_expert_agent.py")
        print("\n💡 Próximos passos:")
        print("   1. Adaptar para suas configurações de banco")
        print("   2. Executar análise real com credenciais")
        print("   3. Gerar plano de migração real")
        print("   4. Integrar com orquestrador de migração")
        
    except Exception as e:
        print(f"\n❌ Erro durante demonstração: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
