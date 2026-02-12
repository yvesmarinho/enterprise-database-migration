#!/usr/bin/env python3
"""
Script universal para criar e configurar usuários MySQL/MariaDB e PostgreSQL com permissões específicas.

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
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError


class DatabaseUserManager(ABC):
    """Gerenciador de usuários e permissões MySQL/MariaDB."""

    # Mapeamento de tipos de usuário para permissões
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

    def __init__(self, host: str, port: int, admin_user: str, admin_password: str):
        """
        Inicializa o gerenciador.

        Args:
            host: Hostname do servidor MySQL
            port: Porta do servidor MySQL
            admin_user: Usuário administrativo
            admin_password: Senha do usuário administrativo
        """
        self.host = host
        self.port = port
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.engine: Optional[Engine] = None

    def connect(self) -> bool:
        """
        Conecta ao servidor MySQL com usuário administrativo.

        Returns:
            True se conectado com sucesso
        """
        try:
            # Conecta sem especificar database (mysql system database)
            conn_str = (
                f"mysql+pymysql://{self.admin_user}:{self.admin_password}"
                f"@{self.host}:{self.port}/mysql?charset=utf8mb4"
            )

            self.engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                connect_args={
                    "connect_timeout": 30
                }
            )

            # Testa conexão
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
                print(f"✅ Conectado ao MySQL/MariaDB: {version}")

            return True

        except OperationalError as e:
            print(f"❌ Erro de conexão: {e}")
            return False
        except SQLAlchemyError as e:
            print(f"❌ Erro ao conectar: {e}")
            return False

    def check_user_exists(self, username: str, host_pattern: str = '%') -> bool:
        """
        Verifica se o usuário existe.

        Args:
            username: Nome do usuário
            host_pattern: Padrão de host (%, localhost, etc)

        Returns:
            True se o usuário existe
        """
        query = text("""
            SELECT COUNT(*)
            FROM mysql.user
            WHERE User = :username AND Host = :host
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {
                    "username": username,
                    "host": host_pattern
                })
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
        """
        Cria um usuário MySQL.

        Args:
            username: Nome do usuário
            password: Senha do usuário
            host_pattern: Padrão de host para conexão (% = qualquer host)

        Returns:
            True se criado com sucesso
        """
        if self.check_user_exists(username, host_pattern):
            response = input(
                f"⚠️  Usuário já existe. Deseja recriar? (s/N): ").strip().lower()
            if response == 's':
                if not self.drop_user(username, host_pattern):
                    return False
            else:
                print("ℹ️  Mantendo usuário existente")
                return True

        # Cria o usuário usando sintaxe compatível
        query = text(f"""
            CREATE USER :username@:host
            IDENTIFIED BY :password
        """)

        try:
            with self.engine.connect() as conn:
                # MySQL não suporta placeholders para identificadores, usar string formatting
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
        """
        Remove um usuário MySQL.

        Args:
            username: Nome do usuário
            host_pattern: Padrão de host

        Returns:
            True se removido com sucesso
        """
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
        """
        Concede privilégios ao usuário baseado no tipo.

        Args:
            username: Nome do usuário
            user_type: Tipo de usuário (write, read, backup, migration)
            database: Nome da database específica ou None para global
            host_pattern: Padrão de host do usuário

        Returns:
            True se privilégios concedidos com sucesso
        """
        if user_type not in self.USER_TYPES:
            print(f"❌ Tipo de usuário inválido: {user_type}")
            print(f"   Tipos válidos: {', '.join(self.USER_TYPES.keys())}")
            return False

        privileges = self.USER_TYPES[user_type]['privileges']

        # Define o escopo das permissões
        if database:
            scope = f"`{database}`.*"
            scope_desc = f"database '{database}'"
        else:
            scope = "*.*"
            scope_desc = "todas as databases (global)"

        print(f"\n📋 Concedendo permissões de '{user_type}' em {scope_desc}...")

        try:
            with self.engine.connect() as conn:
                # Para cada privilégio do tipo de usuário
                for privilege in privileges:
                    grant_sql = f"GRANT {privilege} ON {scope} TO '{username}'@'{host_pattern}'"

                    try:
                        conn.execute(text(grant_sql))
                        print(f"   ✓ {privilege}")
                    except SQLAlchemyError as e:
                        print(f"   ✗ {privilege}: {e}")
                        continue

                # Aplica as mudanças
                conn.execute(text("FLUSH PRIVILEGES"))
                conn.commit()

                print(
                    f"✅ Permissões concedidas com sucesso para '{username}'@'{host_pattern}'")
                return True

        except SQLAlchemyError as e:
            print(f"❌ Erro ao conceder privilégios: {e}")
            return False

    def get_all_databases(self) -> List[str]:
        """
        Obtém lista de todas as databases (exceto system databases).

        Returns:
            Lista com nomes das databases
        """
        query = text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN (
                'information_schema',
                'mysql',
                'performance_schema',
                'sys'
            )
            ORDER BY schema_name
        """)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                databases = [row[0] for row in result]
                return databases

        except SQLAlchemyError as e:
            print(f"❌ Erro ao listar databases: {e}")
            return []

    def show_user_grants(self, username: str, host_pattern: str = '%'):
        """
        Mostra os privilégios de um usuário.

        Args:
            username: Nome do usuário
            host_pattern: Padrão de host
        """
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

    def close(self):
        """Fecha a conexão."""
        if self.engine:
            self.engine.dispose()
            print("\n✅ Conexão encerrada")


def interactive_mode():
    """Modo interativo para coleta de informações."""
    print("="*70)
    print("GERENCIADOR DE USUÁRIOS MYSQL/MARIADB")
    print("="*70)
    print()

    # Informações do servidor
    print("📡 CONEXÃO COM O SERVIDOR")
    print("-" * 70)
    host = input("Host do servidor MySQL [localhost]: ").strip() or "localhost"
    port_str = input("Porta [3306]: ").strip() or "3306"
    try:
        port = int(port_str)
    except ValueError:
        print("❌ Porta inválida, usando 3306")
        port = 3306

    admin_user = input("Usuário administrativo [root]: ").strip() or "root"
    admin_password = getpass.getpass("Senha do usuário administrativo: ")

    if not admin_password:
        print("❌ Senha não pode ser vazia")
        return None

    print()

    # Informações do novo usuário
    print("👤 NOVO USUÁRIO")
    print("-" * 70)
    new_username = input("Nome do novo usuário: ").strip()
    if not new_username:
        print("❌ Nome de usuário não pode ser vazio")
        return None

    new_password = getpass.getpass("Senha do novo usuário: ")
    new_password_confirm = getpass.getpass("Confirme a senha: ")

    if new_password != new_password_confirm:
        print("❌ As senhas não coincidem")
        return None

    if not new_password:
        print("❌ Senha não pode ser vazia")
        return None

    host_pattern = input("Padrão de host [% (qualquer host)]: ").strip() or "%"

    print()

    # Tipo de usuário
    print("🔐 TIPO DE USUÁRIO E PERMISSÕES")
    print("-" * 70)
    print("Tipos disponíveis:")
    for user_type, info in MySQLUserManager.USER_TYPES.items():
        print(f"  • {user_type:12} - {info['description']}")
        print(f"    {', '.join(info['privileges'])}")
    print()

    user_type = input("Tipo de usuário [read]: ").strip().lower() or "read"
    if user_type not in MySQLUserManager.USER_TYPES:
        print(f"❌ Tipo inválido. Usando 'read'")
        user_type = "read"

    print()

    # Base de dados
    print("💾 BASE DE DADOS")
    print("-" * 70)
    database = input(
        "Nome da database (deixe vazio para global): ").strip() or None

    print()
    print("="*70)
    print()

    return {
        'host': host,
        'port': port,
        'admin_user': admin_user,
        'admin_password': admin_password,
        'new_username': new_username,
        'new_password': new_password,
        'host_pattern': host_pattern,
        'user_type': user_type,
        'database': database
    }


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Cria e configura usuários MySQL/MariaDB com permissões específicas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Modo interativo (recomendado)
  python scripts/setup_mysql_user_permissions.py

  # Modo não-interativo
  python scripts/setup_mysql_user_permissions.py \\
    --host localhost \\
    --admin-user root \\
    --admin-password senha_admin \\
    --username backup_user \\
    --password senha_backup \\
    --type backup

  # Usuário global (todas as databases)
  python scripts/setup_mysql_user_permissions.py \\
    --username global_user \\
    --type read

  # Usuário específico de uma database
  python scripts/setup_mysql_user_permissions.py \\
    --username app_user \\
    --type write \\
    --database myapp_db

Tipos de usuário:
  write      - Leitura e escrita (sem DDL)
  read       - Apenas leitura
  backup     - Otimizado para backups
  migration  - Permissões completas (incluindo DDL)
        """
    )

    parser.add_argument('--host', help='Host do servidor MySQL')
    parser.add_argument('--port', type=int, default=3306,
                        help='Porta do servidor (padrão: 3306)')
    parser.add_argument('--admin-user', help='Usuário administrativo')
    parser.add_argument('--admin-password',
                        help='Senha do usuário administrativo')
    parser.add_argument('--username', help='Nome do novo usuário')
    parser.add_argument('--password', help='Senha do novo usuário')
    parser.add_argument('--host-pattern', default='%',
                        help='Padrão de host (padrão: %%)')
    parser.add_argument('--type', choices=list(MySQLUserManager.USER_TYPES.keys()),
                        help='Tipo de usuário')
    parser.add_argument(
        '--database', help='Database específica (deixe vazio para global)')
    parser.add_argument('--show-grants', action='store_true',
                        help='Mostrar privilégios após criação')
    parser.add_argument('--list-databases', action='store_true',
                        help='Listar databases disponíveis')

    args = parser.parse_args()

    # Verifica se deve usar modo interativo
    use_interactive = not all([
        args.host, args.admin_user, args.admin_password,
        args.username, args.password, args.type
    ])

    if use_interactive:
        config = interactive_mode()
        if not config:
            sys.exit(1)
    else:
        config = {
            'host': args.host,
            'port': args.port,
            'admin_user': args.admin_user,
            'admin_password': args.admin_password,
            'new_username': args.username,
            'new_password': args.password,
            'host_pattern': args.host_pattern,
            'user_type': args.type,
            'database': args.database
        }

    # Cria gerenciador e conecta
    manager = MySQLUserManager(
        host=config['host'],
        port=config['port'],
        admin_user=config['admin_user'],
        admin_password=config['admin_password']
    )

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

    # Mostra grants se solicitado ou em modo interativo
    if args.show_grants or use_interactive:
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
  • Usuário: '{config['new_username']}'@'{config['host_pattern']}'
  • Tipo: {config['user_type']}
  • Escopo: {scope}
  • Servidor: {config['host']}:{config['port']}
    """)

    manager.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
