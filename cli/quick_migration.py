#!/usr/bin/env python3
"""
Quick Migration CLI
==================

Interface simplificada para executar migrações PostgreSQL rapidamente.
Oferece comandos diretos para as operações mais comuns.

Versão: 1.0.0
Data: 03/10/2025
"""

import os
import sys
import argparse
from pathlib import Path

# Adicionar diretório do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.migration.migration_orchestrator import MigrationOrchestrator

def quick_full_migration():
    """Executa migração completa com configurações padrão."""
    print("🚀 Migração Completa - Configurações Padrão")
    print("-" * 50)

    orchestrator = MigrationOrchestrator()
    success = orchestrator.run_complete_migration()

    if success:
        print("\\n✅ Migração completa executada com sucesso!")
        return 0
    else:
        print("\\n❌ Migração falhou. Verifique os logs.")
        return 1

def quick_connectivity_test():
    """Testa apenas conectividade."""
    print("🔗 Teste Rápido de Conectividade")
    print("-" * 50)

    orchestrator = MigrationOrchestrator()

    # Executar apenas testes essenciais
    if not orchestrator.load_configurations():
        print("❌ Falha ao carregar configurações")
        return 1

    if not orchestrator.test_connectivity():
        print("❌ Falha nos testes de conectividade")
        return 1

    print("\\n✅ Conectividade testada com sucesso!")
    return 0

def quick_user_discovery():
    """Descobre usuários do servidor origem."""
    print("🔍 Descoberta Rápida de Usuários")
    print("-" * 50)

    orchestrator = MigrationOrchestrator()

    if not orchestrator.load_configurations():
        print("❌ Falha ao carregar configurações")
        return 1

    if not orchestrator.discover_source_structure():
        print("❌ Falha na descoberta de usuários")
        return 1

    print("\\n✅ Descoberta de usuários concluída!")
    return 0

def quick_scram_check():
    """Verifica compatibilidade SCRAM."""
    print("🔐 Verificação Rápida SCRAM-SHA-256")
    print("-" * 50)

    orchestrator = MigrationOrchestrator()

    if not orchestrator.load_configurations():
        print("❌ Falha ao carregar configurações")
        return 1

    if not orchestrator.analyze_scram_compatibility():
        print("❌ Falha na análise SCRAM")
        return 1

    print("\\n✅ Análise SCRAM concluída!")
    return 0

def main():
    """Interface CLI principal."""
    parser = argparse.ArgumentParser(
        description="Quick Migration CLI - Interface simplificada",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos disponíveis:
  full        Migração completa (padrão)
  test        Teste de conectividade apenas
  discover    Descoberta de usuários apenas
  scram       Verificação SCRAM apenas

Exemplos:
  %(prog)s full          # Migração completa
  %(prog)s test          # Só testa conectividade
  %(prog)s discover      # Só descobre usuários
  %(prog)s scram         # Só verifica SCRAM
        """
    )

    parser.add_argument('command', nargs='?', default='full',
                       choices=['full', 'test', 'discover', 'scram'],
                       help='Comando a executar (padrão: full)')

    args = parser.parse_args()

    print("=" * 60)
    print("⚡ Quick Migration CLI v1.0.0")
    print("=" * 60)

    # Mapeamento de comandos
    commands = {
        'full': quick_full_migration,
        'test': quick_connectivity_test,
        'discover': quick_user_discovery,
        'scram': quick_scram_check
    }

    try:
        return commands[args.command]()
    except KeyboardInterrupt:
        print("\\n⚠️ Operação cancelada pelo usuário")
        return 1
    except Exception as e:
        print(f"\\n💥 Erro: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
