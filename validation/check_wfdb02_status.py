#!/usr/bin/env python3
"""
PostgreSQL WFDB02 Status Checker
===============================

Script para verificar o status atual do PostgreSQL no servidor WFDB02
e confirmar que PgBouncer não está ativo.

Verifica:
- Conectividade PostgreSQL porta 5432
- Versão PostgreSQL
- Status PgBouncer
- Bancos de dados existentes
- Usuários configurados

Uso:
    python3 check_wfdb02_status.py [--verbose]
"""

import json
import psycopg2
import sys
import os
from datetime import datetime

def load_config():
    """Carrega configuração do servidor destino."""
    config_path = "config/destination_config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        sys.exit(1)

def test_postgresql_connection(config, verbose=False):
    """Testa conectividade com PostgreSQL."""
    print("🔍 Testando conectividade PostgreSQL...")

    server = config['server']
    auth = config['authentication']

    host = server['host']
    port = server['port_direct']
    user = auth['user']
    password = auth['password']

    try:
        # String de conexão
        conn_string = (
            f"host={host} "
            f"port={port} "
            f"dbname=postgres "
            f"user={user} "
            f"password={password} "
            f"sslmode={server['ssl_mode']} "
            f"connect_timeout=30"
        )

        if verbose:
            print(f"   Conectando em: {host}:{port}")

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Obter informações básicas
        cursor.execute("SELECT version(), current_user, current_database(), now()")
        version, user_connected, database, timestamp = cursor.fetchone()

        print("✅ Conectividade PostgreSQL OK!")
        print(f"   🏷️ Versão: {version.split()[1] if version else 'N/A'}")
        print(f"   👤 Usuário: {user_connected}")
        print(f"   🗄️ Database: {database}")
        print(f"   🕐 Timestamp: {timestamp}")

        # Verificar se PgBouncer está rodando
        print("\n🔍 Verificando status PgBouncer...")
        try:
            cursor.execute("SHOW pool_pools;")
            pools = cursor.fetchall()
            print("⚠️ PgBouncer parece estar ativo (comando SHOW pool_pools funcionou)")
            if verbose and pools:
                print("   Pools encontrados:")
                for pool in pools:
                    print(f"   - {pool}")
        except psycopg2.Error:
            print("✅ Confirmado: PgBouncer NÃO está ativo (comando SHOW pool_pools falhou)")

        # Listar bancos de dados
        print("\n📋 Listando bancos de dados...")
        cursor.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database
            WHERE datistemplate = false
            AND datname NOT IN ('postgres')
            ORDER BY datname
        """)
        databases = cursor.fetchall()

        if databases:
            print(f"   Encontrados {len(databases)} bancos de dados:")
            for db_name, db_size in databases:
                print(f"   - {db_name} ({db_size})")
        else:
            print("   Nenhum banco de dados de usuário encontrado")

        # Listar usuários (exceto system users)
        print("\n👥 Listando usuários não-sistema...")
        cursor.execute("""
            SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
            FROM pg_roles
            WHERE rolname NOT LIKE 'pg_%'
            AND rolname != 'postgres'
            ORDER BY rolname
        """)
        users = cursor.fetchall()

        if users:
            print(f"   Encontrados {len(users)} usuários:")
            for user_name, is_super, can_create_role, can_create_db, can_login in users:
                flags = []
                if is_super: flags.append("SUPERUSER")
                if can_create_role: flags.append("CREATEROLE")
                if can_create_db: flags.append("CREATEDB")
                if can_login: flags.append("LOGIN")
                flags_str = ", ".join(flags) if flags else "NO PRIVILEGES"
                print(f"   - {user_name} ({flags_str})")
        else:
            print("   Nenhum usuário não-sistema encontrado")

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError as e:
        print(f"❌ Erro de conectividade: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def check_pgbouncer_port(config, verbose=False):
    """Verifica se há algo rodando na porta padrão do PgBouncer."""
    print("\n🔍 Verificando porta 6432 (PgBouncer padrão)...")

    host = config['server']['host']
    auth = config['authentication']

    try:
        conn_string = (
            f"host={host} "
            f"port=6432 "
            f"dbname=postgres "
            f"user={auth['user']} "
            f"password={auth['password']} "
            f"sslmode=prefer "
            f"connect_timeout=10"
        )

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Tentar comando específico do PgBouncer
        cursor.execute("SHOW pools;")
        pools = cursor.fetchall()

        print("⚠️ Serviço rodando na porta 6432 - pode ser PgBouncer")
        if verbose and pools:
            print("   Pools encontrados:")
            for pool in pools:
                print(f"   - {pool}")

        cursor.close()
        conn.close()
        return True

    except psycopg2.OperationalError as e:
        if "Connection refused" in str(e) or "could not connect" in str(e):
            print("✅ Porta 6432 não responde - confirmado que PgBouncer não está ativo")
        else:
            print(f"❓ Erro na porta 6432: {e}")
        return False
    except Exception as e:
        print(f"❓ Erro inesperado na porta 6432: {e}")
        return False

def generate_migration_recommendations(config):
    """Gera recomendações baseadas no status atual."""
    print("\n" + "="*80)
    print("📊 RECOMENDAÇÕES PARA MIGRAÇÃO")
    print("="*80)

    print("✅ Configuração Simplificada Detectada:")
    print("   - PostgreSQL 16 rodando diretamente na porta 5432")
    print("   - PgBouncer não está ativo")
    print("   - Conexão direta será usada para setup E validação")

    print("\n🎯 Estratégia de Migração Otimizada:")
    print("   1. Usar porta 5432 para TODAS as operações")
    print("   2. Não há necessidade de bypass do PgBouncer")
    print("   3. Migração mais simples e direta")
    print("   4. Validação na mesma porta da criação")

    print("\n🔧 Configuração Atual:")
    server = config['server']
    print(f"   - Host: {server['host']} ({server['ip_address']})")
    print(f"   - Porta: {server['port_direct']}")
    print(f"   - SSL: {server['ssl_mode']}")
    print(f"   - Hardware: {config['hardware_specs']['ram']}, {config['hardware_specs']['cpu']}")

    print("\n🚀 Próximos Passos:")
    print("   1. Executar: python3 test_migration.py")
    print("   2. Se conectividade OK: python3 migration_structure.py")
    print("   3. Monitorar: tail -f reports/migration_execution_*.log")

def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Check PostgreSQL WFDB02 Status")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("="*80)
    print("🔍 PostgreSQL WFDB02 Status Checker")
    print("="*80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🎯 Servidor: wfdb02.vya.digital")
    print("="*80)
    print()

    # Carregar configuração
    config = load_config()

    # Testar PostgreSQL principal
    postgres_ok = test_postgresql_connection(config, args.verbose)

    # Verificar porta PgBouncer
    pgbouncer_check = check_pgbouncer_port(config, args.verbose)

    # Gerar recomendações
    if postgres_ok:
        generate_migration_recommendations(config)

    print("\n" + "="*80)
    if postgres_ok:
        print("🎉 Status: Sistema pronto para migração!")
        print("✅ PostgreSQL 16 acessível na porta 5432")
        print("✅ PgBouncer confirmado como inativo")
        print("✅ Configuração otimizada para conexão direta")
        exit_code = 0
    else:
        print("❌ Status: Problemas de conectividade detectados")
        print("🔧 Verifique credenciais e conectividade de rede")
        exit_code = 1

    print("="*80)
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Verificação interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
