#!/usr/bin/env python3
"""
Exemplo de Uso do Orquestrador Python
=====================================

Demonstra diferentes formas de usar o orquestrador modular.

Versão: 1.0.0
Data: 03/10/2025
"""

import sys
import logging
from pathlib import Path

# Adicionar diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.migration.orchestrator_pure_python import PostgreSQLMigrationOrchestrator

def exemplo_uso_basico():
    """Exemplo de uso básico do orquestrador."""
    print("=" * 60)
    print("🔧 Exemplo 1: Uso Básico")
    print("=" * 60)

    # Criar orquestrador
    orchestrator = PostgreSQLMigrationOrchestrator(verbose=True)

    # Executar migração completa
    success = orchestrator.run_complete_migration(interactive=False)

    if success:
        print("✅ Migração concluída com sucesso!")
    else:
        print("❌ Migração falhou")

    return success

def exemplo_passos_individuais():
    """Exemplo executando passos individuais."""
    print("\\n" + "=" * 60)
    print("🔧 Exemplo 2: Passos Individuais")
    print("=" * 60)

    orchestrator = PostgreSQLMigrationOrchestrator(verbose=True)

    # Executar apenas validações iniciais
    print("\\n🔍 Executando validações iniciais...")

    # Validar ambiente
    env_ok = orchestrator.validate_environment()
    print(f"Ambiente: {'✅ OK' if env_ok else '❌ Falhou'}")

    # Carregar configurações
    config_ok = orchestrator.load_configurations()
    print(f"Configurações: {'✅ OK' if config_ok else '❌ Falhou'}")

    # Verificar módulos
    modules_ok = orchestrator.check_modules()
    print(f"Módulos: {'✅ OK' if modules_ok else '❌ Falhou'}")

    return env_ok and config_ok and modules_ok

def exemplo_teste_conectividade():
    """Exemplo focado em testes de conectividade."""
    print("\\n" + "=" * 60)
    print("🔧 Exemplo 3: Teste de Conectividade")
    print("=" * 60)

    orchestrator = PostgreSQLMigrationOrchestrator(verbose=True)

    # Setup básico
    if not orchestrator.validate_environment():
        print("❌ Ambiente inválido")
        return False

    if not orchestrator.load_configurations():
        print("❌ Erro nas configurações")
        return False

    # Teste de conectividade
    connectivity_ok = orchestrator.test_connectivity()
    print(f"\\n🔗 Conectividade: {'✅ OK' if connectivity_ok else '❌ Falhou'}")

    return connectivity_ok

def exemplo_com_logging_personalizado():
    """Exemplo com logging personalizado."""
    print("\\n" + "=" * 60)
    print("🔧 Exemplo 4: Logging Personalizado")
    print("=" * 60)

    # Configurar logging personalizado
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    orchestrator = PostgreSQLMigrationOrchestrator(verbose=True)

    # O orquestrador já tem seu próprio sistema de logging integrado
    orchestrator.logger.info("Iniciando exemplo com logging personalizado", "exemplo")

    # Executar algumas validações
    orchestrator.validate_environment()
    orchestrator.check_modules()

    # Verificar estatísticas
    print(f"\\n📊 Estatísticas:")
    print(f"   - Total de passos: {orchestrator.stats['total_steps']}")
    print(f"   - Passos concluídos: {orchestrator.stats['completed_steps']}")
    print(f"   - Passos falharam: {orchestrator.stats['failed_steps']}")

    return True

def exemplo_tratamento_erros():
    """Exemplo de tratamento de erros."""
    print("\\n" + "=" * 60)
    print("🔧 Exemplo 5: Tratamento de Erros")
    print("=" * 60)

    try:
        # Criar orquestrador com diretório inválido
        orchestrator = PostgreSQLMigrationOrchestrator(
            config_dir="/diretorio/inexistente",
            verbose=True
        )

        # Tentar executar validação
        result = orchestrator.validate_environment()
        print(f"Resultado: {result}")

    except Exception as e:
        print(f"❌ Erro capturado: {e}")
        return False

    return True

def exemplo_modulo_scram():
    """Exemplo usando módulo SCRAM diretamente."""
    print("\\n" + "=" * 60)
    print("🔧 Exemplo 6: Módulo SCRAM Direto")
    print("=" * 60)

    try:
        from src.migration.validation.check_scram_auth import ScramAuthChecker

        # Criar checker SCRAM
        scram_checker = ScramAuthChecker()

        print(f"Status do componente: {scram_checker.get_status_info()}")

        # Tentar verificação rápida
        scram_support = scram_checker.check_scram_support()
        print(f"Suporte SCRAM: {'✅ Sim' if scram_support else '❌ Não'}")

        return True

    except ImportError as e:
        print(f"❌ Erro ao importar módulo SCRAM: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no módulo SCRAM: {e}")
        return False

def menu_interativo():
    """Menu interativo para escolher exemplos."""
    exemplos = {
        '1': ("Uso Básico", exemplo_uso_basico),
        '2': ("Passos Individuais", exemplo_passos_individuais),
        '3': ("Teste de Conectividade", exemplo_teste_conectividade),
        '4': ("Logging Personalizado", exemplo_com_logging_personalizado),
        '5': ("Tratamento de Erros", exemplo_tratamento_erros),
        '6': ("Módulo SCRAM Direto", exemplo_modulo_scram),
        '0': ("Executar Todos", None)
    }

    print("\\n" + "=" * 70)
    print("🚀 EXEMPLOS DE USO - PostgreSQL Migration Orchestrator")
    print("=" * 70)
    print("\\n📋 Escolha um exemplo:")

    for key, (nome, _) in exemplos.items():
        if key != '0':
            print(f"  {key}️⃣  {nome}")
    print(f"  {list(exemplos.keys())[-1]}️⃣  Executar Todos os Exemplos")
    print()

    while True:
        try:
            escolha = input("👉 Digite sua escolha (1-6, 0 para todos): ").strip()

            if escolha == '0':
                # Executar todos
                print("\\n🎯 Executando todos os exemplos...")
                resultados = []
                for key, (nome, func) in exemplos.items():
                    if func is not None:
                        try:
                            resultado = func()
                            resultados.append((nome, resultado))
                        except Exception as e:
                            print(f"❌ Erro em {nome}: {e}")
                            resultados.append((nome, False))

                # Resumo final
                print("\\n" + "=" * 70)
                print("📊 RESUMO DOS EXEMPLOS")
                print("=" * 70)
                for nome, resultado in resultados:
                    status = "✅ Sucesso" if resultado else "❌ Falhou"
                    print(f"  {status:<12} - {nome}")
                print("=" * 70)
                break

            elif escolha in exemplos and escolha != '0':
                nome, func = exemplos[escolha]
                print(f"\\n🎯 Executando: {nome}")

                try:
                    resultado = func()
                    status = "✅ Concluído com sucesso" if resultado else "⚠️ Concluído com avisos"
                    print(f"\\n{status}")
                except Exception as e:
                    print(f"\\n❌ Erro durante execução: {e}")
                break

            else:
                print("❌ Opção inválida. Tente novamente.")

        except KeyboardInterrupt:
            print("\\n👋 Saindo...")
            break

def main():
    """Função principal."""
    print("🔧 Exemplos de Uso do PostgreSQL Migration Orchestrator")
    print("📝 Demonstra diferentes formas de utilizar o sistema modular")

    try:
        menu_interativo()
    except KeyboardInterrupt:
        print("\\n⚠️ Interrompido pelo usuário")
        return 1
    except Exception as e:
        print(f"\\n💥 Erro inesperado: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
