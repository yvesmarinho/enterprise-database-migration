#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste do carregamento de arquivo JSON diretamente no PostgreSQLConnectionManager.

Este script demonstra o uso do novo método from_json_file().
"""

import sys
from pathlib import Path

# Adicionar diretório ao path
sys.path.insert(0, str(Path(__file__).parent))


def test_from_json_file():
    """Testa carregamento direto de arquivo JSON."""
    print("=" * 80)
    print("TESTE: PostgreSQLConnectionManager.from_json_file()")
    print("=" * 80)

    try:
        from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager

        # Caminho do arquivo de configuração de exemplo
        config_file = Path(__file__).parent / "config_example_Version2.json"

        if not config_file.exists():
            print(f"⚠ Arquivo de exemplo não encontrado: {config_file}")
            print("Usando configuração de destino das secrets...")

            # Tentar usar o arquivo de destino
            secrets_dir = Path(__file__).parent.parent / "secrets"
            config_file = secrets_dir / "destination_config.txt"

            if not config_file.exists():
                print(f"✗ Arquivo não encontrado: {config_file}")
                return False

        print(f"\n📄 Carregando configuração de: {config_file}")
        print("-" * 80)

        # FORMA NOVA: Carregamento direto
        print("\n🆕 NOVA FORMA (uma linha):")
        print("manager = PostgreSQLConnectionManager.from_json_file(config_file)")

        manager = PostgreSQLConnectionManager.from_json_file(
            config_file,
            use_pool=True,
            auto_validate=False  # Não validar para não conectar
        )

        print("\n✓ Manager criado com sucesso!")
        print(f"  Host: {manager.config.host}")
        print(f"  Porta: {manager.config.port}")
        print(f"  SSL Mode: {manager.config.ssl_mode.value}")
        print(f"  Usuários configurados: {len(manager.config.possible_users)}")

        if hasattr(manager.config, 'db_source'):
            print(f"  Banco origem: {manager.config.db_source}")
        if hasattr(manager.config, 'db_destiny'):
            print(f"  Banco destino: {manager.config.db_destiny}")

        print("\n" + "=" * 80)
        print("COMPARAÇÃO COM FORMA ANTIGA")
        print("=" * 80)

        print("\n📜 FORMA ANTIGA (duas linhas):")
        print("config = PostgreSQLJsonConfig.from_json_file(config_file)")
        print("manager = PostgreSQLConnectionManager(config)")

        from pg_json_config_Version2 import PostgreSQLJsonConfig

        config = PostgreSQLJsonConfig.from_json_file(config_file)
        manager_old = PostgreSQLConnectionManager(config, auto_validate=False)

        print("\n✓ Manager criado (forma antiga)")
        print(f"  Host: {manager_old.config.host}")

        # Verificar se são equivalentes
        if (manager.config.host == manager_old.config.host and
                manager.config.port == manager_old.config.port):
            print("\n✅ Ambas as formas produzem resultado idêntico!")

        print("\n" + "=" * 80)
        print("BENEFÍCIOS DA NOVA FORMA")
        print("=" * 80)
        print("✓ Menos código (1 linha ao invés de 2)")
        print("✓ Mais intuitivo e direto")
        print("✓ Menos imports necessários")
        print("✓ API consistente com PostgreSQLJsonConfig")

        return True

    except ImportError as e:
        print(f"\n✗ Erro ao importar módulos: {e}")
        return False
    except FileNotFoundError as e:
        print(f"\n✗ Arquivo não encontrado: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Função principal."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║          Teste de Carregamento de JSON Direto no Manager                  ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()

    success = test_from_json_file()

    print("\n" + "=" * 80)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        return 0
    else:
        print("⚠ TESTE FALHOU")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
