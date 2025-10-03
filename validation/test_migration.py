#!/usr/bin/env python3
"""
Test Script para PostgreSQL Migration Structure
===============================================

Script de teste para validar a implementação da migração PostgreSQL
antes da execução completa.

Executa testes de:
- Carregamento de configurações
- Conectividade básica
- Validação de estruturas
- Relatórios de status

Uso:
    python test_migration.py [--dry-run] [--verbose]
"""

import sys
import os
import argparse
from datetime import datetime

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from migration_structure import PostgreSQLMigrator, MigrationResult
except ImportError as e:
    print(f"❌ Erro ao importar módulo de migração: {e}")
    print("Certifique-se de que migration_structure.py está no mesmo diretório")
    sys.exit(1)


def print_banner():
    """Imprime banner do teste."""
    print("=" * 80)
    print("🧪 PostgreSQL Migration Structure - Test Suite")
    print("=" * 80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🏗️ Projeto: enterprise-database-install-transfer-structure")
    print(f"📍 Migração: wf004.vya.digital (PG14) → wfdb02.vya.digital (PG16)")
    print("=" * 80)
    print()


def test_configuration_loading():
    """
    Testa carregamento de configurações.

    Returns
    -------
    tuple
        (success: bool, migrator: PostgreSQLMigrator or None)
    """
    print("🔧 TESTE 1: Carregamento de Configurações")
    print("-" * 50)

    try:
        migrator = PostgreSQLMigrator()
        success = migrator.load_configurations()

        if success:
            print("✅ Configurações carregadas com sucesso!")

            # Validar configurações básicas
            if migrator.source_config and migrator.destination_config:
                print(f"   📡 Origem: {migrator.source_config.host}:{migrator.source_config.port}")
                print(f"   🎯 Destino: {migrator.destination_config.host}:{migrator.destination_config.port}")
                print(f"   📋 Regras: {len(migrator.migration_rules)} seções configuradas")
                return True, migrator
            else:
                print("❌ Configurações incompletas")
                return False, None
        else:
            print("❌ Falha ao carregar configurações")
            return False, None

    except Exception as e:
        print(f"❌ Exceção durante carregamento: {e}")
        return False, None


def test_connectivity(migrator: PostgreSQLMigrator, dry_run: bool = False):
    """
    Testa conectividade com servidores.

    Parameters
    ----------
    migrator : PostgreSQLMigrator
        Instância do migrador configurada
    dry_run : bool
        Se True, simula teste sem conexão real

    Returns
    -------
    bool
        Sucesso do teste
    """
    print("\n🔍 TESTE 2: Conectividade com Servidores")
    print("-" * 50)

    if dry_run:
        print("🔸 Modo dry-run: simulando teste de conectividade")
        print("✅ Conexão origem: SIMULADA")
        print("✅ Conexão destino: SIMULADA")
        print("⏱️ Tempo simulado: 0.05s")
        return True

    try:
        result = migrator.test_connectivity()

        if result.success:
            print("✅ Conectividade testada com sucesso!")

            if result.details:
                if 'source' in result.details:
                    src = result.details['source']
                    print(f"   📡 Origem: {src['user']}@{src['host']}")
                    print(f"      Versão: {src['version'].split()[1] if src['version'] else 'N/A'}")

                if 'destination' in result.details:
                    dst = result.details['destination']
                    print(f"   🎯 Destino: {dst['user']}@{dst['host']}")
                    print(f"      Versão: {dst['version'].split()[1] if dst['version'] else 'N/A'}")

            print(f"   ⏱️ Tempo: {result.execution_time:.2f}s")
            return True
        else:
            print(f"❌ Falha na conectividade: {result.error}")
            return False

    except Exception as e:
        print(f"❌ Exceção durante teste: {e}")
        return False


def test_database_enumeration(migrator: PostgreSQLMigrator, dry_run: bool = False):
    """
    Testa enumeração de bancos de dados.

    Parameters
    ----------
    migrator : PostgreSQLMigrator
        Instância do migrador configurada
    dry_run : bool
        Se True, simula enumeração

    Returns
    -------
    bool
        Sucesso do teste
    """
    print("\n📋 TESTE 3: Enumeração de Bancos de Dados")
    print("-" * 50)

    if dry_run:
        print("🔸 Modo dry-run: simulando enumeração")
        print("✅ Bancos simulados:")
        print("   - empresa_producao (150MB)")
        print("   - empresa_homologacao (85MB)")
        print("   - empresa_desenvolvimento (45MB)")
        return True

    try:
        databases = migrator.get_databases_list(migrator.source_config)

        print(f"✅ Encontrados {len(databases)} bancos de dados:")
        for db in databases:
            print(f"   - {db['datname']} ({db['size_pretty']})")

        return True

    except Exception as e:
        print(f"❌ Erro na enumeração: {e}")
        return False


def test_file_structure():
    """
    Testa estrutura de arquivos e diretórios.

    Returns
    -------
    bool
        Sucesso do teste
    """
    print("\n📁 TESTE 4: Estrutura de Arquivos")
    print("-" * 50)

    required_files = [
        "config/source_config.json",
        "config/destination_config.json",
        "config/migration_rules.json",
        "migration_structure.py"
    ]

    required_dirs = [
        "config",
        "sql",
        "reports"
    ]

    all_ok = True

    # Verificar diretórios
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Diretório: {directory}/")
        else:
            print(f"❌ Diretório ausente: {directory}/")
            all_ok = False

    # Verificar arquivos
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ Arquivo: {file_path} ({size} bytes)")
        else:
            print(f"❌ Arquivo ausente: {file_path}")
            all_ok = False

    return all_ok


def main():
    """Função principal do teste."""
    parser = argparse.ArgumentParser(description="Test PostgreSQL Migration Structure")
    parser.add_argument("--dry-run", action="store_true",
                       help="Executa testes sem conexões reais")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Saída detalhada")

    args = parser.parse_args()

    print_banner()

    if args.dry_run:
        print("🔸 Modo DRY-RUN ativado - simulando operações")
        print()

    # Contadores de teste
    tests_passed = 0
    tests_total = 4

    # Teste 1: Estrutura de arquivos
    if test_file_structure():
        tests_passed += 1

    # Teste 2: Carregamento de configurações
    success, migrator = test_configuration_loading()
    if success:
        tests_passed += 1

        # Teste 3: Conectividade (apenas se configurações OK)
        if test_connectivity(migrator, args.dry_run):
            tests_passed += 1

            # Teste 4: Enumeração de bancos (apenas se conectividade OK)
            if test_database_enumeration(migrator, args.dry_run):
                tests_passed += 1

    # Relatório final
    print("\n" + "=" * 80)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 80)
    print(f"✅ Testes aprovados: {tests_passed}/{tests_total}")
    print(f"📈 Taxa de sucesso: {(tests_passed/tests_total)*100:.1f}%")

    if tests_passed == tests_total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema pronto para migração")
        exit_code = 0
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique configurações e conectividade")
        exit_code = 1

    print("=" * 80)

    return exit_code


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal nos testes: {e}")
        sys.exit(1)
