#!/usr/bin/env python3
"""
PostgreSQL Enterprise Migration System v4.0.0 - Main Controller
==============================================================

Controlador principal do sistema de migração PostgreSQL.
Integra todos os componentes do sistema v4.0.0 em uma interface unificada.

Funcionalidades:
- Sistema 3-Fases (Extração → Geração → Execução)
- Interface CLI completa
- Modo interativo e automático
- Dry run e validações
- Logs e relatórios detalhados

Versão: 4.0.0
Validado em: Migração WF004→WFDB02 (Out/2025)
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configurar ambiente do projeto
project_root = Path(__file__).parent.resolve()
os.environ['PROJECT_HOME'] = str(project_root)
sys.path.insert(0, str(project_root))

# Importar sistema v4.0.0
try:
    from app.core.migration_orchestrator import MigrationOrchestrator
    SYSTEM_V4_AVAILABLE = True
except ImportError:
    print("⚠️ Sistema v4.0.0 não encontrado, usando modo de compatibilidade")
    SYSTEM_V4_AVAILABLE = False

# === IMPORTS CONDICIONAIS PARA TODOS OS MÓDULOS ===


def check_module_availability():
    """Verifica disponibilidade de módulos do sistema."""
    modules_to_check = {
        'migration_structure': 'app.core.migration_structure',
        'orchestrator_pure_python': 'app.orchestrators.orchestrator_pure_python',
        'validator': 'app.validation.validator',
        'sqlalchemy_migration': 'app.core.sqlalchemy_migration',
        'complete_migration': 'app.core.complete_migration',
        'migrate_users': 'app.core.migrate_users',
        'cleanup_database': 'cleanup.cleanup_database',
        'monitor': 'monitor',
        'database_utils': 'utils.database_utils',
        'data_validator': 'validation.data_validator',
        'doc_generator': 'docs.doc_generator',
        'cli_interface': 'cli.cli_interface',
        'scheduler': 'utils.scheduler',
        'metrics': 'utils.metrics',
        'backup': 'utils.backup',
        'security': 'utils.security',
        'notifications': 'utils.notifications',
        'rollback': 'utils.rollback',
        'config_manager': 'components.config_manager',
    }

    availability = {}

    for name, module_path in modules_to_check.items():
        try:
            __import__(module_path)
            availability[name] = True
        except ImportError:
            availability[name] = False
        except Exception:
            availability[name] = False

    return availability


def setup_project_environment():
    """Configura ambiente do projeto com todas as variáveis necessárias."""
    project_home = Path(os.environ['PROJECT_HOME'])

    # Definir todos os paths importantes como variáveis de ambiente
    os.environ['PROJECT_CONFIG_DIR'] = str(project_home / 'config')
    os.environ['PROJECT_SECRETS_DIR'] = str(project_home / 'secrets')
    os.environ['PROJECT_CORE_DIR'] = str(project_home / 'core')
    os.environ['PROJECT_UTILS_DIR'] = str(project_home / 'utils')
    os.environ['PROJECT_VALIDATION_DIR'] = str(project_home / 'validation')
    os.environ['PROJECT_ORCHESTRATORS_DIR'] = str(
        project_home / 'orchestrators')
    os.environ['PROJECT_COMPONENTS_DIR'] = str(project_home / 'components')
    os.environ['PROJECT_CLEANUP_DIR'] = str(project_home / 'cleanup')
    os.environ['PROJECT_CLI_DIR'] = str(project_home / 'cli')
    os.environ['PROJECT_DOCS_DIR'] = str(project_home / 'docs')
    os.environ['PROJECT_SCRIPTS_DIR'] = str(project_home / 'scripts')
    os.environ['PROJECT_TEST_DIR'] = str(project_home / 'test')

    # Criar diretórios se não existirem
    for dir_path in [
        project_home / 'config',
        project_home / 'core' / 'reports',
        project_home / 'logs'
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

    return project_home


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configura logging centralizado do sistema."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def show_system_status():
    """Mostra status dos componentes do sistema."""
    logger = setup_logging()

    print("\n" + "="*60)
    print("🚀 ENTERPRISE DATABASE MIGRATION SYSTEM")
    print("="*60)

    # Verificar componentes disponíveis
    components = {
        "📂 Components": "components/base_component.py",
        "🎯 Orchestrators": "orchestrators/",
        "🔍 Validation": "validation/",
        "🧹 Cleanup": "cleanup/",
        "🛠️ Utils": "utils/",
        "🎛️ CLI": "cli/quick_migration.py",
        "📚 Documentation": "docs/exemplos_uso.py"
    }

    print("\n📋 COMPONENTES DISPONÍVEIS:")
    for name, path in components.items():
        full_path = project_root / path
        status = "✅ Disponível" if full_path.exists() else "❌ Não encontrado"
        print(f"   {name}: {status}")

    print(f"\n📁 Diretório do projeto: {project_root}")
    print("="*60)


def run_migration(mode: str = "interactive"):
    """Executa migração usando run_migration.py."""
    logger = setup_logging()
    logger.info(f"Iniciando migração em modo: {mode}")

    try:
        # Salvar argumentos originais
        original_argv = sys.argv.copy()

        # Configurar argumentos para o orquestrador
        if mode == "auto":
            sys.argv = [sys.argv[0], "--auto", "--verbose"]
        else:
            sys.argv = [sys.argv[0]]  # Modo interativo padrão

        from cli.run_migration import main as run_migration_main
        result = run_migration_main()

        # Restaurar argumentos originais
        sys.argv = original_argv
        return result

    except ImportError as e:
        logger.error(f"Erro ao importar cli.run_migration: {e}")
        # Restaurar argumentos mesmo em caso de erro
        if 'original_argv' in locals():
            sys.argv = original_argv
        return False
    except Exception as e:
        logger.error(f"Erro durante execução da migração: {e}")
        # Restaurar argumentos mesmo em caso de erro
        if 'original_argv' in locals():
            sys.argv = original_argv
        return False


def run_orchestrator(orchestrator_type: str = "pure_python"):
    """Executa orquestrador específico."""
    logger = setup_logging()
    logger.info(f"Iniciando orquestrador: {orchestrator_type}")

    try:
        if orchestrator_type == "pure_python":
            from app.orchestrators.orchestrator_pure_python import (
                main as orchestrator_main,
            )
            return orchestrator_main()
        elif orchestrator_type == "sqlalchemy":
            from app.orchestrators.migration_orchestrator import main as migration_main
            return migration_main()
        else:
            logger.error(
                f"Tipo de orquestrador não reconhecido: {orchestrator_type}")
            return False
    except ImportError as e:
        logger.error(f"Erro ao importar orquestrador {orchestrator_type}: {e}")
        return False


def run_validation():
    """Executa validação do sistema."""
    logger = setup_logging()
    logger.info("Iniciando validação do sistema")

    try:
        # Importar e executar validadores
        print("🔍 Executando validação...")
        # TODO: Implementar chamada para validadores
        return True
    except Exception as e:
        logger.error(f"Erro na validação: {e}")
        return False


def run_cleanup():
    """Executa limpeza do sistema."""
    logger = setup_logging()
    logger.info("Iniciando limpeza do sistema")

    try:
        from app.cleanup.cleanup_database import main as cleanup_main
        return cleanup_main()
    except ImportError as e:
        logger.error(f"Erro ao importar cleanup: {e}")
        return False

# === FUNÇÕES ESPECÍFICAS DE CADA MÓDULO ===


def run_core_complete_migration():
    """Executa migração completa psycopg2."""
    logger = setup_logging()
    logger.info("Iniciando migração completa psycopg2")
    try:
        from app.core.complete_migration import main as complete_migration_main
        return complete_migration_main()
    except ImportError as e:
        logger.error(f"Módulo core.complete_migration não disponível: {e}")
        return False


def run_core_migrate_users():
    """Executa migração específica de usuários."""
    logger = setup_logging()
    logger.info("Iniciando migração de usuários")
    try:
        from app.core.migrate_users import main as migrate_users_main
        return migrate_users_main()
    except ImportError as e:
        logger.error(f"Módulo core.migrate_users não disponível: {e}")
        return False


def run_core_migration_structure():
    """Executa migração apenas de estruturas."""
    logger = setup_logging()
    logger.info("Iniciando migração de estruturas")
    try:
        from app.core.migration_structure import main as migration_structure_main
        return migration_structure_main()
    except ImportError as e:
        logger.error(f"Módulo core.migration_structure não disponível: {e}")
        return False


def run_utils_debug_connection():
    """Executa debug de conexões."""
    logger = setup_logging()
    logger.info("Iniciando debug de conexões")
    try:
        from utils.debug_connection import main as debug_connection_main
        return debug_connection_main()
    except ImportError as e:
        logger.error(f"Módulo utils.debug_connection não disponível: {e}")
        return False


def run_utils_discover_users():
    """Executa descoberta de usuários."""
    logger = setup_logging()
    logger.info("Iniciando descoberta de usuários")
    try:
        from utils.discover_users import main as discover_users_main
        return discover_users_main()
    except ImportError as e:
        logger.error(f"Módulo utils.discover_users não disponível: {e}")
        return False


def run_utils_analyze_password():
    """Executa análise de senhas."""
    logger = setup_logging()
    logger.info("Iniciando análise de senhas")
    try:
        from utils.analyze_password import main as analyze_password_main
        return analyze_password_main()
    except ImportError as e:
        logger.error(f"Módulo utils.analyze_password não disponível: {e}")
        return False


def run_validation_test_migration():
    """Executa testes de migração."""
    logger = setup_logging()
    logger.info("Iniciando testes de migração")
    try:
        from app.validation.test_migration import main as test_migration_main
        return test_migration_main()
    except ImportError as e:
        logger.error(f"Módulo validation.test_migration não disponível: {e}")
        return False


def run_validation_wfdb02_tests():
    """Executa testes WFDB02."""
    logger = setup_logging()
    logger.info("Iniciando testes WFDB02")

    print("\n🔍 Testes WFDB02 Disponíveis:")
    print("  1. Teste de Conexão")
    print("  2. Teste Simples")
    print("  3. Teste Mínimo")
    print("  4. Teste Completo")
    print("  5. Verificar Status")

    choice = input("Escolha um teste (1-5): ").strip()

    try:
        if choice == '1':
            from app.validation.test_wfdb02_connection import (
                main as wfdb02_connection_main,
            )
            return wfdb02_connection_main()
        elif choice == '2':
            from app.validation.test_wfdb02_simple import main as wfdb02_simple_main
            return wfdb02_simple_main()
        elif choice == '3':
            from app.validation.test_wfdb02_minimal import main as wfdb02_minimal_main
            return wfdb02_minimal_main()
        elif choice == '4':
            from app.validation.test_wfdb02_only import main as wfdb02_only_main
            return wfdb02_only_main()
        elif choice == '5':
            from app.validation.check_wfdb02_status import main as wfdb02_status_main
            return wfdb02_status_main()
        else:
            print("❌ Opção inválida")
            return False
    except ImportError as e:
        logger.error(f"Módulo de teste WFDB02 não disponível: {e}")
        return False


def run_cleanup_database():
    """Executa limpeza de banco de dados."""
    logger = setup_logging()
    logger.info("Iniciando limpeza de banco")
    try:
        from app.cleanup.cleanup_database import main as cleanup_database_main
        return cleanup_database_main()
    except ImportError as e:
        logger.error(f"Módulo cleanup.cleanup_database não disponível: {e}")
        return False


def run_cleanup_examples():
    """Executa exemplos de limpeza."""
    logger = setup_logging()
    logger.info("Iniciando exemplos de limpeza")
    try:
        from app.cleanup.exemplo_cleanup import run_cleanup_example
        return run_cleanup_example()
    except ImportError as e:
        logger.error(f"Módulo cleanup.exemplo_cleanup não disponível: {e}")
        return False


def run_quick_cli():
    """Executa CLI rápido."""
    logger = setup_logging()
    logger.info("Iniciando CLI rápido")
    try:
        from cli.quick_migration import main as quick_cli_main
        return quick_cli_main()
    except ImportError as e:
        logger.error(f"Módulo cli.quick_migration não disponível: {e}")
        return False


def run_documentation_examples():
    """Executa exemplos de uso."""
    logger = setup_logging()
    logger.info("Iniciando exemplos de uso")
    try:
        from docs.exemplos_uso import main as exemplos_uso_main
        return exemplos_uso_main()
    except ImportError as e:
        logger.error(f"Módulo docs.exemplos_uso não disponível: {e}")
        return False


def create_expanded_menu():
    """Cria menu expandido com todas as funcionalidades."""
    availability = check_module_availability()

    print("\n" + "="*70)
    print("� PostgreSQL Migration Orchestrator v3.0.0 - MENU COMPLETO")
    print("="*70)

    print("\n📋 MIGRAÇÃO PRINCIPAL:")
    print("  1️⃣  Migração Completa SQLAlchemy (recomendado)")
    print("  2️⃣  Teste de Ambiente apenas")
    print("  3️⃣  Validação de Módulos apenas")
    print("  4️⃣  Teste de Conectividade apenas")
    print("  5️⃣  Simulação Completa (dry-run)")

    if availability.get('CORE', False):
        print("\n🔧 MOTORES DE MIGRAÇÃO ALTERNATIVOS:")
        print("  6️⃣  Migração psycopg2 Completa")
        print("  7️⃣  Migração Apenas Usuários")
        print("  8️⃣  Migração Apenas Estruturas")

    if availability.get('UTILS', False):
        print("\n🛠️  UTILITÁRIOS:")
        print("  10️⃣ Debug de Conexões")
        print("  11️⃣ Descoberta de Usuários")
        print("  12️⃣ Análise de Senhas SCRAM")

    if availability.get('VALIDATION', False):
        print("\n🧪 VALIDAÇÕES E TESTES:")
        print("  13️⃣ Testes de Migração")
        print("  14️⃣ Testes WFDB02 (submenu)")
        print("  15️⃣ Verificação de Status")

    if availability.get('CLEANUP', False):
        print("\n🧹 LIMPEZA DE BANCO:")
        print("  16️⃣ Limpeza de Banco de Dados")
        print("  17️⃣ Exemplos de Limpeza")

    if availability.get('CLI', False):
        print("\n⚡ CLI RÁPIDO:")
        print("  18️⃣ Interface CLI Rápida")

    if availability.get('DOCS', False):
        print("\n📚 DOCUMENTAÇÃO:")
        print("  19️⃣ Exemplos de Uso Interativo")

    print("\n📊 SISTEMA:")
    print("  20️⃣ Status do Sistema")
    print("  21️⃣ Ajuda Detalhada")
    print("  0️⃣  Sair")

    print("\n" + "="*70)
    return availability


def handle_menu_choice(choice: str, availability: dict):
    """Processa escolha do menu expandido."""

    # Opções básicas (sempre disponíveis)
    if choice == '1':
        return run_migration()
    elif choice == '2':
        from app.orchestrators.orchestrator_pure_python import (
            PostgreSQLMigrationOrchestrator,
        )
        orch = PostgreSQLMigrationOrchestrator()
        return orch.validate_environment()
    elif choice == '3':
        from app.orchestrators.orchestrator_pure_python import (
            PostgreSQLMigrationOrchestrator,
        )
        orch = PostgreSQLMigrationOrchestrator()
        return orch.check_modules()
    elif choice == '4':
        from app.orchestrators.orchestrator_pure_python import (
            PostgreSQLMigrationOrchestrator,
        )
        orch = PostgreSQLMigrationOrchestrator()
        return orch.test_connectivity()
    elif choice == '5':
        from app.orchestrators.orchestrator_pure_python import (
            PostgreSQLMigrationOrchestrator,
        )
        orch = PostgreSQLMigrationOrchestrator()
        # Executar simulação real
        return True  # Placeholder - implementar simulação

    # Opções de CORE
    elif choice == '6' and availability.get('CORE', False):
        return run_core_complete_migration()
    elif choice == '7' and availability.get('CORE', False):
        return run_core_migrate_users()
    elif choice == '8' and availability.get('CORE', False):
        return run_core_migration_structure()

    # Opções de UTILS
    elif choice == '10' and availability.get('UTILS', False):
        return run_utils_debug_connection()
    elif choice == '11' and availability.get('UTILS', False):
        return run_utils_discover_users()
    elif choice == '12' and availability.get('UTILS', False):
        return run_utils_analyze_password()

    # Opções de VALIDATION
    elif choice == '13' and availability.get('VALIDATION', False):
        return run_validation_test_migration()
    elif choice == '14' and availability.get('VALIDATION', False):
        return run_validation_wfdb02_tests()
    elif choice == '15' and availability.get('VALIDATION', False):
        from app.validation.check_wfdb02_status import main as wfdb02_status_main
        return wfdb02_status_main()

    # Opções de CLEANUP
    elif choice == '16' and availability.get('CLEANUP', False):
        return run_cleanup_database()
    elif choice == '17' and availability.get('CLEANUP', False):
        return run_cleanup_examples()

    # Opções de CLI
    elif choice == '18' and availability.get('CLI', False):
        return run_quick_cli()

    # Opções de DOCS
    elif choice == '19' and availability.get('DOCS', False):
        return run_documentation_examples()

    # Opções do sistema
    elif choice == '20':
        show_system_status()
        return True
    elif choice == '21':
        show_expanded_help()
        return True
    elif choice == '0':
        print("👋 Saindo...")
        return True
    else:
        print("❌ Opção inválida ou módulo não disponível")
        return False


def show_expanded_help():
    """Mostra ajuda expandida do sistema."""
    print("\n" + "="*70)
    print("📚 AJUDA DETALHADA - ENTERPRISE DATABASE MIGRATION")
    print("="*70)

    availability = check_module_availability()

    print("\n📊 STATUS DOS MÓDULOS:")
    for module, available in availability.items():
        status = "✅ Disponível" if available else "❌ Não disponível"
        print(f"  {module}: {status}")

    print("\n📋 COMANDOS CLI ALTERNATIVOS:")
    print("  python main.py status           - Mostra status")
    print("  python main.py migrate          - Migração interativa")
    print("  python main.py migrate-auto     - Migração automática")
    print("  python main.py orchestrate      - Orquestrador")
    print("  python main.py validate         - Validação")
    print("  python main.py cleanup          - Limpeza")
    print("  python main.py help             - Esta ajuda")

    print("\n🔧 CONFIGURAÇÃO:")
    print("  PROJECT_HOME:", os.environ.get('PROJECT_HOME', 'Não configurado'))
    print("  Config file: config.ini")
    print("  Secrets dir: secrets/")

    print("\n📁 ESTRUTURA DO PROJETO:")
    print("  components/    - Componentes base")
    print("  orchestrators/ - Orquestradores principais")
    print("  core/         - Motores de migração")
    print("  utils/        - Utilitários")
    print("  validation/   - Testes e validações")
    print("  cleanup/      - Limpeza de banco")
    print("  cli/          - Interface CLI")
    print("  docs/         - Documentação")

    print("="*70)


def show_help():
    """Mostra ajuda básica do sistema."""
    print("\n" + "="*60)
    print("📚 HELP - ENTERPRISE DATABASE MIGRATION")
    print("="*60)
    print("📋 Comandos disponíveis:")
    print("  status           - Mostra status do sistema")
    print("  migrate          - Executa migração interativa")
    print("  migrate-auto     - Executa migração automática")
    print("  orchestrate      - Executa orquestrador")
    print("  validate         - Executa validação")
    print("  cleanup          - Executa limpeza")
    print("  menu             - Menu interativo completo")
    print("  help             - Mostra esta ajuda")
    print("="*60)


def show_expanded_help():
    """Exibe ajuda expandida do sistema."""
    print("""
🚀 Enterprise Database Migration System - Ajuda Completa

╔═══════════════════════════════════════════════════════════╗
║                    COMANDOS DISPONÍVEIS                  ║
╚═══════════════════════════════════════════════════════════╝

📋 COMANDOS BÁSICOS:
   • status              - Status do sistema e configurações
   • migrate            - Migração interativa com confirmações
   • migrate-auto       - Migração automática (produção)
   • orchestrate        - Orquestrador de migração avançado
   • validate           - Validação completa dos dados
   • cleanup            - Limpeza e manutenção
   • menu               - Menu interativo completo
   • help               - Esta ajuda

🎯 MÓDULOS PRINCIPAIS:
   1.  Migração Principal      - Estruturas e dados básicos
   2.  Orquestrador           - Coordenação avançada
   3.  Validador              - Verificação de integridade
   4.  SQLAlchemy             - Migração via ORM
   5.  Migração Completa      - Processo end-to-end
   6.  Migração Usuários      - Dados de usuários

🛠️  UTILITÁRIOS:
   7.  Limpeza               - Cleanup e manutenção
   8.  Monitoramento         - Métricas em tempo real
   9.  Utilitários           - Ferramentas diversas
   10. Validação Avançada    - Checagens específicas

📚 DOCUMENTAÇÃO E CLI:
   11. Gerador Docs          - Documentação automática
   12. Interface CLI         - Linha de comando

⚙️  OPERAÇÕES AVANÇADAS:
   13. Agendador            - Tarefas programadas
   14. Métricas             - Coleta de dados
   15. Backup               - Cópias de segurança
   16. Segurança            - Validações de segurança
   17. Notificações         - Alertas do sistema
   18. Rollback             - Reversão de migrações
   19. Config Manager       - Gerenciamento de configuração

📊 INFORMAÇÕES:
   20. Status Sistema       - Status completo
   21. Ajuda               - Esta tela de ajuda

╔═══════════════════════════════════════════════════════════╗
║                       EXEMPLOS                           ║
╚═══════════════════════════════════════════════════════════╝

🔧 Linha de comando:
   python main.py                    # Menu interativo
   python main.py status             # Status do sistema
   python main.py migrate            # Migração interativa
   python main.py migrate-auto       # Migração automática
   python main.py orchestrate        # Orquestrador padrão
   python main.py validate           # Validação completa
   python main.py --verbose menu     # Menu com logs detalhados

⚙️  Configuração:
   • config.ini            - Configuração centralizada
   • secrets/*.json        - Configurações de banco
   • PROJECT_HOME          - Diretório base do projeto

📋 Arquivos importantes:
   • main.py              - Ponto de entrada unificado
   • config.ini           - Configuração do sistema
   • components/config_manager.py - Gerenciador de config
   • core/                - Módulos principais de migração
   • utils/               - Utilitários e ferramentas
   • docs/                - Documentação do projeto

Para suporte técnico, consulte: docs/README.md
    """)


def handle_menu_choice(choice, availability):
    """Processa a escolha do menu."""
    try:
        if choice == '1':
            return execute_migration_module()
        elif choice == '2':
            return execute_orchestrator_module()
        elif choice == '3':
            return execute_validator_module()
        elif choice == '4':
            return execute_sqlalchemy_migration()
        elif choice == '5':
            return execute_complete_migration()
        elif choice == '6':
            return execute_user_migration()
        elif choice == '7':
            return execute_cleanup_module()
        elif choice == '8':
            return execute_monitor_module()
        elif choice == '9':
            return execute_utils_module()
        elif choice == '10':
            return execute_validation_module()
        elif choice == '11':
            return execute_docs_generator()
        elif choice == '12':
            return execute_cli_interface()
        elif choice == '13':
            return execute_scheduler_module()
        elif choice == '14':
            return execute_metrics_module()
        elif choice == '15':
            return execute_backup_module()
        elif choice == '16':
            return execute_security_module()
        elif choice == '17':
            return execute_notification_module()
        elif choice == '18':
            return execute_rollback_module()
        elif choice == '19':
            return execute_config_manager()
        elif choice == '20':
            show_system_status()
            return True
        elif choice == '21':
            show_expanded_help()
            return True
        else:
            print("❌ Opção inválida!")
            return False
    except Exception as e:
        print(f"❌ Erro ao executar opção {choice}: {e}")
        return False


# Funções de execução para cada módulo
def execute_migration_module():
    """Executa módulo principal de migração."""
    print("🚀 Executando Módulo de Migração...")
    try:
        from core import migration_structure
        return migration_structure.main() if hasattr(migration_structure, 'main') else True
    except ImportError as e:
        print(f"❌ Erro ao importar migration_structure: {e}")
        return False


def execute_orchestrator_module():
    """Executa orquestrador de migração."""
    print("🎼 Executando Orquestrador de Migração...")
    try:
        from core import orchestrator_pure_python
        if hasattr(orchestrator_pure_python, 'main'):
            return orchestrator_pure_python.main()
        else:
            # Executar função alternativa se main não existir
            if hasattr(orchestrator_pure_python, 'run_migration'):
                return orchestrator_pure_python.run_migration()
            return True
    except ImportError as e:
        print(f"❌ Erro ao importar orchestrator_pure_python: {e}")
        return False


def execute_validator_module():
    """Executa módulo de validação."""
    print("✅ Executando Módulo de Validação...")
    try:
        from core import validator
        if hasattr(validator, 'main'):
            return validator.main()
        elif hasattr(validator, 'validate_all'):
            return validator.validate_all()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar validator: {e}")
        return False


def execute_sqlalchemy_migration():
    """Executa migração via SQLAlchemy."""
    print("🗃️ Executando Migração SQLAlchemy...")
    try:
        from core import sqlalchemy_migration
        if hasattr(sqlalchemy_migration, 'main'):
            return sqlalchemy_migration.main()
        elif hasattr(sqlalchemy_migration, 'run_migration'):
            return sqlalchemy_migration.run_migration()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar sqlalchemy_migration: {e}")
        return False


def execute_complete_migration():
    """Executa migração completa."""
    print("🔄 Executando Migração Completa...")
    try:
        from core import complete_migration
        if hasattr(complete_migration, 'main'):
            return complete_migration.main()
        elif hasattr(complete_migration, 'run_complete_migration'):
            return complete_migration.run_complete_migration()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar complete_migration: {e}")
        return False


def execute_user_migration():
    """Executa migração de usuários."""
    print("👥 Executando Migração de Usuários...")
    try:
        from core import migrate_users
        if hasattr(migrate_users, 'main'):
            return migrate_users.main()
        elif hasattr(migrate_users, 'migrate_users'):
            return migrate_users.migrate_users()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar migrate_users: {e}")
        return False


def execute_cleanup_module():
    """Executa módulo de limpeza."""
    print("🧹 Executando Módulo de Limpeza...")
    try:
        from cleanup import cleanup_database
        if hasattr(cleanup_database, 'main'):
            return cleanup_database.main()
        elif hasattr(cleanup_database, 'cleanup'):
            return cleanup_database.cleanup()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar cleanup_database: {e}")
        return False


def execute_monitor_module():
    """Executa módulo de monitoramento."""
    print("📊 Executando Módulo de Monitoramento...")
    try:
        from core import monitor
        if hasattr(monitor, 'main'):
            return monitor.main()
        elif hasattr(monitor, 'start_monitoring'):
            return monitor.start_monitoring()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar monitor: {e}")
        return False


def execute_utils_module():
    """Executa utilitários do sistema."""
    print("🛠️ Executando Utilitários do Sistema...")
    try:
        from utils import database_utils
        if hasattr(database_utils, 'main'):
            return database_utils.main()
        else:
            print("📋 Utilitários disponíveis carregados com sucesso")
            return True
    except ImportError as e:
        print(f"❌ Erro ao importar database_utils: {e}")
        return False


def execute_validation_module():
    """Executa módulo de validação avançada."""
    print("🔍 Executando Validação Avançada...")
    try:
        from validation import data_validator
        if hasattr(data_validator, 'main'):
            return data_validator.main()
        elif hasattr(data_validator, 'validate'):
            return data_validator.validate()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar data_validator: {e}")
        return False


def execute_docs_generator():
    """Executa gerador de documentação."""
    print("📚 Executando Gerador de Documentação...")
    try:
        from docs import doc_generator
        if hasattr(doc_generator, 'main'):
            return doc_generator.main()
        elif hasattr(doc_generator, 'generate_docs'):
            return doc_generator.generate_docs()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar doc_generator: {e}")
        return False


def execute_cli_interface():
    """Executa interface CLI."""
    print("💻 Executando Interface CLI...")
    try:
        from cli import cli_interface
        if hasattr(cli_interface, 'main'):
            return cli_interface.main()
        elif hasattr(cli_interface, 'run_cli'):
            return cli_interface.run_cli()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar cli_interface: {e}")
        return False


def execute_scheduler_module():
    """Executa módulo agendador."""
    print("📅 Executando Módulo Agendador...")
    try:
        from utils import scheduler
        if hasattr(scheduler, 'main'):
            return scheduler.main()
        elif hasattr(scheduler, 'start_scheduler'):
            return scheduler.start_scheduler()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar scheduler: {e}")
        return False


def execute_metrics_module():
    """Executa módulo de métricas."""
    print("📈 Executando Módulo de Métricas...")
    try:
        from utils import metrics
        if hasattr(metrics, 'main'):
            return metrics.main()
        elif hasattr(metrics, 'collect_metrics'):
            return metrics.collect_metrics()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar metrics: {e}")
        return False


def execute_backup_module():
    """Executa módulo de backup."""
    print("💾 Executando Módulo de Backup...")
    try:
        from utils import backup
        if hasattr(backup, 'main'):
            return backup.main()
        elif hasattr(backup, 'create_backup'):
            return backup.create_backup()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar backup: {e}")
        return False


def execute_security_module():
    """Executa módulo de segurança."""
    print("🔐 Executando Módulo de Segurança...")
    try:
        from utils import security
        if hasattr(security, 'main'):
            return security.main()
        elif hasattr(security, 'check_security'):
            return security.check_security()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar security: {e}")
        return False


def execute_notification_module():
    """Executa módulo de notificações."""
    print("📢 Executando Módulo de Notificações...")
    try:
        from utils import notifications
        if hasattr(notifications, 'main'):
            return notifications.main()
        elif hasattr(notifications, 'send_notification'):
            return notifications.send_notification("Sistema ativo", "Módulo de notificações carregado")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar notifications: {e}")
        return False


def execute_rollback_module():
    """Executa módulo de rollback."""
    print("↩️ Executando Módulo de Rollback...")
    try:
        from utils import rollback
        if hasattr(rollback, 'main'):
            return rollback.main()
        elif hasattr(rollback, 'perform_rollback'):
            return rollback.perform_rollback()
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar rollback: {e}")
        return False


def execute_config_manager():
    """Executa gerenciador de configuração."""
    print("⚙️ Executando Gerenciador de Configuração...")
    try:
        from components import config_manager
        if hasattr(config_manager, 'main'):
            return config_manager.main()
        else:
            # Mostrar informações da configuração atual
            print("📋 Configuração atual do sistema:")
            project_home = config_manager.get_project_home()
            print(f"   • PROJECT_HOME: {project_home}")

            # Mostrar configurações de banco
            try:
                source_config = config_manager.get_db_config_path('source')
                dest_config = config_manager.get_db_config_path('destination')
                print(f"   • Source Config: {source_config}")
                print(f"   • Destination Config: {dest_config}")
            except Exception as e:
                print(f"   • Erro ao carregar configs de DB: {e}")

            return True
    except ImportError as e:
        print(f"❌ Erro ao importar config_manager: {e}")
        return False


class MainController:
    """Controlador principal do sistema v4.0.0."""

    def __init__(self):
        self.project_home = setup_project_environment()
        self.logger = setup_logging()
        self.orchestrator = None

    def initialize_system(self):
        """Inicializa o sistema v4.0.0."""
        try:
            if SYSTEM_V4_AVAILABLE:
                self.orchestrator = MigrationOrchestrator()
                return self.orchestrator.load_config()
            else:
                self.logger.warning("Sistema v4.0.0 não disponível")
                return False
        except Exception as e:
            self.logger.error(f"Erro inicializando sistema: {e}")
            return False

    def run_complete_migration(self, dry_run=False, interactive=False):
        """Executa migração completa usando sistema v4.0.0."""
        if not self.orchestrator:
            return False

        try:
            return self.orchestrator.run_complete_migration(
                dry_run_first=dry_run,
                interactive=interactive
            )
        except Exception as e:
            self.logger.error(f"Erro na migração: {e}")
            return False

    def run_extraction(self, output_file=None):
        """Executa apenas fase de extração."""
        if not self.orchestrator:
            return False

        try:
            result = self.orchestrator.phase_1_extraction(output_file)
            return bool(result)  # Converter string path para boolean
        except Exception as e:
            self.logger.error(f"Erro na extração: {e}")
            return False

    def run_generation(self, input_file=None):
        """Executa apenas fase de geração."""
        if not self.orchestrator:
            return False

        try:
            return self.orchestrator.phase_2_generation(input_file)
        except Exception as e:
            self.logger.error(f"Erro na geração: {e}")
            return False

    def run_execution_only(self, dry_run=False, interactive=False):
        """Executa apenas a fase de execução."""
        if not self.orchestrator:
            return False

        try:
            return self.orchestrator.phase_3_execution(
                dry_run=dry_run,
                interactive=False
            )
        except Exception as e:
            self.logger.error(f"Erro na execução: {e}")
            return False

    def show_system_info(self):
        """Mostra informações do sistema."""
        print("🚀 PostgreSQL Enterprise Migration System v4.0.0")
        print("=" * 60)
        print(f"📁 Projeto: {self.project_home}")
        print(
            f"✅ Sistema v4.0.0: {'Disponível' if SYSTEM_V4_AVAILABLE else 'Indisponível'}")

        if self.orchestrator:
            print(f"⚙️ Orquestrador: Inicializado")
            print(f"📊 Configuração: Carregada")
        else:
            print(f"⚠️ Orquestrador: Não inicializado")


def main():
    """Ponto de entrada principal do sistema."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Enterprise Migration System v4.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                      # Menu interativo
  python main.py --complete           # Migração completa automática
  python main.py --complete --dry-run # Simulação completa
  python main.py --extract            # Apenas extração
  python main.py --generate           # Apenas geração de scripts
  python main.py --execute            # Apenas execução
  python main.py --info               # Informações do sistema
        """
    )

    # Comandos principais
    parser.add_argument('--complete', action='store_true',
                        help='Executar migração completa (3 fases)')
    parser.add_argument('--extract', action='store_true',
                        help='Executar apenas extração de dados')
    parser.add_argument('--generate', action='store_true',
                        help='Executar apenas geração de scripts')
    parser.add_argument('--execute', action='store_true',
                        help='Executar apenas scripts gerados')
    parser.add_argument('--info', action='store_true',
                        help='Mostrar informações do sistema')

    # Opções de controle
    parser.add_argument('--dry-run', action='store_true',
                        help='Modo simulação (não faz alterações)')
    parser.add_argument('--interactive', action='store_true',
                        help='Modo interativo (pede confirmação)')
    parser.add_argument('--config', type=str,
                        help='Arquivo de configuração personalizado')
    parser.add_argument('--output', type=str,
                        help='Arquivo de saída (para extração)')
    parser.add_argument('--input', type=str,
                        help='Arquivo de entrada (para geração/execução)')
    parser.add_argument('--verbose', action='store_true',
                        help='Logs detalhados')

    args = parser.parse_args()

    # Configurar logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logging(log_level)

    try:
        # Inicializar controlador principal
        controller = MainController()

        # Mostrar informações se solicitado
        if args.info:
            controller.show_system_info()
            return 0

        # Se nenhum comando específico, mostrar menu
        if not any([args.complete, args.extract, args.generate, args.execute]):
            return show_interactive_menu(controller)

        # Inicializar sistema v4.0.0
        if not controller.initialize_system():
            logger.error("Falha na inicialização do sistema")
            return 1

        # Executar comandos
        success = True

        if args.complete:
            logger.info("🚀 Executando migração completa...")
            success = controller.run_complete_migration(
                dry_run=args.dry_run,
                interactive=args.interactive
            )

        elif args.extract:
            logger.info("📤 Executando extração de dados...")
            success = controller.run_extraction(args.output)

        elif args.generate:
            logger.info("⚙️ Executando geração de scripts...")
            success = controller.run_generation_only(args.input)

        elif args.execute:
            logger.info("🎯 Executando scripts de migração...")
            success = controller.run_execution_only(
                dry_run=args.dry_run,
                interactive=args.interactive
            )

        if success:
            logger.info("✅ Operação concluída com sucesso!")
            return 0
        else:
            logger.error("❌ Operação falhou")
            return 1

    except KeyboardInterrupt:
        logger.info("⚠️ Operação cancelada pelo usuário")
        return 0
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {e}")
        return 1


def show_interactive_menu(controller):
    """Mostra menu interativo para o usuário."""
    while True:
        print("\n" + "="*60)
        print("🚀 PostgreSQL Enterprise Migration System v4.0.0")
        print("="*60)
        print("1. 📊 Informações do Sistema")
        print("2. 🔄 Migração Completa (Interativa)")
        print("3. ⚡ Migração Completa (Automática)")
        print("4. 🧪 Simulação Completa (Dry Run)")
        print("5. 📤 Apenas Extração")
        print("6. ⚙️ Apenas Geração de Scripts")
        print("7. 🎯 Apenas Execução")
        print("0. 🚪 Sair")
        print("-"*60)

        try:
            choice = input("👉 Escolha uma opção: ").strip()

            if choice == "0":
                print("👋 Saindo...")
                break
            elif choice == "1":
                controller.show_system_info()
            elif choice == "2":
                if controller.initialize_system():
                    controller.run_complete_migration(interactive=True)
            elif choice == "3":
                if controller.initialize_system():
                    controller.run_complete_migration()
            elif choice == "4":
                if controller.initialize_system():
                    controller.run_complete_migration(dry_run=True)
            elif choice == "5":
                if controller.initialize_system():
                    controller.run_extraction()
            elif choice == "6":
                if controller.initialize_system():
                    controller.run_generation_only()
            elif choice == "7":
                if controller.initialize_system():
                    controller.run_execution_only()
            else:
                print("❌ Opção inválida!")

            input("\n⏸️ Pressione Enter para continuar...")

        except KeyboardInterrupt:
            print("\n👋 Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            input("\n⏸️ Pressione Enter para continuar...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
