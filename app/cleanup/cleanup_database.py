#!/usr/bin/env python3
"""
PostgreSQL Database and User Cleanup Utility
============================================

Script independente para apagar todos os bancos de dados e usuários
de um servidor PostgreSQL usando SQLAlchemy.

⚠️  ATENÇÃO: Este script é DESTRUTIVO!
    Use apenas em ambientes de desenvolvimento/teste.

Uso:
    python3 cleanup_database.py [--server origem|destino|ambos]
    python3 cleanup_database.py --dry-run  # Simular sem executar

Versão: 1.0.0
Data: 03/10/2025
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import logging

# SQLAlchemy imports
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

class PostgreSQLCleanup:
    """Classe para limpeza de bancos PostgreSQL."""

    def __init__(self, config: Dict, server_name: str = "servidor"):
        self.config = config
        self.server_name = server_name
        self.engine: Optional[Engine] = None

        # Bancos e usuários protegidos do arquivo de configuração
        cleanup_config = config.get('cleanup_protection', {})

        # Bancos que NÃO devem ser apagados (padrões + configurados)
        default_protected_dbs = {'postgres', 'template0', 'template1'}
        config_protected_dbs = set(cleanup_config.get('protected_databases', []))
        self.protected_databases = default_protected_dbs.union(config_protected_dbs)

        # Usuários que NÃO devem ser apagados (padrões + configurados)
        default_protected_users = {'postgres', 'rds_superuser', 'cloudsqlsuperuser', 'azure_superuser'}
        config_protected_users = set(cleanup_config.get('protected_users', []))
        self.protected_users = default_protected_users.union(config_protected_users)

        logger.info(f"🛡️ Bancos protegidos: {sorted(self.protected_databases)}")
        logger.info(f"🛡️ Usuários protegidos: {sorted(self.protected_users)}")

    def connect(self) -> bool:
        """Conecta ao servidor PostgreSQL."""
        try:
            # Construir URL de conexão usando nova estrutura JSON
            server_config = self.config['server']
            auth_config = self.config['authentication']

            connection_url = (
                f"postgresql://{auth_config['user']}:"
                f"{auth_config['password']}@"
                f"{server_config['host']}:{server_config['port']}/postgres"
                f"?sslmode={server_config['ssl_mode']}"
            )

            logger.info(f"🔌 Conectando ao {self.server_name} ({server_config['host']}:{server_config['port']})...")

            self.engine = create_engine(
                connection_url,
                isolation_level="AUTOCOMMIT",  # Necessário para DROP DATABASE
                echo=False
            )

            # Testar conexão
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"✅ Conectado: {version.split(',')[0]}")

            return True

        except Exception as e:
            logger.error(f"❌ Erro na conexão: {e}")
            return False

    def disconnect(self):
        """Desconecta do servidor."""
        if self.engine:
            self.engine.dispose()
            logger.info("🔌 Desconectado")

    def list_databases(self) -> List[str]:
        """Lista todos os bancos de dados."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT datname FROM pg_database WHERE datistemplate = FALSE"
                ))
                databases = [row[0] for row in result.fetchall()]

            logger.info(f"📋 Bancos encontrados: {len(databases)}")
            for db in databases:
                protected = "🛡️" if db in self.protected_databases else "🗑️"
                logger.info(f"   {protected} {db}")

            return databases

        except Exception as e:
            logger.error(f"❌ Erro ao listar bancos: {e}")
            return []

    def list_users(self) -> List[str]:
        """Lista todos os usuários."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT usename FROM pg_user ORDER BY usename"
                ))
                users = [row[0] for row in result.fetchall()]

            logger.info(f"👥 Usuários encontrados: {len(users)}")
            for user in users:
                protected = "🛡️" if user in self.protected_users else "🗑️"
                logger.info(f"   {protected} {user}")

            return users

        except Exception as e:
            logger.error(f"❌ Erro ao listar usuários: {e}")
            return []

    def terminate_connections(self, database: str) -> bool:
        """Termina todas as conexões ativas para um banco."""
        try:
            with self.engine.connect() as conn:
                # Terminar conexões ativas
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{database}'
                    AND pid <> pg_backend_pid()
                """))

            logger.info(f"🔌 Conexões terminadas para banco '{database}'")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao terminar conexões de '{database}': {e}")
            return False

    def drop_database(self, database: str, dry_run: bool = False) -> bool:
        """Apaga um banco de dados."""
        if database in self.protected_databases:
            logger.warning(f"🛡️ Banco protegido ignorado: {database}")
            return True

        if dry_run:
            logger.info(f"🔍 [DRY-RUN] Apagaria banco: {database}")
            return True

        try:
            # Terminar conexões primeiro
            self.terminate_connections(database)

            # Apagar banco
            with self.engine.connect() as conn:
                conn.execute(text(f'DROP DATABASE IF EXISTS "{database}"'))

            logger.success(f"🗑️ Banco apagado: {database}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao apagar banco '{database}': {e}")
            return False

    def check_user_dependencies(self, username: str) -> Dict:
        """Verifica dependências de um usuário antes de excluir."""
        dependencies = {
            'has_dependencies': False,
            'owned_databases': [],
            'owned_schemas': [],
            'owned_tables': [],
            'granted_permissions': []
        }

        try:
            with self.engine.connect() as conn:
                # Verificar bancos de propriedade do usuário (usando catálogo direto)
                result = conn.execute(text(f"""
                    SELECT datname
                    FROM pg_database d
                    JOIN pg_authid a ON d.datdba = a.oid
                    WHERE a.rolname = '{username}'
                    AND datname NOT IN ('template0', 'template1')
                """))
                dependencies['owned_databases'] = [row[0] for row in result]

                # Verificar schemas de propriedade do usuário (usando catálogo direto)
                result = conn.execute(text(f"""
                    SELECT nspname
                    FROM pg_namespace n
                    JOIN pg_authid a ON n.nspowner = a.oid
                    WHERE a.rolname = '{username}'
                    AND nspname NOT LIKE 'pg_%'
                    AND nspname NOT IN ('information_schema')
                """))
                dependencies['owned_schemas'] = [row[0] for row in result]

                # Verificar tabelas de propriedade do usuário (usando catálogo direto)
                result = conn.execute(text(f"""
                    SELECT n.nspname, c.relname
                    FROM pg_class c
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    JOIN pg_authid a ON c.relowner = a.oid
                    WHERE a.rolname = '{username}'
                    AND c.relkind IN ('r', 't')  -- tabelas regulares e temporárias
                    AND n.nspname NOT LIKE 'pg_%'
                    AND n.nspname NOT IN ('information_schema')
                    LIMIT 10
                """))
                dependencies['owned_tables'] = [f"{row[0]}.{row[1]}" for row in result]

                # Verificar se há dependências
                dependencies['has_dependencies'] = (
                    len(dependencies['owned_databases']) > 0 or
                    len(dependencies['owned_schemas']) > 0 or
                    len(dependencies['owned_tables']) > 0
                )

        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar dependências de '{username}': {e}")
            dependencies['has_dependencies'] = True  # Assume dependências por segurança

        return dependencies

    def drop_user(self, username: str, dry_run: bool = False) -> bool:
        """Apaga um usuário (função legada - use cleanup_all_users para lógica completa)."""
        if username in self.protected_users:
            logger.warning(f"🛡️ Usuário protegido ignorado: {username}")
            return True

        if dry_run:
            logger.info(f"🔍 [DRY-RUN] Apagaria usuário: {username}")
            return True

        try:
            with self.engine.connect() as conn:
                # Terminar sessões ativas do usuário
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE usename = '{username}'
                """))

                # Apagar usuário
                conn.execute(text(f'DROP USER IF EXISTS "{username}"'))

            logger.info(f"🗑️ Usuário apagado: {username}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao apagar usuário '{username}': {e}")
            return False

    def cleanup_all_databases(self, dry_run: bool = False) -> Dict:
        """Apaga todos os bancos não protegidos."""
        logger.info("🗑️ Iniciando limpeza de bancos de dados...")

        databases = self.list_databases()
        target_databases = [db for db in databases if db not in self.protected_databases]

        if not target_databases:
            logger.info("✨ Nenhum banco para apagar")
            return {'success': True, 'deleted': 0, 'protected': len(self.protected_databases)}

        logger.warning(f"⚠️ Será apagado {len(target_databases)} banco(s): {target_databases}")

        deleted_count = 0
        for database in target_databases:
            if self.drop_database(database, dry_run):
                deleted_count += 1

        result = {
            'success': deleted_count == len(target_databases),
            'deleted': deleted_count,
            'total_found': len(databases),
            'protected': len([db for db in databases if db in self.protected_databases])
        }

        logger.info(f"📊 Bancos apagados: {deleted_count}/{len(target_databases)}")
        return result

    def cleanup_all_users(self, dry_run: bool = False) -> Dict:
        """Apaga todos os usuários não protegidos."""
        logger.info("🗑️ Iniciando limpeza de usuários...")

        users = self.list_users()
        target_users = [user for user in users if user not in self.protected_users]

        if not target_users:
            logger.info("✨ Nenhum usuário para apagar")
            return {'success': True, 'deleted': 0, 'skipped': 0, 'protected': len(self.protected_users)}

        logger.warning(f"⚠️ Processando {len(target_users)} usuário(s): {target_users}")

        deleted_count = 0
        skipped_count = 0
        failed_count = 0

        for user in target_users:
            # Verificar dependências primeiro (mesmo em dry-run para informar)
            dependencies = self.check_user_dependencies(user)

            if dependencies['has_dependencies'] and not dry_run:
                logger.warning(f"⚠️ Usuário '{user}' PULADO - possui dependências")
                if dependencies['owned_databases']:
                    logger.warning(f"   📁 Bancos proprietários: {dependencies['owned_databases']}")
                if dependencies['owned_schemas']:
                    logger.warning(f"   📂 Schemas proprietários: {dependencies['owned_schemas']}")
                if dependencies['owned_tables']:
                    tables_preview = dependencies['owned_tables'][:3]
                    more = "..." if len(dependencies['owned_tables']) > 3 else ""
                    logger.warning(f"   📋 Tabelas proprietárias: {tables_preview}{more}")
                skipped_count += 1
                continue

            if dry_run:
                if dependencies['has_dependencies']:
                    logger.info(f"🔍 [DRY-RUN] Usuário '{user}' seria PULADO (possui dependências)")
                    skipped_count += 1
                else:
                    logger.info(f"🔍 [DRY-RUN] Apagaria usuário: {user}")
                    deleted_count += 1
                continue

            # Tentar apagar usuário (apenas se não tem dependências)
            try:
                with self.engine.connect() as conn:
                    # Terminar sessões ativas
                    conn.execute(text(f"""
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE usename = '{user}'
                    """))

                    # Apagar usuário
                    conn.execute(text(f'DROP USER IF EXISTS "{user}"'))

                logger.info(f"🗑️ Usuário apagado: {user}")
                deleted_count += 1

            except Exception as e:
                logger.error(f"❌ Erro ao apagar usuário '{user}': {e}")
                failed_count += 1

        result = {
            'success': failed_count == 0,
            'deleted': deleted_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'total_found': len(users),
            'protected': len([user for user in users if user in self.protected_users])
        }

        logger.info(f"📊 Usuários - Apagados: {deleted_count}, Pulados: {skipped_count}, Falharam: {failed_count}")
        return result

    def full_cleanup(self, dry_run: bool = False) -> Dict:
        """Executa limpeza completa: bancos + usuários."""
        logger.info("🧹 Iniciando limpeza completa...")

        # Apagar bancos primeiro (usuários podem ser donos de bancos)
        db_result = self.cleanup_all_databases(dry_run)
        user_result = self.cleanup_all_users(dry_run)

        return {
            'databases': db_result,
            'users': user_result,
            'overall_success': db_result['success'] and user_result['success']
        }

# Adicionar método success ao logger
def log_success(msg):
    logger.info(f"✅ {msg}")

# Anexar método success ao logger de forma compatível
if not hasattr(logger, 'success'):
    setattr(logger, 'success', log_success)

def load_server_config(server_name: str) -> Optional[Dict]:
    """Carrega configuração de servidor."""
    config_map = {
        'origem': 'postgresql_source_config.json',
        'destino': 'postgresql_destination_config.json'
    }

    if server_name not in config_map:
        logger.error(f"❌ Servidor inválido: {server_name}")
        return None

    config_file = Path("/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration/secrets") / config_map[server_name]

    if not config_file.exists():
        logger.error(f"❌ Arquivo de configuração não encontrado: {config_file}")
        return None

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"📋 Configuração carregada: {server_name}")
        return config
    except Exception as e:
        logger.error(f"❌ Erro ao carregar configuração: {e}")
        return None

def confirm_action(servers_info: List[Dict], dry_run: bool) -> bool:
    """Confirma ação destrutiva com DUPLA confirmação obrigatória."""
    if dry_run:
        return True

    print("\n" + "="*70)
    print("⚠️  ATENÇÃO: OPERAÇÃO DESTRUTIVA!")
    print("="*70)

    # Mostrar informações detalhadas de cada servidor
    print("🎯 Servidor(es) alvo:")
    for server_info in servers_info:
        server_name = server_info['name']
        host = server_info['host']
        port = server_info['port']
        print(f"   • {server_name.upper()}: {host}:{port}")

    print("\n🗑️ Esta operação irá APAGAR:")
    print("   • Todos os bancos de dados (exceto protegidos)")
    print("   • Todos os usuários (exceto protegidos)")
    print("\n🛡️ Bancos protegidos: postgres, template0, template1")
    print("🛡️ Usuários protegidos: postgres, *superuser*")
    print("="*70)

    # PRIMEIRA confirmação (obrigatória para todos)
    response1 = input("\n❓ [1/2] Tem CERTEZA que deseja continuar? Digite 'CONFIRMO': ")
    if response1.strip() != "CONFIRMO":
        print("❌ Primeira confirmação falhou. Operação cancelada.")
        return False

    # SEGUNDA confirmação (obrigatória para todos)
    print("\n" + "🔴"*30)
    print("🚨 CONFIRMAÇÃO FINAL OBRIGATÓRIA!")
    print("🚨 Esta operação é IRREVERSÍVEL!")
    print("🚨 Dados serão PERMANENTEMENTE perdidos!")

    # Mostrar novamente os hosts que serão afetados
    print("\n🎯 HOSTS QUE SERÃO AFETADOS:")
    for server_info in servers_info:
        print(f"   🔴 {server_info['host']}:{server_info['port']} ({server_info['name']})")

    print("🔴"*30)

    # Determinar tipo de confirmação baseado nos servidores
    server_names = [info['name'] for info in servers_info]

    if 'origem' in server_names:
        if len(server_names) == 1:
            # Apenas origem
            response2 = input("\n🔴 [2/2] CONFIRMAÇÃO FINAL - Digite 'ORIGEM-CONFIRMO': ")
            expected_response = "ORIGEM-CONFIRMO"
        else:
            # Origem + outros servidores
            response2 = input("\n🔴 [2/2] CONFIRMAÇÃO FINAL - Digite 'AMBOS-CONFIRMO': ")
            expected_response = "AMBOS-CONFIRMO"
    else:
        # Apenas destino ou outros
        response2 = input("\n🔴 [2/2] CONFIRMAÇÃO FINAL - Digite 'FINAL-CONFIRMO': ")
        expected_response = "FINAL-CONFIRMO"

    if response2.strip() != expected_response:
        print("❌ Segunda confirmação falhou. Operação cancelada por segurança.")
        return False

    print("✅ Confirmação DUPLA realizada com sucesso. Prosseguindo...")
    return True

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Database and User Cleanup Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s --server origem                    # Limpar servidor origem
  %(prog)s --server destino                  # Limpar servidor destino
  %(prog)s --server ambos                    # Limpar ambos servidores
  %(prog)s --server origem --dry-run         # Simular limpeza
  %(prog)s --server origem --databases-only  # Só bancos
  %(prog)s --server origem --users-only      # Só usuários
        """
    )

    parser.add_argument('--server', choices=['origem', 'destino', 'ambos'],
                       default='origem', help='Servidor(es) para limpar')
    parser.add_argument('--dry-run', action='store_true',
                       help='Simular sem executar (modo seguro)')
    parser.add_argument('--databases-only', action='store_true',
                       help='Apagar apenas bancos de dados')
    parser.add_argument('--users-only', action='store_true',
                       help='Apagar apenas usuários')
    parser.add_argument('--force', action='store_true',
                       help='Pular confirmação (cuidado!)')

    args = parser.parse_args()

    print("🧹 PostgreSQL Database & User Cleanup Utility")
    print("="*50)

    if args.dry_run:
        print("🔍 MODO SIMULAÇÃO - Nenhuma alteração será feita")
        print("-"*50)

    # Determinar servidores alvo
    servers_to_clean = []
    if args.server == 'ambos':
        servers_to_clean = ['origem', 'destino']
    else:
        servers_to_clean = [args.server]

    # Carregar informações dos servidores para confirmação
    servers_info = []
    for server_name in servers_to_clean:
        config = load_server_config(server_name)
        if config:
            servers_info.append({
                'name': server_name,
                'host': config['server']['host'],
                'port': config['server']['port']
            })

    # Confirmar ação
    if not args.force and not confirm_action(servers_info, args.dry_run):
        print("❌ Operação cancelada pelo usuário")
        return 1

    overall_success = True

    # Executar limpeza em cada servidor
    for server_name in servers_to_clean:
        print(f"\n🎯 Processando servidor: {server_name}")
        print("-"*30)

        # Carregar configuração
        config = load_server_config(server_name)
        if not config:
            overall_success = False
            continue

        # Criar instância de limpeza
        cleanup = PostgreSQLCleanup(config, server_name)

        # Conectar
        if not cleanup.connect():
            overall_success = False
            continue

        try:
            # Executar limpeza baseada nas opções
            if args.databases_only:
                result = cleanup.cleanup_all_databases(args.dry_run)
                success = result['success']
            elif args.users_only:
                result = cleanup.cleanup_all_users(args.dry_run)
                success = result['success']
            else:
                result = cleanup.full_cleanup(args.dry_run)
                success = result['overall_success']

            if not success:
                overall_success = False

        except KeyboardInterrupt:
            print("\n⚠️ Operação interrompida pelo usuário")
            overall_success = False
            break
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            overall_success = False
        finally:
            cleanup.disconnect()

    # Resultado final
    print("\n" + "="*50)
    if overall_success:
        print("🎉 Limpeza concluída com sucesso!")
        if args.dry_run:
            print("🔍 Modo simulação - nenhuma alteração foi feita")
    else:
        print("⚠️ Limpeza concluída com erros")
        print("📋 Verifique os logs acima para detalhes")
    print("="*50)

    return 0 if overall_success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️ Operação cancelada pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
