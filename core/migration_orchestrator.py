#!/usr/bin/env python3
"""
PostgreSQL Enterprise Migration Orchestrator v4.0.0
Sistema completo de migração PostgreSQL com extração, geração e execução controlada

Desenvolvido a partir dos snippets testados e validados na migração WF004→WFDB02
Consolida todos os componentes em um sistema robusto e reutilizável.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Adicionar módulos locais ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core', 'modules'))

from core.modules.data_extractor import WF004DataExtractor
from core.modules.migration_executor import ControlledMigrationExecutor
from core.modules.script_generator import SQLScriptGenerator


class MigrationOrchestrator:
    """Orquestrador principal de migração PostgreSQL."""

    def __init__(self, config_file: str = "config/migration_config.json"):
        """
        Inicializa o orquestrador de migração.

        Args:
            config_file: Arquivo de configuração principal
        """
        self.version = "4.0.0"
        self.config_file = config_file
        self.config = {}
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Configurar logging
        self.setup_logging()

        # Componentes do sistema
        self.extractor = None
        self.generator = None
        self.executor = None

    def setup_logging(self) -> None:
        """Configura sistema de logging."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"migration_{self.session_id}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"=== Migration Orchestrator v{self.version} ===")
        self.logger.info(f"Session ID: {self.session_id}")
        self.logger.info(f"Log file: {log_file}")

    def load_config(self) -> bool:
        """Carrega configuração principal."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # Criar configuração padrão
                self.config = self.create_default_config()
                self.save_config()

            self.logger.info(f"✅ Configuração carregada: {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Erro carregando configuração: {e}")
            return False

    def create_default_config(self) -> Dict[str, Any]:
        """Cria configuração padrão."""
        return {
            "migration": {
                "name": "PostgreSQL Enterprise Migration",
                "version": self.version,
                "source": {
                    "config_file": "secrets/postgresql_source_config.json",
                    "description": "Servidor PostgreSQL origem"
                },
                "destination": {
                    "config_file": "secrets/postgresql_destination_config.json",
                    "description": "Servidor PostgreSQL destino"
                }
            },
            "extraction": {
                "enabled": True,
                "output_dir": "extracted_data",
                "filters": {
                    "exclude_system_users": True,
                    "exclude_system_databases": True,
                    "exclude_users": ["postgres", "migration_user", "root"]
                }
            },
            "generation": {
                "enabled": True,
                "output_dir": "generated_scripts",
                "locale": {
                    "collation": "pt_BR.UTF-8",
                    "ctype": "pt_BR.UTF-8"
                },
                "templates": {
                    "use_template0": True,
                    "default_owner": "postgres"
                }
            },
            "execution": {
                "enabled": True,
                "dry_run_first": True,
                "interactive_mode": False,
                "continue_on_error": False
            },
            "logging": {
                "level": "INFO",
                "console_output": True,
                "file_output": True,
                "detailed_reports": True
            }
        }

    def save_config(self) -> None:
        """Salva configuração atual."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

        self.logger.info(f"💾 Configuração salva: {self.config_file}")

    def phase_1_extraction(self, output_file: Optional[str] = None) -> str:
        """
        Fase 1: Extração de dados do servidor origem.

        Returns:
            Caminho do arquivo JSON gerado ou string vazia se falhou
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("📊 FASE 1: EXTRAÇÃO DE DADOS")
        self.logger.info("="*60)

        try:
            source_config = self.config['migration']['source']['config_file']
            self.extractor = WF004DataExtractor(source_config)

            if not output_file:
                output_dir = self.config['extraction']['output_dir']
                os.makedirs(output_dir, exist_ok=True)
                output_file = f"{output_dir}/extracted_data_{self.session_id}.json"

            result = self.extractor.run_extraction(output_file)

            if result:
                self.logger.info(f"✅ FASE 1 CONCLUÍDA: {result}")
                return result
            else:
                self.logger.error("❌ FASE 1 FALHOU")
                return ""

        except Exception as e:
            self.logger.error(f"❌ Erro na Fase 1: {e}")
            return ""
        finally:
            if self.extractor:
                self.extractor.close_connection()

    def phase_2_generation(self, json_file: str) -> bool:
        """
        Fase 2: Geração de scripts SQL.

        Args:
            json_file: Arquivo JSON com dados extraídos

        Returns:
            True se bem-sucedido, False caso contrário
        """
        self.logger.info("\n" + "="*60)
        self.logger.info("🛠️ FASE 2: GERAÇÃO DE SCRIPTS")
        self.logger.info("="*60)

        try:
            self.generator = SQLScriptGenerator(json_file)

            # Configurar diretório de saída
            output_dir = self.config['generation']['output_dir']
            self.generator.output_dir = output_dir

            scripts = self.generator.run_generation()

            if scripts:
                self.logger.info(f"✅ FASE 2 CONCLUÍDA: {len(scripts)} scripts gerados")
                return True
            else:
                self.logger.error("❌ FASE 2 FALHOU")
                return False

        except Exception as e:
            self.logger.error(f"❌ Erro na Fase 2: {e}")
            return False

    def phase_3_execution(self, dry_run: bool = False,
                         interactive: bool = False) -> bool:
        """
        Fase 3: Execução controlada da migração.

        Args:
            dry_run: Se True, simula execução sem alterar dados
            interactive: Se True, pede confirmação para cada script

        Returns:
            True se bem-sucedido, False caso contrário
        """
        self.logger.info("\n" + "="*60)
        phase_name = "🔍 FASE 3: DRY RUN" if dry_run else "🚀 FASE 3: EXECUÇÃO"
        self.logger.info(phase_name)
        self.logger.info("="*60)

        try:
            dest_config = self.config['migration']['destination']['config_file']
            self.executor = ControlledMigrationExecutor(dest_config)

            # Configurar diretório de scripts
            scripts_dir = self.config['generation']['output_dir']
            self.executor.scripts_dir = scripts_dir

            success = self.executor.run_migration(
                dry_run=dry_run,
                interactive=interactive
            )

            if success:
                status = "DRY RUN CONCLUÍDO" if dry_run else "EXECUÇÃO CONCLUÍDA"
                self.logger.info(f"✅ FASE 3 {status}")
                return True
            else:
                self.logger.error("❌ FASE 3 FALHOU")
                return False

        except Exception as e:
            self.logger.error(f"❌ Erro na Fase 3: {e}")
            return False
        finally:
            if self.executor:
                self.executor.close_connection()

    def run_complete_migration(self, extraction_file: Optional[str] = None,
                              dry_run_first: bool = True,
                              interactive: bool = False) -> bool:
        """
        Executa migração completa (todas as 3 fases).

        Args:
            extraction_file: Arquivo específico para extração
            dry_run_first: Se True, executa dry run antes da migração real
            interactive: Modo interativo

        Returns:
            True se bem-sucedido, False caso contrário
        """
        self.logger.info("🌟 INICIANDO MIGRAÇÃO COMPLETA")
        self.logger.info(f"🕒 Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        start_time = datetime.now()

        try:
            # Fase 1: Extração
            if self.config['extraction']['enabled']:
                json_file = self.phase_1_extraction(extraction_file)
                if not json_file:
                    return False
            else:
                # Usar arquivo existente
                json_file = extraction_file
                if not json_file or not os.path.exists(json_file):
                    self.logger.error("❌ Arquivo de extração não encontrado")
                    return False

            # Fase 2: Geração
            if self.config['generation']['enabled']:
                if not self.phase_2_generation(json_file):
                    return False

            # Fase 3: Execução
            if self.config['execution']['enabled']:
                # Dry run primeiro (se habilitado)
                if dry_run_first:
                    self.logger.info("\n🔍 Executando DRY RUN primeiro...")
                    if not self.phase_3_execution(dry_run=True, interactive=False):
                        self.logger.error("❌ Dry run falhou - parando execução")
                        return False

                # Execução real
                if not self.phase_3_execution(dry_run=False, interactive=interactive):
                    return False

            # Sucesso!
            end_time = datetime.now()
            duration = end_time - start_time

            self.logger.info("\n" + "="*60)
            self.logger.info("🎉 MIGRAÇÃO COMPLETA CONCLUÍDA COM SUCESSO!")
            self.logger.info(f"🕒 Duração: {duration}")
            self.logger.info(f"📝 Session ID: {self.session_id}")
            self.logger.info("="*60)

            return True

        except Exception as e:
            self.logger.error(f"❌ Erro na migração completa: {e}")
            return False

    def generate_report(self) -> str:
        """Gera relatório da migração."""
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / f"migration_report_{self.session_id}.json"

        report = {
            "session_info": {
                "id": self.session_id,
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
                "config_file": self.config_file
            },
            "configuration": self.config,
            "results": {
                "extraction": "completed" if self.extractor else "not_executed",
                "generation": "completed" if self.generator else "not_executed",
                "execution": "completed" if self.executor else "not_executed"
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"📊 Relatório gerado: {report_file}")
        return str(report_file)


def main():
    """Função principal com interface CLI."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Enterprise Migration Orchestrator v4.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  # Migração completa (extração + geração + execução)
  python migration_orchestrator_v4.py --complete

  # Apenas extração
  python migration_orchestrator_v4.py --extract --output data.json

  # Apenas geração de scripts
  python migration_orchestrator_v4.py --generate --input data.json

  # Apenas execução (modo interativo)
  python migration_orchestrator_v4.py --execute --interactive

  # Dry run completo
  python migration_orchestrator_v4.py --complete --dry-run
        """
    )

    # Operações principais
    parser.add_argument('--complete', action='store_true',
                       help='Executar migração completa (3 fases)')
    parser.add_argument('--extract', action='store_true',
                       help='Executar apenas extração (Fase 1)')
    parser.add_argument('--generate', action='store_true',
                       help='Executar apenas geração (Fase 2)')
    parser.add_argument('--execute', action='store_true',
                       help='Executar apenas execução (Fase 3)')

    # Parâmetros
    parser.add_argument('--config', default='config/migration_config.json',
                       help='Arquivo de configuração principal')
    parser.add_argument('--input', help='Arquivo JSON de entrada')
    parser.add_argument('--output', help='Arquivo de saída')
    parser.add_argument('--dry-run', action='store_true',
                       help='Modo dry run (simular sem alterar)')
    parser.add_argument('--interactive', action='store_true',
                       help='Modo interativo')
    parser.add_argument('--no-dry-run-first', action='store_true',
                       help='Pular dry run automático antes da execução')

    # Debug e relatórios
    parser.add_argument('--verbose', action='store_true',
                       help='Saída detalhada')
    parser.add_argument('--report', action='store_true',
                       help='Gerar relatório ao final')

    args = parser.parse_args()

    # Inicializar orquestrador
    orchestrator = MigrationOrchestrator(args.config)

    if not orchestrator.load_config():
        sys.exit(1)

    success = False

    try:
        if args.complete:
            # Migração completa
            success = orchestrator.run_complete_migration(
                extraction_file=args.input,
                dry_run_first=not args.no_dry_run_first,
                interactive=args.interactive
            )

        elif args.extract:
            # Apenas extração
            result = orchestrator.phase_1_extraction(args.output)
            success = bool(result)
            if result:
                print(f"📄 Arquivo gerado: {result}")

        elif args.generate:
            # Apenas geração
            if not args.input:
                print("❌ --input é obrigatório para geração")
                sys.exit(1)
            success = orchestrator.phase_2_generation(args.input)

        elif args.execute:
            # Apenas execução
            success = orchestrator.phase_3_execution(
                dry_run=args.dry_run,
                interactive=args.interactive
            )

        else:
            parser.print_help()
            sys.exit(1)

        # Gerar relatório se solicitado
        if args.report:
            orchestrator.generate_report()

        # Resultado final
        if success:
            print("\n✅ Operação concluída com sucesso!")
            sys.exit(0)
        else:
            print("\n❌ Operação falhou!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Operação interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
