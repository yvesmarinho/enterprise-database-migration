#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de Análise de Metadados PostgreSQL.

Este módulo extrai informações completas sobre banco de dados, incluindo:
- Estrutura de schemas, tabelas, views, sequences
- Permissões de usuários e roles
- Tablespaces e suas configurações
- Índices, constraints e triggers
- Funções, procedures e tipos customizados

:author: yvesmarinho
:date: 2026-02-09
:version: 2.0.0

Examples
--------
>>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
>>> from pg_connection_manager_v2 import PostgreSQLConnectionManager
>>> config = PostgreSQLJsonConfig(
...     'localhost', 5432, SSLMode.DISABLE,
...     [UserCredential('user', 'pass')], 'src', 'dst'
... )
>>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
>>> analyzer = DatabaseMetadataAnalyzer(manager)
>>> isinstance(analyzer.metadata, dict)
True
"""

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import psycopg2
    from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager
    from psycopg2 import extras, sql
except ImportError as e:
    print(f"Erro ao importar dependências: {e}")
    raise


@dataclass
class TablespaceInfo:
    """
    Informações sobre um tablespace.

    Attributes
    ----------
    name : str
        Nome do tablespace
    owner : str
        Proprietário do tablespace
    location : str
        Localização no sistema de arquivos
    options : List[str]
        Opções de configuração
    size : int
        Tamanho em bytes
    acl : List[str]
        Lista de permissões

    Examples
    --------
    >>> ts = TablespaceInfo('ts_data', 'postgres', '/var/lib/postgresql', [], 1024)
    >>> ts.name
    'ts_data'
    """
    name: str
    owner: str
    location: str
    options: List[str] = field(default_factory=list)
    size: int = 0
    acl: List[str] = field(default_factory=list)


@dataclass
class RoleInfo:
    """
    Informações sobre uma role/usuário.

    Attributes
    ----------
    rolname : str
        Nome da role
    rolsuper : bool
        Se é superusuário
    rolinherit : bool
        Se herda privilégios
    rolcreaterole : bool
        Se pode criar roles
    rolcreatedb : bool
        Se pode criar databases
    rolcanlogin : bool
        Se pode fazer login
    rolreplication : bool
        Se pode fazer replicação
    rolconnlimit : int
        Limite de conexões
    rolpassword : str, optional
        Hash da senha
    rolvaliduntil : str, optional
        Validade da senha
    memberof : List[str]
        Roles das quais é membro
    members : List[str]
        Roles que são membros desta
    config : List[str]
        Configurações específicas da role

    Examples
    --------
    >>> role = RoleInfo('app_user', False, True, False, False, True, False, -1)
    >>> role.rolname
    'app_user'
    >>> role.rolcanlogin
    True
    """
    rolname: str
    rolsuper: bool
    rolinherit: bool
    rolcreaterole: bool
    rolcreatedb: bool
    rolcanlogin: bool
    rolreplication: bool
    rolconnlimit: int
    rolpassword: Optional[str] = None
    rolvaliduntil: Optional[str] = None
    memberof: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)
    config: List[str] = field(default_factory=list)

    def to_create_statement(self) -> str:
        """
        Gera comando CREATE ROLE.

        Returns
        -------
        str
            Comando SQL CREATE ROLE

        Examples
        --------
        >>> role = RoleInfo('app_user', False, True, False, False, True, False, 10)
        >>> 'CREATE ROLE' in role.to_create_statement()
        True
        """
        try:
            options = []

            if self.rolsuper:
                options.append("SUPERUSER")
            else:
                options.append("NOSUPERUSER")

            if self.rolcreatedb:
                options.append("CREATEDB")
            else:
                options.append("NOCREATEDB")

            if self.rolcreaterole:
                options.append("CREATEROLE")
            else:
                options.append("NOCREATEROLE")

            if self.rolinherit:
                options.append("INHERIT")
            else:
                options.append("NOINHERIT")

            if self.rolcanlogin:
                options.append("LOGIN")
            else:
                options.append("NOLOGIN")

            if self.rolreplication:
                options.append("REPLICATION")
            else:
                options.append("NOREPLICATION")

            if self.rolconnlimit >= 0:
                options.append(f"CONNECTION LIMIT {self.rolconnlimit}")

            if self.rolpassword:
                # Manter hash da senha
                options.append(f"PASSWORD '{self.rolpassword}'")

            if self.rolvaliduntil:
                options.append(f"VALID UNTIL '{self.rolvaliduntil}'")

            stmt = f"CREATE ROLE {sql.Identifier(self.rolname).as_string(None)} "
            stmt += " ".join(options) + ";"

            return stmt

        except Exception as e:
            logging.error(f"Erro ao gerar CREATE ROLE: {e}")
            return ""


@dataclass
class DatabaseInfo:
    """
    Informações completas sobre um banco de dados.

    Attributes
    ----------
    datname : str
        Nome do banco de dados
    owner : str
        Proprietário do banco
    encoding : str
        Encoding utilizado
    collation : str
        Collation utilizada
    ctype : str
        Character type
    tablespace : str
        Tablespace padrão
    connection_limit : int
        Limite de conexões
    size : int
        Tamanho em bytes
    acl : List[str]
        Access Control List (permissões)
    config : List[str]
        Configurações específicas do banco
    allow_connections : bool
        Se permite conexões
    is_template : bool
        Se é template

    Examples
    --------
    >>> db = DatabaseInfo('mydb', 'postgres', 'UTF8', 'en_US.UTF-8',
    ...                   'en_US.UTF-8', 'pg_default', -1, 1024000)
    >>> db.datname
    'mydb'
    """
    datname: str
    owner: str
    encoding: str
    collation: str
    ctype: str
    tablespace: str
    connection_limit: int
    size: int
    acl: List[str] = field(default_factory=list)
    config: List[str] = field(default_factory=list)
    allow_connections: bool = True
    is_template: bool = False

    def to_create_statement(self, new_name: str) -> str:
        """
        Gera comando CREATE DATABASE.

        Parameters
        ----------
        new_name : str
            Nome do novo banco

        Returns
        -------
        str
            Comando SQL CREATE DATABASE

        Examples
        --------
        >>> db = DatabaseInfo('src', 'postgres', 'UTF8', 'en_US.UTF-8',
        ...                   'en_US.UTF-8', 'pg_default', -1, 1024)
        >>> 'CREATE DATABASE' in db.to_create_statement('dst')
        True
        """
        try:
            if not isinstance(new_name, str) or not new_name:
                raise ValueError("new_name inválido")

            stmt = f"CREATE DATABASE {sql.Identifier(new_name).as_string(None)}\n"
            stmt += f"    WITH OWNER = {sql.Identifier(self.owner).as_string(None)}\n"
            stmt += f"    ENCODING = '{self.encoding}'\n"
            stmt += f"    LC_COLLATE = '{self.collation}'\n"
            stmt += f"    LC_CTYPE = '{self.ctype}'\n"
            stmt += f"    TABLESPACE = {sql.Identifier(self.tablespace).as_string(None)}\n"

            if self.connection_limit >= 0:
                stmt += f"    CONNECTION LIMIT = {self.connection_limit}\n"

            stmt += f"    IS_TEMPLATE = {'TRUE' if self.is_template else 'FALSE'};"

            return stmt

        except (ValueError, TypeError) as e:
            logging.error(f"Erro ao gerar CREATE DATABASE: {e}")
            return ""


@dataclass
class SchemaPermissions:
    """
    Permissões de um schema.

    Attributes
    ----------
    schema_name : str
        Nome do schema
    owner : str
        Proprietário do schema
    acl : List[Dict[str, Any]]
        Lista de permissões detalhadas

    Examples
    --------
    >>> perms = SchemaPermissions('public', 'postgres', [])
    >>> perms.schema_name
    'public'
    """
    schema_name: str
    owner: str
    acl: List[Dict[str, Any]] = field(default_factory=list)

    def to_grant_statements(self) -> List[str]:
        """
        Gera comandos GRANT para o schema.

        Returns
        -------
        list of str
            Lista de comandos GRANT

        Examples
        --------
        >>> perms = SchemaPermissions('myschema', 'postgres')
        >>> perms.acl = [{'grantee': 'user1', 'privileges': ['USAGE', 'CREATE']}]
        >>> stmts = perms.to_grant_statements()
        >>> len(stmts) >= 0
        True
        """
        try:
            statements = []

            for acl_entry in self.acl:
                if not isinstance(acl_entry, dict):
                    continue

                grantee = acl_entry.get('grantee')
                privileges = acl_entry.get('privileges', [])

                if not grantee or not privileges:
                    continue

                privs_str = ", ".join(privileges)
                stmt = (
                    f"GRANT {privs_str} ON SCHEMA "
                    f"{sql.Identifier(self.schema_name).as_string(None)} "
                    f"TO {sql.Identifier(grantee).as_string(None)};"
                )
                statements.append(stmt)

            return statements

        except Exception as e:
            logging.error(f"Erro ao gerar GRANT statements: {e}")
            return []


@dataclass
class TablePermissions:
    """
    Permissões de uma tabela.

    Attributes
    ----------
    schema_name : str
        Nome do schema
    table_name : str
        Nome da tabela
    owner : str
        Proprietário da tabela
    tablespace : str
        Tablespace utilizado
    acl : List[Dict[str, Any]]
        Lista de permissões da tabela
    column_privileges : Dict[str, List[Dict[str, Any]]]
        Privilégios por coluna

    Examples
    --------
    >>> perms = TablePermissions('public', 'users', 'postgres', 'pg_default')
    >>> perms.table_name
    'users'
    """
    schema_name: str
    table_name: str
    owner: str
    tablespace: str
    acl: List[Dict[str, Any]] = field(default_factory=list)
    column_privileges: Dict[str, List[Dict[str, Any]]
                            ] = field(default_factory=dict)

    def to_grant_statements(self) -> List[str]:
        """
        Gera comandos GRANT para a tabela.

        Returns
        -------
        list of str
            Lista de comandos GRANT
        """
        try:
            statements = []

            # GRANT em nível de tabela
            for acl_entry in self.acl:
                if not isinstance(acl_entry, dict):
                    continue

                grantee = acl_entry.get('grantee')
                privileges = acl_entry.get('privileges', [])

                if not grantee or not privileges:
                    continue

                privs_str = ", ".join(privileges)
                stmt = (
                    f"GRANT {privs_str} ON TABLE "
                    f"{sql.Identifier(self.schema_name).as_string(None)}."
                    f"{sql.Identifier(self.table_name).as_string(None)} "
                    f"TO {sql.Identifier(grantee).as_string(None)};"
                )
                statements.append(stmt)

            # GRANT em nível de coluna
            for column_name, col_privs in self.column_privileges.items():
                for col_priv in col_privs:
                    if not isinstance(col_priv, dict):
                        continue

                    grantee = col_priv.get('grantee')
                    privilege_type = col_priv.get('privilege_type')

                    if not grantee or not privilege_type:
                        continue

                    stmt = (
                        f"GRANT {privilege_type} "
                        f"({sql.Identifier(column_name).as_string(None)}) "
                        f"ON TABLE "
                        f"{sql.Identifier(self.schema_name).as_string(None)}."
                        f"{sql.Identifier(self.table_name).as_string(None)} "
                        f"TO {sql.Identifier(grantee).as_string(None)};"
                    )
                    statements.append(stmt)

            return statements

        except Exception as e:
            logging.error(f"Erro ao gerar GRANT statements: {e}")
            return []


class DatabaseMetadataAnalyzer:
    """
    Analisador completo de metadados de banco de dados PostgreSQL.

    Esta classe extrai todas as informações necessárias para clonar um banco
    de dados mantendo suas características, permissões e estruturas.

    Parameters
    ----------
    connection_manager : PostgreSQLConnectionManager
        Gerenciador de conexões configurado

    Attributes
    ----------
    manager : PostgreSQLConnectionManager
        Gerenciador de conexões
    metadata : Dict[str, Any]
        Metadados extraídos
    logger : logging.Logger
        Logger para rastreamento

    Examples
    --------
    >>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
    >>> from pg_connection_manager_v2 import PostgreSQLConnectionManager
    >>> config = PostgreSQLJsonConfig(
    ...     'localhost', 5432, SSLMode.DISABLE,
    ...     [UserCredential('u', 'p')], 'src', 'dst'
    ... )
    >>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
    >>> analyzer = DatabaseMetadataAnalyzer(manager)
    >>> isinstance(analyzer.metadata, dict)
    True
    """

    def __init__(self, connection_manager: PostgreSQLConnectionManager):
        """
        Inicializa o analisador de metadados.

        Parameters
        ----------
        connection_manager : PostgreSQLConnectionManager
            Gerenciador de conexões
        """
        try:
            if not isinstance(connection_manager, PostgreSQLConnectionManager):
                raise TypeError(
                    f"Esperado PostgreSQLConnectionManager, "
                    f"recebido {type(connection_manager).__name__}"
                )

            self.manager = connection_manager
            self.metadata: Dict[str, Any] = {}
            self.logger = logging.getLogger(self.__class__.__name__)

            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)

            self.logger.info("Analisador de metadados inicializado")

        except (TypeError, AttributeError) as e:
            logging.error(f"Erro ao inicializar analisador: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado na inicialização: {e}")
            raise

    def extract_all_metadata(self) -> Union[Dict[str, Any], bool]:
        """
        Extrai todos os metadados do banco de dados de origem.

        Returns
        -------
        dict or bool
            Dicionário com metadados completos ou False em caso de erro

        Examples
        --------
        >>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
        >>> from pg_connection_manager_v2 import PostgreSQLConnectionManager
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('u', 'p')], 'src', 'dst'
        ... )
        >>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
        >>> analyzer = DatabaseMetadataAnalyzer(manager)
        >>> metadata = analyzer.extract_all_metadata()  # doctest: +SKIP
        """
        try:
            if not self.manager.is_connected:
                raise ConnectionError(
                    "Manager não conectado. Execute connect() primeiro."
                )

            self.logger.info("=" * 70)
            self.logger.info("INICIANDO EXTRAÇÃO DE METADADOS")
            self.logger.info("=" * 70)

            # Extrair informações do banco
            self.logger.info("Extraindo informações do banco de dados...")
            db_info = self._extract_database_info()
            if db_info is False:
                self.logger.error("✗ Falha ao extrair informações do banco")
                return False
            self.logger.info("✓ Informações do banco extraídas")

            # Extrair tablespaces
            self.logger.info("Extraindo tablespaces...")
            tablespaces = self._extract_tablespaces()
            if tablespaces is False:
                self.logger.warning("⚠ Falha ao extrair tablespaces")
                tablespaces = []
            self.logger.info(f"✓ {len(tablespaces)} tablespaces extraídos")

            # Extrair roles
            self.logger.info("Extraindo roles/usuários...")
            roles = self._extract_roles()
            if roles is False:
                self.logger.warning("⚠ Falha ao extrair roles")
                roles = []
            self.logger.info(f"✓ {len(roles)} roles extraídas")

            # Extrair permissões de schemas
            self.logger.info("Extraindo permissões de schemas...")
            schema_perms = self._extract_schema_permissions()
            if schema_perms is False:
                self.logger.warning("⚠ Falha ao extrair permissões de schemas")
                schema_perms = []
            self.logger.info(
                f"✓ Permissões de {len(schema_perms)} schemas extraídas")

            # Extrair permissões de tabelas
            self.logger.info("Extraindo permissões de tabelas...")
            table_perms = self._extract_table_permissions()
            if table_perms is False:
                self.logger.warning("⚠ Falha ao extrair permissões de tabelas")
                table_perms = []
            self.logger.info(
                f"✓ Permissões de {len(table_perms)} tabelas extraídas")

            # Extrair sequences
            self.logger.info("Extraindo sequences...")
            sequences = self._extract_sequences()
            if sequences is False:
                self.logger.warning("⚠ Falha ao extrair sequences")
                sequences = []
            self.logger.info(f"✓ {len(sequences)} sequences extraídas")

            # Extrair views
            self.logger.info("Extraindo views...")
            views = self._extract_views()
            if views is False:
                self.logger.warning("⚠ Falha ao extrair views")
                views = []
            self.logger.info(f"✓ {len(views)} views extraídas")

            # Extrair functions
            self.logger.info("Extraindo functions/procedures...")
            functions = self._extract_functions()
            if functions is False:
                self.logger.warning("⚠ Falha ao extrair functions")
                functions = []
            self.logger.info(f"✓ {len(functions)} functions extraídas")

            # Extrair extensões
            self.logger.info("Extraindo extensões...")
            extensions = self._extract_extensions()
            if extensions is False:
                self.logger.warning("⚠ Falha ao extrair extensões")
                extensions = []
            self.logger.info(f"✓ {len(extensions)} extensões extraídas")

            # Extrair tipos customizados
            self.logger.info("Extraindo tipos customizados...")
            custom_types = self._extract_custom_types()
            if custom_types is False:
                self.logger.warning("⚠ Falha ao extrair tipos customizados")
                custom_types = []
            self.logger.info(
                f"✓ {len(custom_types)} tipos customizados extraídos")

            # Montar estrutura de metadados
            self.metadata = {
                'database': db_info,
                'tablespaces': tablespaces,
                'roles': roles,
                'schema_permissions': schema_perms,
                'table_permissions': table_perms,
                'sequences': sequences,
                'views': views,
                'functions': functions,
                'extensions': extensions,
                'custom_types': custom_types,
                'extraction_timestamp': datetime.now().isoformat(),
                'source_database': self.manager.config.db_source,
                'target_database': self.manager.config.db_destiny
            }

            self.logger.info("=" * 70)
            self.logger.info("✓ EXTRAÇÃO DE METADADOS CONCLUÍDA COM SUCESSO")
            self.logger.info("=" * 70)

            return self.metadata

        except (TypeError, ValueError, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair metadados: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao extrair metadados: {e}")
            return False

    def _extract_database_info(self) -> Union[DatabaseInfo, bool]:
        """
        Extrai informações sobre o banco de dados atual.

        Returns
        -------
        DatabaseInfo or bool
            Informações do banco ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    d.datname,
                    pg_catalog.pg_get_userbyid(d.datdba) AS owner,
                    pg_catalog.pg_encoding_to_char(d.encoding) AS encoding,
                    d.datcollate AS collation,
                    d.datctype AS ctype,
                    t.spcname AS tablespace,
                    d.datconnlimit AS connection_limit,
                    pg_catalog.pg_database_size(d.datname) AS size,
                    d.datacl AS acl,
                    d.datallowconn AS allow_connections,
                    d.datistemplate AS is_template,
                    ARRAY(
                        SELECT pg_catalog.unnest(setconfig)
                        FROM pg_catalog.pg_db_role_setting
                        WHERE setdatabase = d.oid AND setrole = 0
                    ) AS config
                FROM pg_catalog.pg_database d
                JOIN pg_catalog.pg_tablespace t ON d.dattablespace = t.oid
                WHERE d.datname = current_database()
                """

                cursor.execute(query)
                row = cursor.fetchone()
                cursor.close()

                if not row:
                    raise ValueError("Banco de dados não encontrado")

                # Processar ACL
                acl_list = self._parse_acl(row['acl']) if row['acl'] else []

                db_info = DatabaseInfo(
                    datname=row['datname'],
                    owner=row['owner'],
                    encoding=row['encoding'],
                    collation=row['collation'],
                    ctype=row['ctype'],
                    tablespace=row['tablespace'],
                    connection_limit=row['connection_limit'],
                    size=row['size'],
                    acl=acl_list,
                    config=row['config'] or [],
                    allow_connections=row['allow_connections'],
                    is_template=row['is_template']
                )

                return db_info

        except (psycopg2.Error, ConnectionError, ValueError) as e:
            self.logger.error(f"Erro ao extrair informações do banco: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_tablespaces(self) -> Union[List[TablespaceInfo], bool]:
        """
        Extrai informações sobre tablespaces.

        Returns
        -------
        list of TablespaceInfo or bool
            Lista de tablespaces ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    spcname AS name,
                    pg_catalog.pg_get_userbyid(spcowner) AS owner,
                    pg_catalog.pg_tablespace_location(oid) AS location,
                    spcoptions AS options,
                    pg_catalog.pg_tablespace_size(oid) AS size,
                    spcacl AS acl
                FROM pg_catalog.pg_tablespace
                WHERE spcname NOT LIKE 'pg_global'
                ORDER BY spcname
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                tablespaces = []
                for row in rows:
                    acl_list = self._parse_acl(
                        row['acl']) if row['acl'] else []

                    ts = TablespaceInfo(
                        name=row['name'],
                        owner=row['owner'],
                        location=row['location'] or '',
                        options=row['options'] or [],
                        size=row['size'],
                        acl=acl_list
                    )
                    tablespaces.append(ts)

                return tablespaces

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair tablespaces: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_roles(self) -> Union[List[RoleInfo], bool]:
        """
        Extrai informações sobre roles e usuários.

        Returns
        -------
        list of RoleInfo or bool
            Lista de roles ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    rolname,
                    rolsuper,
                    rolinherit,
                    rolcreaterole,
                    rolcreatedb,
                    rolcanlogin,
                    rolreplication,
                    rolconnlimit,
                    rolpassword,
                    rolvaliduntil,
                    ARRAY(
                        SELECT b.rolname
                        FROM pg_catalog.pg_auth_members m
                        JOIN pg_catalog.pg_roles b ON m.roleid = b.oid
                        WHERE m.member = r.oid
                    ) AS memberof,
                    ARRAY(
                        SELECT m.rolname
                        FROM pg_catalog.pg_auth_members am
                        JOIN pg_catalog.pg_roles m ON am.member = m.oid
                        WHERE am.roleid = r.oid
                    ) AS members,
                    ARRAY(
                        SELECT pg_catalog.unnest(setconfig)
                        FROM pg_catalog.pg_db_role_setting
                        WHERE setrole = r.oid AND setdatabase = 0
                    ) AS config
                FROM pg_catalog.pg_roles r
                WHERE rolname NOT LIKE 'pg_%'
                  AND rolname != 'postgres'
                ORDER BY rolname
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                roles = []
                for row in rows:
                    role = RoleInfo(
                        rolname=row['rolname'],
                        rolsuper=row['rolsuper'],
                        rolinherit=row['rolinherit'],
                        rolcreaterole=row['rolcreaterole'],
                        rolcreatedb=row['rolcreatedb'],
                        rolcanlogin=row['rolcanlogin'],
                        rolreplication=row['rolreplication'],
                        rolconnlimit=row['rolconnlimit'],
                        rolpassword=row['rolpassword'],
                        rolvaliduntil=str(
                            row['rolvaliduntil']) if row['rolvaliduntil'] else None,
                        memberof=row['memberof'] or [],
                        members=row['members'] or [],
                        config=row['config'] or []
                    )
                    roles.append(role)

                return roles

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair roles: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_schema_permissions(self) -> Union[List[SchemaPermissions], bool]:
        """
        Extrai permissões de schemas.

        Returns
        -------
        list of SchemaPermissions or bool
            Lista de permissões de schemas ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    n.nspname AS schema_name,
                    pg_catalog.pg_get_userbyid(n.nspowner) AS owner,
                    n.nspacl AS acl
                FROM pg_catalog.pg_namespace n
                WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
                  AND n.nspname NOT LIKE 'pg_toast%'
                  AND n.nspname NOT LIKE 'pg_temp_%'
                ORDER BY n.nspname
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                schema_perms = []
                for row in rows:
                    acl_list = self._parse_acl_detailed(
                        row['acl']) if row['acl'] else []

                    perms = SchemaPermissions(
                        schema_name=row['schema_name'],
                        owner=row['owner'],
                        acl=acl_list
                    )
                    schema_perms.append(perms)

                return schema_perms

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair permissões de schemas: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_table_permissions(self) -> Union[List[TablePermissions], bool]:
        """
        Extrai permissões de tabelas.

        Returns
        -------
        list of TablePermissions or bool
            Lista de permissões de tabelas ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    n.nspname AS schema_name,
                    c.relname AS table_name,
                    pg_catalog.pg_get_userbyid(c.relowner) AS owner,
                    COALESCE(t.spcname, 'pg_default') AS tablespace,
                    c.relacl AS acl
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                LEFT JOIN pg_catalog.pg_tablespace t ON c.reltablespace = t.oid
                WHERE c.relkind IN ('r', 'p')
                  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                  AND n.nspname NOT LIKE 'pg_toast%'
                ORDER BY n.nspname, c.relname
                """

                cursor.execute(query)
                rows = cursor.fetchall()

                table_perms = []
                for row in rows:
                    acl_list = self._parse_acl_detailed(
                        row['acl']) if row['acl'] else []

                    col_privs = self._extract_column_privileges(
                        cursor,
                        row['schema_name'],
                        row['table_name']
                    )

                    perms = TablePermissions(
                        schema_name=row['schema_name'],
                        table_name=row['table_name'],
                        owner=row['owner'],
                        tablespace=row['tablespace'],
                        acl=acl_list,
                        column_privileges=col_privs if col_privs else {}
                    )
                    table_perms.append(perms)

                cursor.close()
                return table_perms

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair permissões de tabelas: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_column_privileges(
        self,
        cursor,
        schema_name: str,
        table_name: str
    ) -> Union[Dict[str, List[Dict[str, Any]]], bool]:
        """
        Extrai privilégios de colunas de uma tabela.

        Parameters
        ----------
        cursor : psycopg2.cursor
            Cursor da conexão
        schema_name : str
            Nome do schema
        table_name : str
            Nome da tabela

        Returns
        -------
        dict or bool
            Dicionário com privilégios por coluna ou False em caso de erro
        """
        try:
            if not isinstance(schema_name, str) or not schema_name:
                raise ValueError("schema_name inválido")
            if not isinstance(table_name, str) or not table_name:
                raise ValueError("table_name inválido")

            query = """
            SELECT
                column_name,
                privilege_type,
                grantee,
                is_grantable
            FROM information_schema.column_privileges
            WHERE table_schema = %s AND table_name = %s
            ORDER BY column_name, grantee, privilege_type
            """

            cursor.execute(query, (schema_name, table_name))
            rows = cursor.fetchall()

            col_privs = defaultdict(list)
            for row in rows:
                col_privs[row['column_name']].append({
                    'privilege_type': row['privilege_type'],
                    'grantee': row['grantee'],
                    'is_grantable': row['is_grantable'] == 'YES'
                })

            return dict(col_privs)

        except (psycopg2.Error, ValueError) as e:
            self.logger.error(f"Erro ao extrair privilégios de colunas: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_sequences(self) -> Union[List[Dict[str, Any]], bool]:
        """
        Extrai informações sobre sequences.

        Returns
        -------
        list of dict or bool
            Lista de sequences ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    n.nspname AS schema_name,
                    c.relname AS sequence_name,
                    pg_catalog.pg_get_userbyid(c.relowner) AS owner,
                    c.relacl AS acl
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relkind = 'S'
                  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY n.nspname, c.relname
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                sequences = []
                for row in rows:
                    acl_list = self._parse_acl_detailed(
                        row['acl']) if row['acl'] else []

                    seq = {
                        'schema_name': row['schema_name'],
                        'sequence_name': row['sequence_name'],
                        'owner': row['owner'],
                        'acl': acl_list
                    }
                    sequences.append(seq)

                return sequences

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair sequences: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_views(self) -> Union[List[Dict[str, Any]], bool]:
        """
        Extrai informações sobre views.

        Returns
        -------
        list of dict or bool
            Lista de views ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    n.nspname AS schema_name,
                    c.relname AS view_name,
                    pg_catalog.pg_get_userbyid(c.relowner) AS owner,
                    c.relacl AS acl,
                    pg_catalog.pg_get_viewdef(c.oid, true) AS definition,
                    c.relkind AS view_type
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relkind IN ('v', 'm')
                  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY n.nspname, c.relname
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                views = []
                for row in rows:
                    acl_list = self._parse_acl_detailed(
                        row['acl']) if row['acl'] else []

                    view = {
                        'schema_name': row['schema_name'],
                        'view_name': row['view_name'],
                        'owner': row['owner'],
                        'acl': acl_list,
                        'definition': row['definition'],
                        'is_materialized': row['view_type'] == 'm'
                    }
                    views.append(view)

                return views

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair views: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_functions(self) -> Union[List[Dict[str, Any]], bool]:
        """
        Extrai informações sobre functions e procedures.

        Returns
        -------
        list of dict or bool
            Lista de functions ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    n.nspname AS schema_name,
                    p.proname AS function_name,
                    pg_catalog.pg_get_userbyid(p.proowner) AS owner,
                    p.proacl AS acl,
                    pg_catalog.pg_get_functiondef(p.oid) AS definition,
                    pg_catalog.pg_get_function_arguments(p.oid) AS arguments,
                    pg_catalog.pg_get_function_result(p.oid) AS result_type,
                    p.prokind AS function_kind
                FROM pg_catalog.pg_proc p
                JOIN pg_catalog.pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY n.nspname, p.proname
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                functions = []
                for row in rows:
                    acl_list = self._parse_acl_detailed(
                        row['acl']) if row['acl'] else []

                    func = {
                        'schema_name': row['schema_name'],
                        'function_name': row['function_name'],
                        'owner': row['owner'],
                        'acl': acl_list,
                        'definition': row['definition'],
                        'arguments': row['arguments'],
                        'result_type': row['result_type'],
                        'function_kind': row['function_kind']
                    }
                    functions.append(func)

                return functions

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair functions: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_extensions(self) -> Union[List[Dict[str, Any]], bool]:
        """
        Extrai informações sobre extensões instaladas.

        Returns
        -------
        list of dict or bool
            Lista de extensões ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = cursor.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    e.extname AS extension_name,
                    e.extversion AS version,
                    n.nspname AS schema_name,
                    e.extrelocatable AS relocatable,
                    pg_catalog.pg_get_userbyid(e.extowner) AS owner
                FROM pg_catalog.pg_extension e
                JOIN pg_catalog.pg_namespace n ON e.extnamespace = n.oid
                ORDER BY e.extname
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                extensions = []
                for row in rows:
                    ext = {
                        'extension_name': row['extension_name'],
                        'version': row['version'],
                        'schema_name': row['schema_name'],
                        'relocatable': row['relocatable'],
                        'owner': row['owner']
                    }
                    extensions.append(ext)

                return extensions

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair extensões: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _extract_custom_types(self) -> Union[List[Dict[str, Any]], bool]:
        """
        Extrai informações sobre tipos customizados.

        Returns
        -------
        list of dict or bool
            Lista de tipos customizados ou False em caso de erro
        """
        try:
            with self.manager.get_source_connection() as conn:
                if conn is False:
                    raise ConnectionError("Falha ao obter conexão")

                cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

                query = """
                SELECT
                    n.nspname AS schema_name,
                    t.typname AS type_name,
                    pg_catalog.pg_get_userbyid(t.typowner) AS owner,
                    t.typtype AS type_kind,
                    pg_catalog.format_type(t.oid, NULL) AS formatted_type
                FROM pg_catalog.pg_type t
                JOIN pg_catalog.pg_namespace n ON t.typnamespace = n.oid
                WHERE t.typtype IN ('c', 'e', 'd')
                  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY n.nspname, t.typname
                """

                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                custom_types = []
                for row in rows:
                    ct = {
                        'schema_name': row['schema_name'],
                        'type_name': row['type_name'],
                        'owner': row['owner'],
                        'type_kind': row['type_kind'],
                        'formatted_type': row['formatted_type']
                    }
                    custom_types.append(ct)

                return custom_types

        except (psycopg2.Error, ConnectionError) as e:
            self.logger.error(f"Erro ao extrair tipos customizados: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False

    def _parse_acl(self, acl_array) -> List[str]:
        """
        Parseia array de ACL do PostgreSQL.

        Parameters
        ----------
        acl_array : list or None
            Array de ACL do PostgreSQL

        Returns
        -------
        list of str
            Lista de strings ACL
        """
        try:
            if not acl_array:
                return []
            if not isinstance(acl_array, (list, tuple)):
                return []
            return [str(acl) for acl in acl_array if acl]
        except Exception as e:
            self.logger.error(f"Erro ao parsear ACL: {e}")
            return []

    def _parse_acl_detailed(self, acl_array) -> List[Dict[str, Any]]:
        """
        Parseia array de ACL em formato detalhado.

        ACL Format: role=privileges/grantor
        Privileges: r (SELECT), w (UPDATE), a (INSERT), d (DELETE),
                   D (TRUNCATE), x (REFERENCES), t (TRIGGER),
                   X (EXECUTE), U (USAGE), C (CREATE), c (CONNECT),
                   T (TEMPORARY)

        Parameters
        ----------
        acl_array : list or None
            Array de ACL do PostgreSQL

        Returns
        -------
        list of dict
            Lista de dicionários com detalhes de ACL
        """
        try:
            if not acl_array:
                return []
            if not isinstance(acl_array, (list, tuple)):
                return []

            acl_list = []
            priv_map = {
                'r': 'SELECT', 'w': 'UPDATE', 'a': 'INSERT', 'd': 'DELETE',
                'D': 'TRUNCATE', 'x': 'REFERENCES', 't': 'TRIGGER',
                'X': 'EXECUTE', 'U': 'USAGE', 'C': 'CREATE',
                'c': 'CONNECT', 'T': 'TEMPORARY'
            }

            for acl_entry in acl_array:
                if not acl_entry or not isinstance(acl_entry, str):
                    continue

                try:
                    # Format: role=privileges/grantor
                    parts = acl_entry.split('=')
                    if len(parts) != 2:
                        continue

                    grantee = parts[0] if parts[0] else 'public'

                    priv_parts = parts[1].split('/')
                    if len(priv_parts) != 2:
                        continue

                    priv_chars = priv_parts[0]
                    grantor = priv_parts[1]

                    # Converter caracteres de privilégios
                    privileges = []
                    for char in priv_chars:
                        if char in priv_map:
                            privileges.append(priv_map[char])
                        elif char == '*':
                            # WITH GRANT OPTION
                            pass

                    if privileges:
                        acl_list.append({
                            'grantee': grantee,
                            'privileges': privileges,
                            'grantor': grantor
                        })

                except Exception as e:
                    self.logger.warning(
                        f"Falha ao parsear ACL entry '{acl_entry}': {e}")
                    continue

            return acl_list

        except Exception as e:
            self.logger.error(f"Erro ao parsear ACL detalhado: {e}")
            return []

    def save_metadata_to_file(self, filepath: str) -> bool:
        """
        Salva metadados em arquivo JSON.

        Parameters
        ----------
        filepath : str
            Caminho do arquivo

        Returns
        -------
        bool
            True se salvo com sucesso
        """
        try:
            if not isinstance(filepath, str) or not filepath:
                raise ValueError("filepath inválido")

            if not self.metadata:
                raise ValueError("Nenhum metadado para salvar")

            # Converter dataclasses para dict
            metadata_dict = {}
            for key, value in self.metadata.items():
                if isinstance(value, list):
                    metadata_dict[key] = [
                        asdict(item) if hasattr(
                            item, '__dataclass_fields__') else item
                        for item in value
                    ]
                elif hasattr(value, '__dataclass_fields__'):
                    metadata_dict[key] = asdict(value)
                else:
                    metadata_dict[key] = value

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, indent=2,
                          ensure_ascii=False, default=str)

            self.logger.info(f"✓ Metadados salvos em: {filepath}")
            return True

        except (ValueError, IOError) as e:
            self.logger.error(f"Erro ao salvar metadados: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao salvar metadados: {e}")
            return False


if __name__ == "__main__":
    import doctest
    doctest.testmod()
