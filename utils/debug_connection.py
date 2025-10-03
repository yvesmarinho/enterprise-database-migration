#!/usr/bin/env python3
"""
Teste de Conexão Manual - Debug de Migração
==========================================

Reproduz exatamente a mesma conexão que funcionou nos outros scripts
para identificar a diferença no migration_structure.py
"""

import psycopg2
import json
from datetime import datetime

def test_manual_connection():
    print("="*80)
    print("🔧 TESTE MANUAL DE CONEXÃO - DEBUG MIGRAÇÃO")
    print("="*80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # Método 1: Conexão que funcionou nos scripts anteriores
    print("\n🎯 MÉTODO 1: Conexão direta (como discover_users.py)")
    print("-" * 50)

    try:
        conn_string1 = (
            "host=wf004.vya.digital "
            "port=5432 "
            "dbname=postgres "
            "user=migration_user "
            "password=REDACTED_WFDB02_PASSWORD "
            "sslmode=prefer "
            "connect_timeout=10"
        )

        print(f"   📡 Conectando: wf004.vya.digital:5432")
        conn1 = psycopg2.connect(conn_string1)
        cursor1 = conn1.cursor()

        cursor1.execute("SELECT current_user, version()")
        user, version = cursor1.fetchone()

        print(f"   ✅ SUCESSO!")
        print(f"   👤 Usuário: {user}")
        print(f"   🐘 Versão: {version.split()[1]}")

        cursor1.close()
        conn1.close()

    except Exception as e:
        print(f"   ❌ FALHA: {e}")

    # Método 2: Carregar configuração do arquivo JSON
    print("\n🔧 MÉTODO 2: Via arquivo source_config.json")
    print("-" * 50)

    try:
        with open('config/source_config.json', 'r', encoding='utf-8') as f:
            source_data = json.load(f)

        print(f"   📋 Configurações carregadas:")
        print(f"      🌐 Host: {source_data['server']['host']}")
        print(f"      🔌 Port: {source_data['server']['port']}")
        print(f"      👤 User: {source_data['authentication']['user']}")
        print(f"      🔒 SSL: {source_data['server']['ssl_mode']}")
        print(f"      ⏱️ Timeout: {source_data['connection_settings']['connection_timeout']}")

        conn_string2 = (
            f"host={source_data['server']['host']} "
            f"port={source_data['server']['port']} "
            f"dbname=postgres "
            f"user={source_data['authentication']['user']} "
            f"password={source_data['authentication']['password']} "
            f"sslmode={source_data['server']['ssl_mode']} "
            f"connect_timeout={source_data['connection_settings']['connection_timeout']}"
        )

        print(f"   📡 Conectando via configuração JSON...")
        conn2 = psycopg2.connect(conn_string2)
        cursor2 = conn2.cursor()

        cursor2.execute("SELECT current_user, inet_client_addr(), inet_server_addr()")
        user, client_ip, server_ip = cursor2.fetchone()

        print(f"   ✅ SUCESSO!")
        print(f"   👤 Usuário: {user}")
        print(f"   🌐 Client IP: {client_ip}")
        print(f"   🖥️ Server IP: {server_ip}")

        cursor2.close()
        conn2.close()

    except Exception as e:
        print(f"   ❌ FALHA: {e}")

    # Método 3: Reproduzir exatamente como migration_structure.py
    print("\n⚙️ MÉTODO 3: Simulando migration_structure.py")
    print("-" * 50)

    try:
        # Simular ConnectionConfig
        class ConnectionConfig:
            def __init__(self, host, port, user, password, ssl_mode, timeout):
                self.host = host
                self.port = port
                self.user = user
                self.password = password
                self.ssl_mode = ssl_mode
                self.timeout = timeout

        # Carregar como migration_structure.py faz
        with open('config/source_config.json', 'r', encoding='utf-8') as f:
            source_data = json.load(f)

        source_config = ConnectionConfig(
            host=source_data['server']['host'],
            port=source_data['server']['port'],
            user=source_data['authentication']['user'],
            password=source_data['authentication']['password'],
            ssl_mode=source_data['server']['ssl_mode'],
            timeout=source_data['connection_settings']['connection_timeout']
        )

        # String de conexão como migration_structure.py
        conn_string3 = (
            f"host={source_config.host} "
            f"port={source_config.port} "
            f"dbname=postgres "
            f"user={source_config.user} "
            f"password={source_config.password} "
            f"sslmode={source_config.ssl_mode} "
            f"connect_timeout={source_config.timeout}"
        )

        print(f"   📡 String de conexão migration_structure:")
        print(f"      {conn_string3}")

        conn3 = psycopg2.connect(conn_string3)
        cursor3 = conn3.cursor()

        cursor3.execute("SELECT current_user, pg_backend_pid(), application_name")
        user, pid, app_name = cursor3.fetchone()

        print(f"   ✅ SUCESSO!")
        print(f"   👤 Usuário: {user}")
        print(f"   🆔 PID: {pid}")
        print(f"   📱 App: {app_name}")

        cursor3.close()
        conn3.close()

    except Exception as e:
        print(f"   ❌ FALHA: {e}")
        print(f"   🔍 Detalhes do erro: {type(e).__name__}")

    print("\n" + "="*80)
    print("📊 RESULTADO DO DEBUG")
    print("="*80)
    print("Se MÉTODO 1 e 2 funcionaram mas MÉTODO 3 falhou,")
    print("o problema está na implementação do migration_structure.py")
    print("="*80)

if __name__ == "__main__":
    test_manual_connection()
