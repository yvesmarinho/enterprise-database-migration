#!/usr/bin/env python3
"""
Script de teste rápido para validar privilégios.
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator

def test_privilege_syntax():
    """Testa se a sintaxe dos privilégios está correta."""
    print("🧪 Testando sintaxe de privilégios...")

    migrator = SQLAlchemyPostgreSQLMigrator()

    # Carregar configurações
    if not migrator.load_configs():
        print("❌ Falha ao carregar configurações")
        return False

    if not migrator.create_engines():
        print("❌ Falha ao criar engines")
        return False

    # Testar aplicação de privilégio simples
    print("\n🔍 Testando sintaxe de GRANT...")

    # Simular dados de teste
    test_databases = [
        {'datname': 'test_db_ficticio', 'owner': 'root'}
    ]

    # Tentar aplicar privilégios (vai falhar porque banco não existe, mas vamos ver os erros)
    result = migrator.apply_database_privileges(test_databases)

    print(f"\n📊 Resultado: {result} privilégios aplicados")
    print("✅ Teste de sintaxe concluído")

    return True

if __name__ == "__main__":
    test_privilege_syntax()
