#!/usr/bin/env python3
"""
Teste específico para criação de usuários após correção de commit.
"""

import json

from sqlalchemy import create_engine, text


def test_user_creation():
    """Testa criação de usuários específicos que falharam."""

    print("🧪 TESTE DE CRIAÇÃO DE USUÁRIOS - PÓS CORREÇÃO")
    print("=" * 60)

    # Carregar configurações
    with open('secrets/destination_config.json', 'r') as f:
        dest_config = json.load(f)

    # Criar engine diretamente
    server = dest_config['server']
    auth = dest_config['authentication']
    conn_str = (
        f"postgresql://{auth['user']}:{auth['password']}"
        f"@{server['host']}:{server['port']}/{server['database']}"
    )
    engine = create_engine(conn_str)

    # Usuários de teste que falharam anteriormente
    test_users = [
        {
            'rolname': 'test_root_user',
            'rolcanlogin': True,
            'rolsuper': False,
            'rolinherit': True,
            'rolcreaterole': False,
            'rolcreatedb': False,
            'rolreplication': False,
            'rolconnlimit': -1,
            'rolpassword': 'hashed_password_test'
        },
        {
            'rolname': 'test_botpress_user',
            'rolcanlogin': True,
            'rolsuper': False,
            'rolinherit': True,
            'rolcreaterole': False,
            'rolcreatedb': False,
            'rolreplication': False,
            'rolconnlimit': -1,
            'rolpassword': None
        }
    ]

    print(f"🎯 Testando criação de {len(test_users)} usuários...")

    # Verificar usuários existentes antes
    existing_before = migrator.get_existing_users()
    print(f"📊 Usuários existentes antes: {len(existing_before)}")

    # Criar usuários com correção
    created = migrator.create_users_in_destination(test_users)
    print(f"📈 Usuários reportados como criados: {created}")

    # Verificar usuários existentes depois
    existing_after = migrator.get_existing_users()
    print(f"📊 Usuários existentes depois: {len(existing_after)}")

    # Verificação específica
    print("\n🔍 Verificação específica dos usuários criados:")
    for user in test_users:
        username = user['rolname']
        exists = any(u['rolname'] == username for u in existing_after)
        status = "✅ EXISTE" if exists else "❌ NÃO EXISTE"
        print(f"   {status}: {username}")

    # Cleanup - remover usuários de teste
    print("\n🧹 Limpeza - removendo usuários de teste...")
    try:
        with migrator.dest_engine.connect() as conn:
            for user in test_users:
                username = user['rolname']
                try:
                    conn.execute(f'DROP USER IF EXISTS "{username}"')
                    conn.commit()
                    print(f"   🗑️ Removido: {username}")
                except Exception as e:
                    print(f"   ⚠️ Erro ao remover {username}: {e}")
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")

if __name__ == "__main__":
    test_user_creation()
