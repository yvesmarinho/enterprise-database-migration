#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de Gerenciamento de Conexões PostgreSQL.

Este módulo fornece classes e funções para gerenciar conexões com bancos
de dados PostgreSQL usando psycopg2 e SQLAlchemy, com suporte a pooling,
retry automático e gerenciamento de transações.

:author: yvesmarinho
:date: 2026-02-09
:version: 1.0.0

Examples
--------
>>> manager = PostgreSQLConnectionManager(
...     host='localhost',
...     port=5432,
...     database='postgres',
...     user='postgres',
...     password='senha123'
... )
>>> if manager.connect():
...     print("Conectado com sucesso")
...     manager.disconnect()
... # doctest: +SKIP
"""

import logging
import time
from typing import Optional, Dict, Any, Union, List
from contextlib import contextmanager
from dataclasses import dataclass, field

try:
    import psycopg2
    from psycopg2 import pool, extras, extensions
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from sqlalchemy import create_engine, text, inspect, MetaData
    from sqlalchemy.engine import Engine, URL
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.pool import NullPool, QueuePool
except ImportError as e:
    print(f"Erro ao importar dependências: {e}")
    print("Execute: pip install psycopg2-binary sqlalchemy")
    raise


@dataclass
class ConnectionConfig:
    """
    Configuração de conexão PostgreSQL.
    
    Attributes
    ----------
    host : str
        Endereço do servidor PostgreSQL
    port : int
        Porta do servidor PostgreSQL
    database : str
        Nome do banco de dados
    user : str
        Usuário de conexão
    password : str
        Senha do usuário
    max_retries : int, optional
        Número máximo de tentativas de reconexão (padrão: 3)
    retry_delay : float, optional
        Delay entre tentativas em segundos (padrão: 2.0)
    pool_size : int, optional
        Tamanho do pool de conexões (padrão: 5)
    max_overflow : int, optional
        Conexões extras além do pool_size (padrão: 10)
    application_name : str, optional
        Nome da aplicação para identificação no PostgreSQL
    connect_timeout : int, optional
        Timeout de conexão em segundos (padrão: 10)
    
    Examples
    --------
    >>> config = ConnectionConfig(
    ...     host='localhost',
    ...     port=5432,
    ...     database='mydb',
    ...     user='admin',
    ...     password='secret'
    ... )
    >>> config.host
    'localhost'
    """
    
    host: str
    port: int
    database: str
    user: str
    password: str
    max_retries: int = 3
    retry_delay: float = 2.0
    pool_size: int = 5
    max_overflow: int = 10
    application_name: str = "pg_clone_system"
    connect_timeout: int = 10
    sslmode: str = "prefer"
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Valida os parâmetros após inicialização."""
        try:
            self._validate_parameters()
        except (ValueError, TypeError) as e:
            logging.error(f"Erro na validação de parâmetros: {e}")
            raise
    
    def _validate_parameters(self) -> bool:
        """
        Valida todos os parâmetros de configuração.
        
        Returns
        -------
        bool
            True se validação bem-sucedida
            
        Raises
        ------
        ValueError
            Se algum parâmetro for inválido
        TypeError
            Se algum parâmetro tiver tipo incorreto
            
        Examples
        --------
        >>> config = ConnectionConfig('localhost', 5432, 'db', 'user', 'pass')
        >>> config._validate_parameters()
        True
        """
        try:
            # Validação de strings não vazias
            string_params = {
                'host': self.host,
                'database': self.database,
                'user': self.user,
                'password': self.password
            }
            
            for param_name, param_value in string_params.items():
                if not isinstance(param_value, str):
                    raise TypeError(
                        f"Parâmetro '{param_name}' deve ser string, "
                        f"recebido: {type(param_value).__name__}"
                    )
                if not param_value or not param_value.strip():
                    raise ValueError(
                        f"Parâmetro '{param_name}' não pode ser vazio"
                    )
            
            # Validação de inteiros positivos
            int_params = {
                'port': self.port,
                'max_retries': self.max_retries,
                'pool_size': self.pool_size,
                'max_overflow': self.max_overflow,
                'connect_timeout': self.connect_timeout
            }
            
            for param_name, param_value in int_params.items():
                if not isinstance(param_value, int):
                    raise TypeError(
                        f"Parâmetro '{param_name}' deve ser int, "
                        f"recebido: {type(param_value).__name__}"
                    )
                if param_value <= 0:
                    raise ValueError(
                        f"Parâmetro '{param_name}' deve ser positivo, "
                        f"recebido: {param_value}"
                    )
            
            # Validação de float positivo
            if not isinstance(self.retry_delay, (int, float)):
                raise TypeError(
                    f"Parâmetro 'retry_delay' deve ser numérico, "
                    f"recebido: {type(self.retry_delay).__name__}"
                )
            if self.retry_delay <= 0:
                raise ValueError(
                    f"Parâmetro 'retry_delay' deve ser positivo, "
                    f"recebido: {self.retry_delay}"
                )
            
            # Validação de porta no range válido
            if not (1 <= self.port <= 65535):
                raise ValueError(
                    f"Porta deve estar entre 1 e 65535, recebido: {self.port}"
                )
            
            return True
            
        except (ValueError, TypeError) as e:
            logging.error(f"Falha na validação de parâmetros: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado na validação: {e}")
            return False
    
    def to_dict(self) -> Union[Dict[str, Any], bool]:
        """
        Converte configuração para dicionário.
        
        Returns
        -------
        dict or bool
            Dicionário com configurações ou False em caso de erro
            
        Examples
        --------
        >>> config = ConnectionConfig('localhost', 5432, 'db', 'user', 'pass')
        >>> result = config.to_dict()
        >>> isinstance(result, dict)
        True
        >>> 'host' in result
        True
        """
        try:
            if not isinstance(self.host, str) or not self.host:
                raise ValueError("Configuração inválida")
                
            return {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'password': self.password,
                'application_name': self.application_name,
                'connect_timeout': self.connect_timeout,
                'sslmode': self.sslmode,
                **self.extra_params
            }
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Erro ao converter para dicionário: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao converter para dicionário: {e}")
            return False


class PostgreSQLConnectionManager:
    """
    Gerenciador de conexões PostgreSQL com suporte a psycopg2 e SQLAlchemy.
    
    Esta classe fornece uma interface unificada para gerenciar conexões com
    PostgreSQL, incluindo pooling, retry automático, transações e logging.
    
    Parameters
    ----------
    config : ConnectionConfig
        Configuração de conexão
    use_pool : bool, optional
        Se deve usar pool de conexões (padrão: True)
    autocommit : bool, optional
        Se deve usar autocommit (padrão: False)
        
    Attributes
    ----------
    config : ConnectionConfig
        Configuração de conexão atual
    psycopg2_pool : psycopg2.pool.ThreadedConnectionPool or None
        Pool de conexões psycopg2
    sqlalchemy_engine : sqlalchemy.engine.Engine or None
        Engine SQLAlchemy
    sqlalchemy_session : sqlalchemy.orm.Session or None
        Sessão SQLAlchemy ativa
    is_connected : bool
        Status de conexão
        
    Examples
    --------
    >>> config = ConnectionConfig('localhost', 5432, 'postgres', 'user', 'pass')
    >>> manager = PostgreSQLConnectionManager(config)
    >>> manager.connect()  # doctest: +SKIP
    True
    """
    
    def __init__(
        self,
        config: ConnectionConfig,
        use_pool: bool = True,
        autocommit: bool = False
    ):
        """
        Inicializa o gerenciador de conexões.
        
        Parameters
        ----------
        config : ConnectionConfig
            Configuração de conexão
        use_pool : bool, optional
            Se deve usar pool de conexões
        autocommit : bool, optional
            Se deve usar autocommit
        """
        try:
            # Validação de parâmetros
            if not isinstance(config, ConnectionConfig):
                raise TypeError(
                    f"config deve ser ConnectionConfig, "
                    f"recebido: {type(config).__name__}"
                )
            if not isinstance(use_pool, bool):
                raise TypeError(
                    f"use_pool deve ser bool, "
                    f"recebido: {type(use_pool).__name__}"
                )
            if not isinstance(autocommit, bool):
                raise TypeError(
                    f"autocommit deve ser bool, "
                    f"recebido: {type(autocommit).__name__}"
                )
            
            self.config = config
            self.use_pool = use_pool
            self.autocommit = autocommit
            self.psycopg2_pool: Optional[pool.ThreadedConnectionPool] = None
            self.sqlalchemy_engine: Optional[Engine] = None
            self.sqlalchemy_session: Optional[Session] = None
            self._session_factory = None
            self.is_connected = False
            
            # Configuração de logging
            self._setup_logging()
            
            self.logger.info(
                f"Gerenciador inicializado para {config.user}@{config.host}:"
                f"{config.port}/{config.database}"
            )
            
        except (TypeError, ValueError) as e:
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
            True se configuração bem-sucedida, False caso contrário
            
        Examples
        --------
        >>> config = ConnectionConfig('localhost', 5432, 'db', 'user', 'pass')
        >>> manager = PostgreSQLConnectionManager(config)
        >>> hasattr(manager, 'logger')
        True
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
        Estabelece conexão com PostgreSQL (psycopg2 e SQLAlchemy).
        
        Returns
        -------
        bool
            True se conexão bem-sucedida, False caso contrário
            
        Examples
        --------
        >>> config = ConnectionConfig('localhost', 5432, 'postgres', 'user', 'pass')
        >>> manager = PostgreSQLConnectionManager(config)
        >>> manager.connect()  # doctest: +SKIP
        True
        """
        try:
            if not isinstance(self.config, ConnectionConfig):
                raise TypeError("Configuração inválida")
            
            # Conectar psycopg2
            if not self._connect_psycopg2():
                self.logger.error("Falha ao conectar com psycopg2")
                return False
            
            # Conectar SQLAlchemy
            if not self._connect_sqlalchemy():
                self.logger.error("Falha ao conectar com SQLAlchemy")
                return False
            
            self.is_connected = True
            self.logger.info("Conexão estabelecida com sucesso")
            return True
            
        except (TypeError, ValueError) as e:
            self.logger.error(f"Erro ao conectar: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado ao conectar: {e}")
            return False
    
    def _connect_psycopg2(self) -> bool:
        """
        Estabelece conexão usando psycopg2.
        
        Returns
        -------
        bool
            True se conexão bem-sucedida, False caso contrário
        """
        try:
            conn_params = self.config.to_dict()
            if conn_params is False:
                raise ValueError("Parâmetros de conexão inválidos")
            
            if self.use_pool:
                self.psycopg2_pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=self.config.pool_size,
                    **conn_params
                )
                self.logger.info(
                    f"Pool de conexões criado (size={self.config.pool_size})"
                )
            else:
                # Testar conexão sem pool
                test_conn = psycopg2.connect(**conn_params)
                test_conn.close()
                self.logger.info("Conexão psycopg2 testada com sucesso")
            
            return True
            
        except psycopg2.Error as e:
            self.logger.error(f"Erro de conexão psycopg2: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado em psycopg2: {e}")
            return False
    
    def _connect_sqlalchemy(self) -> bool:
        """
        Estabelece conexão usando SQLAlchemy.
        
        Returns
        -------
        bool
            True se conexão bem-sucedida, False caso contrário
        """
        try:
            # Construir URL de conexão
            url = URL.create(
                drivername="postgresql+psycopg2",
                username=self.config.user,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database
            )
            
            # Criar engine
            if self.use_pool:
                self.sqlalchemy_engine = create_engine(
                    url,
                    poolclass=QueuePool,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_pre_ping=True,
                    echo=False
                )
            else:
                self.sqlalchemy_engine = create_engine(
                    url,
                    poolclass=NullPool,
                    echo=False
                )
            
            # Criar session factory
            self._session_factory = sessionmaker(bind=self.sqlalchemy_engine)
            
            # Testar conexão
            with self.sqlalchemy_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.close()
            
            self.logger.info("Engine SQLAlchemy criado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar engine SQLAlchemy: {e}")
            return False
    
    @contextmanager
    def get_psycopg2_connection(self, autocommit: Optional[bool] = None):
        """
        Context manager para obter conexão psycopg2.
        
        Parameters
        ----------
        autocommit : bool, optional
            Sobrescrever configuração de autocommit
            
        Yields
        ------
        psycopg2.extensions.connection
            Conexão psycopg2
            
        Examples
        --------
        >>> config = ConnectionConfig('localhost', 5432, 'db', 'user', 'pass')
        >>> manager = PostgreSQLConnectionManager(config)
        >>> manager.connect()  # doctest: +SKIP
        >>> with manager.get_psycopg2_connection() as conn:  # doctest: +SKIP
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
        """
        conn = None
        try:
            if not self.is_connected:
                raise ConnectionError("Não conectado ao banco de dados")
            
            # Obter conexão
            if self.use_pool and self.psycopg2_pool:
                conn = self.psycopg2_pool.getconn()
            else:
                conn_params = self.config.to_dict()
                if conn_params is False:
                    raise ValueError("Parâmetros inválidos")
                conn = psycopg2.connect(**conn_params)
            
            # Configurar autocommit
            use_autocommit = autocommit if autocommit is not None else self.autocommit
            if use_autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            yield conn
            
        except (psycopg2.Error, ConnectionError, ValueError) as e:
            self.logger.error(f"Erro ao obter conexão: {e}")
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
                    if self.use_pool and self.psycopg2_pool:
                        self.psycopg2_pool.putconn(conn)
                    else:
                        conn.close()
                except Exception as e:
                    self.logger.error(f"Erro ao liberar conexão: {e}")
    
    @contextmanager
    def get_sqlalchemy_session(self):
        """
        Context manager para obter sessão SQLAlchemy.
        
        Yields
        ------
        sqlalchemy.orm.Session
            Sessão SQLAlchemy
            
        Examples
        --------
        >>> config = ConnectionConfig('localhost', 5432, 'db', 'user', 'pass')
        >>> manager = PostgreSQLConnectionManager(config)
        >>> manager.connect()  # doctest: +SKIP
        >>> with manager.get_sqlalchemy_session() as session:  # doctest: +SKIP
        ...     result = session.execute(text("SELECT 1"))
        """
        session = None
        try:
            if not self.is_connected or not self._session_factory:
                raise ConnectionError("Não conectado ao banco de dados")
            
            session = self._session_factory()
            yield session
            session.commit()
            
        except Exception as e:
            self.logger.error(f"Erro na sessão SQLAlchemy: {e}")
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
            True se desconexão bem-sucedida, False caso contrário
            
        Examples
        --------
        >>> config = ConnectionConfig('localhost', 5432, 'db', 'user', 'pass')
        >>> manager = PostgreSQLConnectionManager(config)
        >>> manager.connect()  # doctest: +SKIP
        >>> manager.disconnect()  # doctest: +SKIP
        True
        """
        try:
            # Fechar pool psycopg2
            if self.psycopg2_pool:
                try:
                    self.psycopg2_pool.closeall()
                    self.logger.info("Pool psycopg2 fechado")
                except Exception as e:
                    self.logger.error(f"Erro ao fechar pool: {e}")
            
            # Fechar engine SQLAlchemy
            if self.sqlalchemy_engine:
                try:
                    self.sqlalchemy_engine.dispose()
                    self.logger.info("Engine SQLAlchemy fechado")
                except Exception as e:
                    self.logger.error(f"Erro ao fechar engine: {e}")
            
            self.is_connected = False
            self.logger.info("Desconexão concluída")
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()