#!/usr/bin/env python3
"""
Script para configurar permissões do usuário 'backup' em todas as bases de dados PostgreSQL.

Este script:
1. Coleta todos os nomes de bases de dados
2. Verifica se o usuário 'backup' tem as permissões necessárias
3. Adiciona permissões faltantes sem alterar as demais
4. Considera que cada base de dados tem sua própria tablespace

Autor: Sistema de Migração Enterprise
Data: 22/12/2025
Python: 3.11+
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError


@dataclass
class BackupPermissions:
    """Permissões necessárias para o usuário backup."""
    database_connect: bool = False
    schema_usage: Set[str] = None
    table_select: Set[str] = None
    sequence_select: Set[str] = None

    def __post_init__(self):
        if self.schema_usage is None:
            self.schema_usage = set()
        if self.table_select is None:
            self.table_select = set()
        if self.sequence_select is None:
            self.sequence_select = set()


class BackupUserPermissionManager:
    """Gerenciador de permissões do usuário backup."""

    BACKUP_USER = "backup"

    def __init__(self, config_path: str):
        """
        Inicializa o gerenciador.

        Args:
            config_path: Caminho para o arquivo de configuração JSON
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.admin_engine: Optional[Engine] = None

    def _load_config(self) -> Dict:
        """Carrega configuração do arquivo JSON."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Arquivo de configuração não encontrado: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao decodificar JSON: {e}")
            sys.exit(1)

    def _create_connection_string(self, database: str = "postgres") -> str:
        """
        Cria string de conexão SQLAlchemy.

        Args:
            database: Nome da base de dados

        Returns:
            String de conexão PostgreSQL
        """
        auth = self.config["authentication"]
        server = self.config["server"]

        return (
            f"postgresql://{auth['user']}:{auth['password']}"
            f"@{server['host']}:{server['port']}/{database}"
        )

    def connect_admin(self) -> Engine:
        """
        Conecta ao servidor PostgreSQL com usuário administrativo.

        Returns:
            Engine do SQLAlchemy
        """
        try:
            conn_str = self._create_connection_string("postgres")
            self.admin_engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                connect_args={
                    "connect_timeout": self.config["connection_settings"]["connection_timeout"]
                }
            )

            # Testa conexão
            with self.admin_engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Conectado ao PostgreSQL: {version[:50]}...")

            return self.admin_engine

        except SQLAlchemyError as e:
            print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
            sys.exit(1)

    def get_all_databases(self) -> List[str]:
        """
        Obtém lista de todas as bases de dados (exceto templates e postgres).

        Returns:
            Lista com nomes das bases de dados
        """
        query = text("""
            SELECT datname
            FROM pg_database
            WHERE datistemplate = false
              AND datname NOT IN ('postgres', 'template0', 'template1')
            ORDER BY datname
        """)

        try:
            with self.admin_engine.connect() as conn:
                result = conn.execute(query)
                databases = [row[0] for row in result]
                print(f"📊 Encontradas {len(databases)} bases de dados")
                return databases

        except SQLAlchemyError as e:
            print(f"❌ Erro ao listar bases de dados: {e}")
            return []

    def check_user_exists(self) -> bool:
        """
        Verifica se o usuário backup existe.

        Returns:
            True se o usuário existe, False caso contrário
        """
        query = text("""
            SELECT 1 FROM pg_roles WHERE rolname = :username
        """)

        try:
            with self.admin_engine.connect() as conn:
                result = conn.execute(query, {"username": self.BACKUP_USER})
                exists = result.scalar() is not None

                if exists:
                    print(f"✅ Usuário '{self.BACKUP_USER}' existe")
                else:
                    print(f"⚠️  Usuário '{self.BACKUP_USER}' não existe")

                return exists

        except SQLAlchemyError as e:
            print(f"❌ Erro ao verificar usuário: {e}")
            return False

    def create_backup_user(self) -> bool:
        """
        Cria o usuário backup se não existir.

        Returns:
            True se criado com sucesso ou já existe
        """
        if self.check_user_exists():
            return True

        query = text(f"""
            CREATE ROLE {self.BACKUP_USER} WITH
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION
            CONNECTION LIMIT -1
        """)

        try:
            with self.admin_engine.connect() as conn:
                conn.execute(query)
                conn.commit()
                print(f"✅ Usuário '{self.BACKUP_USER}' criado com sucesso")
                return True

        except SQLAlchemyError as e:
            print(f"❌ Erro ao criar usuário: {e}")
            return False

    def get_current_permissions(self, database: str) -> BackupPermissions:
        """
        Obtém permissões atuais do usuário backup em uma base de dados.

        Args:
            database: Nome da base de dados

        Returns:
            Objeto BackupPermissions com permissões atuais
        """
        perms = BackupPermissions()

        try:
            # Conecta à base de dados específica
            engine = create_engine(self._create_connection_string(database))

            with engine.connect() as conn:
                # Verifica permissão CONNECT
                query_connect = text("""
                    SELECT has_database_privilege(:username, :dbname, 'CONNECT')
                """)
                result = conn.execute(query_connect, {
                    "username": self.BACKUP_USER,
                    "dbname": database
                })
                perms.database_connect = result.scalar()

                # Verifica permissões USAGE em schemas
                query_schemas = text("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                      AND has_schema_privilege(:username, schema_name, 'USAGE')
                """)
                result = conn.execute(query_schemas, {"username": self.BACKUP_USER})
                perms.schema_usage = {row[0] for row in result}

            engine.dispose()

        except Exception as e:
            print(f"⚠️  Erro ao verificar permissões em '{database}': {e}")

        return perms

    def grant_database_permissions(self, database: str) -> bool:
        """
        Concede permissões necessárias ao usuário backup em uma base de dados.

        Args:
            database: Nome da base de dados

        Returns:
            True se bem-sucedido
        """
        try:
            engine = create_engine(self._create_connection_string(database))

            with engine.connect() as conn:
                # Inicia transação
                trans = conn.begin()

                try:
                    # GRANT CONNECT na database
                    conn.execute(text(f"""
                        GRANT CONNECT ON DATABASE {database} TO {self.BACKUP_USER}
                    """))

                    # GRANT USAGE em todos os schemas (exceto pg_catalog e information_schema)
                    query_schemas = text("""
                        SELECT schema_name
                        FROM information_schema.schemata
                        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                    """)
                    result = conn.execute(query_schemas)
                    schemas = [row[0] for row in result]

                    for schema in schemas:
                        # USAGE no schema
                        conn.execute(text(f"""
                            GRANT USAGE ON SCHEMA {schema} TO {self.BACKUP_USER}
                        """))

                        # SELECT em todas as tabelas do schema
                        conn.execute(text(f"""
                            GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {self.BACKUP_USER}
                        """))

                        # SELECT em todas as sequences do schema
                        conn.execute(text(f"""
                            GRANT SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {self.BACKUP_USER}
                        """))

                        # Garante permissões para objetos futuros
                        conn.execute(text(f"""
                            ALTER DEFAULT PRIVILEGES IN SCHEMA {schema}
                            GRANT SELECT ON TABLES TO {self.BACKUP_USER}
                        """))

                        conn.execute(text(f"""
                            ALTER DEFAULT PRIVILEGES IN SCHEMA {schema}
                            GRANT SELECT ON SEQUENCES TO {self.BACKUP_USER}
                        """))

                    trans.commit()
                    print(f"✅ Permissões concedidas em '{database}' ({len(schemas)} schemas)")
                    return True

                except Exception as e:
                    trans.rollback()
                    print(f"❌ Erro ao conceder permissões em '{database}': {e}")
                    return False

            engine.dispose()

        except Exception as e:
            print(f"❌ Erro ao processar '{database}': {e}")
            return False

    def process_all_databases(self) -> Dict[str, bool]:
        """
        Processa todas as bases de dados, verificando e corrigindo permissões.

        Returns:
            Dicionário com resultado por base de dados
        """
        results = {}
        databases = self.get_all_databases()

        print("\n" + "="*70)
        print("PROCESSAMENTO DE PERMISSÕES DO USUÁRIO BACKUP")
        print("="*70 + "\n")

        for i, database in enumerate(databases, 1):
            print(f"\n[{i}/{len(databases)}] Processando: {database}")
            print("-" * 70)

            # Verifica permissões atuais
            current_perms = self.get_current_permissions(database)

            needs_update = False
            if not current_perms.database_connect:
                print(f"⚠️  Falta permissão CONNECT")
                needs_update = True
            else:
                print(f"✅ Tem permissão CONNECT")

            if current_perms.schema_usage:
                print(f"✅ Tem USAGE em {len(current_perms.schema_usage)} schemas")
            else:
                print(f"⚠️  Sem permissões USAGE em schemas")
                needs_update = True

            # Aplica permissões se necessário
            if needs_update:
                print(f"🔧 Aplicando permissões...")
                success = self.grant_database_permissions(database)
                results[database] = success
            else:
                print(f"✅ Permissões já estão corretas")
                results[database] = True

        return results

    def print_summary(self, results: Dict[str, bool]):
        """
        Imprime resumo dos resultados.

        Args:
            results: Dicionário com resultados por database
        """
        print("\n" + "="*70)
        print("RESUMO DO PROCESSAMENTO")
        print("="*70)

        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        print(f"\n✅ Sucesso: {success_count}/{total_count}")

        if success_count < total_count:
            print(f"\n❌ Falhas:")
            for db, success in results.items():
                if not success:
                    print(f"   - {db}")

        print("\n" + "="*70 + "\n")

    def run(self):
        """Executa o processo completo."""
        print("="*70)
        print("CONFIGURAÇÃO DE PERMISSÕES DO USUÁRIO BACKUP")
        print("="*70)
        print(f"Servidor: {self.config['server']['host']}")
        print(f"Usuário: {self.BACKUP_USER}")
        print("="*70 + "\n")

        # Conecta ao servidor
        self.connect_admin()

        # Cria usuário backup se não existir
        if not self.create_backup_user():
            print("❌ Não foi possível criar/verificar usuário backup")
            sys.exit(1)

        # Processa todas as bases de dados
        results = self.process_all_databases()

        # Imprime resumo
        self.print_summary(results)

        # Fecha conexão admin
        if self.admin_engine:
            self.admin_engine.dispose()

        # Retorna código de saída apropriado
        if all(results.values()):
            print("✅ Processo concluído com sucesso!")
            sys.exit(0)
        else:
            print("⚠️  Processo concluído com algumas falhas")
            sys.exit(1)


def main():
    """Função principal."""
    # Caminho para o arquivo de configuração
    config_path = Path(__file__).parent.parent / "secrets" / "postgresql_destination_config.json"

    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        sys.exit(1)

    # Cria e executa o gerenciador
    manager = BackupUserPermissionManager(str(config_path))
    manager.run()


if __name__ == "__main__":
    main()
