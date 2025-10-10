#!/usr/bin/env python3
"""
Teste do sistema de cleanup com nova configuração JSON.
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cleanup.cleanup_database import PostgreSQLCleanup, load_server_config

def test_config_loading():
    """Testa o carregamento das configurações."""
    print("🧪 Testando carregamento de configurações...")

    # Testar origem
    print("\n📋 Testando configuração da origem...")
    origem_config = load_server_config('origem')
    if origem_config:
        server_info = origem_config['server']
        auth_info = origem_config['authentication']
        cleanup_info = origem_config['cleanup_protection']

        print(f"   ✅ Servidor: {server_info['host']}:{server_info['port']}")
        print(f"   ✅ Usuário: {auth_info['user']}")
        print(f"   ✅ Bancos protegidos: {cleanup_info['protected_databases']}")
        print(f"   ✅ Usuários protegidos: {cleanup_info['protected_users']}")
    else:
        print("   ❌ Falha ao carregar configuração da origem")
        return False

    # Testar destino
    print("\n📋 Testando configuração do destino...")
    destino_config = load_server_config('destino')
    if destino_config:
        server_info = destino_config['server']
        auth_info = destino_config['authentication']
        cleanup_info = destino_config['cleanup_protection']

        print(f"   ✅ Servidor: {server_info['host']}:{server_info['port']}")
        print(f"   ✅ Usuário: {auth_info['user']}")
        print(f"   ✅ Bancos protegidos: {cleanup_info['protected_databases']}")
        print(f"   ✅ Usuários protegidos: {cleanup_info['protected_users']}")
    else:
        print("   ❌ Falha ao carregar configuração do destino")
        return False

    return True

def test_cleanup_initialization():
    """Testa a inicialização da classe de cleanup."""
    print("\n🧪 Testando inicialização da classe cleanup...")

    config = load_server_config('destino')  # Usar destino para teste
    if not config:
        print("   ❌ Falha ao carregar configuração")
        return False

    cleanup = PostgreSQLCleanup(config, "teste-destino")

    # Verificar se as configurações foram carregadas corretamente
    print(f"   ✅ Bancos protegidos: {sorted(cleanup.protected_databases)}")
    print(f"   ✅ Usuários protegidos: {sorted(cleanup.protected_users)}")

    # Testar conexão (sem realmente conectar)
    print("   ✅ Classe inicializada com sucesso")

    return True

def main():
    """Função principal de teste."""
    print("🧹 Teste do Sistema de Cleanup - Nova Configuração JSON")
    print("=" * 60)

    success = True

    # Teste 1: Carregamento de configurações
    if not test_config_loading():
        success = False

    # Teste 2: Inicialização da classe
    if not test_cleanup_initialization():
        success = False

    # Resultado final
    print("\n" + "=" * 60)
    if success:
        print("🎉 Todos os testes passaram! Sistema compatível com nova configuração JSON.")
    else:
        print("❌ Alguns testes falharam. Verificar implementação.")
    print("=" * 60)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
