#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador de Conexões PostgreSQL - Versão 2.0 com suporte JSON.

Este módulo gerencia conexões PostgreSQL usando configuração JSON,
com suporte a múltiplos usuários, fallback automático e pooling.

:author: yvesmarinho
:date: 2026-02-09
:version: 2.0.0

Examples
--------
>>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
>>> config = PostgreSQLJsonConfig(
...     'localhost', 5432, SSLMode.DISABLE,
...     [UserCredential('user', 'pass')], 'source_db', 'dest_db'
... )
>>> manager = PostgreSQLConnectionManager(config)
>>> manager.config.host
'localhost'
"""

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import psycopg2
    from pg_json_config_Version2 import PostgreSQLJsonConfig, UserCredential
    from psycopg2 import extensions, extras, pool, sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from sqlalchemy import MetaData, create_engine, text
    from sqlalchemy.engine import URL, Engine
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy.pool import NullPool, QueuePool
except ImportError as e:
    print(f"Erro ao importar dependências: {e}")
    raise


class PostgreSQLConnectionManager:
    """
    Gerenciador de conexões PostgreSQL com configuração JSON.

    Esta classe gerencia conexões usando psycopg2 e SQLAlchemy,
    com suporte a configuração JSON, múltiplos usuários e pooling.

    Parameters
    ----------
    config : PostgreSQLJsonConfig
        Configuração JSON do sistema
    use_pool : bool, optional
        Se deve usar pool de conexões (padrão: True)
    auto_validate : bool, optional
        Se deve validar credenciais automaticamente (padrão: True)

    Attributes
    ----------
    config : PostgreSQLJsonConfig
        Configuração atual
    source_pool : psycopg2.pool.ThreadedConnectionPool or None
        Pool para banco de origem
    destiny_pool : psycopg2.pool.ThreadedConnectionPool or None
        Pool para banco de destino
    source_engine : sqlalchemy.engine.Engine or None
        Engine SQLAlchemy para origem
    destiny_engine : sqlalchemy.engine.Engine or None
        Engine SQLAlchemy para destino
    is_connected : bool
        Status de conexão

    Examples
    --------
    >>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
    >>> config = PostgreSQLJsonConfig(
    ...     'localhost', 5432, SSLMode.DISABLE,
    ...     [UserCredential('user', 'pass')], 'src', 'dst'
    ... )
    >>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
    >>> manager.config.db_source
    'src'
    """

    @classmethod
    def from_json_file(
        cls,
        filepath: Union[str, Path],
        use_pool: bool = True,
        auto_validate: bool = True
    ) -> 'PostgreSQLConnectionManager':
        """
        Cria manager diretamente de arquivo JSON.

        Parameters
        ----------
        filepath : str or Path
            Caminho do arquivo de configuração JSON
        use_pool : bool, optional
            Se deve usar pool de conexões (padrão: True)
        auto_validate : bool, optional
            Se deve validar credenciais automaticamente (padrão: True)

        Returns
        -------
        PostgreSQLConnectionManager
            Manager configurado e pronto

        Raises
        ------
        FileNotFoundError
            Se arquivo não existe
        json.JSONDecodeError
            Se JSON inválido
        ConnectionError
            Se falha ao validar credenciais

        Examples
        --------
        >>> import tempfile, json
        >>> data = {
        ...     "host": "localhost", "port": 5432, "ssl_mode": "false",
        ...     "possible_users": [{"username": "u", "password": "p"}],
        ...     "db_source": "src", "db_destiny": "dst"
        ... }
        >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        ...     json.dump(data, f)
        ...     tmpfile = f.name
        >>> manager = PostgreSQLConnectionManager.from_json_file(tmpfile, auto_validate=False)
        >>> manager.config.db_source
        'src'
        >>> import os; os.unlink(tmpfile)
        """
        try:
            from pathlib import Path

            if not isinstance(filepath, (str, Path)):
                raise TypeError(
                    f"filepath deve ser str ou Path, "
                    f"recebido {type(filepath).__name__}"
                )

            # Carregar configuração do arquivo JSON
            config = PostgreSQLJsonConfig.from_json_file(filepath)

            # Criar e retornar manager
            return cls(config, use_pool=use_pool, auto_validate=auto_validate)

        except (FileNotFoundError, TypeError, ValueError, ConnectionError) as e:
            logging.error(f"Erro ao criar manager de arquivo JSON: {e}")
            raise
        except Exception as e:
            logging.error(
                f"Erro inesperado ao criar manager de arquivo JSON: {e}")
            raise

    def __init__(
        self,
        config: PostgreSQLJsonConfig,
        use_pool: bool = True,
        auto_validate: bool = True
    ):
        """
        Inicializa o gerenciador de conexões.

        Parameters
        ----------
        config : PostgreSQLJsonConfig
            Configuração do sistema
        use_pool : bool, optional
            Se deve usar pool de conexões
        auto_validate : bool, optional
            Se deve validar credenciais automaticamente
        """
        try:
            # Validação de parâmetros
            if not isinstance(config, PostgreSQLJsonConfig):
                raise TypeError(
                    f"config deve ser PostgreSQLJsonConfig, "
                    f"recebido {type(config).__name__}"
                )
            if not isinstance(use_pool, bool):
                raise TypeError(
                    f"use_pool deve ser bool, "
                    f"recebido {type(use_pool).__name__}"
                )
            if not isinstance(auto_validate, bool):
                raise TypeError(
                    f"auto_validate deve ser bool, "
                    f"recebido {type(auto_validate).__name__}"
                )

            self.config = config
            self.use_pool = use_pool

            # Pools psycopg2
            self.source_pool: Optional[pool.ThreadedConnectionPool] = None
            self.destiny_pool: Optional[pool.ThreadedConnectionPool] = None
            self.postgres_pool: Optional[pool.ThreadedConnectionPool] = None

            # Engines SQLAlchemy
            self.source_engine: Optional[Engine] = None
            self.destiny_engine: Optional[Engine] = None
            self.postgres_engine: Optional[Engine] = None

            # Session factories
            self._source_session_factory = None
            self._destiny_session_factory = None
            self._postgres_session_factory = None

            self.is_connected = False

            # Configurar logging
            self._setup_logging()

            self.logger.info(
                f"Gerenciador inicializado: {config.host}:{config.port}"
            )
            self.logger.info(
                f"Origem: {config.db_source} → Destino: {config.db_destiny}"
            )

            # Validar credenciais se solicitado
            if auto_validate:
                if not self.config.validate_credentials():
                    raise ConnectionError(
                        "Falha ao validar credenciais. "
                        "Verifique usuários e senhas no JSON."
                    )

        except (TypeError, ValueError, ConnectionError) as e:
            logging.error(f"Erro ao inicializar gerenciador: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado na inicialização: {e}")
            raise

    def _setup_logging(self) -> bool:
        """
        Configura o sistema de logging.

        Returns
        -------
        bool
            True se configuração bem-sucedida
        """
        try:
            self.logger = logging.getLogger(self.__class__.__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
            return True
        except Exception as e:
            print(f"Erro ao configurar logging: {e}")
            return False

    def connect(self) -> bool:
        """
        Estabelece conexões com bancos de origem e destino.

        Returns
        -------
        bool
            True se todas as conexões foram estabelecidas

        Examples
        --------
        >>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('user', 'pass')], 'src', 'dst'
        ... )
        >>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
        >>> manager.connect()  # doctest: +SKIP
        True
        """
        try:
            if not self.config.validated_user:
                raise ConnectionError(
                    "Nenhum usuário validado. Execute validate_credentials() primeiro."
                )

            self.logger.info("Estabelecendo conexões...")

            # Conectar ao banco postgres (para operações DDL)
            if not self._connect_database('postgres'):
                self.logger.error("Falha ao conectar ao banco 'postgres'")
                return False

            # Conectar ao banco de origem
            if not self._connect_database(self.config.db_source, is_source=True):
                self.logger.error(
                    f"Falha ao conectar ao banco '{self.config.db_source}'")
                return False

            # Conectar ao banco de destino (se já existir)
            # Não é erro se não existir - será criado depois
            self._connect_database(self.config.db_destiny, is_destiny=True)

            self.is_connected = True
            self.logger.info("✓ Conexões estabelecidas com sucesso")
            return True

        except (ConnectionError, psycopg2.Error) as e:
            self.logger.error(f"Erro ao conectar: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao conectar: {e}")
            return False

    def _connect_database(
        self,
        database: str,
        is_source: bool = False,
        is_destiny: bool = False
    ) -> bool:
        """
        Conecta a um banco de dados específico.

        Parameters
        ----------
        database : str
            Nome do banco de dados
        is_source : bool, optional
            Se é o banco de origem
        is_destiny : bool, optional
            Se é o banco de destino

        Returns
        -------
        bool
            True se conexão bem-sucedida
        """
        try:
            if not isinstance(database, str) or not database:
                raise ValueError("Nome do banco inválido")

            conn_params = self.config.get_connection_params(database=database)
            if conn_params is False:
                raise ValueError("Falha ao obter parâmetros de conexão")

            self.logger.info(f"Conectando ao banco: {database}")

            # Criar pool psycopg2
            if self.use_pool:
                db_pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=self.config.pool_size,
                    **conn_params
                )
            else:
                # Testar conexão sem pool
                test_conn = psycopg2.connect(**conn_params)
                test_conn.close()
                db_pool = None

            # Criar engine SQLAlchemy
            url = URL.create(
                drivername="postgresql+psycopg2",
                username=self.config.validated_user.username,
                password=self.config.validated_user.password,
                host=self.config.host,
                port=self.config.port,
                database=database
            )

            if self.use_pool:
                db_engine = create_engine(
                    url,
                    poolclass=QueuePool,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_pre_ping=True,
                    echo=False
                )
            else:
                db_engine = create_engine(
                    url,
                    poolclass=NullPool,
                    echo=False
                )

            # Testar engine
            with db_engine.connect() as test_conn:
                result = test_conn.execute(text("SELECT 1"))
                result.close()

            # Criar session factory
            session_factory = sessionmaker(bind=db_engine)

            # Armazenar nas variáveis apropriadas
            if is_source:
                self.source_pool = db_pool
                self.source_engine = db_engine
                self._source_session_factory = session_factory
                self.logger.info(f"✓ Banco de origem conectado: {database}")
            elif is_destiny:
                self.destiny_pool = db_pool
                self.destiny_engine = db_engine
                self._destiny_session_factory = session_factory
                self.logger.info(f"✓ Banco de destino conectado: {database}")
            else:
                self.postgres_pool = db_pool
                self.postgres_engine = db_engine
                self._postgres_session_factory = session_factory
                self.logger.info(f"✓ Banco postgres conectado")

            return True

        except (psycopg2.Error, ValueError) as e:
            self.logger.warning(f"Falha ao conectar '{database}': {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao conectar '{database}': {e}")
            return False

    @contextmanager
    def get_source_connection(self, autocommit: bool = False):
        """
        Context manager para conexão com banco de origem.

        Parameters
        ----------
        autocommit : bool, optional
            Se deve usar autocommit

        Yields
        ------
        psycopg2.extensions.connection
            Conexão com banco de origem

        Examples
        --------
        >>> from pg_json_config import PostgreSQLJsonConfig, UserCredential, SSLMode
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('user', 'pass')], 'src', 'dst'
        ... )
        >>> manager = PostgreSQLConnectionManager(config, auto_validate=False)
        >>> manager.config.validated_user = config.possible_users[0]
        >>> manager.connect()  # doctest: +SKIP
        >>> with manager.get_source_connection() as conn:  # doctest: +SKIP
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
        """
        conn = None
        try:
            if not self.is_connected:
                raise ConnectionError(
                    "Não conectado. Execute connect() primeiro.")

            if self.use_pool and self.source_pool:
                conn = self.source_pool.getconn()
            else:
                conn_params = self.config.get_connection_params(
                    database=self.config.db_source
                )
                if conn_params is False:
                    raise ValueError("Parâmetros inválidos")
                conn = psycopg2.connect(**conn_params)

            if autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            yield conn

        except (psycopg2.Error, ConnectionError, ValueError) as e:
            self.logger.error(f"Erro ao obter conexão de origem: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            yield False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            yield False
        finally:
            if conn:
                try:
                    if self.use_pool and self.source_pool:
                        self.source_pool.putconn(conn)
                    else:
                        conn.close()
                except Exception as e:
                    self.logger.error(f"Erro ao liberar conexão: {e}")

    @contextmanager
    def get_destiny_connection(self, autocommit: bool = False):
        """
        Context manager para conexão com banco de destino.

        Parameters
        ----------
        autocommit : bool, optional
            Se deve usar autocommit

        Yields
        ------
        psycopg2.extensions.connection
            Conexão com banco de destino
        """
        conn = None
        try:
            if not self.is_connected:
                raise ConnectionError(
                    "Não conectado. Execute connect() primeiro.")

            if self.use_pool and self.destiny_pool:
                conn = self.destiny_pool.getconn()
            else:
                conn_params = self.config.get_connection_params(
                    database=self.config.db_destiny
                )
                if conn_params is False:
                    raise ValueError("Parâmetros inválidos")
                conn = psycopg2.connect(**conn_params)

            if autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            yield conn

        except (psycopg2.Error, ConnectionError, ValueError) as e:
            self.logger.error(f"Erro ao obter conexão de destino: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            yield False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            yield False
        finally:
            if conn:
                try:
                    if self.use_pool and self.destiny_pool:
                        self.destiny_pool.putconn(conn)
                    else:
                        conn.close()
                except Exception as e:
                    self.logger.error(f"Erro ao liberar conexão: {e}")

    @contextmanager
    def get_postgres_connection(self, autocommit: bool = True):
        """
        Context manager para conexão com banco postgres (operações DDL).

        Parameters
        ----------
        autocommit : bool, optional
            Se deve usar autocommit (padrão: True para DDL)

        Yields
        ------
        psycopg2.extensions.connection
            Conexão com banco postgres
        """
        conn = None
        try:
            if not self.is_connected:
                raise ConnectionError(
                    "Não conectado. Execute connect() primeiro.")

            if self.use_pool and self.postgres_pool:
                conn = self.postgres_pool.getconn()
            else:
                conn_params = self.config.get_connection_params(
                    database='postgres')
                if conn_params is False:
                    raise ValueError("Parâmetros inválidos")
                conn = psycopg2.connect(**conn_params)

            if autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            yield conn

        except (psycopg2.Error, ConnectionError, ValueError) as e:
            self.logger.error(f"Erro ao obter conexão postgres: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            yield False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            yield False
        finally:
            if conn:
                try:
                    if self.use_pool and self.postgres_pool:
                        self.postgres_pool.putconn(conn)
                    else:
                        conn.close()
                except Exception as e:
                    self.logger.error(f"Erro ao liberar conexão: {e}")

    @contextmanager
    def get_source_session(self):
        """
        Context manager para sessão SQLAlchemy de origem.

        Yields
        ------
        sqlalchemy.orm.Session
            Sessão com banco de origem
        """
        session = None
        try:
            if not self.is_connected or not self._source_session_factory:
                raise ConnectionError("Banco de origem não conectado")

            session = self._source_session_factory()
            yield session
            session.commit()

        except Exception as e:
            self.logger.error(f"Erro na sessão de origem: {e}")
            if session:
                try:
                    session.rollback()
                except Exception:
                    pass
            yield False
        finally:
            if session:
                try:
                    session.close()
                except Exception as e:
                    self.logger.error(f"Erro ao fechar sessão: {e}")

    @contextmanager
    def get_destiny_session(self):
        """
        Context manager para sessão SQLAlchemy de destino.

        Yields
        ------
        sqlalchemy.orm.Session
            Sessão com banco de destino
        """
        session = None
        try:
            if not self.is_connected or not self._destiny_session_factory:
                raise ConnectionError("Banco de destino não conectado")

            session = self._destiny_session_factory()
            yield session
            session.commit()

        except Exception as e:
            self.logger.error(f"Erro na sessão de destino: {e}")
            if session:
                try:
                    session.rollback()
                except Exception:
                    pass
            yield False
        finally:
            if session:
                try:
                    session.close()
                except Exception as e:
                    self.logger.error(f"Erro ao fechar sessão: {e}")

    def disconnect(self) -> bool:
        """
        Fecha todas as conexões.

        Returns
        -------
        bool
            True se desconexão bem-sucedida
        """
        try:
            self.logger.info("Fechando conexões...")

            # Fechar pools psycopg2
            for pool_name, db_pool in [
                ('source', self.source_pool),
                ('destiny', self.destiny_pool),
                ('postgres', self.postgres_pool)
            ]:
                if db_pool:
                    try:
                        db_pool.closeall()
                        self.logger.info(f"Pool {pool_name} fechado")
                    except Exception as e:
                        self.logger.error(
                            f"Erro ao fechar pool {pool_name}: {e}")

            # Fechar engines SQLAlchemy
            for engine_name, db_engine in [
                ('source', self.source_engine),
                ('destiny', self.destiny_engine),
                ('postgres', self.postgres_engine)
            ]:
                if db_engine:
                    try:
                        db_engine.dispose()
                        self.logger.info(f"Engine {engine_name} fechado")
                    except Exception as e:
                        self.logger.error(
                            f"Erro ao fechar engine {engine_name}: {e}")

            self.is_connected = False
            self.logger.info("✓ Desconexão concluída")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao desconectar: {e}")
            return False

    def __enter__(self):
        """Suporte a context manager."""
        try:
            self.connect()
            return self
        except Exception as e:
            self.logger.error(f"Erro no __enter__: {e}")
            return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Suporte a context manager."""
        try:
            self.disconnect()
            return False
        except Exception:
            return False

    def __del__(self):
        """Destrutor para garantir limpeza."""
        try:
            if hasattr(self, 'is_connected') and self.is_connected:
                self.disconnect()
        except Exception:
            pass

    def __repr__(self) -> str:
        """Representação do gerenciador."""
        return (
            f"PostgreSQLConnectionManager(host='{self.config.host}', "
            f"port={self.config.port}, source='{self.config.db_source}', "
            f"destiny='{self.config.db_destiny}', connected={self.is_connected})"
        )


if __name__ == "__main__":
    import doctest
    doctest.testmod()
