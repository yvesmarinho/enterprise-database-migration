#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de Configuração JSON para PostgreSQL Clone System.

Este módulo gerencia configurações de conexão através de arquivos JSON,
suportando múltiplos usuários, validação de credenciais e fallback automático.

:author: yvesmarinho
:date: 2026-02-09
:version: 2.0.0

Examples
--------
>>> import json
>>> config_data = {
...     "host": "localhost",
...     "port": 5432,
...     "ssl_mode": "false",
...     "possible_users": [
...         {"username": "user1", "password": "pass1"}
...     ],
...     "db_source": "source_db",
...     "db_destiny": "dest_db"
... }
>>> config = PostgreSQLJsonConfig.from_dict(config_data)
>>> config.host
'localhost'
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import psycopg2
    from psycopg2 import sql
except ImportError as e:
    print(f"Erro ao importar psycopg2: {e}")
    print("Execute: pip install psycopg2-binary")
    raise


class SSLMode(Enum):
    """
    Modos SSL suportados pelo PostgreSQL.

    Attributes
    ----------
    DISABLE : str
        Sem SSL
    ALLOW : str
        SSL se disponível
    PREFER : str
        Preferir SSL (padrão)
    REQUIRE : str
        Requer SSL
    VERIFY_CA : str
        Verificar certificado CA
    VERIFY_FULL : str
        Verificação completa

    Examples
    --------
    >>> SSLMode.DISABLE.value
    'disable'
    >>> SSLMode.from_string('false')
    <SSLMode.DISABLE: 'disable'>
    """

    DISABLE = 'disable'
    ALLOW = 'allow'
    PREFER = 'prefer'
    REQUIRE = 'require'
    VERIFY_CA = 'verify-ca'
    VERIFY_FULL = 'verify-full'

    @classmethod
    def from_string(cls, value: str) -> 'SSLMode':
        """
        Converte string para SSLMode.

        Parameters
        ----------
        value : str
            Valor string (true/false ou nome do modo)

        Returns
        -------
        SSLMode
            Modo SSL correspondente

        Raises
        ------
        ValueError
            Se valor inválido

        Examples
        --------
        >>> SSLMode.from_string('false')
        <SSLMode.DISABLE: 'disable'>
        >>> SSLMode.from_string('true')
        <SSLMode.PREFER: 'prefer'>
        >>> SSLMode.from_string('require')
        <SSLMode.REQUIRE: 'require'>
        """
        try:
            if not isinstance(value, str):
                raise TypeError(
                    f"Esperado str, recebido {type(value).__name__}")

            value_lower = value.lower().strip()

            # Mapeamento de valores booleanos
            if value_lower in ('false', 'no', '0', 'off'):
                return cls.DISABLE
            elif value_lower in ('true', 'yes', '1', 'on'):
                return cls.PREFER

            # Tentar match direto com enum
            for mode in cls:
                if mode.value == value_lower:
                    return mode

            raise ValueError(f"SSL mode inválido: {value}")

        except (TypeError, ValueError) as e:
            logging.error(f"Erro ao converter SSL mode: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado ao converter SSL mode: {e}")
            raise


@dataclass
class UserCredential:
    """
    Credencial de usuário PostgreSQL.

    Attributes
    ----------
    username : str
        Nome do usuário
    password : str
        Senha do usuário
    priority : int, optional
        Prioridade de tentativa (menor = maior prioridade)
    validated : bool
        Se credencial foi validada
    last_error : str, optional
        Último erro de validação

    Examples
    --------
    >>> cred = UserCredential('postgres', 'senha123')
    >>> cred.username
    'postgres'
    >>> cred.validated
    False
    """

    username: str
    password: str
    priority: int = 0
    validated: bool = False
    last_error: Optional[str] = None

    def __post_init__(self):
        """Valida credenciais após inicialização."""
        try:
            self._validate()
        except (ValueError, TypeError) as e:
            logging.error(f"Erro na validação de credencial: {e}")
            raise

    def _validate(self) -> bool:
        """
        Valida os campos da credencial.

        Returns
        -------
        bool
            True se válido

        Raises
        ------
        ValueError
            Se campo inválido
        TypeError
            Se tipo incorreto

        Examples
        --------
        >>> cred = UserCredential('user', 'pass')
        >>> cred._validate()
        True
        """
        try:
            # Validar username
            if not isinstance(self.username, str):
                raise TypeError(
                    f"username deve ser str, recebido {type(self.username).__name__}"
                )
            if not self.username or not self.username.strip():
                raise ValueError("username não pode ser vazio")

            # Validar password
            if not isinstance(self.password, str):
                raise TypeError(
                    f"password deve ser str, recebido {type(self.password).__name__}"
                )
            if not self.password:
                raise ValueError("password não pode ser vazio")

            # Validar priority
            if not isinstance(self.priority, int):
                raise TypeError(
                    f"priority deve ser int, recebido {type(self.priority).__name__}"
                )

            return True

        except (ValueError, TypeError) as e:
            logging.error(f"Falha na validação de credencial: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado na validação: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte para dicionário (sem senha).

        Returns
        -------
        dict
            Dicionário com dados (senha omitida)

        Examples
        --------
        >>> cred = UserCredential('user', 'pass')
        >>> result = cred.to_dict()
        >>> 'username' in result
        True
        >>> 'password' in result
        False
        """
        try:
            return {
                'username': self.username,
                'priority': self.priority,
                'validated': self.validated,
                'last_error': self.last_error
            }
        except Exception as e:
            logging.error(f"Erro ao converter credencial para dict: {e}")
            return {}

    def __repr__(self) -> str:
        """Representação segura (sem senha)."""
        return f"UserCredential(username='{self.username}', validated={self.validated})"


@dataclass
class PostgreSQLJsonConfig:
    """
    Configuração completa do sistema via JSON.

    Attributes
    ----------
    host : str
        Servidor PostgreSQL
    port : int
        Porta do servidor
    ssl_mode : SSLMode
        Modo SSL
    possible_users : List[UserCredential]
        Lista de credenciais possíveis
    db_source : str
        Banco de dados origem
    db_destiny : str
        Banco de dados destino
    connect_timeout : int, optional
        Timeout de conexão em segundos
    application_name : str, optional
        Nome da aplicação
    pool_size : int, optional
        Tamanho do pool de conexões
    max_overflow : int, optional
        Conexões extras no pool
    max_retries : int, optional
        Tentativas máximas de conexão
    retry_delay : float, optional
        Delay entre tentativas
    validated_user : UserCredential, optional
        Usuário validado para uso

    Examples
    --------
    >>> config = PostgreSQLJsonConfig(
    ...     host='localhost',
    ...     port=5432,
    ...     ssl_mode=SSLMode.DISABLE,
    ...     possible_users=[UserCredential('user', 'pass')],
    ...     db_source='source_db',
    ...     db_destiny='dest_db'
    ... )
    >>> config.host
    'localhost'
    """

    host: str
    port: int
    ssl_mode: SSLMode
    possible_users: List[UserCredential]
    db_source: str
    db_destiny: str
    connect_timeout: int = 10
    application_name: str = "pg_clone_system"
    pool_size: int = 5
    max_overflow: int = 10
    max_retries: int = 3
    retry_delay: float = 2.0
    validated_user: Optional[UserCredential] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Valida configuração após inicialização."""
        try:
            self._validate_all()
        except (ValueError, TypeError) as e:
            logging.error(f"Erro na validação de configuração: {e}")
            raise

    def _validate_all(self) -> bool:
        """
        Valida todos os parâmetros de configuração.

        Returns
        -------
        bool
            True se validação bem-sucedida

        Raises
        ------
        ValueError
            Se parâmetro inválido
        TypeError
            Se tipo incorreto

        Examples
        --------
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('u', 'p')], 'src', 'dst'
        ... )
        >>> config._validate_all()
        True
        """
        try:
            # Validar host
            if not isinstance(self.host, str):
                raise TypeError(
                    f"host deve ser str, recebido {type(self.host).__name__}")
            if not self.host or not self.host.strip():
                raise ValueError("host não pode ser vazio")

            # Validar port
            if not isinstance(self.port, int):
                raise TypeError(
                    f"port deve ser int, recebido {type(self.port).__name__}")
            if not (1 <= self.port <= 65535):
                raise ValueError(
                    f"port deve estar entre 1 e 65535, recebido {self.port}")

            # Validar ssl_mode
            if not isinstance(self.ssl_mode, SSLMode):
                raise TypeError(
                    f"ssl_mode deve ser SSLMode, recebido {type(self.ssl_mode).__name__}"
                )

            # Validar possible_users
            if not isinstance(self.possible_users, list):
                raise TypeError("possible_users deve ser list")
            if not self.possible_users:
                raise ValueError("possible_users não pode ser vazio")

            for user in self.possible_users:
                if not isinstance(user, UserCredential):
                    raise TypeError(
                        f"Elementos de possible_users devem ser UserCredential, "
                        f"recebido {type(user).__name__}"
                    )

            # Validar db_source
            if not isinstance(self.db_source, str):
                raise TypeError(
                    f"db_source deve ser str, recebido {type(self.db_source).__name__}"
                )
            if not self.db_source or not self.db_source.strip():
                raise ValueError("db_source não pode ser vazio")

            # Validar db_destiny
            if not isinstance(self.db_destiny, str):
                raise TypeError(
                    f"db_destiny deve ser str, recebido {type(self.db_destiny).__name__}"
                )
            if not self.db_destiny or not self.db_destiny.strip():
                raise ValueError("db_destiny não pode ser vazio")

            # Validar que source != destiny
            if self.db_source.strip() == self.db_destiny.strip():
                raise ValueError("db_source e db_destiny não podem ser iguais")

            # Validar inteiros positivos
            int_params = {
                'connect_timeout': self.connect_timeout,
                'pool_size': self.pool_size,
                'max_overflow': self.max_overflow,
                'max_retries': self.max_retries
            }

            for param_name, param_value in int_params.items():
                if not isinstance(param_value, int):
                    raise TypeError(
                        f"{param_name} deve ser int, "
                        f"recebido {type(param_value).__name__}"
                    )
                if param_value <= 0:
                    raise ValueError(
                        f"{param_name} deve ser positivo, recebido {param_value}"
                    )

            # Validar retry_delay
            if not isinstance(self.retry_delay, (int, float)):
                raise TypeError(
                    f"retry_delay deve ser numérico, "
                    f"recebido {type(self.retry_delay).__name__}"
                )
            if self.retry_delay <= 0:
                raise ValueError(
                    f"retry_delay deve ser positivo, recebido {self.retry_delay}"
                )

            return True

        except (ValueError, TypeError) as e:
            logging.error(f"Falha na validação de configuração: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado na validação: {e}")
            return False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PostgreSQLJsonConfig':
        """
        Cria configuração a partir de dicionário.

        Parameters
        ----------
        data : dict
            Dicionário com dados de configuração

        Returns
        -------
        PostgreSQLJsonConfig
            Instância configurada

        Raises
        ------
        ValueError
            Se dados inválidos
        TypeError
            Se tipo incorreto
        KeyError
            Se campo obrigatório ausente

        Examples
        --------
        >>> data = {
        ...     "host": "localhost",
        ...     "port": 5432,
        ...     "ssl_mode": "false",
        ...     "possible_users": [{"username": "user", "password": "pass"}],
        ...     "db_source": "src",
        ...     "db_destiny": "dst"
        ... }
        >>> config = PostgreSQLJsonConfig.from_dict(data)
        >>> config.host
        'localhost'
        """
        try:
            if not isinstance(data, dict):
                raise TypeError(
                    f"Esperado dict, recebido {type(data).__name__}")

            # Validar campos obrigatórios
            required_fields = [
                'host', 'port', 'ssl_mode', 'possible_users',
                'db_source', 'db_destiny'
            ]

            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                raise KeyError(
                    f"Campos obrigatórios ausentes: {missing_fields}")

            # Processar ssl_mode
            ssl_mode = SSLMode.from_string(data['ssl_mode'])

            # Processar possible_users
            users = []
            if not isinstance(data['possible_users'], list):
                raise TypeError("possible_users deve ser uma lista")

            for idx, user_data in enumerate(data['possible_users']):
                if not isinstance(user_data, dict):
                    raise TypeError(
                        f"Usuário {idx} deve ser dict, "
                        f"recebido {type(user_data).__name__}"
                    )

                if 'username' not in user_data:
                    raise KeyError(f"Usuário {idx} sem campo 'username'")
                if 'password' not in user_data:
                    raise KeyError(f"Usuário {idx} sem campo 'password'")

                user = UserCredential(
                    username=user_data['username'],
                    password=user_data['password'],
                    priority=user_data.get('priority', idx)
                )
                users.append(user)

            # Ordenar usuários por prioridade
            users.sort(key=lambda u: u.priority)

            # Criar configuração
            config = cls(
                host=data['host'],
                port=int(data['port']),
                ssl_mode=ssl_mode,
                possible_users=users,
                db_source=data['db_source'],
                db_destiny=data['db_destiny'],
                connect_timeout=int(data.get('connect_timeout', 10)),
                application_name=data.get(
                    'application_name', 'pg_clone_system'),
                pool_size=int(data.get('pool_size', 5)),
                max_overflow=int(data.get('max_overflow', 10)),
                max_retries=int(data.get('max_retries', 3)),
                retry_delay=float(data.get('retry_delay', 2.0)),
                extra_params=data.get('extra_params', {})
            )

            return config

        except (ValueError, TypeError, KeyError) as e:
            logging.error(f"Erro ao criar configuração de dict: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado ao criar configuração: {e}")
            raise

    @classmethod
    def from_json_file(cls, filepath: Union[str, Path]) -> 'PostgreSQLJsonConfig':
        """
        Cria configuração a partir de arquivo JSON.

        Parameters
        ----------
        filepath : str or Path
            Caminho do arquivo JSON

        Returns
        -------
        PostgreSQLJsonConfig
            Instância configurada

        Raises
        ------
        FileNotFoundError
            Se arquivo não existe
        json.JSONDecodeError
            Se JSON inválido

        Examples
        --------
        >>> import tempfile
        >>> import json
        >>> data = {
        ...     "host": "localhost", "port": 5432, "ssl_mode": "false",
        ...     "possible_users": [{"username": "u", "password": "p"}],
        ...     "db_source": "src", "db_destiny": "dst"
        ... }
        >>> with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        ...     json.dump(data, f)
        ...     tmpfile = f.name
        >>> config = PostgreSQLJsonConfig.from_json_file(tmpfile)  # doctest: +SKIP
        >>> os.unlink(tmpfile)  # doctest: +SKIP
        """
        try:
            if not isinstance(filepath, (str, Path)):
                raise TypeError(
                    f"filepath deve ser str ou Path, "
                    f"recebido {type(filepath).__name__}"
                )

            filepath = Path(filepath)

            if not filepath.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

            if not filepath.is_file():
                raise ValueError(f"Caminho não é um arquivo: {filepath}")

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logging.info(f"Configuração carregada de: {filepath}")
            return cls.from_dict(data)

        except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError) as e:
            logging.error(f"Erro ao carregar JSON: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado ao carregar JSON: {e}")
            raise

    @classmethod
    def from_json_string(cls, json_str: str) -> 'PostgreSQLJsonConfig':
        """
        Cria configuração a partir de string JSON.

        Parameters
        ----------
        json_str : str
            String JSON

        Returns
        -------
        PostgreSQLJsonConfig
            Instância configurada

        Raises
        ------
        json.JSONDecodeError
            Se JSON inválido

        Examples
        --------
        >>> json_str = '''
        ... {
        ...     "host": "localhost",
        ...     "port": 5432,
        ...     "ssl_mode": "false",
        ...     "possible_users": [{"username": "u", "password": "p"}],
        ...     "db_source": "src",
        ...     "db_destiny": "dst"
        ... }
        ... '''
        >>> config = PostgreSQLJsonConfig.from_json_string(json_str)
        >>> config.db_source
        'src'
        """
        try:
            if not isinstance(json_str, str):
                raise TypeError(
                    f"Esperado str, recebido {type(json_str).__name__}")

            if not json_str or not json_str.strip():
                raise ValueError("JSON string não pode ser vazio")

            data = json.loads(json_str)
            return cls.from_dict(data)

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logging.error(f"Erro ao parsear JSON string: {e}")
            raise
        except Exception as e:
            logging.error(f"Erro inesperado ao parsear JSON: {e}")
            raise

    def to_dict(self, include_passwords: bool = False) -> Dict[str, Any]:
        """
        Converte configuração para dicionário.

        Parameters
        ----------
        include_passwords : bool, optional
            Se deve incluir senhas (padrão: False)

        Returns
        -------
        dict
            Dicionário com configuração

        Examples
        --------
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('u', 'p')], 'src', 'dst'
        ... )
        >>> result = config.to_dict()
        >>> 'host' in result
        True
        """
        try:
            users_data = []
            for user in self.possible_users:
                user_dict = {'username': user.username}
                if include_passwords:
                    user_dict['password'] = user.password
                user_dict['priority'] = user.priority
                user_dict['validated'] = user.validated
                users_data.append(user_dict)

            return {
                'host': self.host,
                'port': self.port,
                'ssl_mode': self.ssl_mode.value,
                'possible_users': users_data,
                'db_source': self.db_source,
                'db_destiny': self.db_destiny,
                'connect_timeout': self.connect_timeout,
                'application_name': self.application_name,
                'pool_size': self.pool_size,
                'max_overflow': self.max_overflow,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'validated_user': self.validated_user.to_dict() if self.validated_user else None,
                'extra_params': self.extra_params
            }

        except Exception as e:
            logging.error(f"Erro ao converter para dict: {e}")
            return {}

    def to_json_file(
        self,
        filepath: Union[str, Path],
        include_passwords: bool = False,
        indent: int = 2
    ) -> bool:
        """
        Salva configuração em arquivo JSON.

        Parameters
        ----------
        filepath : str or Path
            Caminho do arquivo
        include_passwords : bool, optional
            Se deve incluir senhas
        indent : int, optional
            Indentação do JSON

        Returns
        -------
        bool
            True se salvo com sucesso, False caso contrário

        Examples
        --------
        >>> import tempfile
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('u', 'p')], 'src', 'dst'
        ... )
        >>> with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        ...     tmpfile = f.name
        >>> config.to_json_file(tmpfile)  # doctest: +SKIP
        True
        >>> os.unlink(tmpfile)  # doctest: +SKIP
        """
        try:
            if not isinstance(filepath, (str, Path)):
                raise TypeError("filepath deve ser str ou Path")

            filepath = Path(filepath)
            data = self.to_dict(include_passwords=include_passwords)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)

            logging.info(f"Configuração salva em: {filepath}")
            return True

        except (TypeError, IOError) as e:
            logging.error(f"Erro ao salvar JSON: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao salvar JSON: {e}")
            return False

    def _filter_safe_extra_params(self) -> Dict[str, Any]:
        """
        Filtra extra_params para remover parâmetros não suportados pelo psycopg2.

        Parâmetros como 'options' com valores de configuração (-c) não são
        suportados como parâmetros de conexão startup e devem ser aplicados
        após a conexão ser estabelecida.

        Returns
        -------
        dict
            Extra params seguros para usar na conexão
        """
        if not self.extra_params:
            return {}

        # Lista de parâmetros suportados pelo psycopg2 na conexão
        supported_params = {
            'connect_timeout', 'client_encoding', 'options',
            'application_name', 'fallback_application_name',
            'keepalives', 'keepalives_idle', 'keepalives_interval',
            'keepalives_count', 'tcp_user_timeout', 'replication',
            'gssencmode', 'sslmode', 'sslcompression', 'sslcert',
            'sslkey', 'sslrootcert', 'sslcrl', 'requirepeer',
            'ssl_min_protocol_version', 'ssl_max_protocol_version',
            'krbsrvname', 'gsslib', 'service', 'target_session_attrs',
            'channel_binding'
        }

        safe_params = {}
        unsafe_params = []

        for key, value in self.extra_params.items():
            # Verificar se é parâmetro suportado
            if key in supported_params:
                # Validação especial para 'options'
                if key == 'options':
                    # Options com -c não funciona no startup
                    if isinstance(value, str) and '-c' in value:
                        logging.warning(
                            f"Parâmetro 'options' com '-c' não é suportado no startup. "
                            f"Use SET após conectar. Valor ignorado: {value}"
                        )
                        unsafe_params.append(f"{key}={value}")
                        continue

                safe_params[key] = value
            else:
                unsafe_params.append(f"{key}={value}")
                logging.warning(
                    f"Parâmetro extra não suportado ignorado: {key}={value}"
                )

        if unsafe_params:
            logging.info(
                f"Parâmetros não suportados removidos: {', '.join(unsafe_params)}"
            )

        return safe_params

    def get_connection_params(
        self,
        database: Optional[str] = None,
        user: Optional[UserCredential] = None
    ) -> Union[Dict[str, Any], bool]:
        """
        Obtém parâmetros de conexão para psycopg2.

        Parameters
        ----------
        database : str, optional
            Nome do banco (usa db_source se None)
        user : UserCredential, optional
            Credencial a usar (usa validated_user se None)

        Returns
        -------
        dict or bool
            Parâmetros de conexão ou False se inválido

        Examples
        --------
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('u', 'p')], 'src', 'dst'
        ... )
        >>> params = config.get_connection_params()
        >>> params is False
        True
        >>> config.validated_user = config.possible_users[0]
        >>> params = config.get_connection_params()
        >>> isinstance(params, dict)
        True
        """
        try:
            # Determinar usuário
            target_user = user or self.validated_user
            if not target_user:
                logging.error("Nenhum usuário validado disponível")
                return False

            # Determinar database
            target_db = database or self.db_source
            if not target_db:
                raise ValueError("Database não especificado")

            # Filtrar extra_params para parâmetros seguros
            safe_extra_params = self._filter_safe_extra_params()

            params = {
                'host': self.host,
                'port': self.port,
                'database': target_db,
                'user': target_user.username,
                'password': target_user.password,
                'connect_timeout': self.connect_timeout,
                'application_name': self.application_name,
                'sslmode': self.ssl_mode.value,
                **safe_extra_params
            }

            return params

        except (ValueError, AttributeError) as e:
            logging.error(f"Erro ao obter parâmetros de conexão: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao obter parâmetros: {e}")
            return False

    def validate_credentials(self, database: str = 'postgres') -> bool:
        """
        Valida credenciais tentando conectar.

        Tenta conectar com cada usuário em ordem de prioridade até encontrar
        credenciais válidas. Define validated_user se bem-sucedido.

        Parameters
        ----------
        database : str, optional
            Banco para testar conexão (padrão: 'postgres')

        Returns
        -------
        bool
            True se encontrou credenciais válidas, False caso contrário

        Examples
        --------
        >>> config = PostgreSQLJsonConfig(
        ...     'localhost', 5432, SSLMode.DISABLE,
        ...     [UserCredential('postgres', 'wrong'), UserCredential('user', 'pass')],
        ...     'src', 'dst'
        ... )
        >>> config.validate_credentials()  # doctest: +SKIP
        True
        """
        try:
            if not isinstance(database, str) or not database:
                raise ValueError("Database inválido")

            logging.info(
                f"Validando credenciais para {self.host}:{self.port}/{database}"
            )

            for user in self.possible_users:
                try:
                    logging.info(f"Tentando usuário: {user.username}")

                    conn_params = {
                        'host': self.host,
                        'port': self.port,
                        'database': database,
                        'user': user.username,
                        'password': user.password,
                        'connect_timeout': self.connect_timeout,
                        'sslmode': self.ssl_mode.value
                    }

                    # Tentar conectar
                    conn = psycopg2.connect(**conn_params)

                    # Testar query simples
                    cursor = conn.cursor()
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    cursor.close()
                    conn.close()

                    # Sucesso!
                    user.validated = True
                    user.last_error = None
                    self.validated_user = user

                    logging.info(
                        f"✓ Credenciais validadas para usuário: {user.username}"
                    )
                    logging.info(f"PostgreSQL: {version}")

                    return True

                except psycopg2.Error as e:
                    user.validated = False
                    user.last_error = str(e)
                    logging.warning(
                        f"✗ Falha ao validar usuário {user.username}: {e}"
                    )
                    continue
                except Exception as e:
                    user.validated = False
                    user.last_error = str(e)
                    logging.warning(
                        f"✗ Erro inesperado ao validar {user.username}: {e}"
                    )
                    continue

            # Nenhum usuário validado
            logging.error("Nenhuma credencial válida encontrada")
            return False

        except (ValueError, TypeError) as e:
            logging.error(f"Erro ao validar credenciais: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao validar credenciais: {e}")
            return False

    def __repr__(self) -> str:
        """Representação segura da configuração."""
        return (
            f"PostgreSQLJsonConfig(host='{self.host}', port={self.port}, "
            f"db_source='{self.db_source}', db_destiny='{self.db_destiny}', "
            f"users={len(self.possible_users)}, "
            f"validated={self.validated_user is not None})"
        )


if __name__ == "__main__":
    import doctest
    doctest.testmod()
