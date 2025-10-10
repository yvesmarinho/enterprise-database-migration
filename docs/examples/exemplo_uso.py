#!/usr/bin/env python3
"""
Exemplo de uso do PostgreSQL Enterprise Migration System v4.0.0

Este script demonstra como usar o sistema de migração de forma programática.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from migration_orchestrator import MigrationOrchestrator


def exemplo_migracao_completa():
    """Exemplo de migração completa automatizada."""
    print("🌟 Exemplo: Migração Completa Automatizada")
    print("=" * 50)

    # Inicializar orquestrador
    orchestrator = MigrationOrchestrator("config/migration_config.json")

    # Carregar configuração
    if not orchestrator.load_config():
        print("❌ Falha ao carregar configuração")
        return False

    # Executar migração completa
    success = orchestrator.run_complete_migration(
        extraction_file=None,  # Será gerado automaticamente
        dry_run_first=True,    # Dry run antes da execução real
        interactive=False      # Modo não-interativo
    )

    if success:
        # Gerar relatório
        report_file = orchestrator.generate_report()
        print(f"📊 Relatório gerado: {report_file}")
        return True
    else:
        print("❌ Migração falhou")
        return False


def exemplo_migracao_por_fases():
    """Exemplo de migração executada fase por fase."""
    print("\n🔧 Exemplo: Migração Fase por Fase")
    print("=" * 50)

    orchestrator = MigrationOrchestrator("config/migration_config.json")

    if not orchestrator.load_config():
        return False

    # Fase 1: Extração
    print("\n📊 Executando Fase 1: Extração...")
    json_file = orchestrator.phase_1_extraction()
    if not json_file:
        print("❌ Fase 1 falhou")
        return False

    print(f"✅ Dados extraídos: {json_file}")

    # Fase 2: Geração
    print("\n🛠️ Executando Fase 2: Geração...")
    if not orchestrator.phase_2_generation(json_file):
        print("❌ Fase 2 falhou")
        return False

    print("✅ Scripts gerados com sucesso")

    # Fase 3a: Dry Run
    print("\n🔍 Executando Fase 3a: Dry Run...")
    if not orchestrator.phase_3_execution(dry_run=True):
        print("❌ Dry run falhou")
        return False

    print("✅ Dry run bem-sucedido")

    # Fase 3b: Execução Real
    print("\n🚀 Executando Fase 3b: Execução Real...")
    if not orchestrator.phase_3_execution(dry_run=False):
        print("❌ Execução real falhou")
        return False

    print("✅ Execução real bem-sucedida")

    return True


def exemplo_apenas_extracao():
    """Exemplo de apenas extração para backup."""
    print("\n💾 Exemplo: Apenas Extração (Backup)")
    print("=" * 50)

    orchestrator = MigrationOrchestrator("config/migration_config.json")

    if not orchestrator.load_config():
        return False

    # Definir arquivo específico para backup
    backup_file = f"backup_completo_{orchestrator.session_id}.json"

    # Executar apenas extração
    result = orchestrator.phase_1_extraction(backup_file)

    if result:
        print(f"✅ Backup criado: {result}")

        # Verificar tamanho do arquivo
        file_size = os.path.getsize(result) / (1024 * 1024)  # MB
        print(f"📏 Tamanho do arquivo: {file_size:.2f} MB")

        return True
    else:
        print("❌ Falha na criação do backup")
        return False


def exemplo_validacao_ambiente():
    """Exemplo de validação do ambiente de destino."""
    print("\n🔍 Exemplo: Validação do Ambiente")
    print("=" * 50)

    orchestrator = MigrationOrchestrator("config/migration_config.json")

    if not orchestrator.load_config():
        return False

    # Usar dados já extraídos (se existirem)
    extracted_files = list(Path("extracted_data").glob("*.json"))

    if not extracted_files:
        print("⚠️ Nenhum arquivo de dados encontrado. Executando extração...")
        json_file = orchestrator.phase_1_extraction()
        if not json_file:
            return False
    else:
        json_file = str(extracted_files[-1])  # Usar o mais recente
        print(f"📄 Usando arquivo existente: {json_file}")

    # Gerar scripts
    if not orchestrator.phase_2_generation(json_file):
        return False

    # Executar apenas dry run para validar
    success = orchestrator.phase_3_execution(dry_run=True)

    if success:
        print("✅ Ambiente de destino válido e pronto para migração")
        return True
    else:
        print("❌ Problemas detectados no ambiente de destino")
        return False


def main():
    """Função principal com menu de exemplos."""
    print("🚀 PostgreSQL Enterprise Migration System v4.0.0")
    print("🔧 Exemplos de Uso")
    print("=" * 60)

    # Verificar se estamos no diretório correto
    if not Path("migration_orchestrator.py").exists():
        print("❌ Execute este script a partir do diretório do projeto")
        sys.exit(1)

    exemplos = {
        "1": ("Migração Completa Automatizada", exemplo_migracao_completa),
        "2": ("Migração Fase por Fase", exemplo_migracao_por_fases),
        "3": ("Apenas Extração (Backup)", exemplo_apenas_extracao),
        "4": ("Validação do Ambiente", exemplo_validacao_ambiente)
    }

    print("\nExemplos disponíveis:")
    for key, (nome, _) in exemplos.items():
        print(f"  {key}. {nome}")

    print("\n  0. Executar todos os exemplos")
    print("  q. Sair")

    while True:
        try:
            escolha = input("\nEscolha um exemplo (1-4, 0, q): ").strip().lower()

            if escolha == 'q':
                print("👋 Saindo...")
                break

            elif escolha == '0':
                print("\n🔄 Executando todos os exemplos...")
                for key in sorted(exemplos.keys()):
                    nome, funcao = exemplos[key]
                    print(f"\n{'='*20} {nome} {'='*20}")
                    try:
                        resultado = funcao()
                        status = "✅ SUCESSO" if resultado else "❌ FALHA"
                        print(f"\n{status}: {nome}")
                    except Exception as e:
                        print(f"\n💥 ERRO em {nome}: {e}")
                break

            elif escolha in exemplos:
                nome, funcao = exemplos[escolha]
                print(f"\n{'='*20} {nome} {'='*20}")
                try:
                    resultado = funcao()
                    status = "✅ SUCESSO" if resultado else "❌ FALHA"
                    print(f"\n{status}: {nome}")
                except Exception as e:
                    print(f"\n💥 ERRO: {e}")

            else:
                print("❌ Escolha inválida. Tente novamente.")

        except KeyboardInterrupt:
            print("\n\n⚠️ Interrompido pelo usuário")
            break
        except Exception as e:
            print(f"\n💥 Erro inesperado: {e}")
            break

    print("\n🎯 Consulte README_v4.md para documentação completa")
    print("📁 Logs disponíveis em: logs/")
    print("📊 Relatórios disponíveis em: reports/")


if __name__ == "__main__":
    main()
