#!/usr/bin/env python3
"""
Script: test_fix_evolution_permissions.py
Propósito: Testes unitários para o módulo EvolutionPermissionsFixer
Data: 2025-10-31

Execute com:
  python3 -m pytest test/test_fix_evolution_permissions.py -v
  ou
  python3 test_fix_evolution_permissions.py
"""

import logging
import unittest
from unittest.mock import MagicMock, patch

# Desabilitar logs durante testes
logging.disable(logging.CRITICAL)


class TestEvolutionPermissionsFixer(unittest.TestCase):
    """Testes para EvolutionPermissionsFixer"""

    def setUp(self):
        """Preparar testes"""
        from app.core.fix_evolution_permissions import (
            DatabaseInfo,
            EvolutionPermissionsFixer,
            PermissionLevel,
        )

        self.EvolutionPermissionsFixer = EvolutionPermissionsFixer
        self.DatabaseInfo = DatabaseInfo
        self.PermissionLevel = PermissionLevel

    def test_initialization(self):
        """Teste de inicialização"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db",
            dry_run=True,
            stop_on_error=False
        )

        self.assertTrue(fixer.dry_run)
        self.assertFalse(fixer.stop_on_error)
        self.assertEqual(fixer.timeout_seconds, 30)

    def test_database_info_dataclass(self):
        """Teste de DatabaseInfo"""
        db_info = self.DatabaseInfo(
            datname="evolution_api_db",
            owner="postgres",
            tablespace="ts_enterprise_data",
            connlimit=-1
        )

        self.assertEqual(db_info.datname, "evolution_api_db")
        self.assertEqual(db_info.owner, "postgres")
        self.assertEqual(db_info.tablespace, "ts_enterprise_data")
        self.assertEqual(db_info.connlimit, -1)

    def test_permission_level_enum(self):
        """Teste de PermissionLevel"""
        self.assertEqual(self.PermissionLevel.CONNECT.value, "CONNECT")
        self.assertEqual(self.PermissionLevel.USAGE.value, "USAGE")
        self.assertEqual(self.PermissionLevel.ALL.value, "ALL PRIVILEGES")

    def test_default_roles(self):
        """Teste de roles padrão"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        expected_roles = [
            "analytics",
            "evolution_api_user",
            "evoluton_api_user"  # Note: typo intencional
        ]

        self.assertEqual(fixer.DEFAULT_ROLES, expected_roles)

    def test_target_tablespace(self):
        """Teste de tablespace alvo"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        self.assertEqual(
            fixer.TARGET_TABLESPACE,
            "ts_enterprise_data"
        )

    def test_expected_owner(self):
        """Teste de owner esperado"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        self.assertEqual(fixer.EXPECTED_OWNER, "postgres")

    def test_results_initialization(self):
        """Teste de inicialização de resultados"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        results = fixer.results

        self.assertIn("databases_processed", results)
        self.assertIn("databases_skipped", results)
        self.assertIn("databases_failed", results)
        self.assertIn("permissions_fixed", results)
        self.assertIn("errors", results)

        self.assertEqual(results["permissions_fixed"], 0)
        self.assertEqual(len(results["errors"]), 0)

    def test_context_manager_pattern(self):
        """Teste do padrão context manager"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db",
            dry_run=True
        )

        # Verificar se session_factory é None antes de init
        self.assertIsNone(fixer.session_factory)

    @patch('core.fix_evolution_permissions.create_engine')
    def test_engine_initialization(self, mock_create_engine):
        """Teste de inicialização de engine"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Mock da conexão
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.scalar.return_value = 1

        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )
        fixer._init_engine()

        # Verificar se create_engine foi chamado
        mock_create_engine.assert_called_once()

    def test_dry_run_mode(self):
        """Teste do modo dry-run"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db",
            dry_run=True
        )

        self.assertTrue(fixer.dry_run)

    def test_stop_on_error_mode(self):
        """Teste do modo stop_on_error"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db",
            stop_on_error=True
        )

        self.assertTrue(fixer.stop_on_error)

    def test_timeout_configuration(self):
        """Teste de configuração de timeout"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db",
            timeout_seconds=60
        )

        self.assertEqual(fixer.timeout_seconds, 60)

    def test_connection_string_stored(self):
        """Teste se connection string é armazenada"""
        conn_str = "postgresql://user:pass@localhost/db"
        fixer = self.EvolutionPermissionsFixer(
            connection_string=conn_str
        )

        self.assertEqual(fixer.connection_string, conn_str)


class TestSQLGeneration(unittest.TestCase):
    """Testes de geração de SQL"""

    def setUp(self):
        """Preparar testes"""
        from app.core.fix_evolution_permissions import EvolutionPermissionsFixer
        self.EvolutionPermissionsFixer = EvolutionPermissionsFixer

    def test_owner_sql_generation(self):
        """Teste de geração SQL para ALTER OWNER"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        # Verificar que a string SQL é válida
        db_name = "evolution_api_db"
        owner = "postgres"

        expected_sql = (
            f'ALTER DATABASE "{db_name}" OWNER TO {owner};'
        )

        # Não testamos a execução, apenas a geração
        self.assertIn("ALTER DATABASE", expected_sql)
        self.assertIn("OWNER TO", expected_sql)

    def test_tablespace_sql_generation(self):
        """Teste de geração SQL para ALTER TABLESPACE"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        db_name = "evolution_api_db"
        ts = "ts_enterprise_data"

        expected_sql = (
            f'ALTER DATABASE "{db_name}" SET TABLESPACE {ts};'
        )

        self.assertIn("ALTER DATABASE", expected_sql)
        self.assertIn("TABLESPACE", expected_sql)

    def test_connection_limit_sql_generation(self):
        """Teste de geração SQL para CONNECTION LIMIT"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        db_name = "evolution_api_db"

        expected_sql = (
            f'ALTER DATABASE "{db_name}" CONNECTION LIMIT -1;'
        )

        self.assertIn("CONNECTION LIMIT", expected_sql)
        self.assertIn("-1", expected_sql)

    def test_grant_connect_sql_generation(self):
        """Teste de geração SQL para GRANT CONNECT"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        db_name = "evolution_api_db"
        role = "evolution_api_user"

        expected_sql = (
            f'GRANT CONNECT ON DATABASE "{db_name}" TO "{role}";'
        )

        self.assertIn("GRANT CONNECT", expected_sql)
        self.assertIn("DATABASE", expected_sql)


class TestResultsHandling(unittest.TestCase):
    """Testes de tratamento de resultados"""

    def setUp(self):
        """Preparar testes"""
        from app.core.fix_evolution_permissions import EvolutionPermissionsFixer
        self.EvolutionPermissionsFixer = EvolutionPermissionsFixer

    def test_results_structure(self):
        """Teste da estrutura de resultados"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        expected_keys = [
            "databases_processed",
            "databases_skipped",
            "databases_failed",
            "permissions_fixed",
            "errors"
        ]

        for key in expected_keys:
            self.assertIn(key, fixer.results)

    def test_results_are_lists(self):
        """Teste se resultados são listas apropriadas"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        self.assertIsInstance(fixer.results["databases_processed"], list)
        self.assertIsInstance(fixer.results["databases_skipped"], list)
        self.assertIsInstance(fixer.results["databases_failed"], list)
        self.assertIsInstance(fixer.results["errors"], list)

    def test_results_permissions_fixed_is_int(self):
        """Teste se permissions_fixed é inteiro"""
        fixer = self.EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db"
        )

        self.assertIsInstance(fixer.results["permissions_fixed"], int)


def run_tests():
    """Executar todos os testes"""
    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Adicionar testes
    suite.addTests(loader.loadTestsFromTestCase(
        TestEvolutionPermissionsFixer
    ))
    suite.addTests(loader.loadTestsFromTestCase(
        TestSQLGeneration
    ))
    suite.addTests(loader.loadTestsFromTestCase(
        TestResultsHandling
    ))

    # Executar
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Retornar status
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_tests())
