#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemplo de Uso do PostgreSQLConnectionManager com arquivo JSON.

Este exemplo mostra como usar a nova funcionalidade from_json_file()
para carregar configuração diretamente de um arquivo.
"""

from pathlib import Path

from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager
from pg_database_cloner_Version2 import DatabaseCloner


def exemplo_basico():
    """Exemplo básico de carregamento."""
    print("=" * 80)
    print("EXEMPLO 1: Carregamento Básico")
    print("=" * 80)

    # FORMA NOVA - Uma linha!
    manager = PostgreSQLConnectionManager.from_json_file(
        '../secrets/destination_config.txt',
        use_pool=True,
        auto_validate=False  # Não validar ainda
    )

    print(f"✓ Host: {manager.config.host}")
    print(f"✓ Porta: {manager.config.port}")
    print(f"✓ SSL: {manager.config.ssl_mode.value}")
    print(f"✓ Usuários: {len(manager.config.possible_users)}")

    return manager


def exemplo_clonagem():
    """Exemplo de clonagem com arquivo JSON."""
    print("\n" + "=" * 80)
    print("EXEMPLO 2: Clonagem de Banco com JSON")
    print("=" * 80)

    # 1. Carregar configuração do arquivo
    manager = PostgreSQLConnectionManager.from_json_file(
        'config_example_Version2.json',
        auto_validate=False  # Para este exemplo
    )

    print(f"✓ Configuração carregada")
    print(f"  Origem: {manager.config.db_source}")
    print(f"  Destino: {manager.config.db_destiny}")

    # 2. Criar clonador (não vamos executar para não afetar BDs)
    # cloner = DatabaseCloner(manager)
    # success = cloner.clone_database(drop_if_exists=True)

    print("✓ Clonador pode ser criado normalmente")

    return manager


def exemplo_comparacao():
    """Mostra diferença entre forma antiga e nova."""
    print("\n" + "=" * 80)
    print("EXEMPLO 3: Comparação das Formas")
    print("=" * 80)

    print("\n📜 FORMA ANTIGA (2 imports, 2 linhas):")
    print("-" * 80)
    print("from pg_json_config_Version2 import PostgreSQLJsonConfig")
    print("from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager")
    print()
    print("config = PostgreSQLJsonConfig.from_json_file('config.json')")
    print("manager = PostgreSQLConnectionManager(config)")

    print("\n🆕 FORMA NOVA (1 import, 1 linha):")
    print("-" * 80)
    print("from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager")
    print()
    print("manager = PostgreSQLConnectionManager.from_json_file('config.json')")

    print("\n✅ BENEFÍCIOS:")
    print("  • 50% menos código")
    print("  • Mais intuitivo")
    print("  • Menos imports")
    print("  • Mais rápido de escrever")


def main():
    """Executa todos os exemplos."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║        Exemplos de Uso - PostgreSQLConnectionManager.from_json_file()     ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()

    try:
        # Exemplo 1
        manager1 = exemplo_basico()

        # Exemplo 2
        manager2 = exemplo_clonagem()

        # Exemplo 3
        exemplo_comparacao()

        print("\n" + "=" * 80)
        print("📚 DOCUMENTAÇÃO")
        print("=" * 80)
        print("\nParâmetros do from_json_file():")
        print("  • filepath (str|Path) - Caminho do arquivo JSON")
        print("  • use_pool (bool) - Usar pool de conexões (padrão: True)")
        print("  • auto_validate (bool) - Validar credenciais (padrão: True)")

        print("\nExemplo de uso em script de clonagem:")
        print("-" * 80)
        print("manager = PostgreSQLConnectionManager.from_json_file(")
        print("    '/path/to/config.json',")
        print("    use_pool=True,")
        print("    auto_validate=True")
        print(")")
        print("cloner = DatabaseCloner(manager)")
        print("cloner.clone_database(drop_if_exists=True)")

        print("\n" + "=" * 80)
        print("🎉 TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
