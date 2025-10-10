#!/usr/bin/env python3
"""
Teste específico para coleta de privilégios da origem.
"""
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator

def test_privilege_collection():
    """Testa especificamente a coleta de privilégios da origem."""
    print("🧪 Testando coleta de privilégios da origem...")

    migrator = SQLAlchemyPostgreSQLMigrator()

    # Carregar configurações
    if not migrator.load_configs():
        print("❌ Falha ao carregar configurações")
        return False

    if not migrator.create_engines():
        print("❌ Falha ao criar engines")
        return False

    print("\n🔍 Testando coleta de privilégios para bancos específicos...")

    # Testar alguns bancos específicos
    test_databases = ['ai_process_db', 'botpress_db', 'n8n_db']

    for db_name in test_databases:
        print(f"\n📋 Testando banco: {db_name}")
        try:
            privileges = migrator.get_database_privileges(db_name)
            print(f"   📊 Coletados {len(privileges)} conjuntos de privilégios:")

            for i, priv in enumerate(privileges, 1):
                username = priv['username']
                privs = ', '.join(priv['privileges'])
                print(f"     {i}. {username}: {privs}")

        except Exception as e:
            print(f"   ❌ Erro: {e}")

    print("\n✅ Teste de coleta de privilégios concluído")
    return True

if __name__ == "__main__":
    test_privilege_collection()
