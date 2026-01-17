#!/usr/bin/env python3
"""
Script executável: run_fix_evolution_permissions.py
Propósito: Executar correção de permissões em bancos evolution*
Uso:
  python3 run_fix_evolution_permissions.py --help
  python3 run_fix_evolution_permissions.py --server wf004 --dry-run
  python3 run_fix_evolution_permissions.py --server wfdb02 --execute
  python3 run_fix_evolution_permissions.py --server wf004 --execute --verbose
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.core.fix_evolution_permissions import EvolutionPermissionsFixer

# Adicionar diretório raiz ao path para importar modules
sys.path.insert(0, str(Path(__file__).parent.parent))


# Configurar logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Configura sistema de logging"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format=(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ),
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_server_config(server_name: str) -> dict:
    """
    Carrega configurações de conexão do arquivo JSON
    baseado no nome do servidor.

    Args:
        server_name: Nome do servidor (wf004 ou wfdb02)

    Returns:
        Dicionário com configurações
    """
    # Mapa de nomes para arquivos de configuração
    config_files = {
        'wf004': 'secrets/postgresql_source_config.json',
        'source': 'secrets/postgresql_source_config.json',
        'wfdb02': 'secrets/postgresql_destination_config.json',
        'destination': 'secrets/postgresql_destination_config.json',
        'dest': 'secrets/postgresql_destination_config.json',
    }

    config_file = config_files.get(server_name.lower())
    if not config_file:
        logger.error(
            "Servidor desconhecido: %s",
            server_name
        )
        logger.error(
            "Servidores disponíveis: %s",
            ', '.join(config_files.keys())
        )
        sys.exit(1)

    config_path = Path(config_file)
    if not config_path.exists():
        logger.error(
            "Arquivo de configuração não encontrado: %s",
            config_file
        )
        sys.exit(1)

    try:
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)
        logger.info(
            "Configuração carregada de: %s",
            config_file
        )
        return config
    except json.JSONDecodeError as e:
        logger.error("Erro ao ler JSON: %s", e)
        sys.exit(1)
    except IOError as e:
        logger.error("Erro ao carregar configuração: %s", e)
        sys.exit(1)


def build_connection_string(
    user: str,
    password: str,
    host: str,
    port: int,
    database: str
) -> str:
    """Constrói string de conexão PostgreSQL"""
    return (
        f"postgresql://{user}:{password}@{host}:{port}/{database}"
    )


def main():
    """Função principal"""
    # Parser de argumentos
    parser = argparse.ArgumentParser(
        description=(
            "Corretor de permissões para bancos evolution* "
            "após criação de tablespaces"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Testar (dry-run) com variáveis de ambiente
  python3 run_fix_evolution_permissions.py --dry-run

  # Executar de verdade
  python3 run_fix_evolution_permissions.py --execute

  # Com credenciais específicas
  python3 run_fix_evolution_permissions.py --execute \\
    --host wf004.vya.digital \\
    --user postgres \\
    --password sua_senha \\
    --port 5432

  # Verbose (debug)
  python3 run_fix_evolution_permissions.py --execute --verbose
        """
    )

    # Argumentos de modo
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula operações sem executar (padrão seguro)'
    )
    mode_group.add_argument(
        '--execute',
        action='store_true',
        help='Executa as operações de verdade'
    )

    # Argumentos de modo NOVO: usar --server ao invés de credenciais
    parser.add_argument(
        '--server',
        default=None,
        help=(
            'Nome do servidor (wf004, source, wfdb02, destination, dest) '
            '- carrega credenciais do arquivo de config'
        )
    )

    # Argumentos de conexão (legacy - usar com --server ou manual)
    parser.add_argument(
        '--host',
        default=None,
        help='Host do PostgreSQL (usar com --server ou com todos args)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Porta do PostgreSQL (padrão: 5432 com --server)'
    )
    parser.add_argument(
        '--user',
        default=None,
        help='Usuário PostgreSQL (usar com --server ou com todos args)'
    )
    parser.add_argument(
        '--password',
        default=None,
        help='Senha PostgreSQL (usar com --server ou com todos args)'
    )
    parser.add_argument(
        '--database',
        default=None,
        help='Database (padrão: "postgres")'
    )

    # Argumentos de comportamento
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Para no primeiro erro crítico'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Timeout para operações SQL em segundos (padrão: 30)'
    )

    # Argumentos de logging
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Ativa logging em nível DEBUG'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Apenas erros e avisos'
    )

    # Parser
    args = parser.parse_args()

    # Configurar logging
    if args.quiet:
        logging.basicConfig(level=logging.WARNING)
    else:
        setup_logging(verbose=args.verbose)

    logger.info("="*70)
    logger.info("EvolutionPermissionsFixer - Corretor de Permissões")
    logger.info("="*70)

    # Carregar variáveis de ambiente
    load_dotenv()

    # Obter credenciais: preferir --server, depois variáveis de env
    if args.server:
        logger.info("Carregando configuração para servidor: %s", args.server)
        config = load_server_config(args.server)
        host = config['server']['host']
        port = args.port or config['server'].get('port', 5432)
        user = config['authentication']['user']
        password = config['authentication']['password']
        database = args.database or 'postgres'
    else:
        # Legacy: usar argumentos ou variáveis de ambiente
        host = (
            args.host or
            os.getenv("POSTGRES_HOST", "localhost")
        )
        port = (
            args.port or
            int(os.getenv("POSTGRES_PORT", "5432"))
        )
        user = args.user or os.getenv("POSTGRES_USER", "postgres")
        password = args.password or os.getenv("POSTGRES_PASSWORD", "")
        database = args.database or os.getenv("POSTGRES_DB", "postgres")

    # Construir connection string
    connection_string = build_connection_string(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )

    logger.info("Conectando a: %s:%d/%s", host, port, database)
    logger.info("Usuário: %s", user)

    # Modo
    dry_run = args.dry_run
    if dry_run:
        logger.warning(
            "MODO DRY-RUN: Nenhuma alteração será feita"
        )
    else:
        logger.warning(
            "MODO EXECUÇÃO: Alterações serão feitas no banco!"
        )

    logger.info("")

    try:
        # Criar instância
        fixer = EvolutionPermissionsFixer(
            connection_string=connection_string,
            dry_run=dry_run,
            stop_on_error=args.stop_on_error,
            timeout_seconds=args.timeout
        )

        # Processar
        results = fixer.process_evolution_databases()

        # Relatório
        fixer.print_results()

        # Análise de resultados
        if results['databases_failed']:
            logger.error(
                "%d banco(s) falharam!",
                len(results['databases_failed'])
            )
            if results['errors']:
                logger.error("Detalhes dos erros:")
                for error in results['errors']:
                    logger.error(
                        "• %s: %s",
                        error['database'],
                        error['error']
                    )
            return 1
        else:
            logger.info(
                "Sucesso! Todos os bancos foram processados!"
            )
            return 0

    except KeyboardInterrupt:
        logger.warning("Operação cancelada pelo usuário")
        return 130
    except Exception as e:
        logger.error("Erro crítico: %s", e)
        if args.verbose:
            logger.exception("Traceback completo:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
