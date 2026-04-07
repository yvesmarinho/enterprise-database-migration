#!/usr/bin/env python3
"""
Database Expert Agent - Exemplo Prático Real

Exemplo de uso real do agente com conexão a bancos de dados.
Requer configuração de credenciais em arquivos JSON.

Uso:
    # Analisar MySQL
    python examples/expert_agent_real.py --analyze-mysql secrets/mysql_config.json
    
    # Analisar PostgreSQL
    python examples/expert_agent_real.py --analyze-postgresql secrets/postgresql_config.json
    
    # Planejar migração
    python examples/expert_agent_real.py --plan-migration secrets/mysql_config.json
    
    # Otimizar query
    python examples/expert_agent_real.py --optimize-query "SELECT * FROM users"
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents import DatabaseExpertAgent
from app.agents.database_expert_agent import DatabaseType, AnalysisLevel


def load_config(config_file: str) -> dict:
    """Carrega arquivo de configuração JSON."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSON: {e}")
        sys.exit(1)


def analyze_mysql(agent: DatabaseExpertAgent, config_file: str, level: str):
    """Analisa banco MySQL."""
    print("🔍 Analisando banco MySQL...")
    
    config = load_config(config_file)
    
    # Extrair parâmetros de conexão
    if 'server' in config:
        # Formato do projeto
        conn_params = {
            'host': config['server']['host'],
            'port': config['server']['port'],
            'user': config['credentials']['username'],
            'password': config['credentials']['password'],
            'database': config['database']['name'],
            'charset': 'utf8mb4'
        }
    else:
        # Formato direto
        conn_params = config
    
    # Definir nível de análise
    analysis_level = {
        'quick': AnalysisLevel.QUICK,
        'standard': AnalysisLevel.STANDARD,
        'deep': AnalysisLevel.DEEP,
        'forensic': AnalysisLevel.FORENSIC
    }.get(level, AnalysisLevel.STANDARD)
    
    try:
        # Executar análise
        analysis = agent.analyze_database(
            connection_params=conn_params,
            db_type=DatabaseType.MYSQL,
            analysis_level=analysis_level
        )
        
        # Mostrar resultados
        print("\n" + "=" * 70)
        print("  ANÁLISE MYSQL - RESULTADOS")
        print("=" * 70)
        
        db_info = analysis.database_info
        print(f"\n📊 Informações do Banco:")
        print(f"   Tipo: {db_info.db_type.value}")
        print(f"   Versão: {db_info.version}")
        print(f"   Encoding: {db_info.encoding}")
        print(f"   Collation: {db_info.collation}")
        print(f"   Tamanho: {db_info.size_mb:.2f} MB")
        print(f"   Tabelas: {db_info.table_count}")
        
        print(f"\n✅ Recomendações ({len(analysis.recommendations)}):")
        for i, rec in enumerate(analysis.recommendations[:10], 1):
            print(f"   {i}. {rec}")
        
        if analysis.warnings:
            print(f"\n⚠️ Avisos ({len(analysis.warnings)}):")
            for warning in analysis.warnings[:5]:
                print(f"   • {warning}")
        
        if analysis.errors:
            print(f"\n❌ Erros ({len(analysis.errors)}):")
            for error in analysis.errors[:5]:
                print(f"   • {error}")
        
        # Salvar resultado
        output_file = Path(f"reports/mysql_analysis_{db_info.table_count}tables.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': analysis.timestamp.isoformat(),
                'database_info': {
                    'type': db_info.db_type.value,
                    'version': db_info.version,
                    'size_mb': db_info.size_mb,
                    'table_count': db_info.table_count,
                    'encoding': db_info.encoding
                },
                'recommendations': analysis.recommendations,
                'warnings': analysis.warnings,
                'errors': analysis.errors
            }, f, indent=2)
        
        print(f"\n💾 Resultado salvo em: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Erro durante análise: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def analyze_postgresql(agent: DatabaseExpertAgent, config_file: str, level: str):
    """Analisa banco PostgreSQL."""
    print("🔍 Analisando banco PostgreSQL...")
    
    config = load_config(config_file)
    
    # Extrair parâmetros de conexão
    if 'server' in config:
        # Formato do projeto
        conn_params = {
            'host': config['server']['host'],
            'port': config['server']['port'],
            'user': config['credentials']['username'],
            'password': config['credentials']['password'],
            'database': config['database']['name']
        }
    else:
        # Formato direto
        conn_params = config
    
    # Definir nível de análise
    analysis_level = {
        'quick': AnalysisLevel.QUICK,
        'standard': AnalysisLevel.STANDARD,
        'deep': AnalysisLevel.DEEP,
        'forensic': AnalysisLevel.FORENSIC
    }.get(level, AnalysisLevel.STANDARD)
    
    try:
        # Executar análise
        analysis = agent.analyze_database(
            connection_params=conn_params,
            db_type=DatabaseType.POSTGRESQL,
            analysis_level=analysis_level
        )
        
        # Mostrar resultados
        print("\n" + "=" * 70)
        print("  ANÁLISE POSTGRESQL - RESULTADOS")
        print("=" * 70)
        
        db_info = analysis.database_info
        print(f"\n📊 Informações do Banco:")
        print(f"   Tipo: {db_info.db_type.value}")
        print(f"   Versão: {db_info.version}")
        print(f"   Encoding: {db_info.encoding}")
        print(f"   Tamanho: {db_info.size_mb:.2f} MB")
        print(f"   Tabelas: {db_info.table_count}")
        
        print(f"\n✅ Recomendações ({len(analysis.recommendations)}):")
        for i, rec in enumerate(analysis.recommendations[:10], 1):
            print(f"   {i}. {rec}")
        
        # Salvar resultado
        output_file = Path(f"reports/postgresql_analysis_{db_info.table_count}tables.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': analysis.timestamp.isoformat(),
                'database_info': {
                    'type': db_info.db_type.value,
                    'version': db_info.version,
                    'size_mb': db_info.size_mb,
                    'table_count': db_info.table_count,
                    'encoding': db_info.encoding
                },
                'recommendations': analysis.recommendations
            }, f, indent=2)
        
        print(f"\n💾 Resultado salvo em: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Erro durante análise: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def plan_migration(agent: DatabaseExpertAgent, source_config_file: str):
    """Planeja migração MySQL → PostgreSQL."""
    print("📋 Planejando migração MySQL → PostgreSQL...")
    
    config = load_config(source_config_file)
    
    # Extrair parâmetros de conexão
    if 'server' in config:
        conn_params = {
            'host': config['server']['host'],
            'port': config['server']['port'],
            'user': config['credentials']['username'],
            'password': config['credentials']['password'],
            'database': config['database']['name'],
            'charset': 'utf8mb4'
        }
    else:
        conn_params = config
    
    try:
        # 1. Analisar origem
        print("\n1️⃣ Analisando banco de origem...")
        analysis = agent.analyze_database(
            connection_params=conn_params,
            db_type=DatabaseType.MYSQL,
            analysis_level=AnalysisLevel.STANDARD
        )
        
        # 2. Planejar migração
        print("2️⃣ Gerando estratégia de migração...")
        strategy = agent.plan_migration(
            source_analysis=analysis,
            target_db_type=DatabaseType.POSTGRESQL,
            options={'chunk_size': 1000}
        )
        
        # 3. Mostrar plano
        print("\n" + "=" * 70)
        print("  PLANO DE MIGRAÇÃO")
        print("=" * 70)
        
        print(f"\n📋 Estratégia: {strategy.strategy_name}")
        print(f"📊 Descrição: {strategy.description}")
        print(f"⚡ Complexidade: {strategy.complexity}")
        print(f"⏱️ Duração estimada: {strategy.estimated_duration}")
        
        print(f"\n📝 Passos ({len(strategy.steps)}):")
        for step in strategy.steps:
            print(f"   {step}")
        
        print(f"\n⚠️ Riscos identificados ({len(strategy.risks)}):")
        for i, risk in enumerate(strategy.risks[:10], 1):
            print(f"   {i}. {risk}")
        
        print(f"\n💡 Recomendações ({len(strategy.recommendations)}):")
        for i, rec in enumerate(strategy.recommendations[:10], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n🔧 Issues de compatibilidade ({len(strategy.compatibility_issues)}):")
        for issue in strategy.compatibility_issues[:10]:
            print(f"\n   • {issue['feature']} (severity: {issue['severity']})")
            print(f"     MySQL: {issue['mysql']}")
            print(f"     PostgreSQL: {issue['postgresql']}")
            print(f"     💡 {issue['solution']}")
        
        # 4. Gerar relatório completo
        print("\n3️⃣ Gerando relatório completo...")
        report_file = Path('reports/migration_plan_complete.json')
        report_file.parent.mkdir(exist_ok=True)
        
        agent.generate_migration_report(
            analysis=analysis,
            strategy=strategy,
            output_file=report_file
        )
        
        print(f"\n✅ Plano de migração completo!")
        print(f"💾 Relatório salvo em: {report_file}")
        
    except Exception as e:
        print(f"\n❌ Erro durante planejamento: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


def optimize_query(agent: DatabaseExpertAgent, query: str, db_type: str):
    """Otimiza uma query SQL."""
    print(f"🔧 Otimizando query para {db_type}...")
    
    db_type_enum = {
        'mysql': DatabaseType.MYSQL,
        'postgresql': DatabaseType.POSTGRESQL,
        'postgres': DatabaseType.POSTGRESQL,
        'pg': DatabaseType.POSTGRESQL
    }.get(db_type.lower(), DatabaseType.POSTGRESQL)
    
    # Analisar query
    result = agent.optimize_query(
        query=query,
        db_type=db_type_enum
    )
    
    # Mostrar resultados
    print("\n" + "=" * 70)
    print("  OTIMIZAÇÃO DE QUERY")
    print("=" * 70)
    
    print(f"\n📝 Query original:")
    print(result['original_query'])
    
    print(f"\n🔍 Issues encontrados ({len(result['issues'])}):")
    for issue in result['issues']:
        print(f"\n   • {issue['type']} (severity: {issue['severity']})")
        print(f"     {issue['description']}")
        print(f"     Impact: {issue['impact']}")
    
    print(f"\n💡 Sugestões ({len(result['suggestions'])}):")
    for i, suggestion in enumerate(result['suggestions'], 1):
        print(f"   {i}. {suggestion}")
    
    return 0


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Database Expert Agent - Análise e Migração de Bancos de Dados',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  Analisar MySQL:
    python expert_agent_real.py --analyze-mysql secrets/mysql_config.json
  
  Analisar PostgreSQL:
    python expert_agent_real.py --analyze-postgresql secrets/postgresql_config.json
  
  Planejar migração:
    python expert_agent_real.py --plan-migration secrets/mysql_config.json
  
  Otimizar query:
    python expert_agent_real.py --optimize-query "SELECT * FROM users" --db-type postgresql
        """
    )
    
    parser.add_argument('--analyze-mysql', metavar='CONFIG',
                       help='Analisar banco MySQL usando arquivo de configuração')
    parser.add_argument('--analyze-postgresql', metavar='CONFIG',
                       help='Analisar banco PostgreSQL usando arquivo de configuração')
    parser.add_argument('--plan-migration', metavar='CONFIG',
                       help='Planejar migração MySQL→PostgreSQL')
    parser.add_argument('--optimize-query', metavar='QUERY',
                       help='Otimizar uma query SQL')
    parser.add_argument('--db-type', default='postgresql',
                       choices=['mysql', 'postgresql', 'postgres', 'pg'],
                       help='Tipo do banco para otimização de query (default: postgresql)')
    parser.add_argument('--level', default='standard',
                       choices=['quick', 'standard', 'deep', 'forensic'],
                       help='Nível de análise (default: standard)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Modo verbose (mais detalhes)')
    
    args = parser.parse_args()
    
    # Configurar logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    # Criar agente
    print("🤖 Inicializando Database Expert Agent...")
    agent = DatabaseExpertAgent(log_level=log_level)
    
    # Executar ação
    if args.analyze_mysql:
        return analyze_mysql(agent, args.analyze_mysql, args.level)
    
    elif args.analyze_postgresql:
        return analyze_postgresql(agent, args.analyze_postgresql, args.level)
    
    elif args.plan_migration:
        return plan_migration(agent, args.plan_migration)
    
    elif args.optimize_query:
        return optimize_query(agent, args.optimize_query, args.db_type)
    
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
