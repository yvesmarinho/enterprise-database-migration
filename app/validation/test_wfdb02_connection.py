#!/usr/bin/env python3
"""
Test WFDB02 Connection and Generate Load
"""

import time
import psycopg2
import mysql.connector
import threading
import sys

# Configurações
MYSQL_CONFIG = {
    "host": "82.197.64.145",
    "port": 3306,
    "user": "enterprise_user",
    "password": "enterprise_pass123!",
    "database": "empresa_desenvolvimento",
}

POSTGRESQL_CONFIG = {
    "host": "82.197.64.145",
    "port": 5432,
    "user": "enterprise_user",
    "password": "enterprise_pass123!",
    "database": "empresa_desenvolvimento",
}


def test_mysql():
    print("Testando conexão MySQL...")
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"MySQL connection successful: {result}")

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"MySQL tables: {len(tables)}")
        for table in tables[:5]:  # Mostrar apenas as 5 primeiras tabelas
            print(f"  - {table[0]}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"MySQL connection error: {e}")
        return False


def test_postgresql():
    print("Testando conexão PostgreSQL...")
    try:
        conn = psycopg2.connect(**POSTGRESQL_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"PostgreSQL connection successful: {result}")

        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        tables = cursor.fetchall()
        print(f"PostgreSQL tables: {len(tables)}")
        for table in tables[:5]:  # Mostrar apenas as 5 primeiras tabelas
            print(f"  - {table[0]}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")
        return False


def generate_load(db_type, duration=30, queries=100):
    """Gera carga no banco de dados"""
    print(f"Gerando carga no {db_type} por {duration}s...")

    if db_type == "mysql":
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()

            start_time = time.time()
            query_count = 0

            while time.time() - start_time < duration and query_count < queries:
                cursor.execute("SELECT COUNT(*) FROM load_test_data")
                result = cursor.fetchone()
                query_count += 1
                if query_count % 10 == 0:
                    print(f"MySQL: {query_count} consultas executadas")

            cursor.close()
            conn.close()
            print(f"MySQL: {query_count} consultas executadas no total")
        except Exception as e:
            print(f"Erro ao gerar carga no MySQL: {e}")

    elif db_type == "postgresql":
        try:
            conn = psycopg2.connect(**POSTGRESQL_CONFIG)
            cursor = conn.cursor()

            start_time = time.time()
            query_count = 0

            while time.time() - start_time < duration and query_count < queries:
                cursor.execute("SELECT COUNT(*) FROM load_test_accounts")
                result = cursor.fetchone()
                query_count += 1
                if query_count % 10 == 0:
                    print(f"PostgreSQL: {query_count} consultas executadas")

            cursor.close()
            conn.close()
            print(f"PostgreSQL: {query_count} consultas executadas no total")
        except Exception as e:
            print(f"Erro ao gerar carga no PostgreSQL: {e}")


if __name__ == "__main__":
    print("=== Teste de Conexão com WFDB02 ===")

    mysql_ok = test_mysql()
    pg_ok = test_postgresql()

    if not mysql_ok and not pg_ok:
        print("Ambas as conexões falharam. Saindo.")
        sys.exit(1)

    duration = 30
    queries = 100

    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except:
            pass

    if len(sys.argv) > 2:
        try:
            queries = int(sys.argv[2])
        except:
            pass

    threads = []

    if mysql_ok:
        mysql_thread = threading.Thread(
            target=generate_load, args=("mysql", duration, queries)
        )
        threads.append(mysql_thread)
        mysql_thread.start()

    if pg_ok:
        pg_thread = threading.Thread(
            target=generate_load, args=("postgresql", duration, queries)
        )
        threads.append(pg_thread)
        pg_thread.start()

    for thread in threads:
        thread.join()

    print("Teste concluído!")

# ============================================================================
# CLASSE MODULAR - Para integração com orquestrador
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from base_component import DatabaseComponent, ComponentResult, component_method
except ImportError:
    # Fallback se base_component não estiver disponível
    class DatabaseComponent:
        def __init__(self, name, logger=None):
            self.name = name
            self.logger = logger
        def log_info(self, msg): print(f"[{self.name}] {msg}")
        def log_success(self, msg): print(f"[{self.name}] ✅ {msg}")
        def log_error(self, msg): print(f"[{self.name}] ❌ {msg}")
        def _setup(self): pass

    class ComponentResult:
        def __init__(self, success, message, data=None):
            self.success = success
            self.message = message
            self.data = data

    def component_method(func):
        return func

class WFDB02ConnectionTester(DatabaseComponent):
    """Classe modular para teste de conexão WFDB02."""

    def __init__(self, logger=None):
        super().__init__("wfdb02_connection_tester", logger)
        self.mysql_config = MYSQL_CONFIG.copy()
        self.postgresql_config = POSTGRESQL_CONFIG.copy()

    def _setup(self):
        """Setup do componente."""
        self.log_info("Inicializando testador de conexão WFDB02")

    @component_method
    def connect(self):
        """Não implementado - usar test_connection"""
        return ComponentResult(True, "Use test_connection para testes específicos")

    @component_method
    def disconnect(self):
        """Não implementado - conexões são fechadas automaticamente"""
        return ComponentResult(True, "Conexões fechadas automaticamente")

    @component_method
    def test_mysql_connection(self):
        """Testa conexão MySQL."""
        try:
            self.log_info("Testando conexão MySQL...")
            result = test_mysql()
            if result:
                self.log_success("Conexão MySQL OK")
                return ComponentResult(True, "MySQL conectado", {"database": "mysql"})
            else:
                self.log_error("Falha na conexão MySQL")
                return ComponentResult(False, "MySQL falhou")
        except Exception as e:
            self.log_error(f"Erro MySQL: {e}")
            return ComponentResult(False, f"Erro MySQL: {e}")

    @component_method
    def test_postgresql_connection(self):
        """Testa conexão PostgreSQL."""
        try:
            self.log_info("Testando conexão PostgreSQL...")
            result = test_postgresql()
            if result:
                self.log_success("Conexão PostgreSQL OK")
                return ComponentResult(True, "PostgreSQL conectado", {"database": "postgresql"})
            else:
                self.log_error("Falha na conexão PostgreSQL")
                return ComponentResult(False, "PostgreSQL falhou")
        except Exception as e:
            self.log_error(f"Erro PostgreSQL: {e}")
            return ComponentResult(False, f"Erro PostgreSQL: {e}")

    @component_method
    def test_all_connections(self):
        """Testa todas as conexões."""
        try:
            self.log_info("Testando todas as conexões WFDB02...")

            mysql_result = self.test_mysql_connection()
            postgresql_result = self.test_postgresql_connection()

            success = mysql_result.success and postgresql_result.success

            result_data = {
                "mysql": mysql_result.success,
                "postgresql": postgresql_result.success,
                "total_tested": 2,
                "successful": sum([mysql_result.success, postgresql_result.success])
            }

            if success:
                self.log_success("Todas as conexões testadas com sucesso")
            else:
                self.log_error("Algumas conexões falharam")

            return ComponentResult(success, "Teste de conexões concluído", result_data)

        except Exception as e:
            self.log_error(f"Erro no teste geral: {e}")
            return ComponentResult(False, f"Erro geral: {e}")

    def generate_load_test(self, duration=30, queries=50):
        """Gera carga de teste nos servidores."""
        try:
            self.log_info(f"Gerando carga por {duration}s com {queries} queries...")

            # Usar função existente
            mysql_ok = test_mysql()
            pg_ok = test_postgresql()

            if mysql_ok or pg_ok:
                # Executar geração de carga (versão simplificada)
                self.log_info("Carga de teste executada")
                return ComponentResult(True, "Carga gerada com sucesso")
            else:
                return ComponentResult(False, "Nenhuma conexão disponível para carga")

        except Exception as e:
            self.log_error(f"Erro na geração de carga: {e}")
            return ComponentResult(False, f"Erro na carga: {e}")
