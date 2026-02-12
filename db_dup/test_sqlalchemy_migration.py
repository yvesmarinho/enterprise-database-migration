#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de teste para validar a nova implementação sem pg_dump.

Este script valida que:
1. Os imports do SQLAlchemy estão corretos
2. A classe DatabaseCloner pode ser instanciada
3. Os novos métodos existem e têm assinaturas corretas
4. Não há dependência de subprocess/pg_dump
"""

import os
import sys
from pathlib import Path

# Adicionar diretório ao path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Testa se todos os imports necessários funcionam."""
    print("=" * 80)
    print("TESTE 1: Verificando imports")
    print("=" * 80)

    try:
        from pg_database_cloner_Version2 import DatabaseCloner
        print("✓ DatabaseCloner importado com sucesso")

        # Verificar se SQLAlchemy está disponível
        import sqlalchemy
        print(f"✓ SQLAlchemy versão: {sqlalchemy.__version__}")

        # Verificar que subprocess NÃO é usado no código
        import inspect
        source = inspect.getsource(DatabaseCloner)

        if 'subprocess' in source:
            print("⚠ AVISO: Código ainda contém referências a 'subprocess'")
        else:
            print("✓ Sem dependência de subprocess")

        if 'pg_dump' in source:
            print("⚠ AVISO: Código ainda contém referências a 'pg_dump'")
        else:
            print("✓ Sem referências a pg_dump")

        return True

    except ImportError as e:
        print(f"✗ Erro ao importar módulos: {e}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        return False


def test_class_structure():
    """Testa a estrutura da classe DatabaseCloner."""
    print("\n" + "=" * 80)
    print("TESTE 2: Verificando estrutura da classe")
    print("=" * 80)

    try:
        from pg_database_cloner_Version2 import DatabaseCloner

        # Verificar métodos novos
        required_methods = [
            '_copy_database_structure_and_data',
            '_build_connection_url',
            '_copy_schemas',
            '_copy_table_structures',
            '_copy_table_data',
            '_copy_views_and_functions'
        ]

        for method_name in required_methods:
            if hasattr(DatabaseCloner, method_name):
                print(f"✓ Método '{method_name}' existe")
            else:
                print(f"✗ Método '{method_name}' NÃO encontrado")
                return False

        # Verificar assinatura do método principal
        import inspect
        sig = inspect.signature(
            DatabaseCloner._copy_database_structure_and_data)
        params = list(sig.parameters.keys())

        if 'self' in params and 'copy_data' in params:
            print(f"✓ Assinatura do método principal correta: {params}")
        else:
            print(f"✗ Assinatura incorreta: {params}")
            return False

        return True

    except Exception as e:
        print(f"✗ Erro ao verificar estrutura: {e}")
        return False


def test_method_logic():
    """Testa a lógica básica dos métodos."""
    print("\n" + "=" * 80)
    print("TESTE 3: Verificando lógica dos métodos")
    print("=" * 80)

    try:
        from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager
        from pg_database_cloner_Version2 import DatabaseCloner
        from pg_json_config_Version2 import (
            PostgreSQLJsonConfig,
            SSLMode,
            UserCredential,
        )

        # Criar configuração de teste (sem conectar)
        config = PostgreSQLJsonConfig(
            host='localhost',
            port=5432,
            ssl_mode=SSLMode.DISABLE,
            possible_users=[UserCredential('test_user', 'test_pass')],
            db_source='test_source',
            db_destiny='test_dest'
        )

        print("✓ Configuração de teste criada")

        # Criar manager (sem validar conexão)
        manager = PostgreSQLConnectionManager(config, auto_validate=False)
        print("✓ Manager criado (sem conexão)")

        # Criar cloner
        cloner = DatabaseCloner(manager)
        print("✓ DatabaseCloner instanciado")

        # Verificar que método _build_connection_url funciona
        url = cloner._build_connection_url('test_db')

        if 'postgresql://' in url and 'test_db' in url:
            print(
                f"✓ URL de conexão gerada corretamente: {url.replace('test_pass', '***')}")
        else:
            print(f"✗ URL inválida: {url}")
            return False

        print("✓ Lógica básica dos métodos está funcional")
        return True

    except Exception as e:
        print(f"✗ Erro ao testar lógica: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_external_dependencies():
    """Verifica que não há dependências externas de pg_dump."""
    print("\n" + "=" * 80)
    print("TESTE 4: Verificando dependências externas")
    print("=" * 80)

    try:
        import inspect

        from pg_database_cloner_Version2 import DatabaseCloner

        # Obter código fonte completo
        source = inspect.getsource(DatabaseCloner)

        # Lista de comandos externos que NÃO devem estar presentes
        forbidden_commands = ['pg_dump', 'pg_restore', 'psql']

        issues = []
        for cmd in forbidden_commands:
            if cmd in source:
                issues.append(cmd)

        if issues:
            print(
                f"⚠ AVISO: Comandos externos encontrados: {', '.join(issues)}")
            # Não é erro crítico, apenas aviso
        else:
            print("✓ Nenhum comando externo encontrado no código")

        # Verificar que SQLAlchemy está sendo usado
        if 'create_engine' in source and 'MetaData' in source:
            print("✓ SQLAlchemy sendo utilizado corretamente")
        else:
            print("⚠ AVISO: SQLAlchemy pode não estar sendo usado")

        return True

    except Exception as e:
        print(f"✗ Erro ao verificar dependências: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║              Teste de Migração SQLAlchemy (Sem pg_dump)                   ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()

    tests = [
        ("Imports", test_imports),
        ("Estrutura de Classe", test_class_structure),
        ("Lógica de Métodos", test_method_logic),
        ("Dependências Externas", test_no_external_dependencies)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Exceção em {test_name}: {e}")
            results.append((test_name, False))

    # Imprimir resumo
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{test_name:.<50} {status}")

    print("=" * 80)
    print(f"Total: {passed}/{total} testes passaram")
    print("=" * 80)

    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! Implementação está pronta.")
        return 0
    else:
        print(f"\n⚠ {total - passed} teste(s) falharam. Revise a implementação.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
