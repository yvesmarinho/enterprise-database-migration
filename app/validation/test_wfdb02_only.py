#!/usr/bin/env python3
"""
Test WFDB02 Only - Focused Connectivity Test
============================================

Script para testar APENAS o servidor de destino WFDB02,
ignorando temporariamente o servidor de origem wf004.

Isso nos permite:
1. Validar se as credenciais funcionam no WFDB02
2. Verificar se o usuário migration_user existe
3. Identificar se o problema é só no wf004 ou em ambos

Uso:
    python3 test_wfdb02_only.py [--verbose]
"""

import json
import psycopg2
import psycopg2.extras
import sys
from datetime import datetime

def load_destination_config():
    """Carrega apenas a configuração do servidor destino."""
    try:
        from components.config_manager import get_db_config_path
        dest_config_path = get_db_config_path('postgresql_destination_config')
        with open(dest_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        sys.exit(1)

def test_wfdb02_connectivity(config, verbose=False):
    """Testa conectividade apenas com WFDB02."""
    print("🎯 Testando conectividade WFDB02...")

    server = config['server']
    auth = config['authentication']

    host = server['host']
    port = server['port_direct']
    user = auth['user']
    password = auth['password']

    if verbose:
        print(f"   Host: {host}")
        print(f"   Porta: {port}")
        print(f"   Usuário: {user}")
        print(f"   SSL: {server['ssl_mode']}")

    try:
        conn_string = (
            f"host={host} "
            f"port={port} "
            f"dbname=postgres "
            f"user={user} "
            f"password={password} "
            f"sslmode={server['ssl_mode']} "
            f"connect_timeout=30"
        )

        print("🔌 Estabelecendo conexão...")
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Informações básicas
        print("📊 Coletando informações do servidor...")
        cursor.execute("SELECT version(), current_user, current_database(), now()")
        result = cursor.fetchone()

        print("✅ Conexão WFDB02 bem-sucedida!")
        print(f"   🏷️ Versão PostgreSQL: {result['version'].split()[1] if result['version'] else 'N/A'}")
        print(f"   👤 Usuário conectado: {result['current_user']}")
        print(f"   🗄️ Database: {result['current_database']}")
        print(f"   🕐 Timestamp servidor: {result['now']}")

        # Verificar privilégios do usuário
        print("\n🔐 Verificando privilégios do usuário...")
        cursor.execute("""
            SELECT
                rolname,
                rolsuper,
                rolcreaterole,
                rolcreatedb,
                rolcanlogin,
                rolreplication
            FROM pg_roles
            WHERE rolname = current_user
        """)
        user_info = cursor.fetchone()

        if user_info:
            privileges = []
            if user_info['rolsuper']: privileges.append("SUPERUSER")
            if user_info['rolcreaterole']: privileges.append("CREATEROLE")
            if user_info['rolcreatedb']: privileges.append("CREATEDB")
            if user_info['rolcanlogin']: privileges.append("LOGIN")
            if user_info['rolreplication']: privileges.append("REPLICATION")

            print(f"   👤 Usuário: {user_info['rolname']}")
            print(f"   🔑 Privilégios: {', '.join(privileges) if privileges else 'Nenhum privilégio especial'}")

            # Verificar se tem privilégios suficientes para migração
            can_migrate = user_info['rolcreatedb'] or user_info['rolsuper']
            if can_migrate:
                print("   ✅ Usuário tem privilégios suficientes para migração")
            else:
                print("   ⚠️ Usuário pode não ter privilégios suficientes (necessário CREATEDB ou SUPERUSER)")

        # Listar bancos existentes
        print("\n📋 Bancos de dados existentes...")
        cursor.execute("""
            SELECT
                datname,
                pg_size_pretty(pg_database_size(datname)) as size,
                datowner::regrole as owner
            FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname
        """)
        databases = cursor.fetchall()

        print(f"   Encontrados {len(databases)} bancos:")
        for db in databases:
            print(f"   - {db['datname']} ({db['size']}) - Owner: {db['owner']}")

        # Verificar se há outros usuários migration-related
        print("\n👥 Usuários relacionados à migração...")
        cursor.execute("""
            SELECT rolname, rolcanlogin, rolcreatedb, rolsuper
            FROM pg_roles
            WHERE rolname LIKE '%migration%' OR rolname LIKE '%migrate%'
            ORDER BY rolname
        """)
        migration_users = cursor.fetchall()

        if migration_users:
            print(f"   Encontrados {len(migration_users)} usuários relacionados:")
            for user in migration_users:
                status = "ATIVO" if user['rolcanlogin'] else "INATIVO"
                print(f"   - {user['rolname']} ({status})")
        else:
            print("   Nenhum outro usuário relacionado à migração encontrado")

        cursor.close()
        conn.close()

        return True, user_info

    except psycopg2.OperationalError as e:
        print(f"❌ Erro de conectividade WFDB02: {e}")
        return False, None
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return False, None

def test_create_database_permission(config, verbose=False):
    """Testa se consegue criar um banco de teste."""
    print("\n🧪 Testando permissões de criação de banco...")

    server = config['server']
    auth = config['authentication']

    try:
        conn_string = (
            f"host={server['host']} "
            f"port={server['port_direct']} "
            f"dbname=postgres "
            f"user={auth['user']} "
            f"password={auth['password']} "
            f"sslmode={server['ssl_mode']} "
            f"connect_timeout=30"
        )

        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()

        # Tentar criar um banco de teste
        test_db_name = f"migration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            cursor.execute(f'CREATE DATABASE "{test_db_name}" WITH OWNER = CURRENT_USER')
            print(f"   ✅ Banco de teste criado: {test_db_name}")

            # Tentar se conectar ao banco criado
            test_conn_string = conn_string.replace("dbname=postgres", f"dbname={test_db_name}")
            test_conn = psycopg2.connect(test_conn_string)
            test_cursor = test_conn.cursor()

            # Criar uma tabela de teste
            test_cursor.execute("""
                CREATE TABLE migration_test (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("   ✅ Tabela de teste criada")

            test_cursor.close()
            test_conn.close()

            # Remover banco de teste
            cursor.execute(f'DROP DATABASE "{test_db_name}"')
            print("   ✅ Banco de teste removido - Permissões OK!")

            cursor.close()
            conn.close()
            return True

        except psycopg2.Error as e:
            print(f"   ❌ Erro ao criar banco de teste: {e}")
            # Tentar limpar se banco foi criado parcialmente
            try:
                cursor.execute(f'DROP DATABASE IF EXISTS "{test_db_name}"')
            except:
                pass
            cursor.close()
            conn.close()
            return False

    except Exception as e:
        print(f"   ❌ Erro no teste de permissões: {e}")
        return False

def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Test WFDB02 Only Connectivity")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("="*80)
    print("🎯 WFDB02 Connectivity Test - Focused Validation")
    print("="*80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🏗️ Servidor: wfdb02.vya.digital (PostgreSQL 16)")
    print(f"👤 Usuário: migration_user")
    print("="*80)
    print()

    # Carregar configuração
    config = load_destination_config()

    # Testar conectividade
    success, user_info = test_wfdb02_connectivity(config, args.verbose)

    permissions_ok = False
    if success and user_info:
        # Testar permissões se conectividade OK
        if user_info['rolcreatedb'] or user_info['rolsuper']:
            permissions_ok = test_create_database_permission(config, args.verbose)
        else:
            print("\n⚠️ Usuário não tem privilégios CREATEDB - pulando teste de criação")

    # Relatório final
    print("\n" + "="*80)
    print("📊 RELATÓRIO FINAL - WFDB02")
    print("="*80)

    if success:
        print("✅ CONECTIVIDADE: OK")
        print(f"   - Host: {config['server']['host']}")
        print(f"   - Porta: {config['server']['port_direct']}")
        print(f"   - Usuário: migration_user autenticado")

        if user_info:
            if user_info['rolsuper']:
                print("✅ PRIVILÉGIOS: SUPERUSER (todos os privilégios)")
            elif user_info['rolcreatedb']:
                print("✅ PRIVILÉGIOS: CREATEDB (suficiente para migração)")
            else:
                print("⚠️ PRIVILÉGIOS: Limitados (pode afetar migração)")

        if permissions_ok:
            print("✅ TESTES: Criação/remoção de banco funcionando")
        elif user_info and (user_info['rolcreatedb'] or user_info['rolsuper']):
            print("⚠️ TESTES: Problemas na criação de banco")
        else:
            print("➖ TESTES: Não executados (privilégios insuficientes)")
    else:
        print("❌ CONECTIVIDADE: FALHA")
        print("   - Verificar credenciais do migration_user")
        print("   - Verificar se usuário existe no WFDB02")
        print("   - Verificar conectividade de rede")

    print("\n🔍 PRÓXIMOS PASSOS:")
    if success:
        print("   1. ✅ WFDB02 está pronto para receber migração")
        print("   2. 🔧 Focar na correção do problema no servidor wf004")
        print("   3. 🚀 Após correção wf004: executar migração completa")
    else:
        print("   1. 🔧 Corrigir credenciais do migration_user no WFDB02")
        print("   2. 🔐 Verificar se usuário existe e tem senha correta")
        print("   3. 🔄 Re-executar este teste após correções")

    print("="*80)

    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
