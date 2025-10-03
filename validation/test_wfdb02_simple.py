#!/usr/bin/env python3
"""
Teste Simplificado de Conexão com WFDB02
"""

import mysql.connector
import psycopg2
import sys
import time

# Configurações
MYSQL_CONFIG = {
    "host": "82.197.64.145",
    "port": 3306,
    "user": "enterprise_user",
    "password": "enterprise_pass123!",
    "database": "empresa_desenvolvimento",
    "connection_timeout": 10,  # Timeout de 10 segundos
}

POSTGRESQL_CONFIG = {
    "host": "82.197.64.145",
    "port": 5432,
    "user": "enterprise_user",
    "password": "enterprise_pass123!",
    "database": "empresa_desenvolvimento",
    "connect_timeout": 10,  # Timeout de 10 segundos
}


def test_mysql_connection():
    print("Testando conexão MySQL...")
    start_time = time.time()
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"MySQL connection successful: {result}")
        cursor.close()
        conn.close()
        print(f"Tempo de conexão MySQL: {time.time() - start_time:.2f} segundos")
        return True
    except Exception as e:
        print(f"MySQL connection error: {e}")
        print(f"Tempo até falha MySQL: {time.time() - start_time:.2f} segundos")
        return False


def test_postgresql_connection():
    print("Testando conexão PostgreSQL...")
    start_time = time.time()
    try:
        conn = psycopg2.connect(**POSTGRESQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"PostgreSQL connection successful: {result}")
        cursor.close()
        conn.close()
        print(f"Tempo de conexão PostgreSQL: {time.time() - start_time:.2f} segundos")
        return True
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")
        print(f"Tempo até falha PostgreSQL: {time.time() - start_time:.2f} segundos")
        return False


if __name__ == "__main__":
    print("=== Teste Simplificado de Conexão com WFDB02 ===")
    print(f"Timestamp: {time.time()}")

    mysql_ok = test_mysql_connection()
    pg_ok = test_postgresql_connection()

    if mysql_ok and pg_ok:
        print("✅ Ambas as conexões funcionaram com sucesso!")
        sys.exit(0)
    elif mysql_ok:
        print("⚠️ Apenas a conexão MySQL funcionou.")
        sys.exit(1)
    elif pg_ok:
        print("⚠️ Apenas a conexão PostgreSQL funcionou.")
        sys.exit(1)
    else:
        print("❌ Ambas as conexões falharam.")
        sys.exit(2)
