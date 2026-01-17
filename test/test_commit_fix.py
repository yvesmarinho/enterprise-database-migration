#!/usr/bin/env python3
"""
Teste simples para verificar se a correção de commit funciona.
"""

import json

from sqlalchemy import create_engine, text

from app.core.sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator


def test_commit_fix():
    """Testa se a correção de commit resolve o problema."""

    print("🧪 TESTE RÁPIDO - CORREÇÃO DE COMMIT NA FASE 1")
    print("=" * 60)

    # Carregar configuração do destino
    with open('secrets/postgresql_destination_config.json', 'r') as f:
        dest_config = json.load(f)

    # Criar engine usando a mesma abordagem do sistema
    from components.config_normalizer import get_sqlalchemy_url

    dest_url = get_sqlalchemy_url(dest_config, database='postgres')
    engine = create_engine(dest_url)

    # Criar uma instância do migrador
    migrator = SQLAlchemyPostgreSQLMigrator()
    migrator.dest_engine = engine

    # Usuário de teste simples
    test_user = [{
        'rolname': 'test_commit_fix_user',
        'rolcanlogin': True,
        'rolsuper': False,
        'rolinherit': True,
        'rolcreaterole': False,
        'rolcreatedb': False,
        'rolreplication': False,
        'rolconnlimit': -1,
        'rolpassword': None
    }]

    print(f"🎯 Testando criação de usuário: {test_user[0]['rolname']}")

    # Limpar usuário se existir
    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP USER IF EXISTS "{test_user[0]["rolname"]}"'))
            conn.commit()
    except Exception:
        pass

    # Testar criação
    print("\n📝 Executando create_users_in_destination()...")
    created_count = migrator.create_users_in_destination(test_user)

    # Verificar se realmente existe
    print("\n🔍 Verificando se usuário existe após criação...")
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT rolname FROM pg_roles WHERE rolname = :username"),
                {"username": test_user[0]['rolname']}
            )
            exists = result.fetchone() is not None

            if exists:
                print(f"   ✅ SUCESSO: Usuário existe no banco!")
                print(f"   📊 Reportado como criado: {created_count}")
                print(f"   🎯 CORREÇÃO FUNCIONOU! Problema de commit resolvido.")
            else:
                print(f"   ❌ FALHA: Usuário não existe no banco!")
                print(f"   📊 Reportado como criado: {created_count}")
                print(f"   ⚠️ Problema de commit ainda persiste.")

    except Exception as e:
        print(f"   ❌ Erro ao verificar: {e}")

    # Cleanup
    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP USER IF EXISTS "{test_user[0]["rolname"]}"'))
            conn.commit()
            print(f"\n🧹 Usuário de teste removido")
    except Exception:
        pass


if __name__ == "__main__":
    test_commit_fix()
