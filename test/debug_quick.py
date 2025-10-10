#!/usr/bin/env python3
"""
Script de Diagnóstico Rápido - Problema Privilégios Fase 3
==========================================================

Baseado na análise pgAdmin4, investiga por que get_existing_users()
não encontra usuários criados na Fase 1.
"""

import json
import sys
from datetime import datetime

from sqlalchemy import create_engine, text


def load_config():
    """Carrega configuração do destino."""
    try:
        with open('secrets/postgresql_destination_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar config: {e}")
        return None


def create_dest_engine(config):
    """Cria engine de destino igual ao sistema principal."""
    try:
        server = config.get('server', {})
        auth = config.get('authentication', {})

        host = server.get('host', 'localhost')
        port = server.get('port', 5432)
        database = server.get('database', 'postgres')
        user = auth.get('user', 'postgres')
        password = auth.get('password', '')

        url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            echo=False
        )

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        print(f"✅ Conectado ao destino: {host}:{port}/{database}")
        return engine

    except Exception as e:
        print(f"❌ Erro na engine: {e}")
        return None


def test_get_existing_users(engine):
    """Testa o método exato usado pelo sistema."""
    print("\n🔍 Testando get_existing_users() original...")

    try:
        # Método EXATO do sistema
        with engine.connect() as conn:
            result = conn.execute(text("SELECT rolname FROM pg_roles"))
            users = {row.rolname for row in result}

        print(f"   📊 Total de usuários encontrados: {len(users)}")

        # Buscar usuários não-sistema que podem ser da migração
        migration_users = {u for u in users if not u.startswith('pg_')
                          and u not in ['postgres', 'root', 'migration_user']}

        print(f"   👤 Usuários não-sistema: {len(migration_users)}")
        if migration_users:
            print(f"   📋 Lista: {', '.join(sorted(migration_users))}")

        return users, migration_users

    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return set(), set()


def test_specific_users(engine):
    """Testa usuários específicos mencionados no log da sessão anterior."""
    print("\n🎯 Testando usuários específicos do log...")

    # Usuários mencionados no log como "não existe"
    test_users = [
        'root', 'botpress_user', 'admin@vya.digital', 'chatwoot_user',
        'journey_system', 'evolution_api_user', 'n8n_admin', 'n8n_user'
    ]

    try:
        with engine.connect() as conn:
            for user in test_users:
                result = conn.execute(
                    text("SELECT rolname FROM pg_roles WHERE rolname = :username"),
                    {"username": user}
                )
                exists = result.fetchone() is not None

                status = "✅ EXISTE" if exists else "❌ NÃO EXISTE"
                print(f"   {status}: {user}")

    except Exception as e:
        print(f"   ❌ Erro: {e}")


def test_timing_issue(engine):
    """Testa se há problema de timing entre conexões."""
    print("\n⏰ Testando problema de timing...")

    test_user = f"debug_user_{datetime.now().strftime('%H%M%S')}"

    try:
        # 1. Criar usuário
        with engine.connect() as conn:
            conn = conn.execution_options(autocommit=True)
            conn.execute(text(f'CREATE USER "{test_user}"'))
            print(f"   ✅ Criado: {test_user}")

        # 2. Verificar imediatamente com nova conexão
        with engine.connect() as conn:
            result = conn.execute(text("SELECT rolname FROM pg_roles"))
            all_users = {row.rolname for row in result}
            found = test_user in all_users

        print(f"   📍 Encontrado na lista: {found}")

        # 3. Verificar diretamente
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT rolname FROM pg_roles WHERE rolname = :username"),
                {"username": test_user}
            )
            direct_found = result.fetchone() is not None

        print(f"   📍 Busca direta: {direct_found}")

        # 4. Cleanup
        with engine.connect() as conn:
            conn = conn.execution_options(autocommit=True)
            conn.execute(text(f'DROP USER "{test_user}"'))
            print(f"   🗑️ Removido: {test_user}")

    except Exception as e:
        print(f"   ❌ Erro: {e}")


def main():
    """Executa diagnóstico principal."""
    print("🚀 DIAGNÓSTICO RÁPIDO - PROBLEMA PRIVILÉGIOS FASE 3")
    print("=" * 60)

    # Load config
    config = load_config()
    if not config:
        return False

    # Create engine
    engine = create_dest_engine(config)
    if not engine:
        return False

    # Run tests
    all_users, migration_users = test_get_existing_users(engine)
    test_specific_users(engine)
    test_timing_issue(engine)

    # Summary
    print(f"\n📋 RESUMO:")
    print(f"   📊 Total usuários no destino: {len(all_users)}")
    print(f"   👤 Usuários de migração: {len(migration_users)}")

    if len(migration_users) < 38:
        print("   ⚠️ PROBLEMA: Esperados 38 usuários, encontrados apenas",
              len(migration_users))
        print("   💡 HIPÓTESE: Usuários não foram realmente criados na Fase 1")
    else:
        print("   ✅ Usuários encontrados - problema pode estar na verificação")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
