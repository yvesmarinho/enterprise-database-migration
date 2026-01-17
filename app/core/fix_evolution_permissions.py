"""
Módulo: fix_evolution_permissions.py
Propósito: Corrigir permissões no schema public para bancos evolution*
          após criação de tablespaces. Implementa lógica equivalente ao SQL
          com controles robustos de transação e tratamento de erros.

Autor: Database Migration System
Data: 2025-10-31
"""

import logging
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, exc, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

# =====================================================================
# Configuração de Logging
# =====================================================================

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# =====================================================================
# Modelos de Dados
# =====================================================================

class PermissionLevel(Enum):
    """Níveis de permissão a conceder"""
    CONNECT = "CONNECT"
    USAGE = "USAGE"
    CREATE = "CREATE"
    ALL = "ALL PRIVILEGES"


@dataclass
class DatabaseInfo:
    """Informações sobre um banco de dados"""
    datname: str
    owner: str
    tablespace: str
    connlimit: int

    def __repr__(self):
        return (f"DatabaseInfo(name={self.datname}, owner={self.owner}, "
                f"tablespace={self.tablespace}, connlimit={self.connlimit})")


@dataclass
class RoleInfo:
    """Informações sobre um role/usuário"""
    rolname: str
    is_superuser: bool
    can_login: bool

    def __repr__(self):
        return f"RoleInfo(name={self.rolname}, superuser={self.is_superuser})"


# =====================================================================
# Classe Principal: EvolutionPermissionsFixer
# =====================================================================

class EvolutionPermissionsFixer:
    """
    Corrige permissões em bancos de dados evolution* após criação de
    tablespaces.

    Funcionalidades:
    - Busca bancos que correspondem ao padrão 'evolution*'
    - Verifica e ajusta OWNER para postgres
    - Verifica e ajusta TABLESPACE para 'ts_enterprise_data'
    - Ajusta CONNECTION LIMIT para -1 (ilimitado)
    - Revoga ALL do PUBLIC no database
    - Concede CONNECT ao database para roles específicas
    - Corrige permissões no schema public e suas tabelas
    - Transações atômicas com rollback em caso de erro
    """

    # Constantes
    TARGET_TABLESPACE = "ts_enterprise_data"
    EXPECTED_OWNER = "postgres"
    DEFAULT_ROLES = [
        "analytics",
        "evolution_api_user",
        "evoluton_api_user"  # Nota: typo intencional conforme banco original
    ]

    def __init__(
        self,
        connection_string: str,
        dry_run: bool = False,
        stop_on_error: bool = False,
        timeout_seconds: int = 30
    ):
        """
        Inicializa o corretor de permissões.

        Args:
            connection_string: String de conexão PostgreSQL
            dry_run: Se True, apenas simula as operações sem executar
            stop_on_error: Se True, para no primeiro erro crítico
            timeout_seconds: Timeout para operações SQL (segundos)
        """
        self.connection_string = connection_string
        self.dry_run = dry_run
        self.stop_on_error = stop_on_error
        self.timeout_seconds = timeout_seconds
        self.engine = None
        self.session_factory = None
        self.results = {
            "databases_processed": [],
            "databases_skipped": [],
            "databases_failed": [],
            "permissions_fixed": 0,
            "errors": []
        }

    def _init_engine(self):
        """Inicializa a conexão do SQLAlchemy"""
        if self.engine is not None:
            return

        try:
            # Configurar engine com pool apropriado
            if self.dry_run:
                # NullPool para dry-run (sem caching)
                self.engine = create_engine(
                    self.connection_string,
                    poolclass=NullPool,
                    echo=False
                )
            else:
                # QueuePool para produção (com caching)
                self.engine = create_engine(
                    self.connection_string,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    echo=False
                )

            self.session_factory = sessionmaker(
                bind=self.engine,
                expire_on_commit=False
            )

            # Teste de conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info(
                "✓ Conexão com banco de dados estabelecida com sucesso"
            )

        except Exception as e:
            logger.error(f"✗ Erro ao inicializar engine: {e}")
            raise

    @contextmanager
    def _session_context(self):
        """Context manager para gerenciar sessões com transações"""
        session = None
        try:
            session = self.session_factory()
            yield session

            if not self.dry_run:
                session.commit()
                logger.debug("✓ Transação confirmada")
            else:
                session.rollback()
                logger.debug("⊘ Transação revertida (dry-run)")

        except Exception as e:
            if session:
                session.rollback()
                logger.error(f"✗ Transação revertida por erro: {e}")
            raise
        finally:
            if session:
                session.close()

    def _execute_sql(
        self,
        session: Session,
        sql: str,
        description: str = "",
        raise_on_error: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Executa SQL com tratamento robusto de erros.

        Args:
            session: Sessão SQLAlchemy
            sql: Comando SQL a executar
            description: Descrição da operação (para logging)
            raise_on_error: Se True, levanta exceção em caso de erro

        Returns:
            Tupla (sucesso, mensagem_erro)
        """
        try:
            if self.dry_run:
                logger.info(f"  ⊘ [DRY-RUN] {description}")
                logger.debug(f"     SQL: {sql}")
                return True, None

            logger.debug(f"  Executando: {description}")
            session.execute(text(sql))
            logger.info(f"  ✓ {description}")
            return True, None

        except exc.ProgrammingError as e:
            error_msg = f"Erro SQL: {str(e)}"
            logger.warning(f"  ⚠ {error_msg}")
            if raise_on_error and self.stop_on_error:
                raise
            return False, error_msg

        except Exception as e:
            error_msg = f"Erro inesperado: {str(e)}"
            logger.error(f"  ✗ {error_msg}")
            if raise_on_error:
                raise
            return False, error_msg

    def find_evolution_databases(self, session: Session) -> List[str]:
        """
        Localiza todos os bancos que começam com 'evolution'.

        Args:
            session: Sessão SQLAlchemy

        Returns:
            Lista de nomes de bancos
        """
        try:
            query = """
                SELECT datname
                FROM pg_database
                WHERE datname LIKE 'evolution%'
                AND datname NOT IN ('template0', 'template1')
                ORDER BY datname;
            """

            result = session.execute(text(query))
            databases = [row[0] for row in result.fetchall()]

            logger.info(
                f"✓ Encontrados {len(databases)} banco(s) evolution*: "
                f"{databases}"
            )
            return databases

        except Exception as e:
            logger.error(f"✗ Erro ao buscar bancos evolution*: {e}")
            raise

    def get_database_info(
        self,
        session: Session,
        database_name: str
    ) -> Optional[DatabaseInfo]:
        """
        Obtém informações do banco de dados.

        Args:
            session: Sessão SQLAlchemy
            database_name: Nome do banco

        Returns:
            Objeto DatabaseInfo ou None se banco não existe
        """
        try:
            query = """
                SELECT
                    d.datname,
                    pg_roles.rolname as owner,
                    COALESCE(ts.spcname, 'pg_default') as tablespace,
                    d.datconnlimit
                FROM pg_database d
                LEFT JOIN pg_roles ON pg_roles.oid = d.datdba
                LEFT JOIN pg_tablespace ts ON ts.oid = d.dattablespace
                WHERE d.datname = :db_name;
            """

            result = session.execute(
                text(query),
                {"db_name": database_name}
            )
            row = result.fetchone()

            if not row:
                logger.warning(f"  ⚠ Banco '{database_name}' não encontrado")
                return None

            return DatabaseInfo(
                datname=row[0],
                owner=row[1],
                tablespace=row[2],
                connlimit=row[3]
            )

        except Exception as e:
            logger.error(
                f"✗ Erro ao obter info do banco '{database_name}': {e}"
            )
            raise

    def role_exists(self, session: Session, role_name: str) -> bool:
        """Verifica se um role existe"""
        try:
            query = (
                "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE "
                "rolname = :role)"
            )
            result = session.execute(text(query), {"role": role_name})
            return bool(result.scalar())
        except Exception as e:
            logger.warning(f"  ⚠ Erro ao verificar role '{role_name}': {e}")
            return False

    def fix_database_owner(
        self,
        session: Session,
        database_name: str,
        current_owner: str
    ) -> bool:
        """Corrige o owner do banco"""
        if current_owner == self.EXPECTED_OWNER:
            logger.info(f"  ✓ Owner já é '{self.EXPECTED_OWNER}'; pulando")
            return True

        sql = (
            f"ALTER DATABASE \"{database_name}\" OWNER TO "
            f"{self.EXPECTED_OWNER};"
        )
        success, error = self._execute_sql(
            session,
            sql,
            f"Alterando owner de '{database_name}' para "
            f"'{self.EXPECTED_OWNER}'"
        )
        return success

    def fix_database_tablespace(
        self,
        session: Session,
        database_name: str,
        current_tablespace: str
    ) -> bool:
        """Corrige o tablespace do banco"""
        if current_tablespace == self.TARGET_TABLESPACE:
            logger.info(
                f"  ✓ Tablespace já é '{self.TARGET_TABLESPACE}'; "
                f"pulando"
            )
            return True

        # Desconectar outras conexões para permitir alteração
        self._disconnect_other_connections(session, database_name)

        sql = (
            f"ALTER DATABASE \"{database_name}\" "
            f"SET TABLESPACE {self.TARGET_TABLESPACE};"
        )
        success, error = self._execute_sql(
            session,
            sql,
            f"Alterando tablespace de '{database_name}' para "
            f"'{self.TARGET_TABLESPACE}'"
        )
        return success

    def fix_connection_limit(
        self,
        session: Session,
        database_name: str,
        current_limit: int
    ) -> bool:
        """Corrige o connection limit do banco"""
        if current_limit == -1:
            logger.info("  ✓ Connection limit já é -1; pulando")
            return True

        sql = f"ALTER DATABASE \"{database_name}\" CONNECTION LIMIT -1;"
        success, error = self._execute_sql(
            session,
            sql,
            f"Ajustando connection limit de '{database_name}' para -1"
        )
        return success

    def revoke_public_privileges(
        self,
        session: Session,
        database_name: str
    ) -> bool:
        """Revoga ALL do PUBLIC no database"""
        sql = f"REVOKE ALL ON DATABASE \"{database_name}\" FROM PUBLIC;"
        success, error = self._execute_sql(
            session,
            sql,
            f"Revogando ALL do PUBLIC em '{database_name}'",
            raise_on_error=False
        )
        return success

    def grant_database_connect(
        self,
        session: Session,
        database_name: str,
        role_name: str
    ) -> bool:
        """Concede CONNECT no database para um role"""
        if not self.role_exists(session, role_name):
            logger.info(f"  ⊘ Role '{role_name}' não existe; pulando")
            return True

        sql = (
            f"GRANT CONNECT ON DATABASE \"{database_name}\" "
            f"TO \"{role_name}\";"
        )
        success, error = self._execute_sql(
            session,
            sql,
            f"Concedendo CONNECT em '{database_name}' a '{role_name}'",
            raise_on_error=False
        )
        return success

    def _disconnect_other_connections(
        self,
        session: Session,
        database_name: str
    ):
        """
        Desconecta outras conexões do banco antes de alterações
        estruturais
        """
        try:
            if self.dry_run:
                logger.debug(
                    f"  ⊘ [DRY-RUN] Desconectando outras conexões de "
                    f"'{database_name}'"
                )
                return

            sql = """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = :db_name AND pid <> pg_backend_pid();
            """

            result = session.execute(text(sql), {"db_name": database_name})
            terminated = sum(1 for _ in result if result.scalar())

            if terminated > 0:
                logger.info(
                    f"  ✓ Desconectadas {terminated} conexão(ões) de "
                    f"'{database_name}'"
                )

        except Exception as e:
            logger.warning(f"  ⚠ Erro ao desconectar conexões: {e}")

    def fix_schema_public_permissions(
        self,
        database_name: str,
        roles: Optional[List[str]] = None
    ) -> bool:
        """
        Corrige permissões do schema public e suas tabelas.
        Requer conexão específica ao banco.

        Args:
            database_name: Nome do banco
            roles: Lista de roles para conceder permissões

        Returns:
            True se bem-sucedido
        """
        if roles is None:
            roles = self.DEFAULT_ROLES

        try:
            # Criar connection string para o banco específico
            base_conn = self.connection_string.rsplit('/', 1)[0]
            db_conn_string = f"{base_conn}/{database_name}"

            # Usar NullPool para evitar caching de conexões
            db_engine = create_engine(
                db_conn_string,
                poolclass=NullPool,
                echo=False
            )

            with db_engine.connect() as conn:
                logger.info(
                    f"  Corrigindo permissões do schema public em "
                    f"'{database_name}'"
                )

                for role in roles:
                    # Verificar se role existe
                    result = conn.execute(
                        text(
                            "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE "
                            "rolname = :role)"
                        ),
                        {"role": role}
                    )
                    role_exists = result.scalar()

                    if not role_exists:
                        logger.debug(
                            f"    ⊘ Role '{role}' não existe; pulando"
                        )
                        continue

                    if not self.dry_run:
                        # Conceder USAGE no schema public
                        conn.execute(
                            text(
                                f'GRANT USAGE ON SCHEMA public TO "{role}";'
                            )
                        )
                        logger.debug(
                            f"    ✓ USAGE em schema public concedido a "
                            f"'{role}'"
                        )

                        # Conceder SELECT nas tabelas existentes
                        conn.execute(
                            text(
                                f"GRANT SELECT ON ALL TABLES IN SCHEMA "
                                f"public TO \"{role}\";"
                            )
                        )
                        logger.debug(
                            f"    ✓ SELECT nas tabelas concedido a '{role}'"
                        )

                        # Definir permissões padrão para futuras tabelas
                        conn.execute(
                            text(
                                f"ALTER DEFAULT PRIVILEGES IN SCHEMA "
                                f"public GRANT SELECT ON TABLES TO "
                                f"\"{role}\";"
                            )
                        )
                        logger.debug(
                            f"    ✓ Permissões padrão definidas para "
                            f"'{role}'"
                        )
                    else:
                        logger.info(
                            f"    ⊘ [DRY-RUN] USAGE e SELECT seriam "
                            f"concedidos a '{role}'"
                        )

                if not self.dry_run:
                    conn.commit()

            logger.info(
                f"  ✓ Permissões do schema public corrigidas em "
                f"'{database_name}'"
            )
            return True

        except Exception as e:
            logger.error(
                f"  ✗ Erro ao corrigir permissões do schema public: {e}"
            )
            if self.stop_on_error:
                raise
            return False
        finally:
            if 'db_engine' in locals():
                db_engine.dispose()

    def process_evolution_databases(self) -> Dict:
        """
        Processa todos os bancos evolution* encontrados.

        Returns:
            Dicionário com resultados do processamento
        """
        self._init_engine()

        try:
            with self._session_context() as session:
                # Localizar bancos
                databases = self.find_evolution_databases(session)

                if not databases:
                    logger.warning("Nenhum banco evolution* encontrado")
                    return self.results

                # Processar cada banco
                for db_name in databases:
                    logger.info(f"\n{'='*70}")
                    logger.info(f"Processando banco: {db_name}")
                    logger.info(f"{'='*70}")

                    try:
                        # Obter informações do banco
                        db_info = self.get_database_info(session, db_name)
                        if not db_info:
                            self.results["databases_skipped"].append(db_name)
                            continue

                        logger.info(f"Info atual: {db_info}")

                        # Corrigir owner
                        self.fix_database_owner(
                            session, db_name, db_info.owner
                        )

                        # Corrigir tablespace
                        self.fix_database_tablespace(
                            session, db_name, db_info.tablespace
                        )

                        # Corrigir connection limit
                        self.fix_connection_limit(
                            session, db_name, db_info.connlimit
                        )

                        # Revogar PUBLIC
                        self.revoke_public_privileges(session, db_name)

                        # Conceder CONNECT aos roles
                        for role in self.DEFAULT_ROLES:
                            self.grant_database_connect(session, db_name, role)

                        self.results["databases_processed"].append(db_name)
                        self.results["permissions_fixed"] += 1

                    except Exception as e:
                        logger.error(f"✗ Erro ao processar '{db_name}': {e}")
                        self.results["databases_failed"].append(db_name)
                        self.results["errors"].append({
                            "database": db_name,
                            "error": str(e)
                        })

                        if self.stop_on_error:
                            raise
                        continue

                    # Processar schema public (conexão separada)
                    try:
                        self.fix_schema_public_permissions(db_name)
                    except Exception as e:
                        logger.error(
                            f"✗ Erro ao corrigir schema public de "
                            f"'{db_name}': {e}"
                        )
                        if self.stop_on_error:
                            raise

        except Exception as e:
            logger.error(f"✗ Erro geral no processamento: {e}")
            traceback.print_exc()
            if self.stop_on_error:
                raise

        finally:
            self._close()

        return self.results

    def _close(self):
        """Fecha conexões e libera recursos"""
        if self.engine:
            self.engine.dispose()
            logger.info("✓ Conexões fechadas")

    def print_results(self):
        """Exibe um relatório dos resultados"""
        logger.info(f"\n{'='*70}")
        logger.info("RELATÓRIO FINAL")
        logger.info(f"{'='*70}")
        logger.info(
            f"Bancos processados: "
            f"{len(self.results['databases_processed'])}"
        )
        for db in self.results['databases_processed']:
            logger.info(f"  ✓ {db}")

        logger.info(
            f"\nBancos pulados: {len(self.results['databases_skipped'])}"
        )
        for db in self.results['databases_skipped']:
            logger.info(f"  ⊘ {db}")

        logger.info(
            f"\nBancos com falha: "
            f"{len(self.results['databases_failed'])}"
        )
        for db in self.results['databases_failed']:
            logger.error(f"  ✗ {db}")

        if self.results['errors']:
            logger.info("Erros encontrados:")
            for error in self.results['errors']:
                logger.error(
                    f"  - {error['database']}: {error['error']}"
                )

        logger.info(
            f"\nPermissões ajustadas: "
            f"{self.results['permissions_fixed']}"
        )
        logger.info(f"{'='*70}\n")


# =====================================================================
# Função de Conveniência
# =====================================================================

def fix_evolution_database_permissions(
    connection_string: str,
    dry_run: bool = False,
    stop_on_error: bool = False
) -> Dict:
    """
    Função de conveniência para corrigir permissões em bancos evolution*.

    Args:
        connection_string: String de conexão PostgreSQL
        dry_run: Se True, apenas simula operações
        stop_on_error: Se True, para no primeiro erro crítico

    Returns:
        Dicionário com resultados
    """
    fixer = EvolutionPermissionsFixer(
        connection_string=connection_string,
        dry_run=dry_run,
        stop_on_error=stop_on_error
    )

    results = fixer.process_evolution_databases()
    fixer.print_results()

    return results


# =====================================================================
# Script de Execução
# =====================================================================

if __name__ == "__main__":
    import os
    import sys

    from dotenv import load_dotenv

    # Carregar variáveis de ambiente
    load_dotenv()

    # Obter string de conexão
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")

    connection_string = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # Argumentos de linha de comando
    dry_run = "--dry-run" in sys.argv or "--simulate" in sys.argv
    stop_on_error = "--stop-on-error" in sys.argv

    if dry_run:
        logger.info("⊘ Modo DRY-RUN ativado - nenhuma alteração será feita")

    # Executar corretor
    results = fix_evolution_database_permissions(
        connection_string=connection_string,
        dry_run=dry_run,
        stop_on_error=stop_on_error
    )

    # Retornar código de saída apropriado
    sys.exit(0 if not results['databases_failed'] else 1)
