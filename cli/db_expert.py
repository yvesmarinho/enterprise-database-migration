#!/usr/bin/env python3
"""
Database Expert CLI

Interface de linha de comando para o Database Expert Agent.
Fornece comandos para análise, migração e otimização de bancos de dados.

Instalação:
    chmod +x cli/db_expert.py
    
Uso:
    ./cli/db_expert.py analyze mysql --config secrets/mysql_config.json
    ./cli/db_expert.py analyze postgresql --config secrets/postgresql_config.json
    ./cli/db_expert.py migrate plan --source secrets/mysql_config.json
    ./cli/db_expert.py optimize --query "SELECT * FROM users"
    ./cli/db_expert.py knowledge export
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


class DatabaseExpertCLI:
    """Interface CLI para Database Expert Agent."""
    
    def __init__(self, verbose: bool = False):
        """Inicializa CLI."""
        self.verbose = verbose
        log_level = logging.DEBUG if verbose else logging.INFO
        self.agent = DatabaseExpertAgent(log_level=log_level)
    
    def cmd_analyze(self, args):
        """Comando: analyze"""
        if args.database == 'mysql':
            return self._analyze_mysql(args.config, args.level, args.output)
        elif args.database == 'postgresql':
            return self._analyze_postgresql(args.config, args.level, args.output)
        else:
            print(f"❌ Database type not supported: {args.database}")
            return 1
    
    def cmd_migrate(self, args):
        """Comando: migrate"""
        if args.action == 'plan':
            return self._plan_migration(args.source, args.output)
        elif args.action == 'validate':
            return self._validate_migration(args.source, args.target)
        else:
            print(f"❌ Migration action not supported: {args.action}")
            return 1
    
    def cmd_optimize(self, args):
        """Comando: optimize"""
        return self._optimize_query(args.query, args.database, args.output)
    
    def cmd_knowledge(self, args):
        """Comando: knowledge"""
        if args.action == 'export':
            return self._export_knowledge(args.output)
        elif args.action == 'show':
            return self._show_knowledge(args.section)
        else:
            print(f"❌ Knowledge action not supported: {args.action}")
            return 1
    
    def _load_config(self, config_file: str) -> dict:
        """Carrega configuração JSON."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Converter para formato padrão se necessário
            if 'server' in config:
                # Formato do projeto
                if 'database' in config and 'name' in config['database']:
                    db_name = config['database']['name']
                else:
                    db_name = config.get('database', 'postgres')
                
                return {
                    'host': config['server']['host'],
                    'port': config['server']['port'],
                    'user': config['credentials']['username'],
                    'password': config['credentials']['password'],
                    'database': db_name
                }
            else:
                # Formato direto
                return config
                
        except FileNotFoundError:
            print(f"❌ Config file not found: {config_file}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            sys.exit(1)
    
    def _analyze_mysql(self, config_file: str, level: str, output: str):
        """Analisa banco MySQL."""
        print("🔍 Analyzing MySQL database...")
        
        config = self._load_config(config_file)
        if 'charset' not in config:
            config['charset'] = 'utf8mb4'
        
        analysis_level = getattr(AnalysisLevel, level.upper())
        
        try:
            analysis = self.agent.analyze_database(
                connection_params=config,
                db_type=DatabaseType.MYSQL,
                analysis_level=analysis_level
            )
            
            self._print_analysis_results(analysis)
            
            if output:
                self._save_analysis(analysis, output)
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _analyze_postgresql(self, config_file: str, level: str, output: str):
        """Analisa banco PostgreSQL."""
        print("🔍 Analyzing PostgreSQL database...")
        
        config = self._load_config(config_file)
        analysis_level = getattr(AnalysisLevel, level.upper())
        
        try:
            analysis = self.agent.analyze_database(
                connection_params=config,
                db_type=DatabaseType.POSTGRESQL,
                analysis_level=analysis_level
            )
            
            self._print_analysis_results(analysis)
            
            if output:
                self._save_analysis(analysis, output)
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _print_analysis_results(self, analysis):
        """Imprime resultados da análise."""
        print("\n" + "=" * 70)
        print("  ANALYSIS RESULTS")
        print("=" * 70)
        
        db = analysis.database_info
        print(f"\n📊 Database Information:")
        print(f"   Type: {db.db_type.value}")
        print(f"   Version: {db.version}")
        print(f"   Encoding: {db.encoding}")
        print(f"   Size: {db.size_mb:.2f} MB")
        print(f"   Tables: {db.table_count}")
        
        if analysis.recommendations:
            print(f"\n✅ Recommendations ({len(analysis.recommendations)}):")
            for i, rec in enumerate(analysis.recommendations[:10], 1):
                print(f"   {i}. {rec}")
        
        if analysis.warnings:
            print(f"\n⚠️ Warnings ({len(analysis.warnings)}):")
            for warning in analysis.warnings[:5]:
                print(f"   • {warning}")
        
        if analysis.errors:
            print(f"\n❌ Errors ({len(analysis.errors)}):")
            for error in analysis.errors[:5]:
                print(f"   • {error}")
    
    def _save_analysis(self, analysis, output_file: str):
        """Salva análise em arquivo."""
        db = analysis.database_info
        data = {
            'timestamp': analysis.timestamp.isoformat(),
            'analysis_level': analysis.analysis_level.value,
            'database_info': {
                'type': db.db_type.value,
                'version': db.version,
                'size_mb': db.size_mb,
                'table_count': db.table_count,
                'encoding': db.encoding
            },
            'recommendations': analysis.recommendations,
            'warnings': analysis.warnings,
            'errors': analysis.errors
        }
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
    
    def _plan_migration(self, source_config: str, output: str):
        """Planeja migração."""
        print("📋 Planning migration MySQL → PostgreSQL...")
        
        config = self._load_config(source_config)
        if 'charset' not in config:
            config['charset'] = 'utf8mb4'
        
        try:
            # Analisar origem
            print("\n1️⃣ Analyzing source database...")
            analysis = self.agent.analyze_database(
                connection_params=config,
                db_type=DatabaseType.MYSQL,
                analysis_level=AnalysisLevel.STANDARD
            )
            
            # Planejar migração
            print("2️⃣ Generating migration strategy...")
            strategy = self.agent.plan_migration(
                source_analysis=analysis,
                target_db_type=DatabaseType.POSTGRESQL
            )
            
            # Mostrar resultados
            print("\n" + "=" * 70)
            print("  MIGRATION PLAN")
            print("=" * 70)
            
            print(f"\n📋 Strategy: {strategy.strategy_name}")
            print(f"⚡ Complexity: {strategy.complexity}")
            print(f"⏱️ Duration: {strategy.estimated_duration}")
            
            print(f"\n📝 Steps:")
            for step in strategy.steps:
                print(f"   {step}")
            
            print(f"\n⚠️ Risks ({len(strategy.risks)}):")
            for risk in strategy.risks[:5]:
                print(f"   • {risk}")
            
            print(f"\n🔧 Compatibility Issues ({len(strategy.compatibility_issues)}):")
            for issue in strategy.compatibility_issues[:5]:
                print(f"   • {issue['feature']}: {issue['mysql']} → {issue['postgresql']}")
            
            # Salvar relatório
            if output:
                report_file = Path(output)
            else:
                report_file = Path('reports/migration_plan.json')
            
            report_file.parent.mkdir(parents=True, exist_ok=True)
            self.agent.generate_migration_report(analysis, strategy, report_file)
            print(f"\n💾 Full report saved to: {report_file}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _validate_migration(self, source_config: str, target_config: str):
        """Valida migração."""
        print("✅ Validating migration...")
        print("⚠️ Feature not yet fully implemented")
        return 0
    
    def _optimize_query(self, query: str, db_type: str, output: str):
        """Otimiza query."""
        print(f"🔧 Optimizing query for {db_type}...")
        
        db_type_enum = {
            'mysql': DatabaseType.MYSQL,
            'postgresql': DatabaseType.POSTGRESQL,
            'postgres': DatabaseType.POSTGRESQL
        }.get(db_type.lower(), DatabaseType.POSTGRESQL)
        
        result = self.agent.optimize_query(query, db_type_enum)
        
        print("\n" + "=" * 70)
        print("  QUERY OPTIMIZATION")
        print("=" * 70)
        
        print(f"\n📝 Original Query:")
        print(result['original_query'])
        
        print(f"\n🔍 Issues ({len(result['issues'])}):")
        for issue in result['issues']:
            print(f"\n   • {issue['type']} ({issue['severity']})")
            print(f"     {issue['description']}")
        
        print(f"\n💡 Suggestions:")
        for suggestion in result['suggestions']:
            print(f"   • {suggestion}")
        
        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Results saved to: {output}")
        
        return 0
    
    def _export_knowledge(self, output: str):
        """Exporta base de conhecimento."""
        if not output:
            output = 'knowledge_base.json'
        
        print(f"📤 Exporting knowledge base to {output}...")
        self.agent.export_knowledge_base(Path(output))
        print(f"✅ Knowledge base exported successfully")
        return 0
    
    def _show_knowledge(self, section: str):
        """Mostra seção da base de conhecimento."""
        kb = self.agent.knowledge_base
        
        if section == 'types':
            print("\n📋 Type Mappings (MySQL → PostgreSQL):")
            for mysql, pg in kb['mysql_to_postgresql']['type_mappings'].items():
                print(f"   {mysql:20} → {pg}")
        
        elif section == 'functions':
            print("\n📋 Function Mappings:")
            for mysql, pg in kb['mysql_to_postgresql']['function_mappings'].items():
                print(f"   {mysql:20} → {pg}")
        
        elif section == 'incompatibilities':
            print("\n⚠️ Known Incompatibilities:")
            for issue in kb['mysql_to_postgresql']['incompatibilities']:
                print(f"\n   • {issue['feature']} ({issue['severity']})")
                print(f"     MySQL: {issue['mysql']}")
                print(f"     PostgreSQL: {issue['postgresql']}")
                print(f"     Solution: {issue['solution']}")
        
        elif section == 'best-practices':
            print("\n✅ PostgreSQL Best Practices:")
            for practice in kb['postgresql_best_practices']:
                print(f"   • {practice}")
            
            print("\n✅ MySQL Best Practices:")
            for practice in kb['mysql_best_practices']:
                print(f"   • {practice}")
        
        else:
            print(f"❌ Unknown section: {section}")
            print("Available sections: types, functions, incompatibilities, best-practices")
            return 1
        
        return 0


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Database Expert CLI - MySQL & PostgreSQL Analysis and Migration',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Comando: analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analyze database')
    analyze_parser.add_argument('database', choices=['mysql', 'postgresql'],
                               help='Database type')
    analyze_parser.add_argument('--config', required=True,
                               help='Configuration file')
    analyze_parser.add_argument('--level', default='standard',
                               choices=['quick', 'standard', 'deep', 'forensic'],
                               help='Analysis level')
    analyze_parser.add_argument('--output', help='Output file (JSON)')
    
    # Comando: migrate
    migrate_parser = subparsers.add_parser('migrate', help='Migration operations')
    migrate_parser.add_argument('action', choices=['plan', 'validate'],
                               help='Migration action')
    migrate_parser.add_argument('--source', required=True,
                               help='Source database config')
    migrate_parser.add_argument('--target', help='Target database config (for validate)')
    migrate_parser.add_argument('--output', help='Output file (JSON)')
    
    # Comando: optimize
    optimize_parser = subparsers.add_parser('optimize', help='Optimize SQL query')
    optimize_parser.add_argument('--query', required=True,
                                help='SQL query to optimize')
    optimize_parser.add_argument('--database', default='postgresql',
                                choices=['mysql', 'postgresql', 'postgres'],
                                help='Database type')
    optimize_parser.add_argument('--output', help='Output file (JSON)')
    
    # Comando: knowledge
    knowledge_parser = subparsers.add_parser('knowledge', help='Knowledge base operations')
    knowledge_parser.add_argument('action', choices=['export', 'show'],
                                 help='Knowledge action')
    knowledge_parser.add_argument('--section',
                                 choices=['types', 'functions', 'incompatibilities', 'best-practices'],
                                 help='Section to show (for show action)')
    knowledge_parser.add_argument('--output', help='Output file (for export)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Criar CLI e executar comando
    cli = DatabaseExpertCLI(verbose=args.verbose)
    
    if args.command == 'analyze':
        return cli.cmd_analyze(args)
    elif args.command == 'migrate':
        return cli.cmd_migrate(args)
    elif args.command == 'optimize':
        return cli.cmd_optimize(args)
    elif args.command == 'knowledge':
        return cli.cmd_knowledge(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
