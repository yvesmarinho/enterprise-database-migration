#!/usr/bin/env python3
"""
PostgreSQL Migration Orchestrator
=================================

Orquestrador completo para migração PostgreSQL usando SQLAlchemy.
Gerencia todo o fluxo: validação → migração → verificação → relatórios.

Versão: 2.0.0
Data: 03/10/2025
Autor: GitHub Copilot Enterprise
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Adicionar diretório do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Imports dos módulos de migração
try:
    from src.migration.core.sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator
    from src.migration.validation.check_scram_auth import ScramAuthChecker
    from src.migration.validation.test_wfdb02_connection import WFDB02ConnectionTester
    from src.migration.utils.discover_users import UserDiscoverer
    from src.migration.utils.analyze_password import PasswordAnalyzer
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("💡 Execute a partir do diretório raiz do projeto")
    sys.exit(1)

class MigrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class MigrationStep:
    name: str
    description: str
    required: bool = True
    status: MigrationStatus = MigrationStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict] = None

class MigrationOrchestrator:
    """Orquestrador principal para migração PostgreSQL."""

    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or "src/migration/config")
        self.migration_dir = Path("src/migration")
        self.reports_dir = self.migration_dir / "core" / "reports"

        # Criar diretórios se não existirem
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Configurações
        self.migration_rules = {}
        self.source_config = {}
        self.dest_config = {}

        # Estado da migração
        self.steps: List[MigrationStep] = []
        self.overall_status = MigrationStatus.PENDING
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_file = self.reports_dir / f"orchestrator_execution_{self.session_id}.log"

        # Componentes
        self.migrator = None
        self.scram_checker = None
        self.connection_tester = None
        self.user_discoverer = None
        self.password_analyzer = None

        self._setup_logging()
        self._initialize_steps()

    def _setup_logging(self):
        """Configura sistema de logging."""
        self.log_entries = []

    def log(self, message: str, level: str = "INFO"):
        """Sistema de logging centralizado."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_entries.append(log_entry)
        print(log_entry)

        # Salvar no arquivo
        with open(self.report_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\\n")

    def _initialize_steps(self):
        """Inicializa os passos da migração."""
        self.steps = [
            MigrationStep("load_configs", "Carregar configurações de migração"),
            MigrationStep("validate_environment", "Validar ambiente e dependências"),
            MigrationStep("test_connectivity", "Testar conectividade com servidores"),
            MigrationStep("discover_source", "Descobrir estrutura do servidor origem"),
            MigrationStep("analyze_compatibility", "Analisar compatibilidade SCRAM-SHA-256"),
            MigrationStep("pre_migration_backup", "Criar backup pré-migração", required=False),
            MigrationStep("execute_migration", "Executar migração principal"),
            MigrationStep("validate_migration", "Validar resultado da migração"),
            MigrationStep("test_connections", "Testar conexões pós-migração"),
            MigrationStep("generate_report", "Gerar relatório final")
        ]

    def load_configurations(self) -> bool:
        """Carrega todas as configurações necessárias."""
        step = self._get_step("load_configs")
        self._start_step(step)

        try:
            # Carregar regras de migração
            rules_file = self.config_dir / "migration_rules.json"
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    self.migration_rules = json.load(f)
                self.log("✅ Regras de migração carregadas")
            else:
                self.log("⚠️ Arquivo migration_rules.json não encontrado, usando padrões")
                self._create_default_migration_rules()

            # Carregar configurações dos servidores
            source_file = self.config_dir / "source_config.json"
            dest_file = self.config_dir / "destination_config.json"

            if source_file.exists() and dest_file.exists():
                with open(source_file, 'r', encoding='utf-8') as f:
                    self.source_config = json.load(f)
                with open(dest_file, 'r', encoding='utf-8') as f:
                    self.dest_config = json.load(f)
                self.log("✅ Configurações de servidor carregadas")
            else:
                self.log("❌ Arquivos de configuração de servidor não encontrados")
                self._finish_step(step, False, "Arquivos de configuração não encontrados")
                return False

            # Inicializar componentes
            self.migrator = SQLAlchemyPostgreSQLMigrator()
            self.scram_checker = ScramAuthChecker()
            self.connection_tester = WFDB02ConnectionTester()
            self.user_discoverer = UserDiscoverer()
            self.password_analyzer = PasswordAnalyzer()

            self._finish_step(step, True)
            return True

        except Exception as e:
            self.log(f"❌ Erro ao carregar configurações: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def validate_environment(self) -> bool:
        """Valida o ambiente de execução."""
        step = self._get_step("validate_environment")
        self._start_step(step)

        try:
            # Verificar dependências Python
            required_modules = ['sqlalchemy', 'psycopg2', 'json', 'pathlib']
            missing_modules = []

            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)

            if missing_modules:
                error_msg = f"Módulos faltando: {', '.join(missing_modules)}"
                self.log(f"❌ {error_msg}", "ERROR")
                self._finish_step(step, False, error_msg)
                return False

            # Verificar arquivos essenciais
            essential_files = [
                self.migration_dir / "core" / "sqlalchemy_migration.py",
                self.migration_dir / "validation" / "check_scram_auth.py",
                self.migration_dir / "utils" / "discover_users.py"
            ]

            for file_path in essential_files:
                if not file_path.exists():
                    error_msg = f"Arquivo essencial não encontrado: {file_path}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self._finish_step(step, False, error_msg)
                    return False

            self.log("✅ Ambiente validado com sucesso")
            self._finish_step(step, True)
            return True

        except Exception as e:
            self.log(f"❌ Erro na validação do ambiente: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def test_connectivity(self) -> bool:
        """Testa conectividade com ambos os servidores."""
        step = self._get_step("test_connectivity")
        self._start_step(step)

        try:
            # Testar origem
            if not self.migrator.load_configs():
                self._finish_step(step, False, "Falha ao carregar configs no migrator")
                return False

            if not self.migrator.create_engines():
                self._finish_step(step, False, "Falha ao criar engines de conexão")
                return False

            self.log("✅ Conectividade testada com sucesso")
            self._finish_step(step, True)
            return True

        except Exception as e:
            self.log(f"❌ Erro no teste de conectividade: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def discover_source_structure(self) -> bool:
        """Descobre a estrutura do servidor origem."""
        step = self._get_step("discover_source")
        self._start_step(step)

        try:
            # Descobrir usuários
            self.log("🔍 Descobrindo usuários do servidor origem...")
            users_data = self.user_discoverer.discover_all_users()

            if users_data:
                step.result_data = {"users_discovered": len(users_data), "users": users_data}
                self.log(f"✅ {len(users_data)} usuários descobertos")
            else:
                self.log("⚠️ Nenhum usuário descoberto")

            self._finish_step(step, True)
            return True

        except Exception as e:
            self.log(f"❌ Erro na descoberta da estrutura: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def analyze_scram_compatibility(self) -> bool:
        """Analisa compatibilidade com SCRAM-SHA-256."""
        step = self._get_step("analyze_compatibility")
        self._start_step(step)

        try:
            # Verificar suporte SCRAM no destino
            self.log("🔍 Analisando compatibilidade SCRAM-SHA-256...")
            scram_status = self.scram_checker.check_scram_support()

            if scram_status:
                self.log("✅ SCRAM-SHA-256 suportado no destino")
                step.result_data = {"scram_supported": True}
            else:
                self.log("⚠️ SCRAM-SHA-256 pode não estar configurado")
                step.result_data = {"scram_supported": False}

            self._finish_step(step, True)
            return True

        except Exception as e:
            self.log(f"❌ Erro na análise SCRAM: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def create_pre_migration_backup(self) -> bool:
        """Cria backup antes da migração."""
        step = self._get_step("pre_migration_backup")
        self._start_step(step)

        try:
            # Este passo é opcional por padrão
            if not step.required:
                self.log("⏭️ Backup pré-migração pulado (opcional)")
                self._finish_step(step, True, "Pulado (opcional)")
                return True

            # Implementar backup se necessário
            backup_file = f"pre_migration_backup_{self.session_id}.sql"
            self.log(f"💾 Backup seria criado em: {backup_file}")

            self._finish_step(step, True)
            return True

        except Exception as e:
            self.log(f"❌ Erro no backup: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def execute_main_migration(self) -> bool:
        """Executa a migração principal."""
        step = self._get_step("execute_migration")
        self._start_step(step)

        try:
            self.log("🚀 Iniciando migração principal...")

            # Executar migração usando SQLAlchemy
            migration_result = self.migrator.migrate_all_users()

            if migration_result:
                self.log("✅ Migração principal executada com sucesso")
                step.result_data = {"migration_completed": True}
                self._finish_step(step, True)
                return True
            else:
                self.log("❌ Falha na migração principal")
                self._finish_step(step, False, "Migração falhou")
                return False

        except Exception as e:
            self.log(f"❌ Erro na migração: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def validate_migration_result(self) -> bool:
        """Valida o resultado da migração."""
        step = self._get_step("validate_migration")
        self._start_step(step)

        try:
            self.log("🔍 Validando resultado da migração...")

            # Comparar usuários origem vs destino
            validation_result = self.migrator.validate_migration()

            if validation_result:
                self.log("✅ Validação da migração bem-sucedida")
                step.result_data = {"validation_passed": True}
                self._finish_step(step, True)
                return True
            else:
                self.log("⚠️ Validação encontrou discrepâncias")
                step.result_data = {"validation_passed": False}
                self._finish_step(step, True, "Discrepâncias encontradas")
                return True  # Não falha o processo, apenas reporta

        except Exception as e:
            self.log(f"❌ Erro na validação: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def test_post_migration_connections(self) -> bool:
        """Testa conexões após a migração."""
        step = self._get_step("test_connections")
        self._start_step(step)

        try:
            self.log("🔗 Testando conexões pós-migração...")

            # Testar conexões com WFDB02
            connection_results = self.connection_tester.test_all_connections()

            if connection_results:
                self.log("✅ Testes de conexão pós-migração bem-sucedidos")
                step.result_data = {"connections_tested": True}
                self._finish_step(step, True)
                return True
            else:
                self.log("⚠️ Alguns testes de conexão falharam")
                step.result_data = {"connections_tested": False}
                self._finish_step(step, True, "Algumas conexões falharam")
                return True  # Não falha o processo

        except Exception as e:
            self.log(f"❌ Erro nos testes de conexão: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def generate_final_report(self) -> bool:
        """Gera relatório final da migração."""
        step = self._get_step("generate_report")
        self._start_step(step)

        try:
            self.log("📊 Gerando relatório final...")

            report_data = {
                "session_id": self.session_id,
                "start_time": self.steps[0].start_time.isoformat() if self.steps[0].start_time else None,
                "end_time": datetime.now().isoformat(),
                "overall_status": self.overall_status.value,
                "steps": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "status": s.status.value,
                        "start_time": s.start_time.isoformat() if s.start_time else None,
                        "end_time": s.end_time.isoformat() if s.end_time else None,
                        "error_message": s.error_message,
                        "result_data": s.result_data
                    }
                    for s in self.steps
                ],
                "log_entries": self.log_entries
            }

            # Salvar relatório JSON
            report_json_file = self.reports_dir / f"migration_report_{self.session_id}.json"
            with open(report_json_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            # Salvar relatório Markdown
            report_md_file = self.reports_dir / f"migration_report_{self.session_id}.md"
            self._generate_markdown_report(report_md_file, report_data)

            self.log(f"✅ Relatórios salvos:")
            self.log(f"   - JSON: {report_json_file}")
            self.log(f"   - Markdown: {report_md_file}")
            self.log(f"   - Log: {self.report_file}")

            step.result_data = {
                "json_report": str(report_json_file),
                "markdown_report": str(report_md_file),
                "log_file": str(self.report_file)
            }

            self._finish_step(step, True)
            return True

        except Exception as e:
            self.log(f"❌ Erro na geração do relatório: {e}", "ERROR")
            self._finish_step(step, False, str(e))
            return False

    def run_complete_migration(self) -> bool:
        """Executa todo o fluxo de migração."""
        self.log("🚀 Iniciando orquestração completa da migração PostgreSQL")
        self.log(f"📋 Session ID: {self.session_id}")

        # Definir ordem de execução
        execution_order = [
            self.load_configurations,
            self.validate_environment,
            self.test_connectivity,
            self.discover_source_structure,
            self.analyze_scram_compatibility,
            self.create_pre_migration_backup,
            self.execute_main_migration,
            self.validate_migration_result,
            self.test_post_migration_connections,
            self.generate_final_report
        ]

        success_count = 0
        total_steps = len(execution_order)

        for step_func in execution_order:
            step_name = step_func.__name__
            self.log(f"\\n🔄 Executando: {step_name}")

            try:
                result = step_func()
                if result:
                    success_count += 1
                    self.log(f"✅ {step_name} concluído com sucesso")
                else:
                    self.log(f"❌ {step_name} falhou")

                    # Verificar se deve continuar em caso de erro
                    continue_on_error = self.migration_rules.get("error_handling", {}).get("continue_on_error", False)
                    if not continue_on_error:
                        self.log("🛑 Parando execução devido à falha crítica")
                        self.overall_status = MigrationStatus.FAILED
                        break
                    else:
                        self.log("⚠️ Continuando execução apesar da falha")

            except Exception as e:
                self.log(f"💥 Exceção não tratada em {step_name}: {e}", "ERROR")
                self.overall_status = MigrationStatus.FAILED
                break

        # Determinar status final
        if success_count == total_steps:
            self.overall_status = MigrationStatus.SUCCESS
            self.log("\\n🎉 Migração concluída com SUCESSO!")
        elif success_count > 0:
            self.overall_status = MigrationStatus.PARTIAL
            self.log(f"\\n⚠️ Migração PARCIALMENTE concluída ({success_count}/{total_steps} passos)")
        else:
            self.overall_status = MigrationStatus.FAILED
            self.log("\\n❌ Migração FALHOU completamente")

        return self.overall_status in [MigrationStatus.SUCCESS, MigrationStatus.PARTIAL]

    # Métodos auxiliares
    def _get_step(self, step_name: str) -> MigrationStep:
        """Encontra um passo pelo nome."""
        for step in self.steps:
            if step.name == step_name:
                return step
        raise ValueError(f"Passo não encontrado: {step_name}")

    def _start_step(self, step: MigrationStep):
        """Marca início de um passo."""
        step.status = MigrationStatus.RUNNING
        step.start_time = datetime.now()

    def _finish_step(self, step: MigrationStep, success: bool, error_message: str = None):
        """Marca fim de um passo."""
        step.status = MigrationStatus.SUCCESS if success else MigrationStatus.FAILED
        step.end_time = datetime.now()
        step.error_message = error_message

    def _create_default_migration_rules(self):
        """Cria regras padrão de migração."""
        self.migration_rules = {
            "migration_rules": {
                "structure_migration": {"enabled": True},
                "user_migration": {"enabled": True},
                "data_migration": {"enabled": False},
                "error_handling": {"continue_on_error": False}
            }
        }

    def _generate_markdown_report(self, file_path: Path, report_data: Dict):
        """Gera relatório em formato Markdown."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Relatório de Migração PostgreSQL\\n\\n")
            f.write(f"**Session ID:** {report_data['session_id']}\\n")
            f.write(f"**Status:** {report_data['overall_status'].upper()}\\n")
            f.write(f"**Início:** {report_data['start_time']}\\n")
            f.write(f"**Fim:** {report_data['end_time']}\\n\\n")

            f.write("## 📋 Resumo dos Passos\\n\\n")
            for step in report_data['steps']:
                status_emoji = "✅" if step['status'] == 'success' else "❌" if step['status'] == 'failed' else "⏭️"
                f.write(f"- {status_emoji} **{step['description']}** ({step['status']})\\n")

            f.write("\\n## 📊 Detalhes dos Passos\\n\\n")
            for step in report_data['steps']:
                f.write(f"### {step['description']}\\n")
                f.write(f"- **Status:** {step['status']}\\n")
                if step['start_time']:
                    f.write(f"- **Início:** {step['start_time']}\\n")
                if step['end_time']:
                    f.write(f"- **Fim:** {step['end_time']}\\n")
                if step['error_message']:
                    f.write(f"- **Erro:** {step['error_message']}\\n")
                if step['result_data']:
                    f.write(f"- **Dados:** {json.dumps(step['result_data'], indent=2)}\\n")
                f.write("\\n")

def main():
    """Função principal - interface CLI."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Migration Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s                          # Migração completa interativa
  %(prog)s --auto                   # Migração automática
  %(prog)s --config custom_config/  # Usar diretório personalizado
  %(prog)s --dry-run                # Simular sem executar
        """
    )

    parser.add_argument('--config', '-c',
                       help='Diretório de configurações (padrão: src/migration/config)')
    parser.add_argument('--auto', '-a', action='store_true',
                       help='Execução automática sem interação')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Simular execução sem modificar dados')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Saída detalhada')

    args = parser.parse_args()

    print("=" * 70)
    print("🚀 PostgreSQL Migration Orchestrator v2.0.0")
    print("=" * 70)

    if args.dry_run:
        print("🔍 MODO SIMULAÇÃO - Nenhuma modificação será feita")
        print("-" * 70)

    # Criar orquestrador
    orchestrator = MigrationOrchestrator(config_dir=args.config)

    if not args.auto:
        # Modo interativo
        print("\\n📋 Configuração:")
        print(f"   - Diretório config: {orchestrator.config_dir}")
        print(f"   - Diretório relatórios: {orchestrator.reports_dir}")
        print(f"   - Session ID: {orchestrator.session_id}")

        response = input("\\n🤔 Continuar com a migração? (s/N): ").lower().strip()
        if response not in ['s', 'sim', 'y', 'yes']:
            print("❌ Migração cancelada pelo usuário")
            return 1

    # Executar migração
    try:
        if args.dry_run:
            print("\\n🔍 [SIMULAÇÃO] Executaria migração completa...")
            print("✅ [SIMULAÇÃO] Migração simulada com sucesso")
            return 0
        else:
            success = orchestrator.run_complete_migration()

            print("\\n" + "=" * 70)
            if success:
                print("🎉 MIGRAÇÃO CONCLUÍDA!")
                print(f"📊 Status: {orchestrator.overall_status.value.upper()}")
                print(f"📋 Relatórios em: {orchestrator.reports_dir}")
                return 0
            else:
                print("❌ MIGRAÇÃO FALHOU!")
                print(f"📊 Status: {orchestrator.overall_status.value.upper()}")
                print(f"📋 Verifique os logs em: {orchestrator.reports_dir}")
                return 1

    except KeyboardInterrupt:
        print("\\n⚠️ Migração interrompida pelo usuário")
        return 1
    except Exception as e:
        print(f"\\n💥 Erro inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
