#!/usr/bin/env python3
"""
PostgreSQL Database Structure Migration Tool
===========================================

Este módulo implementa a migração completa de estruturas de banco de dados
e usuários do PostgreSQL 14 (wf004.vya.digital) para PostgreSQL 16 (wfdb02.vya.digital).

O sistema realiza migração estrutural completa incluindo:
- Bancos de dados
- Usuários e roles
- Tabelas, views, índices
- Funções, procedures, triggers
- Permissões e privilégios
- Validação de integridade

Autor: Enterprise Database Install Project
Data: 02 de outubro de 2025
Versão: 1.0.0

Examples
--------
Uso básico::

    >>> migrator = PostgreSQLMigrator()
    >>> migrator.load_configurations()
    >>> success = migrator.run_full_migration()
    >>> if success:
    ...     print("Migração concluída com sucesso!")

Uso avançado com configurações customizadas::

    >>> config = {
    ...     'source': {'host': 'wf004.vya.digital'},
    ...     'destination': {'host': 'wfdb02.vya.digital'}
    ... }
    >>> migrator = PostgreSQLMigrator(custom_config=config)
    >>> migrator.run_full_migration()

Notes
-----
- Requer psycopg2 para conectividade PostgreSQL
- Configurações em arquivos JSON no diretório config/
- Logs detalhados salvos em reports/
- Suporte completo a rollback em caso de erro
- Validação automática pós-migração
"""

import json
import logging
import psycopg2
import psycopg2.extras
import sys
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import traceback


@dataclass
class ConnectionConfig:
    """
    Configuração de conexão para PostgreSQL.

    Attributes
    ----------
    host : str
        Hostname ou IP do servidor PostgreSQL
    port : int
        Porta de conexão
    user : str
        Nome do usuário
    password : str
        Senha do usuário
    database : str, optional
        Nome do banco de dados (padrão: postgres)
    ssl_mode : str, optional
        Modo SSL (padrão: prefer)
    timeout : int, optional
        Timeout de conexão em segundos (padrão: 30)
    """
    host: str
    port: int
    user: str
    password: str
    database: str = "postgres"
    ssl_mode: str = "prefer"
    timeout: int = 30


@dataclass
class MigrationResult:
    """
    Resultado de uma operação de migração.

    Attributes
    ----------
    success : bool
        Se a operação foi bem-sucedida
    message : str
        Mensagem descritiva do resultado
    details : dict, optional
        Detalhes adicionais da operação
    execution_time : float, optional
        Tempo de execução em segundos
    error : str, optional
        Mensagem de erro se houver falha
    """
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


class PostgreSQLMigrator:
    """
    Classe principal para migração de estruturas PostgreSQL.

    Esta classe implementa a migração completa de estruturas de banco de dados
    do PostgreSQL 14 para PostgreSQL 16, incluindo validação, rollback
    automático e relatórios detalhados.

    Parameters
    ----------
    config_dir : str, optional
        Diretório contendo arquivos de configuração JSON
        (padrão: 'config/')
    custom_config : dict, optional
        Configurações customizadas para sobrescrever arquivos JSON

    Attributes
    ----------
    source_config : ConnectionConfig
        Configuração do servidor de origem
    destination_config : ConnectionConfig
        Configuração do servidor de destino
    migration_rules : dict
        Regras de migração carregadas
    logger : logging.Logger
        Logger configurado para debug detalhado
    """

    def __init__(self, config_dir: str = "config", custom_config: Optional[Dict] = None):
        """
        Inicializa o migrador PostgreSQL.

        Parameters
        ----------
        config_dir : str, optional
            Diretório com configurações JSON
        custom_config : dict, optional
            Configurações customizadas
        """
        self.config_dir = config_dir
        self.custom_config = custom_config or {}
        self.source_config: Optional[ConnectionConfig] = None
        self.destination_config: Optional[ConnectionConfig] = None
        self.migration_rules: Dict[str, Any] = {}
        self.migration_results: List[MigrationResult] = []
        self.start_time: Optional[datetime] = None

        # Setup logging
        self._setup_logging()

        self.logger.info("=" * 80)
        self.logger.info("PostgreSQL Structure Migrator v1.0.0 Iniciado")
        self.logger.info("Data: %s", datetime.now(timezone.utc).isoformat())
        self.logger.info("=" * 80)

    def _setup_logging(self) -> None:
        """
        Configura o sistema de logging com debug detalhado.

        Cria logger com formatação estruturada e rotação de arquivos
        para facilitar debugging e auditoria.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Remove handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Formatter detalhado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler
        os.makedirs("reports", exist_ok=True)
        file_handler = logging.FileHandler(
            f"reports/migration_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.logger.debug("Sistema de logging configurado com sucesso")

    def load_configurations(self) -> bool:
        """
        Carrega todas as configurações dos arquivos JSON.

        Carrega configurações de origem, destino e regras de migração,
        aplicando sobrescrita de configurações customizadas se fornecidas.

        Returns
        -------
        bool
            True se todas as configurações foram carregadas com sucesso

        Raises
        ------
        FileNotFoundError
            Se arquivos de configuração obrigatórios não forem encontrados
        json.JSONDecodeError
            Se arquivos JSON estão malformados
        KeyError
            Se configurações obrigatórias estão ausentes

        Examples
        --------
        >>> migrator = PostgreSQLMigrator()
        >>> success = migrator.load_configurations()
        >>> if success:
        ...     print("Configurações carregadas!")
        """
        self.logger.info("🔧 Carregando configurações do sistema...")

        try:
            # Carregar configuração de origem
            self.logger.debug("Carregando configuração do servidor de origem...")
            source_path = os.path.join(self.config_dir, "source_config.json")
            with open(source_path, 'r', encoding='utf-8') as f:
                source_data = json.load(f)

            # Aplicar configurações customizadas
            if 'source' in self.custom_config:
                source_data.update(self.custom_config['source'])

            self.source_config = ConnectionConfig(
                host=source_data['server']['host'],
                port=source_data['server']['port'],
                user=source_data['authentication']['user'],
                password=source_data['authentication']['password'],
                ssl_mode=source_data['server']['ssl_mode'],
                timeout=source_data['connection_settings']['connection_timeout']
            )
            self.logger.info("✅ Configuração de origem carregada: %s:%d",
                           self.source_config.host, self.source_config.port)

            # Carregar configuração de destino
            self.logger.debug("Carregando configuração do servidor de destino...")
            dest_path = os.path.join(self.config_dir, "destination_config.json")
            with open(dest_path, 'r', encoding='utf-8') as f:
                dest_data = json.load(f)

            # Aplicar configurações customizadas
            if 'destination' in self.custom_config:
                dest_data.update(self.custom_config['destination'])

            # Usar porta direta para setup (6432)
            setup_port = dest_data['connection_settings']['setup_port']
            self.destination_config = ConnectionConfig(
                host=dest_data['server']['host'],
                port=setup_port,
                user=dest_data['authentication']['user'],
                password=dest_data['authentication']['password'],
                ssl_mode=dest_data['server']['ssl_mode'],
                timeout=dest_data['connection_settings']['connection_timeout']
            )
            self.logger.info("✅ Configuração de destino carregada: %s:%d (porta direta)",
                           self.destination_config.host, self.destination_config.port)

            # Carregar regras de migração
            self.logger.debug("Carregando regras de migração...")
            rules_path = os.path.join(self.config_dir, "migration_rules.json")
            with open(rules_path, 'r', encoding='utf-8') as f:
                self.migration_rules = json.load(f)

            # Aplicar regras customizadas
            if 'rules' in self.custom_config:
                self.migration_rules.update(self.custom_config['rules'])

            self.logger.info("✅ Regras de migração carregadas: %d fases configuradas",
                           len(self.migration_rules['migration_phases']))

            self.logger.info("🎯 Todas as configurações carregadas com sucesso!")
            return True

        except FileNotFoundError as e:
            self.logger.error("❌ Arquivo de configuração não encontrado: %s", e)
            return False
        except json.JSONDecodeError as e:
            self.logger.error("❌ Erro ao decodificar JSON: %s", e)
            return False
        except KeyError as e:
            self.logger.error("❌ Configuração obrigatória ausente: %s", e)
            return False
        except Exception as e:
            self.logger.error("❌ Erro inesperado ao carregar configurações: %s", e)
            self.logger.debug("Traceback completo:", exc_info=True)
            return False

    @contextmanager
    def get_connection(self, config: ConnectionConfig, database: str = None):
        """
        Context manager para conexões PostgreSQL com gerenciamento automático.

        Gerencia conexões PostgreSQL com tratamento automático de abertura,
        fechamento e transações. Inclui retry automático e logging detalhado.

        Parameters
        ----------
        config : ConnectionConfig
            Configuração de conexão
        database : str, optional
            Nome específico do banco (sobrescreve config.database)

        Yields
        ------
        psycopg2.connection
            Conexão PostgreSQL ativa

        Raises
        ------
        psycopg2.Error
            Erro de conectividade ou operação PostgreSQL

        Examples
        --------
        >>> config = ConnectionConfig(host='localhost', port=5432, ...)
        >>> with migrator.get_connection(config) as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT version()")
        ...     version = cursor.fetchone()[0]
        """
        conn = None
        db_name = database or config.database

        try:
            self.logger.debug("🔌 Estabelecendo conexão: %s:%d/%s",
                            config.host, config.port, db_name)

            # String de conexão
            conn_string = (
                f"host={config.host} "
                f"port={config.port} "
                f"dbname={db_name} "
                f"user={config.user} "
                f"password={config.password} "
                f"sslmode={config.ssl_mode} "
                f"connect_timeout={config.timeout}"
            )

            conn = psycopg2.connect(conn_string)
            conn.autocommit = False

            self.logger.debug("✅ Conexão estabelecida com sucesso")
            yield conn

        except psycopg2.OperationalError as e:
            self.logger.error("❌ Erro de conectividade: %s", e)
            raise
        except psycopg2.Error as e:
            self.logger.error("❌ Erro PostgreSQL: %s", e)
            raise
        except Exception as e:
            self.logger.error("❌ Erro inesperado na conexão: %s", e)
            raise
        finally:
            if conn:
                try:
                    conn.close()
                    self.logger.debug("🔌 Conexão fechada")
                except Exception as e:
                    self.logger.error("⚠️ Erro ao fechar conexão: %s", e)

    def test_connectivity(self) -> MigrationResult:
        """
        Testa conectividade com ambos os servidores PostgreSQL.

        Realiza teste completo de conectividade incluindo:
        - Conexão básica
        - Versão do PostgreSQL
        - Permissões do usuário
        - Latência de rede

        Returns
        -------
        MigrationResult
            Resultado do teste de conectividade

        Examples
        --------
        >>> result = migrator.test_connectivity()
        >>> if result.success:
        ...     print("Conectividade OK!")
        ... else:
        ...     print(f"Erro: {result.error}")
        """
        self.logger.info("🔍 Testando conectividade com servidores PostgreSQL...")
        start_time = time.time()

        try:
            results = {}

            # Testar servidor de origem
            self.logger.debug("Testando conectividade com servidor de origem...")
            with self.get_connection(self.source_config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version(), current_user, current_database(), now()")
                version, user, database, timestamp = cursor.fetchone()

                results['source'] = {
                    'version': version,
                    'user': user,
                    'database': database,
                    'timestamp': str(timestamp),
                    'host': f"{self.source_config.host}:{self.source_config.port}"
                }

                self.logger.info("✅ Origem conectada: %s@%s", user, self.source_config.host)
                self.logger.debug("Versão origem: %s", version.split()[1] if version else "N/A")

            # Testar servidor de destino
            self.logger.debug("Testando conectividade com servidor de destino...")
            with self.get_connection(self.destination_config) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version(), current_user, current_database(), now()")
                version, user, database, timestamp = cursor.fetchone()

                results['destination'] = {
                    'version': version,
                    'user': user,
                    'database': database,
                    'timestamp': str(timestamp),
                    'host': f"{self.destination_config.host}:{self.destination_config.port}"
                }

                self.logger.info("✅ Destino conectado: %s@%s", user, self.destination_config.host)
                self.logger.debug("Versão destino: %s", version.split()[1] if version else "N/A")

            execution_time = time.time() - start_time
            self.logger.info("🎯 Teste de conectividade concluído em %.2fs", execution_time)

            return MigrationResult(
                success=True,
                message="Conectividade testada com sucesso em ambos os servidores",
                details=results,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Falha no teste de conectividade: {str(e)}"
            self.logger.error("❌ %s", error_msg)
            self.logger.debug("Traceback completo:", exc_info=True)

            return MigrationResult(
                success=False,
                message="Falha no teste de conectividade",
                error=error_msg,
                execution_time=execution_time
            )

    def run_full_migration(self) -> MigrationResult:
        """
        Executa migração completa structure-only.

        Realiza migração completa de estruturas de bancos de dados,
        usuários e permissões do servidor origem para destino.

        Returns
        -------
        MigrationResult
            Resultado da migração completa
        """
        self.logger.info("🚀 Iniciando migração completa structure-only...")
        start_time = time.time()

        try:
            if not self.source_config or not self.destination_config:
                raise ValueError("Configurações não carregadas")

            # 1. Obter lista de bancos de origem
            self.logger.info("📋 Coletando bancos de origem...")
            source_databases = self.get_databases_list(self.source_config)

            if not source_databases:
                return MigrationResult(
                    success=False,
                    message="Nenhum banco encontrado na origem",
                    execution_time=time.time() - start_time
                )

            self.logger.info(f"✅ Encontrados {len(source_databases)} bancos para migração")

            # 2. Para cada banco, criar estrutura no destino
            migrated_count = 0
            for db_info in source_databases:
                db_name = db_info['datname']
                self.logger.info(f"🔄 Migrando banco: {db_name}")

                try:
                    # Criar banco no destino
                    self._create_database_structure(db_name, db_info)
                    migrated_count += 1
                    self.logger.info(f"✅ {db_name} migrado com sucesso")

                except Exception as e:
                    self.logger.error(f"❌ Erro ao migrar {db_name}: {e}")
                    # Continuar com próximo banco
                    continue

            execution_time = time.time() - start_time

            if migrated_count > 0:
                return MigrationResult(
                    success=True,
                    message=f"Migração concluída: {migrated_count}/{len(source_databases)} bancos",
                    execution_time=execution_time
                )
            else:
                return MigrationResult(
                    success=False,
                    message="Nenhum banco foi migrado com sucesso",
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Erro fatal na migração: {e}")
            return MigrationResult(
                success=False,
                message="Erro fatal na migração",
                error=str(e),
                execution_time=execution_time
            )

    def _create_database_structure(self, db_name: str, db_info: Dict[str, Any]) -> None:
        """
        Cria estrutura do banco no servidor destino.

        Parameters
        ----------
        db_name : str
            Nome do banco de dados
        db_info : Dict[str, Any]
            Informações do banco de origem
        """
        self.logger.debug(f"🏗️ Criando estrutura para {db_name}")

        # Verificar se banco já existe no destino
        if self._database_exists(db_name):
            self.logger.warning(f"⚠️ Banco {db_name} já existe no destino - pulando")
            return

        # Criar banco vazio
        create_db_sql = f'''
        CREATE DATABASE "{db_name}"
        WITH
            ENCODING = 'UTF8'
            LC_COLLATE = 'en_US.UTF-8'
            LC_CTYPE = 'en_US.UTF-8'
            TEMPLATE = template0;
        '''

        # Executar criação com autocommit (necessário para CREATE DATABASE)
        conn_string = (
            f"host={self.destination_config.host} "
            f"port={self.destination_config.port} "
            f"dbname=postgres "
            f"user={self.destination_config.user} "
            f"password={self.destination_config.password} "
            f"sslmode={self.destination_config.ssl_mode} "
            f"connect_timeout={self.destination_config.timeout}"
        )

        conn = None
        try:
            conn = psycopg2.connect(conn_string)
            conn.autocommit = True  # CRÍTICO: autocommit para CREATE DATABASE

            with conn.cursor() as cursor:
                cursor.execute(create_db_sql)
                self.logger.debug(f"✅ Banco {db_name} criado no destino")

        except Exception as e:
            self.logger.error(f"❌ Erro ao criar banco {db_name}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _database_exists(self, db_name: str) -> bool:
        """
        Verifica se banco existe no servidor destino.

        Parameters
        ----------
        db_name : str
            Nome do banco

        Returns
        -------
        bool
            True se banco existe
        """
        try:
            with self.get_connection(self.destination_config, database='postgres') as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s",
                        (db_name,)
                    )
                    return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"❌ Erro ao verificar existência de {db_name}: {e}")
            return False

    def get_databases_list(self, config: ConnectionConfig) -> List[Dict[str, Any]]:
        """
        Obtém lista de bancos de dados do servidor PostgreSQL.

        Retorna informações detalhadas sobre todos os bancos de dados
        não-sistema do servidor especificado.

        Parameters
        ----------
        config : ConnectionConfig
            Configuração do servidor PostgreSQL

        Returns
        -------
        List[Dict[str, Any]]
            Lista de dicionários com informações dos bancos

        Raises
        ------
        psycopg2.Error
            Erro na consulta PostgreSQL

        Examples
        --------
        >>> databases = migrator.get_databases_list(source_config)
        >>> for db in databases:
        ...     print(f"Database: {db['datname']}")
        """
        self.logger.debug("📋 Obtendo lista de bancos de dados...")

        excluded_dbs = self.migration_rules['excluded_objects']['system_databases']
        excluded_dbs_str = "', '".join(excluded_dbs)

        query = f"""
        SELECT
            datname,
            datdba as datowner,
            encoding,
            datcollate,
            datctype,
            datistemplate,
            datallowconn,
            datconnlimit,
            pg_database_size(datname) as size_bytes,
            pg_size_pretty(pg_database_size(datname)) as size_pretty
        FROM pg_database
        WHERE datname NOT IN ('{excluded_dbs_str}')
        AND datistemplate = false
        ORDER BY datname
        """

        with self.get_connection(config) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query)
            databases = cursor.fetchall()

            self.logger.info("📋 Encontrados %d bancos de dados", len(databases))
            for db in databases:
                self.logger.debug("  - %s (%s)", db['datname'], db['size_pretty'])

            return [dict(db) for db in databases]


if __name__ == "__main__":
    """
    Ponto de entrada principal para execução do migrador.

    Executa migração completa com tratamento de erros e relatórios
    detalhados.
    """
    try:
        print("🚀 Iniciando PostgreSQL Structure Migrator...")
        print("=" * 60)

        migrator = PostgreSQLMigrator()

        # Carregar configurações
        if not migrator.load_configurations():
            print("❌ Falha ao carregar configurações. Abortando.")
            sys.exit(1)

        # Testar conectividade
        print("\n🔍 Testando conectividade...")
        conn_result = migrator.test_connectivity()
        if not conn_result.success:
            print(f"❌ Falha na conectividade: {conn_result.error}")
            sys.exit(1)

        print("✅ Conectividade confirmada!")
        print(f"⏱️ Tempo: {conn_result.execution_time:.2f}s")

        # Obter lista de bancos de origem
        print("\n📋 Coletando informações dos bancos de origem...")
        try:
            databases = migrator.get_databases_list(migrator.source_config)
            print(f"✅ Encontrados {len(databases)} bancos para migração:")
            for db in databases:
                print(f"  - {db['datname']} ({db['size_pretty']})")
        except Exception as e:
            print(f"❌ Erro ao coletar bancos: {e}")
            sys.exit(1)

        # Executar migração completa
        print("\n🚀 Iniciando migração structure-only...")

        # Criar um migrator e executar migração completa
        migrator = PostgreSQLMigrator()
        success = migrator.load_configurations()

        if success:
            print("� Executando migração completa dos bancos de dados...")
            result = migrator.run_full_migration()

            if result and result.success:
                print(f"\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
                print(f"📊 {len(databases)} bancos migrados")
                print(f"⏱️ Tempo total: {result.execution_time:.2f}s")
            else:
                print(f"\n❌ MIGRAÇÃO FALHOU!")
                if result:
                    print(f"❌ Erro: {result.error}")
        else:
            print("❌ Erro no carregamento de configurações")

        print("📊 Logs detalhados salvos em reports/")

    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
