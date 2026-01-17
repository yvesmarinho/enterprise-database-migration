#!/usr/bin/env python3
"""
Teste específico para privilégios - diagnóstico de problemas.
"""
from app.core.sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator
import os
import sys

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_privileges_debug():
    """Testa especificamente a aplicação de privilégios com debug."""
    print("🧪 Teste de DEBUG para privilégios...")

    migrator = SQLAlchemyPostgreSQLMigrator()

    # Carregar configurações
    if not migrator.load_configs():
        print("❌ Falha ao carregar configurações")
        return False

    if not migrator.create_engines():
        print("❌ Falha ao criar engines")
        return False

    print("\n🔍 Testando busca de usuários existentes...")

    # Testar função get_existing_users diretamente
    from sqlalchemy import text
    with migrator.dest_engine.connect() as conn:
        result = conn.execute(text(
            "SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%' ORDER BY rolname"))
        users = [row.rolname for row in result]

    print(f"\n📋 USUÁRIOS ENCONTRADOS ({len(users)}):")
    for i, user in enumerate(users, 1):
        print(f"  {i:2d}. {user}")
        if i > 20:  # Limitar para não poluir
            print(f"      ... e mais {len(users) - 20} usuários")
            break

    # Testar algumas buscas específicas
    test_users = ['root', 'botpress_user', 'airflow_user', 'ai_process_user']
    print(f"\n🔍 Verificando usuários específicos:")
    for user in test_users:
        exists = user in users
        print(
            f"  {'✅' if exists else '❌'} {user}: {'existe' if exists else 'NÃO existe'}")

    print("\n✅ Teste de diagnóstico concluído")
    return True


if __name__ == "__main__":
    test_privileges_debug()
