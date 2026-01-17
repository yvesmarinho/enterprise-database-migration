#!/usr/bin/env python3
"""
Script de teste para validar proteções de usuários e bancos.
"""
import json
import sys
import os

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator

def test_protections():
    """Testa se as proteções estão sendo aplicadas corretamente."""
    print("🧪 Testando sistema de proteções...")

    migrator = SQLAlchemyPostgreSQLMigrator()

    # Carregar configurações
    if not migrator.load_configs():
        print("❌ Falha ao carregar configurações")
        return False

    # Testar obtenção de proteções
    protected_users, protected_databases = migrator.get_protected_items()

    print(f"\n🛡️ USUÁRIOS PROTEGIDOS ({len(protected_users)}):")
    for user in sorted(protected_users):
        print(f"   - {user}")

    print(f"\n🛡️ BANCOS PROTEGIDOS ({len(protected_databases)}):")
    for db in sorted(protected_databases):
        print(f"   - {db}")

    # Simular lista de usuários para teste
    test_users = [
        {'rolname': 'postgres'},          # PROTEGIDO
        {'rolname': 'migration_user'},    # PROTEGIDO
        {'rolname': 'test_user'},         # NÃO PROTEGIDO
        {'rolname': 'yves_marinho'},      # PROTEGIDO
    ]

    print(f"\n🧪 TESTE FILTRO DE USUÁRIOS:")
    filtered_users = migrator.filter_protected_users(test_users)
    print(f"   Original: {len(test_users)} usuários")
    print(f"   Filtrado: {len(filtered_users)} usuários")

    # Simular lista de bancos para teste
    test_databases = [
        {'datname': 'postgres'},          # PROTEGIDO
        {'datname': 'template0'},         # PROTEGIDO
        {'datname': 'template1'},         # PROTEGIDO
        {'datname': 'test_db'},           # NÃO PROTEGIDO
        {'datname': 'app_db'},            # NÃO PROTEGIDO
    ]

    print(f"\n🧪 TESTE FILTRO DE BANCOS:")
    filtered_databases = migrator.filter_protected_databases(test_databases)
    print(f"   Original: {len(test_databases)} bancos")
    print(f"   Filtrado: {len(filtered_databases)} bancos")

    return True

if __name__ == "__main__":
    test_protections()
