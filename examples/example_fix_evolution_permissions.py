#!/usr/bin/env python3
"""
Script: example_fix_evolution_permissions.py
Propósito: Exemplo de uso do módulo fix_evolution_permissions
Data: 2025-10-31

Este script demonstra como usar o EvolutionPermissionsFixer para corrigir
permissões em bancos evolution* após criação de tablespaces.
"""

import logging
import sys
from pathlib import Path

from app.core.fix_evolution_permissions import (
    EvolutionPermissionsFixer,
    fix_evolution_database_permissions,
)

# Adicionar raiz ao path para garantir imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def example_1_basic_usage():
    """Exemplo 1: Uso básico com configurações padrão"""
    print("\n" + "="*70)
    print("EXEMPLO 1: Uso Básico")
    print("="*70)

    # String de conexão (substituir com valores reais)
    connection_string = (
        "postgresql://postgres:senha@localhost:5432/postgres"
    )

    # Corrigir permissões (dry-run para testar)
    results = fix_evolution_database_permissions(
        connection_string=connection_string,
        dry_run=True  # Mude para False para executar de verdade
    )

    print("\nResultados:")
    print(f"  Processados: {results['databases_processed']}")
    print(f"  Falhados: {results['databases_failed']}")


def example_2_advanced_usage():
    """Exemplo 2: Uso avançado com controle fino"""
    print("\n" + "="*70)
    print("EXEMPLO 2: Uso Avançado")
    print("="*70)

    connection_string = (
        "postgresql://postgres:senha@localhost:5432/postgres"
    )

    # Criar instância do corretor
    fixer = EvolutionPermissionsFixer(
        connection_string=connection_string,
        dry_run=False,  # Executa de verdade
        stop_on_error=False,  # Continua mesmo com erros
        timeout_seconds=60  # Timeout de 60 segundos
    )

    # Processar bancos
    results = fixer.process_evolution_databases()

    # Imprimir resultados detalhados
    fixer.print_results()

    # Analisar resultados
    if results['databases_failed']:
        print("\n⚠ Alguns bancos falharam!")
        for db in results['databases_failed']:
            print(f"  - {db}")
    else:
        print("\n✓ Todos os bancos foram processados com sucesso!")


def example_3_with_custom_roles():
    """Exemplo 3: Usando roles customizadas"""
    print("\n" + "="*70)
    print("EXEMPLO 3: Com Roles Customizadas")
    print("="*70)

    connection_string = (
        "postgresql://postgres:senha@localhost:5432/postgres"
    )

    fixer = EvolutionPermissionsFixer(
        connection_string=connection_string,
        dry_run=True
    )

    # Sobrescrever roles padrão
    custom_roles = [
        "app_user",
        "readonly_user",
        "analytics_user"
    ]
    fixer.DEFAULT_ROLES = custom_roles

    results = fixer.process_evolution_databases()

    print(f"\nRoles customizados usados: {custom_roles}")
    print(f"Bancos processados: {results['databases_processed']}")


def example_4_environment_variables():
    """Exemplo 4: Usando variáveis de ambiente"""
    print("\n" + "="*70)
    print("EXEMPLO 4: Com Variáveis de Ambiente")
    print("="*70)

    import os

    from dotenv import load_dotenv

    # Carregar variáveis de ambiente do arquivo .env
    load_dotenv()

    # Construir connection string a partir de variáveis
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")

    connection_string = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    print(f"Conectando a: {POSTGRES_HOST}:{POSTGRES_PORT}")

    results = fix_evolution_database_permissions(
        connection_string=connection_string,
        dry_run=True
    )

    print(f"Resultado: {len(results['databases_processed'])} processados")


def example_5_error_handling():
    """Exemplo 5: Tratamento de erros"""
    print("\n" + "="*70)
    print("EXEMPLO 5: Tratamento de Erros")
    print("="*70)

    connection_string = (
        "postgresql://postgres:senha@localhost:5432/postgres"
    )

    try:
        fixer = EvolutionPermissionsFixer(
            connection_string=connection_string,
            stop_on_error=True  # Para no primeiro erro
        )

        results = fixer.process_evolution_databases()

        # Verificar se houve erros
        if results['errors']:
            print("\nErros encontrados:")
            for error in results['errors']:
                print(f"  Database: {error['database']}")
                print(f"  Erro: {error['error']}")
        else:
            print("\n✓ Nenhum erro encontrado")

    except Exception as e:
        print(f"\n✗ Erro crítico: {e}")
        sys.exit(1)


def main():
    """Função principal"""
    print("\n" + "="*70)
    print("EXEMPLOS DE USO - EvolutionPermissionsFixer")
    print("="*70)

    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    print("\nEscolha um exemplo para executar:")
    print("  1. Uso Básico (dry-run)")
    print("  2. Uso Avançado (com execução)")
    print("  3. Com Roles Customizadas")
    print("  4. Com Variáveis de Ambiente")
    print("  5. Tratamento de Erros")

    choice = input("\nOpção (1-5): ").strip()

    if choice == "1":
        example_1_basic_usage()
    elif choice == "2":
        example_2_advanced_usage()
    elif choice == "3":
        example_3_with_custom_roles()
    elif choice == "4":
        example_4_environment_variables()
    elif choice == "5":
        example_5_error_handling()
    else:
        print("Opção inválida!")
        sys.exit(1)


if __name__ == "__main__":
    main()
