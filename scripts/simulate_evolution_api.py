#!/usr/bin/env python3
"""
Simulador: Evolution API - Buscar Instâncias
Propósito: Simular o acesso à API Evolution para buscar instâncias
           e validar as configurações de acesso (PostgreSQL)

Uso:
  python3 simulate_evolution_api.py --server wfdb02
  python3 simulate_evolution_api.py --server wfdb02 --validate-all
  python3 simulate_evolution_api.py --server wfdb02 --list-users
  python3 simulate_evolution_api.py --server wfdb02 --check-permissions
  python3 simulate_evolution_api.py --server wfdb02 --report report.json
"""

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Configuração de banco de dados"""
    host: str
    port: int
    user: str
    password: str
    database: str
    sslmode: str = 'disable'

    def to_connection_string(self) -> str:
        """Converte config para string de conexão psycopg2"""
        return (
            f"host={self.host} port={self.port} user={self.user} "
            f"password={self.password} dbname={self.database} "
            f"sslmode={self.sslmode}"
        )


@dataclass
class InstanceData:
    """Dados de uma instância Evolution"""
    id: str
    name: str
    number: Optional[str]
    status: str
    token: str
    integration: str
    client_name: str
    created_at: str
    updated_at: str


@dataclass
class AccessValidation:
    """Resultado de validação de acesso"""
    test_name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0


class EvolutionAPISimulator:
    """Simula acesso à Evolution API buscando instâncias"""

    def __init__(
        self,
        db_config: DatabaseConfig,
        verbose: bool = False
    ):
        self.db_config = db_config
        self.verbose = verbose
        self.connection = None
        self.validation_results: List[AccessValidation] = []

        if verbose:
            logger.setLevel(logging.DEBUG)

    def connect(self) -> bool:
        """Conecta ao banco de dados"""
        try:
            logger.info(
                "Conectando em %s:%s/%s...",
                self.db_config.host,
                self.db_config.port,
                self.db_config.database
            )

            self.connection = psycopg2.connect(
                self.db_config.to_connection_string()
            )
            logger.info("✅ Conexão estabelecida com sucesso")
            return True

        except psycopg2.OperationalError as e:
            logger.error("❌ Erro ao conectar: %s", e)
            return False
        except psycopg2.Error as e:
            logger.error("❌ Erro inesperado: %s", e)
            return False

    def disconnect(self):
        """Desconecta do banco de dados"""
        if self.connection:
            self.connection.close()
            logger.debug("Conexão fechada")

    def execute_query(
        self,
        query: str,
        params: tuple = ()
    ) -> Optional[List[Dict[str, Any]]]:
        """Executa query no banco de dados"""
        try:
            cursor = self.connection.cursor(
                cursor_factory=RealDictCursor
            )
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results

        except psycopg2.ProgrammingError as e:
            logger.error("❌ Erro SQL: %s", e)
            return None
        except psycopg2.Error as e:
            logger.error("❌ Erro ao executar query: %s", e)
            return None

    def fetch_instances(self) -> Optional[List[InstanceData]]:
        """
        Simula: GET /instance/fetchInstances
        Query real da Evolution API
        """
        import time
        start_time = time.time()

        logger.info("\n📊 [SIMULAÇÃO] Buscando Instâncias Evolution...")
        logger.info("Equivalente a: GET /instance/fetchInstances")

        query = """
        SELECT
            id,
            name,
            number,
            "connectionStatus" as status,
            token,
            integration,
            "clientName" as client_name,
            "createdAt" as created_at,
            "updatedAt" as updated_at
        FROM "Instance"
        ORDER BY "createdAt" DESC;
        """

        logger.debug("SQL: %s", query)

        results = self.execute_query(query)
        duration_ms = (time.time() - start_time) * 1000

        if results is None:
            return None

        instances = [
            InstanceData(
                id=row['id'],
                name=row['name'],
                number=row.get('number'),
                status=row['status'],
                token=row['token'],
                integration=row['integration'],
                client_name=row['client_name'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in results
        ]

        logger.info(
            "✅ %d instâncias encontradas (%.2fms)",
            len(instances),
            duration_ms
        )

        return instances

    def validate_user_permissions(self) -> bool:
        """
        Valida se usuário conectado tem permissões necessárias
        """
        import time
        start_time = time.time()

        logger.info("\n🔐 [VALIDAÇÃO] Permissões do Usuário...")

        # Test 1: Pode ler tabela Instance?
        test1_query = "SELECT COUNT(*) as count FROM \"Instance\";"
        result1 = self.execute_query(test1_query)

        if result1 is None:
            self._add_validation(
                "SELECT Instance",
                False,
                "Usuário NÃO tem permissão SELECT em Instance"
            )
            return False

        self._add_validation(
            "SELECT Instance",
            True,
            f"✅ Permissão SELECT confirmada ({result1[0]['count']} rows)",
            {'row_count': result1[0]['count']},
            (time.time() - start_time) * 1000
        )

        # Test 2: Pode ler colunas sensíveis (token)?
        test2_query = (
            'SELECT COUNT(*) as count FROM "Instance" '
            'WHERE token IS NOT NULL;'
        )
        result2 = self.execute_query(test2_query)

        if result2 is None:
            self._add_validation(
                "SELECT Instance (token)",
                False,
                "Usuário NÃO consegue ler coluna 'token'"
            )
            return False

        self._add_validation(
            "SELECT Instance (token)",
            True,
            f"✅ Acesso a dados sensíveis confirmado ({result2[0]['count']} "
            f"instances com token)",
            {'instances_with_token': result2[0]['count']},
            (time.time() - start_time) * 1000
        )

        # Test 3: Pode ler schema?
        test3_query = (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' LIMIT 1;"
        )
        result3 = self.execute_query(test3_query)

        if result3 is None:
            self._add_validation(
                "SELECT information_schema",
                False,
                "Usuário NÃO tem acesso ao information_schema"
            )
            return False

        self._add_validation(
            "SELECT information_schema",
            True,
            "✅ Acesso ao schema confirmado",
            {},
            (time.time() - start_time) * 1000
        )

        return True

    def inspect_schema(self, table_name: str) -> bool:
        """Inspeciona schema de uma tabela"""
        import time
        start_time = time.time()

        logger.info("\n📋 [INSPEÇÃO] Schema da Tabela: %s", table_name)

        query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            ordinal_position
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
        """

        try:
            if not self.connection:
                logger.error("❌ Sem conexão com banco de dados")
                return False

            cursor = self.connection.cursor(
                cursor_factory=RealDictCursor
            )
            cursor.execute(query, (table_name,))
            results = cursor.fetchall()
            cursor.close()

            if not results:
                logger.warning(
                    "⚠️ Tabela '%s' não encontrada ou sem colunas",
                    table_name
                )
                return False

            logger.info(
                "✅ Tabela '%s' encontrada com %d colunas",
                table_name,
                len(results)
            )
            logger.info("\n")

            # Exibir colunas em formato tabular
            for row in results:
                is_null = row['is_nullable'] == 'YES'
                nullable = "NULL" if is_null else "NOT NULL"
                default = (
                    f" DEFAULT {row['column_default']}"
                    if row['column_default'] else ""
                )
                logger.info(
                    "  %2d. %-20s %-15s %8s%s",
                    row['ordinal_position'],
                    row['column_name'],
                    row['data_type'],
                    nullable,
                    default
                )

            duration_ms = (time.time() - start_time) * 1000
            logger.info("\n✅ Inspeção concluída em %.2fms", duration_ms)
            return True

        except Exception as e:
            logger.error("❌ Erro ao inspecionar schema: %s", str(e))
            return False

    def get_table_statistics(self) -> Optional[Dict[str, Any]]:
        """Obtém estatísticas das tabelas do Evolution"""
        logger.info("\n📈 [ESTATÍSTICAS] Tabelas Evolution...")

        query = """
        SELECT
            table_name,
            row_count,
            pg_size_pretty(total_bytes) as total_size
        FROM (
            SELECT
                schemaname,
                tablename as table_name,
                n_live_tup as row_count,
                pg_total_relation_size(
                    schemaname || '.' || tablename
                ) as total_bytes
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY total_bytes DESC
            LIMIT 10
        ) stats;
        """

        logger.debug("SQL: %s", query)
        results = self.execute_query(query)

        if results is None:
            logger.error("❌ Não conseguiu obter estatísticas")
            return None

        stats = {
            'tables': [
                {
                    'name': row['table_name'],
                    'rows': row['row_count'],
                    'size': row['total_size']
                }
                for row in results
            ]
        }

        logger.info("✅ Estatísticas obtidas:")
        for table in stats['tables']:
            logger.info(
                "  - %s: %s rows, %s",
                table['name'],
                table['rows'],
                table['size']
            )

        return stats

    def check_privileges_user(self, username: str) -> bool:
        """Verifica privilégios de um usuário específico"""
        logger.info("\n👤 [PRIVILÉGIOS] Verificando usuário: %s", username)

        # Query 1: Verificar se usuário existe
        query1 = (
            "SELECT usename FROM pg_user WHERE usename = %s;"
        )
        result1 = self.execute_query(query1, (username,))

        if not result1:
            logger.error("❌ Usuário %s NÃO existe", username)
            return False

        logger.info("✅ Usuário existe: %s", username)

        # Query 2: Listar privilégios
        query2 = """
        SELECT
            grantee,
            privilege_type,
            is_grantable
        FROM information_schema.role_table_grants
        WHERE grantee = %s
        LIMIT 20;
        """

        result2 = self.execute_query(query2, (username,))

        if result2:
            logger.info("📋 Privilégios encontrados:")
            for priv in result2:
                logger.info(
                    "  - %s on %s (grantable: %s)",
                    priv['privilege_type'],
                    priv['grantee'],
                    priv['is_grantable']
                )
        else:
            logger.warning("⚠️  Nenhum privilégio específico encontrado")

        return True

    def list_all_databases(self) -> Optional[List[Dict[str, Any]]]:
        """Lista todos os bancos de dados"""
        logger.info("\n🗄️  [BANCOS] Listando bases de dados...")

        query = """
        SELECT
            datname,
            owner,
            spcname as tablespace,
            pg_size_pretty(pg_database_size(datname)) as size
        FROM pg_database
        JOIN pg_tablespace ON pg_database.dattablespace = pg_tablespace.oid
        JOIN pg_user ON pg_database.datdba = pg_user.usesysid
        ORDER BY pg_database_size(datname) DESC;
        """

        results = self.execute_query(query)

        if results:
            logger.info("✅ Bancos de dados encontrados:")
            for db in results:
                logger.info(
                    "  - %s (owner: %s, tablespace: %s, size: %s)",
                    db['datname'],
                    db['owner'],
                    db['tablespace'],
                    db['size']
                )
        else:
            logger.error("❌ Não conseguiu listar bancos")

        return results

    def validate_all(self) -> bool:
        """Executa todas as validações"""
        logger.info("="*70)
        logger.info("🔍 SIMULAÇÃO: Evolution API - Buscar Instâncias")
        logger.info("="*70)

        # 1. Conectar
        if not self.connect():
            return False

        try:
            # 2. Validar permissões
            if not self.validate_user_permissions():
                logger.error("❌ Permissões insuficientes")
                return False

            # 3. Buscar instâncias
            instances = self.fetch_instances()
            if instances is None:
                logger.error("❌ Falha ao buscar instâncias")
                return False

            if instances:
                self._print_instances(instances)
            else:
                logger.warning("⚠️  Nenhuma instância encontrada")

            # 4. Estatísticas
            stats = self.get_table_statistics()
            if stats:
                logger.info("✅ Estatísticas obtidas com sucesso")

            # 5. Listar bancos
            dbs = self.list_all_databases()
            if dbs:
                logger.info("✅ Bancos listados com sucesso")

            return True

        finally:
            self.disconnect()

    def _print_instances(self, instances: List[InstanceData]):
        """Formata e exibe instâncias"""
        logger.info("="*70)
        logger.info("📋 INSTÂNCIAS EVOLUTION API")
        logger.info("="*70)

        for idx, inst in enumerate(instances, 1):
            logger.info("[%d] %s", idx, inst.name)
            logger.info("    ID: %s", inst.id)
            logger.info("    Status: %s", inst.status)
            logger.info("    Integration: %s", inst.integration)
            logger.info("    Number: %s", inst.number or "N/A")
            logger.info("    Token: %s...", inst.token[:20])
            logger.info("    Created: %s", inst.created_at)

    def _add_validation(
        self,
        test_name: str,
        passed: bool,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0
    ):
        """Adiciona resultado de validação"""
        validation = AccessValidation(
            test_name=test_name,
            passed=passed,
            message=message,
            details=details or {},
            duration_ms=duration_ms
        )
        self.validation_results.append(validation)

        status = "✅" if passed else "❌"
        logger.info(
            "%s %s: %s (%.2fms)",
            status,
            test_name,
            message,
            duration_ms
        )

    def print_summary(self):
        """Exibe resumo de validações"""
        logger.info("="*70)
        logger.info("📊 RESUMO DE VALIDAÇÕES")
        logger.info("="*70)

        passed = sum(1 for v in self.validation_results if v.passed)
        total = len(self.validation_results)

        logger.info("Total: %d/%d testes passaram", passed, total)
        if total > 0:
            logger.info("Taxa de sucesso: %.1f%%", (passed/total*100))
        else:
            msg = "Nenhum teste executado (servidor nao acessivel)"
            logger.warning("⚠️ %s", msg)
        logger.info("")

        for validation in self.validation_results:
            status = "✅" if validation.passed else "❌"
            logger.info(
                "%s %-30s %s (%.2fms)",
                status,
                validation.test_name,
                validation.message,
                validation.duration_ms
            )

    def save_report(self, filepath: str):
        """Salva relatório em JSON"""
        logger.info("\n💾 Salvando relatório: %s", filepath)

        report = {
            'timestamp': datetime.now().isoformat(),
            'database': {
                'host': self.db_config.host,
                'port': self.db_config.port,
                'database': self.db_config.database,
                'user': self.db_config.user
            },
            'validations': [
                {
                    'test': v.test_name,
                    'passed': v.passed,
                    'message': v.message,
                    'details': v.details,
                    'duration_ms': v.duration_ms
                }
                for v in self.validation_results
            ],
            'summary': {
                'total': len(self.validation_results),
                'passed': sum(
                    1 for v in self.validation_results if v.passed
                ),
                'failed': sum(
                    1 for v in self.validation_results if not v.passed
                )
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("✅ Relatório salvo")


def load_config(server_name: str) -> Optional[DatabaseConfig]:
    """Carrega configuração do servidor"""
    config_files = {
        'wf004': 'secrets/postgresql_source_config.json',
        'source': 'secrets/postgresql_source_config.json',
        'wfdb02': 'secrets/postgresql_destination_config.json',
        'destination': 'secrets/postgresql_destination_config.json',
    }

    config_file = config_files.get(server_name.lower())
    if not config_file:
        logger.error("Servidor desconhecido: %s", server_name)
        return None

    config_path = Path(config_file)
    if not config_path.exists():
        logger.error("Arquivo de configuração não encontrado: %s", config_file)
        return None

    try:
        with open(config_path, encoding='utf-8') as f:
            data = json.load(f)

        # Extrair credenciais da estrutura do arquivo
        # Suporta dois formatos:
        # 1. Novo formato (nested): server.host, authentication.user
        # 2. Formato legado (flat): host, user

        # Tentar formato aninhado primeiro
        if 'server' in data and 'authentication' in data:
            host = data['server'].get('host', 'localhost')
            port = data['server'].get('port_direct') or data['server'].get(
                'port', 5432
            )
            user = data['authentication'].get('user', 'postgres')
            password = data['authentication'].get('password', '')
        else:
            # Fallback para formato legado
            host = data.get('host', 'localhost')
            port = data.get('port', 5432)
            user = data.get('user', 'postgres')
            password = data.get('password', '')

        # Database pode estar em várias localizações
        # Prioridade: server.database > database > databases.default
        if 'server' in data and 'database' in data['server']:
            database = data['server'].get('database')
        elif 'databases' in data:
            database = data['databases'].get('default', 'postgres')
        elif 'database' in data:
            database = data.get('database', 'postgres')
        else:
            # Se não encontrar, usar 'postgres' (sempre existe)
            database = 'postgres'

        logger.debug(
            "Config carregada: host=%s, port=%s, user=%s, database=%s",
            host, port, user, database
        )

        return DatabaseConfig(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            sslmode=data['server'].get('ssl_mode', 'prefer')
            if 'server' in data else 'prefer'
        )

    except (json.JSONDecodeError, IOError) as e:
        logger.error("Erro ao carregar configuração: %s", e)
        return None


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Simulador: Evolution API - Buscar Instâncias'
    )

    parser.add_argument(
        '--server',
        required=True,
        choices=['wf004', 'source', 'wfdb02', 'destination'],
        help='Servidor PostgreSQL'
    )

    parser.add_argument(
        '--database',
        type=str,
        default=None,
        help='Nome do banco de dados (padrão: evolution_api_wea001_db)'
    )

    parser.add_argument(
        '--validate-all',
        action='store_true',
        help='Executar todas as validações'
    )

    parser.add_argument(
        '--list-users',
        action='store_true',
        help='Listar usuários do banco'
    )

    parser.add_argument(
        '--check-permissions',
        action='store_true',
        help='Verificar permissões do usuário atual'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verbose (debug)'
    )

    parser.add_argument(
        '--report',
        type=str,
        help='Salvar relatório em JSON'
    )

    parser.add_argument(
        '--inspect-schema',
        type=str,
        metavar='TABLE_NAME',
        help='Inspecionar schema de uma tabela (ex: Instance)'
    )

    args = parser.parse_args()

    # Carregar configuração
    db_config = load_config(args.server)
    if not db_config:
        logger.error(
            "Falha ao carregar configuração do servidor: %s", args.server
        )
        logger.error(
            "Verifique se o arquivo secrets/postgresql_%s_config.json "
            "existe e está bem formatado",
            'source' if args.server in ['wf004', 'source'] else 'destination'
        )
        sys.exit(1)

    # Sobrescrever banco de dados se fornecido como parâmetro
    if args.database:
        db_config.database = args.database
        logger.info("Usando banco de dados: %s", args.database)
    else:
        logger.info("Usando banco de dados padrão: %s", db_config.database)

    # Criar simulador
    simulator = EvolutionAPISimulator(db_config, args.verbose)

    # Executar operações
    if args.validate_all:
        success = simulator.validate_all()
    elif args.list_users:
        if simulator.connect():
            simulator.list_all_databases()
            simulator.disconnect()
        success = True
    elif args.check_permissions:
        if simulator.connect():
            simulator.validate_user_permissions()
            simulator.print_summary()
            simulator.disconnect()
        success = True
    elif args.inspect_schema:
        if simulator.connect():
            simulator.inspect_schema(args.inspect_schema)
            simulator.disconnect()
        success = True
    else:
        # Operação padrão: buscar instâncias
        if simulator.connect():
            simulator.validate_user_permissions()
            simulator.fetch_instances()
            simulator.disconnect()
        success = True

    # Salvar relatório se solicitado
    if args.report:
        simulator.save_report(args.report)

    simulator.print_summary()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
