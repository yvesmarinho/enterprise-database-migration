#!/usr/bin/env python3
"""
Teste da Configuração de Proteção de Usuários
==============================================

Script para testar se as configurações de usuários e bancos protegidos
estão sendo lidas corretamente dos arquivos JSON.

Uso:
    python3 test_protection_config.py
"""

import json
import sys
from pathlib import Path

def test_config_file(config_path: str):
    """Testa um arquivo de configuração específico."""
    try:
        print(f"\n📁 Testando: {config_path}")

        if not Path(config_path).exists():
            print(f"❌ Arquivo não encontrado: {config_path}")
            return False

        with open(config_path, 'r') as f:
            config = json.load(f)

        print(f"✅ JSON válido")

        # Verificar se tem a seção de proteção
        if 'cleanup_protection' in config:
            protection = config['cleanup_protection']

            protected_dbs = protection.get('protected_databases', [])
            protected_users = protection.get('protected_users', [])

            print(f"🛡️ Bancos protegidos ({len(protected_dbs)}): {protected_dbs}")
            print(f"🛡️ Usuários protegidos ({len(protected_users)}): {protected_users}")

            return True
        else:
            print(f"⚠️ Seção 'cleanup_protection' não encontrada")
            return False

    except json.JSONDecodeError as e:
        print(f"❌ Erro no JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Função principal."""
    print("🧪 Teste de Configuração de Proteção")
    print("=" * 50)

    # Arquivos para testar
    config_files = [
        "src/migration/config/source_config.json",
        "src/migration/config/destination_config.json",
        "src/postgresql/config/source_config.json",
        "src/postgresql/config/destination_config.json"
    ]

    success_count = 0
    total_count = len(config_files)

    for config_file in config_files:
        if test_config_file(config_file):
            success_count += 1

    print(f"\n📊 Resultado: {success_count}/{total_count} arquivos válidos")

    if success_count == total_count:
        print("🎉 Todos os arquivos estão corretos!")
        return 0
    else:
        print("⚠️ Alguns arquivos precisam de correção")
        return 1

if __name__ == "__main__":
    sys.exit(main())
