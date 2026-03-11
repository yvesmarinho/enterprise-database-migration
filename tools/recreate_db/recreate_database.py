#!/usr/bin/env python3
"""
Módulo para recriar bancos de dados MySQL/PostgreSQL

Este módulo permite:
- Conectar a bancos MySQL ou PostgreSQL
- Coletar metadados de criação da base (charset, encoding, grants)
- Coletar permissões (grants) dos usuários
- Apagar a base de dados existente (SEMPRE termina conexões ativas)
- Recriar a base vazia com os mesmos parâmetros

Uso:
    python recreate_database.py --config secrets/mysql_config.json --database nome_db
    python recreate_database.py --config secrets/postgresql_source_config.json --database nome_db
    python recreate_database.py -c secrets/wfdb02_postgres.json -d chatwoot_dev_db --verbose
"""

import json
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseRecreator:
    """Classe para gerenciar recriação de bancos de dados"""

    def __init__(self, config_path: str, database_name: str):
        """
        Inicializa o recreador de banco de dados

        Args:
            config_path: Caminho para o arquivo JSON de configuração
            database_name: Nome do banco de dados a ser recriado
        """
        self.config_path = Path(config_path)
        self.database_name = database_name
        self.config = self._load_config()
        self.db_type = self._detect_db_type()
        self.connection = None
        self.metadata = {}

    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo JSON"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        logger.info(f"Configuração carregada de: {self.config_path}")
        return config

    def _detect_db_type(self) -> str:
        """Detecta o tipo de banco de dados baseado na configuração"""
        # Verifica se há indicação de porta típica
        if 'source' in self.config:
            port = self.config['source'].get('port', 0)
        elif 'server' in self.config:
            port = self.config['server'].get('port', 0)
        elif 'destination' in self.config:
            port = self.config['destination'].get('port', 0)
        else:
            raise ValueError("Estrutura de configuração não reconhecida")

        if port == 3306:
            logger.info("Tipo de banco detectado: MySQL")
            return 'mysql'
        elif port == 5432:
            logger.info("Tipo de banco detectado: PostgreSQL")
            return 'postgresql'
        else:
            raise ValueError(f"Porta {port} não corresponde a MySQL (3306) ou PostgreSQL (5432)")

    def _get_connection_params(self) -> Dict[str, Any]:
        """Extrai parâmetros de conexão baseado na estrutura do JSON"""
        params = {}

        # Tenta diferentes estruturas de configuração
        if 'source' in self.config:
            conn_info = self.config['source']
        elif 'server' in self.config:
            conn_info = self.config['server']
            if 'authentication' in self.config:
                conn_info.update(self.config['authentication'])
        elif 'destination' in self.config:
            conn_info = self.config['destination']
        else:
            raise ValueError("Estrutura de configuração não reconhecida")

        params['host'] = conn_info.get('host')
        params['port'] = conn_info.get('port')
        params['user'] = conn_info.get('user')
        params['password'] = conn_info.get('password')

        if self.db_type == 'mysql':
            params['charset'] = conn_info.get('charset', 'utf8mb4')

        return params

    def connect(self) -> None:
        """Estabelece conexão com o banco de dados"""
        params = self._get_connection_params()

        try:
            if self.db_type == 'mysql':
                import pymysql
                self.connection = pymysql.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['user'],
                    password=params['password'],
                    charset=params['charset'],
                    cursorclass=pymysql.cursors.DictCursor
                )
                logger.info(f"Conectado ao MySQL em {params['host']}:{params['port']}")

            elif self.db_type == 'postgresql':
                import psycopg2
                from psycopg2.extras import RealDictCursor
                self.connection = psycopg2.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['user'],
                    password=params['password'],
                    database='postgres',  # Conecta ao banco padrão primeiro
                    cursor_factory=RealDictCursor
                )
                self.connection.autocommit = True
                logger.info(f"Conectado ao PostgreSQL em {params['host']}:{params['port']}")

        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def collect_metadata(self) -> Dict[str, Any]:
        """Coleta metadados da base de dados antes de apagar"""
        logger.info(f"Coletando metadados da base '{self.database_name}'...")

        try:
            cursor = self.connection.cursor()

            if self.db_type == 'mysql':
                metadata = self._collect_mysql_metadata(cursor)
            elif self.db_type == 'postgresql':
                metadata = self._collect_postgresql_metadata(cursor)

            self.metadata = metadata
            logger.info(f"Metadados coletados: {json.dumps(metadata, indent=2, default=str)}")
            return metadata

        except Exception as e:
            logger.error(f"Erro ao coletar metadados: {e}")
            raise
        finally:
            cursor.close()

    def _collect_mysql_metadata(self, cursor) -> Dict[str, Any]:
        """Coleta metadados específicos do MySQL"""
        # Verifica se o banco existe
        cursor.execute(
            "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
            (self.database_name,)
        )
        exists = cursor.fetchone()

        if not exists:
            logger.warning(f"Banco de dados '{self.database_name}' não existe")
            return {
                'database_name': self.database_name,
                'exists': False,
                'type': 'mysql',
                'timestamp': datetime.now().isoformat()
            }

        # Coleta informações do banco
        cursor.execute(
            """
            SELECT
                SCHEMA_NAME,
                DEFAULT_CHARACTER_SET_NAME,
                DEFAULT_COLLATION_NAME
            FROM information_schema.SCHEMATA
            WHERE SCHEMA_NAME = %s
            """,
            (self.database_name,)
        )
        db_info = cursor.fetchone()

        # Conta tabelas
        cursor.execute(
            "SELECT COUNT(*) as table_count FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s",
            (self.database_name,)
        )
        table_count = cursor.fetchone()['table_count']

        # Coleta grants/permissões
        grants = self._collect_mysql_grants(cursor)

        return {
            'database_name': self.database_name,
            'exists': True,
            'type': 'mysql',
            'charset': db_info['DEFAULT_CHARACTER_SET_NAME'],
            'collation': db_info['DEFAULT_COLLATION_NAME'],
            'table_count': table_count,
            'grants': grants,
            'timestamp': datetime.now().isoformat()
        }

    def _collect_postgresql_metadata(self, cursor) -> Dict[str, Any]:
        """Coleta metadados específicos do PostgreSQL"""
        # Verifica se o banco existe
        cursor.execute(
            "SELECT datname FROM pg_database WHERE datname = %s",
            (self.database_name,)
        )
        exists = cursor.fetchone()

        if not exists:
            logger.warning(f"Banco de dados '{self.database_name}' não existe")
            return {
                'database_name': self.database_name,
                'exists': False,
                'type': 'postgresql',
                'timestamp': datetime.now().isoformat()
            }

        # Coleta informações do banco
        cursor.execute(
            """
            SELECT
                datname,
                pg_encoding_to_char(encoding) as encoding,
                datcollate,
                datctype,
                pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database
            WHERE datname = %s
            """,
            (self.database_name,)
        )
        db_info = cursor.fetchone()

        # Conecta ao banco específico para contar tabelas
        cursor.execute(
            """
            SELECT COUNT(*) as table_count
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            """
        )
        table_count = cursor.fetchone()

        # Coleta grants/permissões
        grants = self._collect_postgresql_grants(cursor)

        return {
            'database_name': self.database_name,
            'exists': True,
            'type': 'postgresql',
            'encoding': db_info['encoding'],
            'collate': db_info['datcollate'],
            'ctype': db_info['datctype'],
            'size': db_info['size'],
            'table_count': table_count['table_count'] if table_count else 0,
            'grants': grants,
            'timestamp': datetime.now().isoformat()
        }

    def _collect_mysql_grants(self, cursor) -> dict:
        """Coleta grants/permissões do MySQL para o banco de dados"""
        try:
            grants_info = {
                'database': self.database_name,
                'schema_privileges': [],
                'table_privileges': [],
                'column_privileges': [],
                'total_grants': 0
            }

            # 1. Coleta grants a nível de SCHEMA (banco de dados)
            cursor.execute(
                """
                SELECT
                    GRANTEE,
                    PRIVILEGE_TYPE,
                    IS_GRANTABLE
                FROM information_schema.SCHEMA_PRIVILEGES
                WHERE TABLE_SCHEMA = %s
                ORDER BY GRANTEE, PRIVILEGE_TYPE
                """,
                (self.database_name,)
            )
            schema_grants = cursor.fetchall()
            grants_info['schema_privileges'] = [dict(g) for g in schema_grants] if schema_grants else []

            # 2. Coleta grants a nível de TABELA
            cursor.execute(
                """
                SELECT
                    GRANTEE,
                    TABLE_NAME,
                    PRIVILEGE_TYPE,
                    IS_GRANTABLE
                FROM information_schema.TABLE_PRIVILEGES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, GRANTEE, PRIVILEGE_TYPE
                LIMIT 100
                """,
                (self.database_name,)
            )
            table_grants = cursor.fetchall()

            # Agrupa grants por tabela
            table_grants_dict = {}
            for tg in table_grants:
                table_name = tg['TABLE_NAME']
                if table_name not in table_grants_dict:
                    table_grants_dict[table_name] = []
                table_grants_dict[table_name].append({
                    'grantee': tg['GRANTEE'],
                    'privilege_type': tg['PRIVILEGE_TYPE'],
                    'is_grantable': tg['IS_GRANTABLE']
                })

            for table_name, privs in table_grants_dict.items():
                grants_info['table_privileges'].append({
                    'table_name': table_name,
                    'privileges': privs
                })

            # 3. Coleta grants a nível de COLUNA (se houver)
            cursor.execute(
                """
                SELECT
                    GRANTEE,
                    TABLE_NAME,
                    COLUMN_NAME,
                    PRIVILEGE_TYPE,
                    IS_GRANTABLE
                FROM information_schema.COLUMN_PRIVILEGES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, COLUMN_NAME, GRANTEE
                LIMIT 50
                """,
                (self.database_name,)
            )
            column_grants = cursor.fetchall()
            grants_info['column_privileges'] = [dict(g) for g in column_grants] if column_grants else []

            # Calcula total de grants
            grants_info['total_grants'] = (
                len(grants_info['schema_privileges']) +
                sum(len(t['privileges']) for t in grants_info['table_privileges']) +
                len(grants_info['column_privileges'])
            )

            logger.info(f"Coletados {grants_info['total_grants']} grants do MySQL: "
                       f"schema={len(grants_info['schema_privileges'])}, "
                       f"tables={sum(len(t['privileges']) for t in grants_info['table_privileges'])}, "
                       f"columns={len(grants_info['column_privileges'])}")
            return grants_info

        except Exception as e:
            logger.warning(f"Erro ao coletar grants MySQL: {e}")
            return {
                'database': self.database_name,
                'schema_privileges': [],
                'table_privileges': [],
                'column_privileges': [],
                'total_grants': 0
            }

    def _collect_postgresql_grants(self, cursor) -> dict:
        """Coleta grants/permissões do PostgreSQL para o banco de dados"""
        try:
            # 1. Coleta informações do banco e owner
            cursor.execute(
                """
                SELECT
                    datname,
                    datacl,
                    pg_catalog.pg_get_userbyid(datdba) as owner
                FROM pg_database
                WHERE datname = %s
                """,
                (self.database_name,)
            )
            db_acl = cursor.fetchone()

            grants_info = {
                'database': db_acl['datname'] if db_acl else None,
                'owner': db_acl['owner'] if db_acl else None,
                'database_acl': db_acl['datacl'] if db_acl and db_acl['datacl'] else [],
                'schema_privileges': [],
                'table_privileges': [],
                'total_grants': 0
            }

            # 2. Conecta temporariamente ao banco específico para coletar grants detalhados
            # Salva a conexão atual
            original_connection = self.connection

            try:
                # Cria conexão temporária ao banco específico
                params = self._get_connection_params()
                import psycopg2
                from psycopg2.extras import RealDictCursor

                temp_conn = psycopg2.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['user'],
                    password=params['password'],
                    database=self.database_name,
                    cursor_factory=RealDictCursor
                )
                temp_cursor = temp_conn.cursor()

                # 2.1. Coleta grants a nível de SCHEMA
                temp_cursor.execute("""
                    SELECT
                        nspname as schema_name,
                        nspowner::regrole::text as schema_owner,
                        nspacl as schema_acl
                    FROM pg_namespace
                    WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                    ORDER BY nspname
                """)
                schema_grants = temp_cursor.fetchall()

                for sg in schema_grants:
                    grants_info['schema_privileges'].append({
                        'schema': sg['schema_name'],
                        'owner': sg['schema_owner'],
                        'acl': sg['schema_acl'] if sg['schema_acl'] else []
                    })

                # 2.2. Coleta grants a nível de TABLE/VIEW
                temp_cursor.execute("""
                    SELECT
                        schemaname,
                        tablename as object_name,
                        tableowner as object_owner,
                        'table' as object_type
                    FROM pg_tables
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')

                    UNION ALL

                    SELECT
                        schemaname,
                        viewname as object_name,
                        viewowner as object_owner,
                        'view' as object_type
                    FROM pg_views
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')

                    ORDER BY schemaname, object_name
                    LIMIT 100
                """)
                table_grants = temp_cursor.fetchall()

                for tg in table_grants:
                    # Para cada tabela/view, coleta suas permissões específicas
                    temp_cursor.execute("""
                        SELECT
                            grantee,
                            privilege_type,
                            is_grantable
                        FROM information_schema.table_privileges
                        WHERE table_schema = %s
                        AND table_name = %s
                        ORDER BY grantee, privilege_type
                    """, (tg['schemaname'], tg['object_name']))

                    privs = temp_cursor.fetchall()

                    if privs:
                        grants_info['table_privileges'].append({
                            'schema': tg['schemaname'],
                            'object_name': tg['object_name'],
                            'object_type': tg['object_type'],
                            'owner': tg['object_owner'],
                            'privileges': [dict(p) for p in privs]
                        })

                # Calcula total de grants coletados
                grants_info['total_grants'] = (
                    len(grants_info.get('database_acl', [])) +
                    len(grants_info['schema_privileges']) +
                    sum(len(t.get('privileges', [])) for t in grants_info['table_privileges'])
                )

                temp_cursor.close()
                temp_conn.close()

            except Exception as e:
                logger.warning(f"Erro ao coletar grants detalhados: {e}")
                # Se não conseguir conectar ao banco específico, mantém apenas informações básicas

            # Restaura conexão original
            self.connection = original_connection

            logger.info(f"Coletados grants do PostgreSQL: owner={grants_info['owner']}, "
                       f"schemas={len(grants_info['schema_privileges'])}, "
                       f"table_grants={len(grants_info['table_privileges'])}, "
                       f"total={grants_info['total_grants']}")
            return grants_info

        except Exception as e:
            logger.warning(f"Erro ao coletar grants PostgreSQL: {e}")
            return {
                'database': self.database_name,
                'owner': None,
                'database_acl': [],
                'schema_privileges': [],
                'table_privileges': [],
                'total_grants': 0
            }

    def drop_database(self, force: bool = True) -> bool:
        """
        Apaga o banco de dados

        Args:
            force: Se True, força a exclusão terminando conexões ativas (padrão: True)

        Returns:
            True se o banco foi apagado, False se não existia
        """
        if not self.metadata.get('exists', False):
            logger.warning(f"Banco de dados '{self.database_name}' não existe, nada a apagar")
            return False

        logger.warning(f"ATENÇÃO: Apagando banco de dados '{self.database_name}'...")

        try:
            cursor = self.connection.cursor()

            if self.db_type == 'mysql':
                # MySQL: Termina conexões se force=True
                if force:
                    try:
                        cursor.execute(
                            f"""
                            SELECT CONCAT('KILL ', id, ';') as kill_cmd
                            FROM information_schema.PROCESSLIST
                            WHERE DB = '{self.database_name}' AND id != CONNECTION_ID()
                            """
                        )
                        kill_commands = cursor.fetchall()
                        for cmd in kill_commands:
                            try:
                                cursor.execute(cmd['kill_cmd'])
                            except:
                                pass
                        if kill_commands:
                            logger.info(f"Terminadas {len(kill_commands)} conexões MySQL ativas")
                    except Exception as e:
                        logger.warning(f"Aviso ao terminar conexões MySQL: {e}")

                cursor.execute(f"DROP DATABASE IF EXISTS `{self.database_name}`")
                logger.info(f"✓ Banco MySQL '{self.database_name}' apagado com sucesso")

            elif self.db_type == 'postgresql':
                # PostgreSQL: SEMPRE termina conexões ativas
                try:
                    cursor.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{self.database_name}'
                        AND pid <> pg_backend_pid()
                    """)
                    logger.info("Conexões ativas PostgreSQL terminadas (force)")
                except Exception as e:
                    logger.warning(f"Aviso ao terminar conexões: {e}")

                cursor.execute(f'DROP DATABASE IF EXISTS "{self.database_name}"')
                logger.info(f"✓ Banco PostgreSQL '{self.database_name}' apagado com sucesso")

            cursor.close()
            return True

        except Exception as e:
            logger.error(f"Erro ao apagar banco de dados: {e}")
            raise

    def create_database(self) -> bool:
        """
        Recria o banco de dados vazio usando os metadados coletados

        Returns:
            True se o banco foi criado com sucesso
        """
        logger.info(f"Recriando banco de dados '{self.database_name}'...")

        try:
            cursor = self.connection.cursor()

            if self.db_type == 'mysql':
                charset = self.metadata.get('charset', 'utf8mb4')
                collation = self.metadata.get('collation', 'utf8mb4_unicode_ci')

                create_sql = f"""
                    CREATE DATABASE `{self.database_name}`
                    CHARACTER SET {charset}
                    COLLATE {collation}
                """
                cursor.execute(create_sql)
                logger.info(f"✓ Banco MySQL '{self.database_name}' criado (charset: {charset}, collation: {collation})")

            elif self.db_type == 'postgresql':
                encoding = self.metadata.get('encoding', 'UTF8')

                create_sql = f"""
                    CREATE DATABASE "{self.database_name}"
                    WITH ENCODING '{encoding}'
                """
                cursor.execute(create_sql)
                logger.info(f"✓ Banco PostgreSQL '{self.database_name}' criado (encoding: {encoding})")

            cursor.close()
            return True

        except Exception as e:
            logger.error(f"Erro ao criar banco de dados: {e}")
            raise

    def save_metadata_report(self, output_dir: str = "reports") -> str:
        """
        Salva relatório dos metadados coletados

        Args:
            output_dir: Diretório onde salvar o relatório

        Returns:
            Caminho do arquivo gerado
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recreate_{self.database_name}_{timestamp}.json"
        filepath = output_path / filename

        report = {
            'operation': 'database_recreation',
            'database': self.database_name,
            'type': self.db_type,
            'metadata_before': self.metadata,
            'config_file': str(self.config_path),
            'timestamp': timestamp
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Relatório salvo em: {filepath}")
        return str(filepath)

    def close(self) -> None:
        """Fecha a conexão com o banco de dados"""
        if self.connection:
            self.connection.close()
            logger.info("Conexão fechada")

    def execute_full_recreation(self, force: bool = True, save_report: bool = True) -> Dict[str, Any]:
        """
        Executa o processo completo de recriação

        Args:
            force: Força a exclusão terminando conexões ativas
            save_report: Se True, salva relatório dos metadados

        Returns:
            Dicionário com resultado da operação
        """
        result = {
            'success': False,
            'steps_completed': [],
            'errors': []
        }

        try:
            # 1. Conecta ao banco
            self.connect()
            result['steps_completed'].append('connection_established')

            # 2. Coleta metadados
            self.collect_metadata()
            result['steps_completed'].append('metadata_collected')

            # 3. Salva relatório (antes de apagar)
            if save_report:
                report_file = self.save_metadata_report()
                result['report_file'] = report_file
                result['steps_completed'].append('report_saved')

            # 4. Apaga banco
            if self.metadata.get('exists', False):
                self.drop_database(force=force)
                result['steps_completed'].append('database_dropped')
            else:
                logger.info("Banco não existe, pulando etapa de exclusão")
                result['steps_completed'].append('database_didnt_exist')

            # 5. Recria banco vazio
            self.create_database()
            result['steps_completed'].append('database_created')

            result['success'] = True
            result['metadata'] = self.metadata

            logger.info("✓ Processo de recriação concluído com sucesso!")

        except Exception as e:
            logger.error(f"Erro durante recriação: {e}")
            result['errors'].append(str(e))
            raise

        finally:
            self.close()

        return result


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Recria um banco de dados MySQL ou PostgreSQL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s --config secrets/mysql_config.json --database perfexcrm_db
  %(prog)s --config secrets/postgresql_source_config.json --database app_workforce
  %(prog)s -c secrets/wfdb02_postgres.json -d chatwoot_dev_db --verbose
  %(prog)s -c secrets/mysql_config.json -d test_db --no-force  # Sem forçar desconexão
        """
    )

    parser.add_argument(
        '-c', '--config',
        required=True,
        help='Caminho para o arquivo JSON de configuração'
    )

    parser.add_argument(
        '-d', '--database',
        required=True,
        help='Nome do banco de dados a ser recriado'
    )

    parser.add_argument(
        '--no-force',
        action='store_true',
        help='NÃO força a exclusão de conexões ativas (padrão é sempre forçar)'
    )

    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Não gera relatório de metadados'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verboso (DEBUG)'
    )

    args = parser.parse_args()

    # Ajusta nível de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Confirmação de segurança
    print(f"\n{'='*60}")
    print(f"ATENÇÃO: Esta operação irá APAGAR o banco '{args.database}'")
    print(f"Configuração: {args.config}")
    print(f"Force: {'NÃO' if args.no_force else 'SIM (conexões serão terminadas)'}")
    print(f"{'='*60}\n")

    confirm = input("Digite 'SIM' para confirmar: ")
    if confirm != 'SIM':
        print("Operação cancelada pelo usuário")
        return 1

    # Executa recriação
    try:
        recreator = DatabaseRecreator(args.config, args.database)
        result = recreator.execute_full_recreation(
            force=not args.no_force,  # Padrão é sempre forçar (True)
            save_report=not args.no_report
        )

        print(f"\n{'='*60}")
        print("RESULTADO DA OPERAÇÃO")
        print(f"{'='*60}")
        print(f"Sucesso: {result['success']}")
        print(f"Etapas completadas: {', '.join(result['steps_completed'])}")
        if result.get('report_file'):
            print(f"Relatório: {result['report_file']}")
        print(f"{'='*60}\n")

        return 0 if result['success'] else 1

    except Exception as e:
        logger.error(f"Falha na execução: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
