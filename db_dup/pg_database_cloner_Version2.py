#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de Clonagem de Banco de Dados PostgreSQL.

Este módulo implementa a clonagem completa de bancos de dados PostgreSQL,
preservando estrutura, dados, permissões, tablespaces e todas as configurações.

:author: yvesmarinho
:date: 2026-02-09
:version: 2.0.0

Examples
--------
>>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
>>> from pg_connection_manager_v2 import PostgreSQLConnectionManager
>>> from pg_metadata_analyzer import DatabaseMetadataAnalyzer
>>> config = PostgreSQLJsonConfig(
...     'localhost', 5432, SSLMode.DISABLE,
...     [UserCredential('user', 'pass')], 'src', 'dst'
... )
>>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
>>> cloner = DatabaseCloner(manager)
>>> isinstance(cloner.manager, PostgreSQLConnectionManager)
True
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import psycopg2
    from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager
    from pg_metadata_analyzer_Version2 import (
        DatabaseInfo,
        DatabaseMetadataAnalyzer,
        RoleInfo,
        SchemaPermissions,
        TablePermissions,
        TablespaceInfo,
    )
    from psycopg2 import extras, sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from sqlalchemy import MetaData, Table, create_engine, inspect, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.schema import CreateIndex, CreateTable
except ImportError as e:
    print(f"Erro ao importar dependências: {e}")
    raise


class DatabaseCloner:
    """
    Clonador completo de banco de dados PostgreSQL.

    Esta classe gerencia todo o processo de clonagem, incluindo:
    - Criação do banco de destino
    - Recreação de roles e permissões
    - Cópia da estrutura e dados
    - Aplicação de permissões
    - Validação da clonagem

    Parameters
    ----------
    connection_manager : PostgreSQLConnectionManager
        Gerenciador de conexões configurado
    metadata_analyzer : DatabaseMetadataAnalyzer, optional
        Analisador de metadados (cria novo se None)

    Attributes
    ----------
    manager : PostgreSQLConnectionManager
        Gerenciador de conexões
    analyzer : DatabaseMetadataAnalyzer
        Analisador de metadados
    metadata : dict
        Metadados extraídos
    logger : logging.Logger
        Logger para rastreamento
    clone_stats : dict
        Estatísticas da clonagem

    Examples
    --------
    >>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
    >>> from pg_connection_manager_v2 import PostgreSQLConnectionManager
    >>> config = PostgreSQLJsonConfig(
    ...     'localhost', 5432, SSLMode.DISABLE,
    ...     [UserCredential('u', 'p')], 'src', 'dst'
    ... )
    >>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
    >>> cloner = DatabaseCloner(manager)
    >>> cloner.manager is not None
    True
    """

    def __init__(
        self,
        connection_manager: PostgreSQLConnectionManager,
        metadata_analyzer: Optional[DatabaseMetadataAnalyzer] = None
    ):
        """
        Inicializa o clonador de banco de dados.

        Parameters
        ----------
        connection_manager : PostgreSQLConnectionManager
            Gerenciador de conexões
        metadata_analyzer : DatabaseMetadataAnalyzer, optional
            Analisador de metadados
        """
        try:
            if not isinstance(connection_manager, PostgreSQLConnectionManager):
                raise TypeError(
                    f"Esperado PostgreSQLConnectionManager, "
                    f"recebido {type(connection_manager).__name__}"
                )

            self.manager = connection_manager

            if metadata_analyzer is None:
                self.analyzer = DatabaseMetadataAnalyzer(connection_manager)
            else:
                if not isinstance(metadata_analyzer, DatabaseMetadataAnalyzer):
                    raise TypeError(
                        f"Esperado DatabaseMetadataAnalyzer, "
                        f"recebido {type(metadata_analyzer).__name__}"
                    )
                self.analyzer = metadata_analyzer

            self.metadata: Dict[str, Any] = {}
            self.clone_stats: Dict[str, Any] = {
                'start_time': None,
                'end_time': None,
                'duration_seconds': 0,
                'roles_created': 0,
                'schemas_created': 0,
                'tables_copied': 0,
                'views_created': 0,
                'functions_created': 0,
                'permissions_applied': 0,
                'errors': []
            }

            # Configurar logging
            self.logger = logging.getLogger(self.__class__.__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

            self.logger.info("Clonador de banco de dados inicializado")

        except (TypeError, AttributeError) as e:
            logging.error(f"Erro ao inicializar clonador: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado na inicialização: {e}")
            raise

    def clone_database(
        self,
        drop_if_exists: bool = False,
        copy_data: bool = True,
        verify_clone: bool = True
    ) -> bool:
        """
        Executa a clonagem completa do banco de dados.

        Parameters
        ----------
        drop_if_exists : bool, optional
            Se deve dropar banco de destino se existir (padrão: False)
        copy_data : bool, optional
            Se deve copiar dados das tabelas (padrão: True)
        verify_clone : bool, optional
            Se deve verificar a clonagem ao final (padrão: True)

        Returns
        -------
        bool
            True se clonagem bem-sucedida, False caso contrário

        Examples
        --------
        >>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
        >>> from pg_connection_manager_v2 import PostgreSQLConnectionManager
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('u', 'p')], 'src', 'dst'
        ... )
        >>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
        >>> cloner = DatabaseCloner(manager)
        >>> cloner.clone_database()  # doctest: +SKIP
        True
        """
        try:
            if not isinstance(drop_if_exists, bool):
                raise TypeError("drop_if_exists deve ser bool")
            if not isinstance(copy_data, bool):
                raise TypeError("copy_data deve ser bool")
            if not isinstance(verify_clone, bool):
                raise TypeError("verify_clone deve ser bool")

            self.clone_stats['start_time'] = datetime.now()

            self.logger.info("=" * 80)
            self.logger.info("INICIANDO CLONAGEM DE BANCO DE DADOS")
            self.logger.info("=" * 80)
            self.logger.info(f"Origem: {self.manager.config.db_source}")
            self.logger.info(f"Destino: {self.manager.config.db_destiny}")
            self.logger.info(
                f"Servidor: {self.manager.config.host}:{self.manager.config.port}")
            self.logger.info("=" * 80)

            # Passo 1: Extrair metadados
            self.logger.info(
                "\n[1/8] Extraindo metadados do banco de origem...")
            self.metadata = self.analyzer.extract_all_metadata()
            if self.metadata is False:
                raise RuntimeError("Falha ao extrair metadados")

            # Passo 2: Verificar/Dropar banco de destino
            self.logger.info("\n[2/8] Verificando banco de destino...")
            if not self._prepare_target_database(drop_if_exists):
                raise RuntimeError("Falha ao preparar banco de destino")

            # Passo 3: Criar roles
            self.logger.info("\n[3/8] Criando roles e usuários...")
            if not self._create_roles():
                self.logger.warning(
                    "⚠ Algumas roles podem não ter sido criadas")

            # Passo 4: Criar banco de destino
            self.logger.info("\n[4/8] Criando banco de dados de destino...")
            if not self._create_target_database():
                raise RuntimeError("Falha ao criar banco de destino")

            # Passo 5: Copiar estrutura e dados
            self.logger.info("\n[5/8] Copiando estrutura e dados...")
            if not self._copy_database_structure_and_data(copy_data):
                raise RuntimeError("Falha ao copiar estrutura/dados")

            # Passo 6: Aplicar permissões
            self.logger.info("\n[6/8] Aplicando permissões...")
            if not self._apply_permissions():
                self.logger.warning(
                    "⚠ Algumas permissões podem não ter sido aplicadas")

            # Passo 7: Atualizar sequences
            self.logger.info("\n[7/8] Atualizando sequences...")
            if not self._update_sequences():
                self.logger.warning(
                    "⚠ Algumas sequences podem não ter sido atualizadas")

            # Passo 8: Verificar clonagem
            if verify_clone:
                self.logger.info("\n[8/8] Verificando clonagem...")
                if not self._verify_clone():
                    self.logger.warning(
                        "⚠ Verificação detectou inconsistências")
            else:
                self.logger.info("\n[8/8] Verificação desabilitada")

            self.clone_stats['end_time'] = datetime.now()
            duration = self.clone_stats['end_time'] - \
                self.clone_stats['start_time']
            self.clone_stats['duration_seconds'] = duration.total_seconds()

            self._print_clone_summary()

            self.logger.info("=" * 80)
            self.logger.info("✓ CLONAGEM CONCLUÍDA COM SUCESSO!")
            self.logger.info("=" * 80)

            return True

        except (TypeError, ValueError, RuntimeError) as e:
            self.logger.error(f"✗ Erro ao clonar banco de dados: {e}")
            self.clone_stats['errors'].append(str(e))
            return False
        except Exception as e:
            self.logger.error(
                f"✗ Erro inesperado ao clonar banco de dados: {e}")
            self.clone_stats['errors'].append(str(e))
            return False

    def _prepare_target_database(self, drop_if_exists: bool) -> bool:
        """
        Prepara o banco de destino (verifica existência, dropa se necessário).

        Parameters
        ----------
        drop_if_exists : bool
            Se deve dropar se existir

        Returns
        -------
        bool
            True se preparação bem-sucedida
        """
        try:
            with self.manager.get_postgres_connection(autocommit=True) as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor()

                # Verificar se banco de destino existe
                check_query = """
                SELECT 1 FROM pg_database WHERE datname = %s
                """
                cursor.execute(check_query, (self.manager.config.db_destiny,))
                exists = cursor.fetchone() is not None

                if exists:
                    if drop_if_exists:
                        self.logger.warning(
                            f"Banco '{self.manager.config.db_destiny}' existe - DROPANDO..."
                        )

                        # Terminar conexões ativas
                        terminate_query = """
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = %s AND pid <> pg_backend_pid()
                        """
                        cursor.execute(terminate_query,
                                       (self.manager.config.db_destiny,))

                        # Dropar banco
                        drop_query = sql.SQL("DROP DATABASE IF EXISTS {}").format(
                            sql.Identifier(self.manager.config.db_destiny)
                        )
                        cursor.execute(drop_query)
                        self.logger.info(
                            f"✓ Banco '{self.manager.config.db_destiny}' dropado")
                    else:
                        self.logger.error(
                            f"✗ Banco '{self.manager.config.db_destiny}' já existe. "
                            f"Use drop_if_exists=True para sobrescrever."
                        )
                        cursor.close()
                        return False
                else:
                    self.logger.info(
                        f"✓ Banco '{self.manager.config.db_destiny}' não existe - OK"
                    )

                cursor.close()
                return True

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"✗ Erro ao preparar banco de destino: {e}")
            return False
        except Exception as e:
            self.logger.error(
                f"✗ Erro inesperado ao preparar banco de destino: {e}")
            return False

    def _create_roles(self) -> bool:
        """
        Cria roles/usuários no banco de destino.

        Returns
        -------
        bool
            True se roles criadas com sucesso
        """
        try:
            roles = self.metadata.get('roles', [])
            if not roles:
                self.logger.info("Nenhuma role para criar")
                return True

            with self.manager.get_postgres_connection(autocommit=True) as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor()
                created_count = 0

                for role_data in roles:
                    try:
                        # Converter dict para RoleInfo se necessário
                        if isinstance(role_data, dict):
                            role = RoleInfo(**role_data)
                        else:
                            role = role_data

                        # Verificar se role já existe
                        check_query = "SELECT 1 FROM pg_roles WHERE rolname = %s"
                        cursor.execute(check_query, (role.rolname,))

                        if cursor.fetchone():
                            self.logger.info(
                                f"  Role '{role.rolname}' já existe - pulando")
                            continue

                        # Criar role (sem senha para evitar problemas)
                        create_stmt = f"CREATE ROLE {sql.Identifier(role.rolname).as_string(conn)}"

                        options = []
                        if role.rolsuper:
                            options.append("SUPERUSER")
                        else:
                            options.append("NOSUPERUSER")

                        if role.rolcreatedb:
                            options.append("CREATEDB")
                        else:
                            options.append("NOCREATEDB")

                        if role.rolcreaterole:
                            options.append("CREATEROLE")
                        else:
                            options.append("NOCREATEROLE")

                        if role.rolinherit:
                            options.append("INHERIT")
                        else:
                            options.append("NOINHERIT")

                        if role.rolcanlogin:
                            options.append("LOGIN")
                        else:
                            options.append("NOLOGIN")

                        if role.rolreplication:
                            options.append("REPLICATION")
                        else:
                            options.append("NOREPLICATION")

                        if role.rolconnlimit >= 0:
                            options.append(
                                f"CONNECTION LIMIT {role.rolconnlimit}")

                        if options:
                            create_stmt += " WITH " + " ".join(options)

                        cursor.execute(create_stmt)
                        created_count += 1
                        self.logger.info(f"  ✓ Role '{role.rolname}' criada")

                    except psycopg2.Error as e:
                        self.logger.warning(
                            f"  ⚠ Falha ao criar role '{role.rolname}': {e}")
                        continue
                    except Exception as e:
                        self.logger.warning(
                            f"  ⚠ Erro inesperado ao criar role '{role.rolname}': {e}")
                        continue

                # Criar memberships (GRANT role TO role)
                for role_data in roles:
                    try:
                        if isinstance(role_data, dict):
                            role = RoleInfo(**role_data)
                        else:
                            role = role_data

                        for member_of in role.memberof:
                            try:
                                grant_stmt = sql.SQL("GRANT {} TO {}").format(
                                    sql.Identifier(member_of),
                                    sql.Identifier(role.rolname)
                                )
                                cursor.execute(grant_stmt)
                                self.logger.info(
                                    f"  ✓ '{role.rolname}' adicionado a '{member_of}'"
                                )
                            except psycopg2.Error as e:
                                self.logger.warning(
                                    f"  ⚠ Falha ao adicionar '{role.rolname}' a '{member_of}': {e}"
                                )
                    except Exception as e:
                        self.logger.warning(
                            f"  ⚠ Erro ao processar memberships: {e}")

                cursor.close()

                self.clone_stats['roles_created'] = created_count
                self.logger.info(f"✓ {created_count} roles criadas")
                return True

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"✗ Erro ao criar roles: {e}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Erro inesperado ao criar roles: {e}")
            return False

    def _create_target_database(self) -> bool:
        """
        Cria o banco de dados de destino.

        Returns
        -------
        bool
            True se banco criado com sucesso
        """
        try:
            db_info = self.metadata.get('database')
            if not db_info:
                raise ValueError(
                    "Informações do banco não encontradas nos metadados")

            # Converter dict para DatabaseInfo se necessário
            if isinstance(db_info, dict):
                db_info = DatabaseInfo(**db_info)

            with self.manager.get_postgres_connection(autocommit=True) as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor()

                # Verificar se tablespace existe
                check_ts_query = "SELECT 1 FROM pg_tablespace WHERE spcname = %s"
                cursor.execute(check_ts_query, (db_info.tablespace,))

                if not cursor.fetchone():
                    self.logger.warning(
                        f"⚠ Tablespace '{db_info.tablespace}' não existe - "
                        f"usando 'pg_default'"
                    )
                    tablespace = 'pg_default'
                else:
                    tablespace = db_info.tablespace

                # Criar banco de dados
                create_stmt = sql.SQL(
                    "CREATE DATABASE {} WITH OWNER = {} "
                    "ENCODING = {} LC_COLLATE = {} LC_CTYPE = {} "
                    "TABLESPACE = {}"
                ).format(
                    sql.Identifier(self.manager.config.db_destiny),
                    sql.Identifier(db_info.owner),
                    sql.Literal(db_info.encoding),
                    sql.Literal(db_info.collation),
                    sql.Literal(db_info.ctype),
                    sql.Identifier(tablespace)
                )

                if db_info.connection_limit >= 0:
                    create_stmt = sql.SQL(
                        str(create_stmt) + f" CONNECTION LIMIT {db_info.connection_limit}")

                cursor.execute(create_stmt)
                cursor.close()

                self.logger.info(
                    f"✓ Banco '{self.manager.config.db_destiny}' criado")
                return True

        except (psycopg2.Error, ConnectionError, ValueError) as e:
            self.logger.error(f"✗ Erro ao criar banco de destino: {e}")
            return False
        except Exception as e:
            self.logger.error(
                f"✗ Erro inesperado ao criar banco de destino: {e}")
            return False

    def _copy_database_structure_and_data(self, copy_data: bool) -> bool:
        """
        Copia estrutura e dados usando SQLAlchemy (sem pg_dump).

        Parameters
        ----------
        copy_data : bool
            Se deve copiar dados

        Returns
        -------
        bool
            True se cópia bem-sucedida
        """
        try:
            self.logger.info(
                "Usando SQLAlchemy para copiar banco (sem pg_dump)...")

            # Criar engines SQLAlchemy
            source_url = self._build_connection_url(
                self.manager.config.db_source)
            dest_url = self._build_connection_url(
                self.manager.config.db_destiny)

            source_engine = create_engine(source_url, echo=False)
            dest_engine = create_engine(dest_url, echo=False)

            try:
                # Etapa 1: Copiar schemas
                self.logger.info("  [1/4] Copiando schemas...")
                if not self._copy_schemas(source_engine, dest_engine):
                    self.logger.warning("⚠ Falha ao copiar alguns schemas")

                # Etapa 2: Copiar estrutura de tabelas
                self.logger.info("  [2/4] Copiando estrutura de tabelas...")
                tables_copied = self._copy_table_structures(
                    source_engine, dest_engine)
                self.logger.info(
                    f"✓ {tables_copied} tabelas estruturadas criadas")

                # Etapa 3: Copiar dados (se solicitado)
                if copy_data:
                    self.logger.info("  [3/4] Copiando dados das tabelas...")
                    rows_copied = self._copy_table_data(
                        source_engine, dest_engine)
                    self.logger.info(f"✓ {rows_copied} linhas copiadas")
                else:
                    self.logger.info(
                        "  [3/4] Cópia de dados desabilitada (--no-data)")

                # Etapa 4: Copiar views e functions
                self.logger.info("  [4/4] Copiando views e functions...")
                if not self._copy_views_and_functions():
                    self.logger.warning(
                        "⚠ Falha ao copiar algumas views/functions")

                self.logger.info("✓ Cópia de estrutura e dados concluída")
                return True

            finally:
                source_engine.dispose()
                dest_engine.dispose()

        except Exception as e:
            self.logger.error(
                f"✗ Erro ao copiar estrutura/dados: {e}", exc_info=True)
            return False

    def _build_connection_url(self, database: str) -> str:
        """Constrói URL de conexão SQLAlchemy."""
        config = self.manager.config
        user = config.validated_user or config.possible_users[0]
        return (
            f"postgresql://{user.username}:{user.password}@"
            f"{config.host}:{config.port}/{database}"
        )

    def _copy_schemas(self, source_engine: Engine, dest_engine: Engine) -> bool:
        """Copia schemas do banco de origem para destino."""
        try:
            inspector = inspect(source_engine)
            schemas = inspector.get_schema_names()

            # Filtrar schemas do sistema
            user_schemas = [
                s for s in schemas
                if s not in ('information_schema', 'pg_catalog', 'pg_toast')
            ]

            with dest_engine.connect() as conn:
                for schema in user_schemas:
                    if schema == 'public':
                        continue  # public já existe

                    try:
                        conn.execute(
                            text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                        conn.commit()
                        self.logger.debug(f"    Schema '{schema}' criado")
                    except Exception as e:
                        self.logger.warning(
                            f"    ⚠ Falha ao criar schema '{schema}': {e}")

            return True

        except Exception as e:
            self.logger.error(f"Erro ao copiar schemas: {e}")
            return False

    def _copy_table_structures(self, source_engine: Engine, dest_engine: Engine) -> int:
        """Copia estrutura de todas as tabelas."""
        try:
            inspector = inspect(source_engine)
            metadata = MetaData()
            tables_created = 0

            # Obter schemas
            schemas = inspector.get_schema_names()
            user_schemas = [
                s for s in schemas
                if s not in ('information_schema', 'pg_catalog', 'pg_toast')
            ]

            for schema in user_schemas:
                table_names = inspector.get_table_names(schema=schema)

                for table_name in table_names:
                    try:
                        # Refletir tabela do banco de origem
                        table = Table(
                            table_name,
                            metadata,
                            autoload_with=source_engine,
                            schema=schema
                        )

                        # Criar tabela no destino
                        with dest_engine.connect() as conn:
                            table.create(bind=conn, checkfirst=True)
                            conn.commit()

                        tables_created += 1
                        self.logger.debug(
                            f"    Tabela '{schema}.{table_name}' criada")

                    except Exception as e:
                        self.logger.warning(
                            f"    ⚠ Falha ao criar tabela '{schema}.{table_name}': {e}"
                        )

            return tables_created

        except Exception as e:
            self.logger.error(f"Erro ao copiar estrutura de tabelas: {e}")
            return 0

    def _copy_table_data(self, source_engine: Engine, dest_engine: Engine,
                         batch_size: int = 1000) -> int:
        """Copia dados de todas as tabelas em lotes."""
        try:
            inspector = inspect(source_engine)
            total_rows = 0

            schemas = inspector.get_schema_names()
            user_schemas = [
                s for s in schemas
                if s not in ('information_schema', 'pg_catalog', 'pg_toast')
            ]

            for schema in user_schemas:
                table_names = inspector.get_table_names(schema=schema)

                for table_name in table_names:
                    try:
                        # Contar registros na origem
                        with source_engine.connect() as src_conn:
                            count_result = src_conn.execute(
                                text(
                                    f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
                            )
                            row_count = count_result.scalar()

                        if row_count == 0:
                            continue

                        self.logger.debug(
                            f"    Copiando {row_count} linhas de '{schema}.{table_name}'..."
                        )

                        # Copiar dados em lotes
                        with source_engine.connect() as src_conn:
                            with dest_engine.connect() as dst_conn:
                                # Obter nomes das colunas
                                columns = inspector.get_columns(
                                    table_name, schema=schema)
                                col_names = [c['name'] for c in columns]
                                col_list = ', '.join(
                                    [f'"{c}"' for c in col_names])

                                # Ler dados em lotes
                                offset = 0
                                while offset < row_count:
                                    # Ler lote da origem
                                    select_query = text(
                                        f'SELECT {col_list} FROM "{schema}"."{table_name}" '
                                        f'LIMIT {batch_size} OFFSET {offset}'
                                    )
                                    result = src_conn.execute(select_query)
                                    rows = result.fetchall()

                                    if not rows:
                                        break

                                    # Preparar placeholders para INSERT
                                    placeholders = ', '.join(
                                        ['%s'] * len(col_names))
                                    insert_query = (
                                        f'INSERT INTO "{schema}"."{table_name}" '
                                        f'({col_list}) VALUES ({placeholders})'
                                    )

                                    # Inserir lote no destino usando psycopg2 direto
                                    raw_conn = dst_conn.connection
                                    cursor = raw_conn.cursor()
                                    extras.execute_batch(
                                        cursor, insert_query, rows)
                                    dst_conn.commit()
                                    cursor.close()

                                    total_rows += len(rows)
                                    offset += batch_size

                    except Exception as e:
                        self.logger.warning(
                            f"    ⚠ Falha ao copiar dados de '{schema}.{table_name}': {e}"
                        )

            return total_rows

        except Exception as e:
            self.logger.error(f"Erro ao copiar dados: {e}")
            return 0

    def _copy_views_and_functions(self) -> bool:
        """Copia views e functions usando DDL direto."""
        try:
            with self.manager.get_source_connection() as src_conn:
                if src_conn is False:
                    return False

                with self.manager.get_destiny_connection() as dst_conn:
                    if dst_conn is False:
                        return False

                    src_cursor = src_conn.cursor()
                    dst_cursor = dst_conn.cursor()

                    # Copiar views
                    view_query = """
                    SELECT schemaname, viewname, definition
                    FROM pg_views
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY schemaname, viewname
                    """
                    src_cursor.execute(view_query)

                    for schema, view_name, definition in src_cursor.fetchall():
                        try:
                            create_view = f'CREATE OR REPLACE VIEW "{schema}"."{view_name}" AS {definition}'
                            dst_cursor.execute(create_view)
                            self.logger.debug(
                                f"    View '{schema}.{view_name}' criada")
                        except Exception as e:
                            self.logger.warning(
                                f"    ⚠ Falha ao criar view '{schema}.{view_name}': {e}"
                            )

                    # Copiar functions
                    func_query = """
                    SELECT n.nspname, p.proname, pg_get_functiondef(p.oid) as definition
                    FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY n.nspname, p.proname
                    """
                    src_cursor.execute(func_query)

                    for schema, func_name, definition in src_cursor.fetchall():
                        try:
                            dst_cursor.execute(definition)
                            self.logger.debug(
                                f"    Function '{schema}.{func_name}' criada")
                        except Exception as e:
                            self.logger.warning(
                                f"    ⚠ Falha ao criar function '{schema}.{func_name}': {e}"
                            )

                    dst_conn.commit()
                    src_cursor.close()
                    dst_cursor.close()

            return True

        except Exception as e:
            self.logger.error(f"Erro ao copiar views/functions: {e}")
            return False

    def _apply_permissions(self) -> bool:
        """
        Aplica permissões de schemas, tabelas, sequences, etc.

        Returns
        -------
        bool
            True se permissões aplicadas com sucesso
        """
        try:
            # Reconectar ao banco de destino
            if not self.manager._connect_database(
                self.manager.config.db_destiny,
                is_destiny=True
            ):
                self.logger.warning(
                    "⚠ Falha ao reconectar ao banco de destino")

            permissions_count = 0

            with self.manager.get_destiny_connection(autocommit=True) as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor()

                # Aplicar permissões de schemas
                schema_perms = self.metadata.get('schema_permissions', [])
                for schema_perm_data in schema_perms:
                    try:
                        if isinstance(schema_perm_data, dict):
                            schema_perm = SchemaPermissions(**schema_perm_data)
                        else:
                            schema_perm = schema_perm_data

                        # Alterar owner do schema
                        alter_stmt = sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                            sql.Identifier(schema_perm.schema_name),
                            sql.Identifier(schema_perm.owner)
                        )
                        cursor.execute(alter_stmt)

                        # Aplicar GRANTs
                        for acl_entry in schema_perm.acl:
                            if not isinstance(acl_entry, dict):
                                continue

                            grantee = acl_entry.get('grantee')
                            privileges = acl_entry.get('privileges', [])

                            if not grantee or not privileges:
                                continue

                            for priv in privileges:
                                try:
                                    grant_stmt = sql.SQL(
                                        "GRANT {} ON SCHEMA {} TO {}"
                                    ).format(
                                        sql.SQL(priv),
                                        sql.Identifier(
                                            schema_perm.schema_name),
                                        sql.Identifier(grantee)
                                    )
                                    cursor.execute(grant_stmt)
                                    permissions_count += 1
                                except psycopg2.Error as e:
                                    self.logger.warning(
                                        f"  ⚠ Falha ao aplicar permissão {priv} "
                                        f"no schema {schema_perm.schema_name}: {e}"
                                    )

                    except Exception as e:
                        self.logger.warning(
                            f"  ⚠ Erro ao aplicar permissões de schema: {e}"
                        )

                # Aplicar permissões de tabelas
                table_perms = self.metadata.get('table_permissions', [])
                for table_perm_data in table_perms:
                    try:
                        if isinstance(table_perm_data, dict):
                            table_perm = TablePermissions(**table_perm_data)
                        else:
                            table_perm = table_perm_data

                        # Alterar owner da tabela
                        alter_stmt = sql.SQL("ALTER TABLE {}.{} OWNER TO {}").format(
                            sql.Identifier(table_perm.schema_name),
                            sql.Identifier(table_perm.table_name),
                            sql.Identifier(table_perm.owner)
                        )
                        cursor.execute(alter_stmt)

                        # Aplicar GRANTs em nível de tabela
                        for acl_entry in table_perm.acl:
                            if not isinstance(acl_entry, dict):
                                continue

                            grantee = acl_entry.get('grantee')
                            privileges = acl_entry.get('privileges', [])

                            if not grantee or not privileges:
                                continue

                            for priv in privileges:
                                try:
                                    grant_stmt = sql.SQL(
                                        "GRANT {} ON TABLE {}.{} TO {}"
                                    ).format(
                                        sql.SQL(priv),
                                        sql.Identifier(table_perm.schema_name),
                                        sql.Identifier(table_perm.table_name),
                                        sql.Identifier(grantee)
                                    )
                                    cursor.execute(grant_stmt)
                                    permissions_count += 1
                                except psycopg2.Error as e:
                                    self.logger.warning(
                                        f"  ⚠ Falha ao aplicar permissão {priv} "
                                        f"na tabela {table_perm.schema_name}."
                                        f"{table_perm.table_name}: {e}"
                                    )

                        # Aplicar GRANTs em nível de coluna
                        for col_name, col_privs in table_perm.column_privileges.items():
                            for col_priv in col_privs:
                                if not isinstance(col_priv, dict):
                                    continue

                                grantee = col_priv.get('grantee')
                                priv_type = col_priv.get('privilege_type')

                                if not grantee or not priv_type:
                                    continue

                                try:
                                    grant_stmt = sql.SQL(
                                        "GRANT {} ({}) ON TABLE {}.{} TO {}"
                                    ).format(
                                        sql.SQL(priv_type),
                                        sql.Identifier(col_name),
                                        sql.Identifier(table_perm.schema_name),
                                        sql.Identifier(table_perm.table_name),
                                        sql.Identifier(grantee)
                                    )
                                    cursor.execute(grant_stmt)
                                    permissions_count += 1
                                except psycopg2.Error as e:
                                    self.logger.warning(
                                        f"  ⚠ Falha ao aplicar permissão de coluna: {e}"
                                    )

                    except Exception as e:
                        self.logger.warning(
                            f"  ⚠ Erro ao aplicar permissões de tabela: {e}"
                        )

                # Aplicar permissões de sequences
                sequences = self.metadata.get('sequences', [])
                for seq_data in sequences:
                    try:
                        schema_name = seq_data.get('schema_name')
                        seq_name = seq_data.get('sequence_name')
                        owner = seq_data.get('owner')

                        if not all([schema_name, seq_name, owner]):
                            continue

                        # Alterar owner
                        alter_stmt = sql.SQL("ALTER SEQUENCE {}.{} OWNER TO {}").format(
                            sql.Identifier(schema_name),
                            sql.Identifier(seq_name),
                            sql.Identifier(owner)
                        )
                        cursor.execute(alter_stmt)

                        # Aplicar GRANTs
                        for acl_entry in seq_data.get('acl', []):
                            if not isinstance(acl_entry, dict):
                                continue

                            grantee = acl_entry.get('grantee')
                            privileges = acl_entry.get('privileges', [])

                            for priv in privileges:
                                try:
                                    grant_stmt = sql.SQL(
                                        "GRANT {} ON SEQUENCE {}.{} TO {}"
                                    ).format(
                                        sql.SQL(priv),
                                        sql.Identifier(schema_name),
                                        sql.Identifier(seq_name),
                                        sql.Identifier(grantee)
                                    )
                                    cursor.execute(grant_stmt)
                                    permissions_count += 1
                                except psycopg2.Error as e:
                                    self.logger.warning(
                                        f"  ⚠ Falha ao aplicar permissão de sequence: {e}"
                                    )

                    except Exception as e:
                        self.logger.warning(
                            f"  ⚠ Erro ao aplicar permissões de sequence: {e}"
                        )

                cursor.close()

            self.clone_stats['permissions_applied'] = permissions_count
            self.logger.info(f"✓ {permissions_count} permissões aplicadas")
            return True

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"✗ Erro ao aplicar permissões: {e}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Erro inesperado ao aplicar permissões: {e}")
            return False

    def _update_sequences(self) -> bool:
        """
        Atualiza valores das sequences para o valor correto.

        Returns
        -------
        bool
            True se sequences atualizadas com sucesso
        """
        try:
            with self.manager.get_destiny_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor()
                updated_count = 0

                sequences = self.metadata.get('sequences', [])
                for seq_data in sequences:
                    try:
                        schema_name = seq_data.get('schema_name')
                        seq_name = seq_data.get('sequence_name')

                        if not schema_name or not seq_name:
                            continue

                        # Buscar tabela e coluna associadas
                        find_table_query = """
                        SELECT
                            schemaname,
                            tablename,
                            columnname
                        FROM pg_catalog.pg_tables t
                        JOIN pg_catalog.pg_class c ON c.relname = t.tablename
                        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                        JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
                        WHERE n.nspname = %s
                          AND pg_get_serial_sequence(
                              quote_ident(n.nspname) || '.' || quote_ident(c.relname),
                              a.attname
                          ) = quote_ident(%s) || '.' || quote_ident(%s)
                        LIMIT 1
                        """

                        cursor.execute(find_table_query,
                                       (schema_name, schema_name, seq_name))
                        result = cursor.fetchone()

                        if result:
                            table_schema, table_name, column_name = result

                            # Atualizar sequence para MAX(coluna) + 1
                            update_query = sql.SQL(
                                "SELECT setval({}, COALESCE(MAX({}), 1)) FROM {}.{}"
                            ).format(
                                sql.Literal(f"{schema_name}.{seq_name}"),
                                sql.Identifier(column_name),
                                sql.Identifier(table_schema),
                                sql.Identifier(table_name)
                            )
                            cursor.execute(update_query)
                            updated_count += 1

                    except psycopg2.Error as e:
                        self.logger.warning(
                            f"  ⚠ Falha ao atualizar sequence "
                            f"{schema_name}.{seq_name}: {e}"
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"  ⚠ Erro inesperado ao atualizar sequence: {e}"
                        )

                cursor.close()
                conn.commit()

                self.logger.info(f"✓ {updated_count} sequences atualizadas")
                return True

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"✗ Erro ao atualizar sequences: {e}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Erro inesperado ao atualizar sequences: {e}")
            return False

    def _verify_clone(self) -> bool:
        """
        Verifica se a clonagem foi bem-sucedida.

        Returns
        -------
        bool
            True se verificação passou, False se encontrou problemas
        """
        try:
            self.logger.info("Verificando clonagem...")

            issues = []

            # Verificar contagem de tabelas
            with self.manager.get_source_connection() as src_conn:
                if src_conn is False:
                    raise ConnectionError("Falha ao conectar à origem")

                with self.manager.get_destiny_connection() as dst_conn:
                    if dst_conn is False:
                        raise ConnectionError("Falha ao conectar ao destino")

                    src_cursor = src_conn.cursor()
                    dst_cursor = dst_conn.cursor()

                    # Contar tabelas
                    count_query = """
                    SELECT COUNT(*) FROM pg_tables
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    """

                    src_cursor.execute(count_query)
                    src_table_count = src_cursor.fetchone()[0]

                    dst_cursor.execute(count_query)
                    dst_table_count = dst_cursor.fetchone()[0]

                    if src_table_count != dst_table_count:
                        issues.append(
                            f"Contagem de tabelas diferente: "
                            f"origem={src_table_count}, destino={dst_table_count}"
                        )
                    else:
                        self.logger.info(
                            f"  ✓ Tabelas: {dst_table_count} (OK)"
                        )
                        self.clone_stats['tables_copied'] = dst_table_count

                    # Contar views
                    view_query = """
                    SELECT COUNT(*) FROM pg_views
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    """

                    src_cursor.execute(view_query)
                    src_view_count = src_cursor.fetchone()[0]

                    dst_cursor.execute(view_query)
                    dst_view_count = dst_cursor.fetchone()[0]

                    if src_view_count != dst_view_count:
                        issues.append(
                            f"Contagem de views diferente: "
                            f"origem={src_view_count}, destino={dst_view_count}"
                        )
                    else:
                        self.logger.info(
                            f"  ✓ Views: {dst_view_count} (OK)"
                        )
                        self.clone_stats['views_created'] = dst_view_count

                    # Contar functions
                    func_query = """
                    SELECT COUNT(*) FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
                    """

                    src_cursor.execute(func_query)
                    src_func_count = src_cursor.fetchone()[0]

                    dst_cursor.execute(func_query)
                    dst_func_count = dst_cursor.fetchone()[0]

                    if src_func_count != dst_func_count:
                        issues.append(
                            f"Contagem de functions diferente: "
                            f"origem={src_func_count}, destino={dst_func_count}"
                        )
                    else:
                        self.logger.info(
                            f"  ✓ Functions: {dst_func_count} (OK)"
                        )
                        self.clone_stats['functions_created'] = dst_func_count

                    src_cursor.close()
                    dst_cursor.close()

            if issues:
                self.logger.warning("⚠ Verificação detectou problemas:")
                for issue in issues:
                    self.logger.warning(f"  - {issue}")
                return False
            else:
                self.logger.info(
                    "✓ Verificação concluída - nenhum problema detectado")
                return True

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"✗ Erro ao verificar clonagem: {e}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Erro inesperado ao verificar clonagem: {e}")
            return False

    def _print_clone_summary(self):
        """Imprime resumo da clonagem."""
        try:
            self.logger.info("\n" + "=" * 80)
            self.logger.info("RESUMO DA CLONAGEM")
            self.logger.info("=" * 80)
            self.logger.info(f"Início: {self.clone_stats['start_time']}")
            self.logger.info(f"Fim: {self.clone_stats['end_time']}")
            self.logger.info(
                f"Duração: {self.clone_stats['duration_seconds']:.2f} segundos"
            )
            self.logger.info("-" * 80)
            self.logger.info(
                f"Roles criadas: {self.clone_stats['roles_created']}")
            self.logger.info(
                f"Tabelas copiadas: {self.clone_stats['tables_copied']}")
            self.logger.info(
                f"Views criadas: {self.clone_stats['views_created']}")
            self.logger.info(
                f"Functions criadas: {self.clone_stats['functions_created']}")
            self.logger.info(
                f"Permissões aplicadas: {self.clone_stats['permissions_applied']}")

            if self.clone_stats['errors']:
                self.logger.info("-" * 80)
                self.logger.info(f"Erros: {len(self.clone_stats['errors'])}")
                for idx, error in enumerate(self.clone_stats['errors'], 1):
                    self.logger.info(f"  {idx}. {error}")

            self.logger.info("=" * 80)

        except Exception as e:
            self.logger.error(f"Erro ao imprimir resumo: {e}")


if __name__ == "__main__":
    import doctest
    doctest.testmod()
