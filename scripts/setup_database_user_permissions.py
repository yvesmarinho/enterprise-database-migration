#!/usr/bin/env python3
"""
Script universal para criar e configurar usuários MySQL/MariaDB e PostgreSQL.

Este script:
1. Solicita informações do usuário (nome, senha, database, tipo)
2. Cria o usuário no MySQL/MariaDB ou PostgreSQL
3. Concede permissões baseadas no tipo de usuário
4. Suporta usuários globais (todas as databases) ou específicos
5. Usa SQLAlchemy para evitar duplicação de código

Tipos de usuário suportados:
- write: Permissões completas de leitura e escrita
- read: Apenas permissões de leitura (SELECT)
- backup: Permissões de leitura otimizadas para backup
- migration: Permissões completas incluindo DDL

Autor: Sistema de Migração Enterprise
Data: 27/01/2026
Python: 3.11+
"""

import argparse
import getpass
import json
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError


class DatabaseUserManager(ABC):
    """Classe base abstrata para gerenciamento de usuários de banco de dados."""

    # Mapeamento de tipos de usuário para permissões (pode ser sobrescrito)
    USER_TYPES = {
        'write': {
            'description': 'Permissões de leitura e escrita (sem DDL)',
            'privileges': []
        },
        'read': {
            'description': 'Apenas permissões de leitura',
            'privileges': []
        },
        'backup': {
            'description': 'Permissões otimizadas para backup',
            'privileges': []
        },
        'migration': {
            'description': 'Permissões completas incluindo DDL',
            'privileges': []
        }
    }

    def __init__(self, host: str, port: int, admin_user: str, admin_password: str):
        """
        Inicializa o gerenciador.

        Args:
            host: Hostname do servidor
            port: Porta do servidor
            admin_user: Usuário administrativo
            admin_password: Senha do usuário administrativo
        """
        self.host = host
        self.port = port
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.engine: Optional[Engine] = None

    @abstractmethod
    def connect(self) -> bool:
        """Conecta ao servidor com usuário administrativo."""
        pass

    @abstractmethod
    def check_user_exists(self, username: str, host_pattern: str = '%') -> bool:
        """Verifica se o usuário existe."""
        pass

    @abstractmethod
    def create_user(self, username: str, password: str, host_pattern: str = '%') -> bool:
        """Cria um usuário."""
        pass

    @abstractmethod
    def drop_user(self, username: str, host_pattern: str = '%') -> bool:
        """Remove um usuário."""
        pass

    @abstractmethod
    def grant_privileges(
        self,
        username: str,
        user_type: str,
        database: Optional[str] = None,
        host_pattern: str = '%'
    ) -> bool:
        """Concede privilégios ao usuário."""
        pass

    @abstractmethod
    def get_all_databases(self) -> List[str]:
        """Obtém lista de todas as databases."""
        pass

    @abstractmethod
    def show_user_grants(self, username: str, host_pattern: str = '%'):
        """Mostra os privilégios de um usuário."""
        pass

    def close(self):
        """Fecha a conexão."""
        if self.engine:
            self.engine.dispose()
            print("\n✅ Conexão encerrada")


class MySQLUserManager(DatabaseUserManager):
    """Gerenciador de usuários e permissões MySQL/MariaDB."""

    USER_TYPES = {
        'write': {
            'description': 'Permissões de leitura e escrita (sem DDL)',
            'privileges': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'EXECUTE', 'SHOW VIEW']
        },
        'read': {
            'description': 'Apenas permissões de leitura',
            'privileges': ['SELECT', 'SHOW VIEW']
        },
        'backup': {
            'description': 'Permissões otimizadas para backup',
            'privileges': ['SELECT', 'SHOW VIEW', 'LOCK TABLES', 'RELOAD', 'REPLICATION CLIENT']
        },
        'migration': {
            'description': 'Permissões completas incluindo DDL',
            'privileges': ['ALL PRIVILEGES']
        }
    }

    def connect(self) -> bool:
        """Conecta ao servidor MySQL com usuário administrativo."""
        try:
            conn_str = (
                f"mysql+pymysql://{self.admin_user}:{self.admin_password}"
                f"@{self.host}:{self.port}/mysql?charset=utf8mb4"
            )

            self.engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 30}
            )

            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
                print(f"✅ Conectado ao MySQL/MariaDB: {version}")

            return True

        except (OperationalError, SQLAlchemyError) as e:
            print(f"❌ Erro ao conectar: {e}")
            return False

    def check_user_exists(self, username: str, host_pattern: str = '%') -> bool:
        """Verifica se o usuário existe no MySQL."""
        query = text("""
            SELECT COUNT(*)
            FROM mysql.user
            WHERE User = :username AND Host = :host
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    query, {"username": username, "host": host_pattern})
                count = result.scalar()

                if count > 0:
                    print(
                        f"ℹ️  Usuário '{username}'@'{host_pattern}' já existe")
                    return True
                else:
                    print(
                        f"ℹ️  Usuário '{username}'@'{host_pattern}' não existe")
                    return False

        except SQLAlchemyError as e:
            print(f"❌ Erro ao verificar usuário: {e}")
            return False

    def create_user(self, username: str, password: str, host_pattern: str = '%') -> bool:
        """Cria um usuário MySQL."""
        if self.check_user_exists(username, host_pattern):
            response = input(
                f"⚠️  Usuário já existe. Deseja recriar? (s/N): ").strip().lower()
            if response == 's':
                if not self.drop_user(username, host_pattern):
                    return False
            else:
                print("ℹ️  Mantendo usuário existente")
                return True

        try:
            with self.engine.connect() as conn:
                create_sql = f"CREATE USER '{username}'@'{host_pattern}' IDENTIFIED BY '{password}'"
                conn.execute(text(create_sql))
                conn.commit()
                print(
                    f"✅ Usuário '{username}'@'{host_pattern}' criado com sucesso")
                return True

        except SQLAlchemyError as e:
            print(f"❌ Erro ao criar usuário: {e}")
            return False

    def drop_user(self, username: str, host_pattern: str = '%') -> bool:
        """Remove um usuário MySQL."""
        try:
            with self.engine.connect() as conn:
                drop_sql = f"DROP USER IF EXISTS '{username}'@'{host_pattern}'"
                conn.execute(text(drop_sql))
                conn.commit()
                print(f"✅ Usuário '{username}'@'{host_pattern}' removido")
                return True

        except SQLAlchemyError as e:
            print(f"❌ Erro ao remover usuário: {e}")
            return False

    def grant_privileges(
        self,
        username: str,
        user_type: str,
        database: Optional[str] = None,
        host_pattern: str = '%'
    ) -> bool:
        """Concede privilégios ao usuário MySQL."""
        if user_type not in self.USER_TYPES:
            print(f"❌ Tipo de usuário inválido: {user_type}")
            return False

        # Validação de segurança: tipo backup não pode ser global
        if user_type == 'backup' and database is None:
            print("\n" + "="*70)
            print("🚨 ERRO DE SEGURANÇA: Tipo 'backup' não pode ter acesso global")
            print("="*70)
            print(
                "\nUsuários do tipo 'backup' devem ser restritos a databases específicas.")
            print("Use o parâmetro --database para especificar a database.")
            print("\nExemplo:")
            print("  --database perfexcrm --type backup")
            print("\n❌ Operação cancelada por motivos de segurança.\n")
            return False

        # Aviso de perigo para acesso global
        if database is None:
            databases = self.get_all_databases()
            print("\n" + "="*70)
            print("⚠️  ATENÇÃO: ACESSO GLOBAL A TODAS AS DATABASES")
            print("="*70)
            print(
                f"\n🔓 O usuário '{username}'@'{host_pattern}' terá permissões em {len(databases)} databases:")
            # Mostra algumas databases como exemplo
            for i, db in enumerate(databases[:5]):
                print(f"   • {db}")
            if len(databases) > 5:
                print(f"   ... e mais {len(databases) - 5} databases")
            print(f"\n⚠️  Tipo de permissão: '{user_type}'")
            print("\n" + "="*70)
            response = input(
                "\nDeseja continuar? (digite 'SIM' para confirmar): ").strip()
            if response != 'SIM':
                print("\n❌ Operação cancelada pelo usuário.\n")
                return False
            print()

        privileges = self.USER_TYPES[user_type]['privileges']
        scope = f"`{database}`.*" if database else "*.*"
        scope_desc = f"database '{database}'" if database else "todas as databases (global)"

        print(f"\n📋 Concedendo permissões de '{user_type}' em {scope_desc}...")

        try:
            with self.engine.connect() as conn:
                for privilege in privileges:
                    grant_sql = f"GRANT {privilege} ON {scope} TO '{username}'@'{host_pattern}'"
                    try:
                        conn.execute(text(grant_sql))
                        print(f"   ✓ {privilege}")
                    except SQLAlchemyError as e:
                        print(f"   ✗ {privilege}: {e}")
                        continue

                conn.execute(text("FLUSH PRIVILEGES"))
                conn.commit()

                print(f"✅ Permissões concedidas com sucesso")
                return True

        except SQLAlchemyError as e:
            print(f"❌ Erro ao conceder privilégios: {e}")
            return False

    def get_all_databases(self) -> List[str]:
        """Obtém lista de todas as databases MySQL."""
        query = text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            ORDER BY schema_name
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [row[0] for row in result]

        except SQLAlchemyError as e:
            print(f"❌ Erro ao listar databases: {e}")
            return []

    def show_user_grants(self, username: str, host_pattern: str = '%'):
        """Mostra os privilégios de um usuário MySQL."""
        try:
            with self.engine.connect() as conn:
                show_grants = f"SHOW GRANTS FOR '{username}'@'{host_pattern}'"
                result = conn.execute(text(show_grants))

                print(f"\n📜 Privilégios de '{username}'@'{host_pattern}':")
                print("─" * 70)
                for row in result:
                    print(f"  {row[0]}")
                print("─" * 70)

        except SQLAlchemyError as e:
            print(f"❌ Erro ao mostrar privilégios: {e}")


class PostgreSQLUserManager(DatabaseUserManager):
    """Gerenciador de usuários e permissões PostgreSQL."""

    USER_TYPES = {
        'write': {
            'description': 'Permissões de leitura e escrita (sem DDL)',
            'privileges': ['CONNECT', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'USAGE']
        },
        'read': {
            'description': 'Apenas permissões de leitura',
            'privileges': ['CONNECT', 'SELECT', 'USAGE']
        },
        'backup': {
            'description': 'Permissões otimizadas para backup',
            'privileges': ['CONNECT', 'SELECT', 'USAGE']
        },
        'migration': {
            'description': 'Permissões completas incluindo DDL',
            'privileges': ['ALL']
        }
    }

    def connect(self) -> bool:
        """Conecta ao servidor PostgreSQL com usuário administrativo."""
        try:
            conn_str = (
                f"postgresql://{self.admin_user}:{self.admin_password}"
                f"@{self.host}:{self.port}/postgres"
            )

            self.engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 30}
            )

            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Conectado ao PostgreSQL: {version[:50]}...")

            return True

        except (OperationalError, SQLAlchemyError) as e:
            print(f"❌ Erro ao conectar: {e}")
            return False

    def check_user_exists(self, username: str, host_pattern: str = '%') -> bool:
        """Verifica se o usuário existe no PostgreSQL."""
        query = text("SELECT 1 FROM pg_roles WHERE rolname = :username")

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {"username": username})
                exists = result.scalar() is not None

                if exists:
                    print(f"ℹ️  Usuário '{username}' já existe")
                    return True
                else:
                    print(f"ℹ️  Usuário '{username}' não existe")
                    return False

        except SQLAlchemyError as e:
            print(f"❌ Erro ao verificar usuário: {e}")
            return False

    def create_user(self, username: str, password: str, host_pattern: str = '%') -> bool:
        """Cria um usuário PostgreSQL."""
        if self.check_user_exists(username):
            response = input(
                f"⚠️  Usuário já existe. Deseja recriar? (s/N): ").strip().lower()
            if response == 's':
                if not self.drop_user(username):
                    return False
            else:
                print("ℹ️  Mantendo usuário existente")
                return True

        try:
            with self.engine.connect() as conn:
                create_sql = f"""
                    CREATE ROLE {username} WITH
                    LOGIN
                    PASSWORD '{password}'
                    NOSUPERUSER
                    NOCREATEDB
                    NOCREATEROLE
                    NOINHERIT
                    NOREPLICATION
                """
                conn.execute(text(create_sql))
                conn.commit()
                print(f"✅ Usuário '{username}' criado com sucesso")
                return True

        except SQLAlchemyError as e:
            print(f"❌ Erro ao criar usuário: {e}")
            return False

    def drop_user(self, username: str, host_pattern: str = '%') -> bool:
        """Remove um usuário PostgreSQL."""
        try:
            with self.engine.connect() as conn:
                drop_sql = f"DROP ROLE IF EXISTS {username}"
                conn.execute(text(drop_sql))
                conn.commit()
                print(f"✅ Usuário '{username}' removido")
                return True

        except SQLAlchemyError as e:
            print(f"❌ Erro ao remover usuário: {e}")
            return False

    def grant_privileges(
        self,
        username: str,
        user_type: str,
        database: Optional[str] = None,
        host_pattern: str = '%'
    ) -> bool:
        """Concede privilégios ao usuário PostgreSQL."""
        if user_type not in self.USER_TYPES:
            print(f"❌ Tipo de usuário inválido: {user_type}")
            return False

        # Validação de segurança: tipo backup não pode ser global
        if user_type == 'backup' and database is None:
            print("\n" + "="*70)
            print("🚨 ERRO DE SEGURANÇA: Tipo 'backup' não pode ter acesso global")
            print("="*70)
            print(
                "\nUsuários do tipo 'backup' devem ser restritos a databases específicas.")
            print("Use o parâmetro --database para especificar a database.")
            print("\nExemplo:")
            print("  --database app_workforce --type backup")
            print("\n❌ Operação cancelada por motivos de segurança.\n")
            return False

        databases = [database] if database else self.get_all_databases()
        if not databases:
            print("❌ Nenhuma database encontrada")
            return False

        # Aviso de perigo para acesso global
        if database is None:
            print("\n" + "="*70)
            print("⚠️  ATENÇÃO: ACESSO GLOBAL A TODAS AS DATABASES")
            print("="*70)
            print(
                f"\n🔓 O usuário '{username}' terá permissões em {len(databases)} databases:")
            # Mostra algumas databases como exemplo
            for i, db in enumerate(databases[:5]):
                print(f"   • {db}")
            if len(databases) > 5:
                print(f"   ... e mais {len(databases) - 5} databases")
            print(f"\n⚠️  Tipo de permissão: '{user_type}'")
            print("\n" + "="*70)
            response = input(
                "\nDeseja continuar? (digite 'SIM' para confirmar): ").strip()
            if response != 'SIM':
                print("\n❌ Operação cancelada pelo usuário.\n")
                return False
            print()

        scope_desc = f"database '{database}'" if database else f"{len(databases)} databases"
        print(f"\n📋 Concedendo permissões de '{user_type}' em {scope_desc}...")

        success = True
        for db in databases:
            try:
                # Conecta à database específica
                db_engine = create_engine(
                    f"postgresql://{self.admin_user}:{self.admin_password}"
                    f"@{self.host}:{self.port}/{db}"
                )

                with db_engine.connect() as conn:
                    # GRANT CONNECT
                    if 'CONNECT' in self.USER_TYPES[user_type]['privileges'] or user_type == 'migration':
                        conn.execute(
                            text(f"GRANT CONNECT ON DATABASE {db} TO {username}"))

                    # Obtém schemas
                    schemas_query = text("""
                        SELECT schema_name
                        FROM information_schema.schemata
                        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                    """)
                    result = conn.execute(schemas_query)
                    schemas = [row[0] for row in result]

                    for schema in schemas:
                        if user_type == 'migration':
                            # Permissões completas
                            conn.execute(
                                text(f"GRANT ALL PRIVILEGES ON SCHEMA {schema} TO {username}"))
                            conn.execute(
                                text(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema} TO {username}"))
                            conn.execute(
                                text(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {schema} TO {username}"))
                            conn.execute(text(
                                f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT ALL ON TABLES TO {username}"))
                        else:
                            # USAGE no schema
                            if 'USAGE' in self.USER_TYPES[user_type]['privileges']:
                                conn.execute(
                                    text(f"GRANT USAGE ON SCHEMA {schema} TO {username}"))

                            # SELECT nas tabelas
                            if 'SELECT' in self.USER_TYPES[user_type]['privileges']:
                                conn.execute(
                                    text(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {username}"))
                                conn.execute(
                                    text(f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {username}"))
                                conn.execute(text(
                                    f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO {username}"))

                            # INSERT, UPDATE, DELETE para write
                            if user_type == 'write':
                                conn.execute(text(
                                    f"GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO {username}"))
                                conn.execute(
                                    text(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA {schema} TO {username}"))
                                conn.execute(text(
                                    f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT INSERT, UPDATE, DELETE ON TABLES TO {username}"))

                    conn.commit()
                    print(f"   ✓ {db} ({len(schemas)} schemas)")

                db_engine.dispose()

            except SQLAlchemyError as e:
                print(f"   ✗ {db}: {e}")
                success = False
                continue

        if success:
            print(f"✅ Permissões concedidas com sucesso")
        return success

    def get_all_databases(self) -> List[str]:
        """Obtém lista de todas as databases PostgreSQL."""
        query = text("""
            SELECT datname
            FROM pg_database
            WHERE datistemplate = false
              AND datname NOT IN ('postgres', 'template0', 'template1')
            ORDER BY datname
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [row[0] for row in result]

        except SQLAlchemyError as e:
            print(f"❌ Erro ao listar databases: {e}")
            return []

    def show_user_grants(self, username: str, host_pattern: str = '%'):
        """Mostra os privilégios de um usuário PostgreSQL."""
        try:
            with self.engine.connect() as conn:
                # Informações básicas do role
                role_query = text("""
                    SELECT rolname, rolsuper, rolcreatedb, rolcreaterole
                    FROM pg_roles
                    WHERE rolname = :username
                """)
                result = conn.execute(role_query, {"username": username})
                row = result.fetchone()

                if row:
                    print(f"\n📜 Privilégios de '{username}':")
                    print("─" * 70)
                    print(f"  Superuser: {'Sim' if row[1] else 'Não'}")
                    print(f"  Create DB: {'Sim' if row[2] else 'Não'}")
                    print(f"  Create Role: {'Sim' if row[3] else 'Não'}")
                    print("─" * 70)

                    # Lista databases com acesso
                    databases = self.get_all_databases()
                    print(f"\n  Databases ({len(databases)} total):")
                    for db in databases[:10]:  # Mostra primeiras 10
                        print(f"    • {db}")
                    if len(databases) > 10:
                        print(
                            f"    ... e mais {len(databases) - 10} databases")
                else:
                    print(f"❌ Usuário '{username}' não encontrado")

        except SQLAlchemyError as e:
            print(f"❌ Erro ao mostrar privilégios: {e}")


def create_manager(db_type: str, host: str, port: int, admin_user: str, admin_password: str) -> DatabaseUserManager:
    """
    Factory para criar o gerenciador apropriado.

    Args:
        db_type: Tipo de banco ('mysql' ou 'postgresql')
        host: Hostname do servidor
        port: Porta do servidor
        admin_user: Usuário administrativo
        admin_password: Senha do admin

    Returns:
        Instância do gerenciador apropriado
    """
    if db_type.lower() in ['mysql', 'mariadb']:
        return MySQLUserManager(host, port, admin_user, admin_password)
    elif db_type.lower() in ['postgresql', 'postgres', 'pg']:
        return PostgreSQLUserManager(host, port, admin_user, admin_password)
    else:
        raise ValueError(
            f"Tipo de banco não suportado: {db_type}. Use 'mysql' ou 'postgresql'")


def load_config_file(config_path: str) -> Optional[Dict]:
    """
    Carrega arquivo de configuração JSON.

    Args:
        config_path: Caminho para o arquivo de configuração

    Returns:
        Dicionário com configurações ou None se erro
    """
    try:
        path = Path(config_path)
        if not path.exists():
            print(f"⚠️  Arquivo de configuração não encontrado: {config_path}")
            return None

        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"✅ Configuração carregada de: {config_path}")
            return config

    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar configuração: {e}")
        return None


def get_default_config_path(db_type: str) -> Optional[str]:
    """
    Retorna o caminho padrão do arquivo de configuração baseado no tipo de banco.

    Args:
        db_type: Tipo de banco ('mysql' ou 'postgresql')

    Returns:
        Caminho do arquivo de configuração ou None
    """
    project_root = Path(__file__).parent.parent
    secrets_dir = project_root / "secrets"

    if db_type in ['mysql', 'mariadb']:
        config_file = secrets_dir / "mysql_config.json"
    elif db_type in ['postgresql', 'postgres', 'pg']:
        config_file = secrets_dir / "postgresql_destination_config.json"
    else:
        return None

    return str(config_file) if config_file.exists() else None


def extract_connection_info(config: Dict, db_type: str) -> Optional[Dict]:
    """
    Extrai informações de conexão do arquivo de configuração.

    Args:
        config: Dicionário de configuração
        db_type: Tipo de banco

    Returns:
        Dicionário com host, port, user, password
    """
    try:
        if db_type in ['mysql', 'mariadb']:
            # Formato: mysql_config.json
            # Usa 'destination' se existir, senão 'source'
            conn_info = config.get('destination') or config.get('source')
            if not conn_info:
                print("❌ Formato de configuração MySQL inválido")
                return None

            return {
                'host': conn_info.get('host'),
                'port': conn_info.get('port', 3306),
                'admin_user': conn_info.get('user'),
                'admin_password': conn_info.get('password')
            }

        elif db_type in ['postgresql', 'postgres', 'pg']:
            # Formato: postgresql_destination_config.json
            server = config.get('server', {})
            auth = config.get('authentication', {})

            return {
                'host': server.get('host'),
                'port': server.get('port', 5432),
                'admin_user': auth.get('user'),
                'admin_password': auth.get('password')
            }

        return None

    except Exception as e:
        print(f"❌ Erro ao extrair informações de conexão: {e}")
        return None


def validate_admin_user_and_get_password(
    config: Dict,
    db_type: str,
    requested_admin_user: str
) -> Optional[str]:
    """
    Valida se o admin_user solicitado existe no JSON e retorna sua senha.

    Args:
        config: Dicionário de configuração do JSON
        db_type: Tipo de banco de dados
        requested_admin_user: Nome do usuário admin solicitado via CLI

    Returns:
        Senha do usuário se encontrado, None caso contrário
    """
    try:
        if db_type in ['mysql', 'mariadb']:
            conn_info = config.get('destination') or config.get('source')
            if not conn_info:
                return None

            config_user = conn_info.get('user')
            config_password = conn_info.get('password')

        elif db_type in ['postgresql', 'postgres', 'pg']:
            auth = config.get('authentication', {})
            config_user = auth.get('user')
            config_password = auth.get('password')

        else:
            return None

        # Valida se o usuário solicitado corresponde ao usuário no JSON
        if config_user != requested_admin_user:
            print(
                f"❌ ERRO: Usuário '{requested_admin_user}' não encontrado no arquivo de configuração")
            print(f"   Usuário disponível no JSON: '{config_user}'")
            print(
                f"   Use --admin-user {config_user} ou atualize o arquivo de configuração")
            return None

        if not config_password:
            print(
                f"❌ ERRO: Senha não encontrada no JSON para o usuário '{config_user}'")
            return None

        return config_password

    except Exception as e:
        print(f"❌ Erro ao validar usuário e senha: {e}")
        return None


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Cria e configura usuários MySQL/MariaDB ou PostgreSQL com permissões específicas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # PostgreSQL - Usando arquivo de configuração (recomendado)
  python scripts/setup_database_user_permissions.py \\
    --db-type postgresql \\
    --username backup_user \\
    --password senha_backup \\
    --type backup \\
    --database app_workforce
  python scripts/setup_database_user_permissions.py \\
    --db-type mysql \\
    --config secrets/mysql_config.json \\
    --username backup_user \\
    --password senha_backup \\
    --type backup \\
    --database perfexcrm

  # PostgreSQL - Usando arquivo de configuração
  python scripts/setup_database_user_permissions.py \\
    --db-type postgresql \\
    --config secrets/postgresql_destination_config.json \\
    --username backup_user \\
    --password senha_backup \\
    --type backup \\
    --database app_workforce

  # PostgreSQL - Busca senha do admin_user automaticamente do JSON
  python scripts/setup_database_user_permissions.py \\
    --db-type postgresql \\
    --host wfdb02.vya.digital \\
    --admin-user migration_user \\
    --username backup_user \\
    --password senha_backup \\
    --type backup \\
    --database app_workforce

  # MySQL - Sem arquivo de configuração (manual - requer senha do admin)
  python scripts/setup_database_user_permissions.py \\
    --db-type mysql \\
    --host localhost \\
    --admin-user root \\
    --admin-password senha_admin \\
    --username backup_user \\
    --password senha_backup \\
    --type backup \\
    --database perfexcrm

Comportamento de Autenticação:
  - Se --admin-user for fornecido COM arquivo de configuração:
    * A senha será BUSCADA AUTOMATICAMENTE do JSON
    * Se o usuário não existir no JSON, o script será ENCERRADO com erro

  - Se --admin-user for fornecido SEM arquivo de configuração:
    * É OBRIGATÓRIO informar --admin-password

  - Se --admin-user NÃO for fornecido:
    * Usa as credenciais do arquivo de configuração

Tipos de banco suportados:
  mysql, mariadb       - MySQL/MariaDB
  postgresql, postgres - PostgreSQL

Tipos de usuário:
  write      - Leitura e escrita (sem DDL)
  read       - Apenas leitura
  backup     - Otimizado para backups
  migration  - Permissões completas (incluindo DDL)

🚨 REGRAS DE SEGURANÇA OBRIGATÓRIAS:

  1. Parâmetro --database é OBRIGATÓRIO:
     - TODOS os tipos de usuário devem especificar --database
     - Acesso global NÃO é permitido em nenhuma hipótese
     - Princípio do menor privilégio aplicado rigorosamente

  2. Sem exceções:
     - Não há opção de acesso global
     - Todos os usuários são restritos a databases específicas
     - Operação será BLOQUEADA sem --database

Exemplos de Uso (TODOS requerem --database):
  # ✅ Backup em database específica
  --type backup --database app_workforce

  # ✅ Read-only em database específica
  --type read --database kutt

  # ❌ Qualquer tipo sem --database (BLOQUEADO)
  --type read    # ERRO - database obrigatória
  --type backup  # ERRO - database obrigatória
  --type write   # ERRO - database obrigatória
        """
    )

    parser.add_argument('--db-type', choices=['mysql', 'mariadb', 'postgresql', 'postgres'],
                        help='Tipo de banco de dados')
    parser.add_argument(
        '--config', help='Arquivo de configuração JSON (secrets/)')
    parser.add_argument('--host', help='Host do servidor (sobrescreve config)')
    parser.add_argument('--port', type=int,
                        help='Porta do servidor (sobrescreve config)')
    parser.add_argument(
        '--admin-user', help='Usuário administrativo (busca senha do JSON se disponível)')
    parser.add_argument('--admin-password',
                        help='Senha do usuário administrativo (opcional se usar JSON)')
    parser.add_argument('--username', help='Nome do novo usuário')
    parser.add_argument('--password', help='Senha do novo usuário')
    parser.add_argument('--host-pattern', default='%',
                        help='Padrão de host MySQL (padrão: %%)')
    parser.add_argument(
        '--type', help='Tipo de usuário (write, read, backup, migration)')
    parser.add_argument(
        '--database', required=False, help='Database específica (OBRIGATÓRIO para segurança)')
    parser.add_argument('--show-grants', action='store_true',
                        help='Mostrar privilégios após criação')
    parser.add_argument('--list-databases', action='store_true',
                        help='Listar databases disponíveis')

    args = parser.parse_args()

    # Se nenhum argumento foi fornecido, mostra help e sai
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # Verifica se todos os parâmetros obrigatórios foram fornecidos
    if not all([args.db_type, args.username, args.password, args.type, args.database]):
        print("\n❌ ERRO: Parâmetros obrigatórios faltando\n")
        print("Parâmetros obrigatórios:")
        print("  --db-type      Tipo de banco (mysql, mariadb, postgresql, postgres)")
        print("  --username     Nome do novo usuário")
        print("  --password     Senha do novo usuário")
        print("  --type         Tipo de usuário (write, read, backup, migration)")
        print("  --database     Database específica (obrigatório)")
        print("\nUse --help para ver exemplos completos\n")
        sys.exit(1)

    config = None
    config = None

    # Tenta carregar configuração de arquivo
    conn_info = None
    file_config = None

    if args.config:
        # Usa arquivo especificado
        file_config = load_config_file(args.config)
        if file_config:
            conn_info = extract_connection_info(file_config, args.db_type)
    elif args.db_type:
        # Tenta usar configuração padrão
        default_config_path = get_default_config_path(args.db_type)
        if default_config_path:
            print(f"ℹ️  Usando configuração padrão: {default_config_path}")
            file_config = load_config_file(default_config_path)
            if file_config:
                conn_info = extract_connection_info(
                    file_config, args.db_type)

    # Determina host e porta
    if conn_info:
        host = args.host or conn_info['host']
        port = args.port or conn_info['port']
    else:
        if not args.host:
            print(
                "❌ Erro: --host é obrigatório quando não há arquivo de configuração")
            sys.exit(1)
        host = args.host
        port = args.port

    # Define porta padrão se não especificada
    if port is None:
        port = 3306 if args.db_type in ['mysql', 'mariadb'] else 5432

    # Determina admin_user e admin_password
    if args.admin_user and file_config:
        # Usuário especificado via CLI - busca senha no JSON
        admin_password = validate_admin_user_and_get_password(
            file_config,
            args.db_type,
            args.admin_user
        )
        if not admin_password:
            print("\n❌ OPERAÇÃO CANCELADA: Não foi possível autenticar o usuário")
            sys.exit(1)
        admin_user = args.admin_user
    elif conn_info:
        # Usa credenciais do arquivo de configuração
        admin_user = args.admin_user or conn_info['admin_user']
        admin_password = args.admin_password or conn_info['admin_password']
    else:
        # Sem arquivo - requer admin_user e admin_password via CLI
        if not all([args.admin_user, args.admin_password]):
            print("❌ Erro: Sem arquivo de configuração, é necessário informar:")
            print("   --admin-user e --admin-password")
            sys.exit(1)
        admin_user = args.admin_user
        admin_password = args.admin_password

    config = {
        'db_type': args.db_type,
        'host': host,
        'port': port,
        'admin_user': admin_user,
        'admin_password': admin_password,
        'new_username': args.username,
        'new_password': args.password,
        'host_pattern': args.host_pattern,
        'user_type': args.type,
        'database': args.database
    }
    # Cria gerenciador apropriado
    try:
        manager = create_manager(
            db_type=config['db_type'],
            host=config['host'],
            port=config['port'],
            admin_user=config['admin_user'],
            admin_password=config['admin_password']
        )
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    if not manager.connect():
        print("❌ Falha ao conectar ao servidor")
        sys.exit(1)

    print()

    # Lista databases se solicitado
    if args.list_databases:
        databases = manager.get_all_databases()
        print(f"\n📚 Databases disponíveis ({len(databases)}):")
        for db in databases:
            print(f"  • {db}")
        print()

    # Cria usuário
    print("🔨 CRIANDO USUÁRIO")
    print("-" * 70)
    if not manager.create_user(
        username=config['new_username'],
        password=config['new_password'],
        host_pattern=config['host_pattern']
    ):
        print("❌ Falha ao criar usuário")
        manager.close()
        sys.exit(1)

    print()

    # Concede privilégios
    print("🔑 CONCEDENDO PRIVILÉGIOS")
    print("-" * 70)
    if not manager.grant_privileges(
        username=config['new_username'],
        user_type=config['user_type'],
        database=config['database'],
        host_pattern=config['host_pattern']
    ):
        print("❌ Falha ao conceder privilégios")
        manager.close()
        sys.exit(1)

    # Mostra grants se solicitado
    if args.show_grants:
        manager.show_user_grants(
            username=config['new_username'],
            host_pattern=config['host_pattern']
        )

    print()
    print("="*70)
    print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    print("="*70)

    # Resumo
    scope = config['database'] if config['database'] else "GLOBAL (todas as databases)"
    print(f"""
📋 Resumo:
  • Banco: {config['db_type'].upper()}
  • Usuário: '{config['new_username']}'{'@' + config['host_pattern'] if config['db_type'] == 'mysql' else ''}
  • Tipo: {config['user_type']}
  • Escopo: {scope}
  • Servidor: {config['host']}:{config['port']}
    """)

    manager.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
