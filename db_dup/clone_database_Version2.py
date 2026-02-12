#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Principal de Clonagem de Banco de Dados PostgreSQL.

Este script orquestra todo o processo de clonagem de banco de dados PostgreSQL,
lendo configuração de arquivo JSON e executando todas as etapas necessárias.

:author: yvesmarinho
:date: 2026-02-09
:version: 2.0.0

Usage
-----
    python clone_database.py config.json [options]

Examples
--------
    # Clonagem básica
    python clone_database.py config.json

    # Clonagem com drop do banco existente
    python clone_database.py config.json --drop-if-exists

    # Clonagem apenas estrutura (sem dados)
    python clone_database.py config.json --no-data

    # Clonagem com verificação desabilitada
    python clone_database.py config.json --no-verify

    # Salvar metadados em arquivo
    python clone_database.py config.json --save-metadata metadata.json

    # Modo verboso
    python clone_database.py config.json --verbose
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager
    from pg_database_cloner_Version2 import DatabaseCloner
    from pg_json_config_Version2 import PostgreSQLJsonConfig
    from pg_metadata_analyzer_Version2 import DatabaseMetadataAnalyzer
except ImportError as e:
    print(f"ERRO: Falha ao importar módulos necessários: {e}")
    print("\nCertifique-se de que todos os módulos estão no mesmo diretório:")
    print("  - pg_json_config.py")
    print("  - pg_connection_manager_v2.py")
    print("  - pg_metadata_analyzer.py")
    print("  - pg_database_cloner.py")
    sys.exit(1)


def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """
    Configura o sistema de logging.

    Parameters
    ----------
    verbose : bool, optional
        Se deve usar modo verboso (DEBUG)
    log_file : str, optional
        Caminho do arquivo de log
    """
    try:
        log_level = logging.DEBUG if verbose else logging.INFO

        # Configurar formato
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Configurar handlers
        handlers = []

        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(
            logging.Formatter(log_format, datefmt=date_format)
        )
        handlers.append(console_handler)

        # Handler para arquivo (se especificado)
        if log_file:
            try:
                file_handler = logging.FileHandler(
                    log_file, mode='w', encoding='utf-8')
                file_handler.setLevel(log_level)
                file_handler.setFormatter(
                    logging.Formatter(log_format, datefmt=date_format)
                )
                handlers.append(file_handler)
            except Exception as e:
                print(f"AVISO: Não foi possível criar arquivo de log: {e}")

        # Configurar logger raiz
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt=date_format,
            handlers=handlers
        )

        # Silenciar logs de bibliotecas externas (se não verbose)
        if not verbose:
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)

        return True

    except Exception as e:
        print(f"ERRO ao configurar logging: {e}")
        return False


def parse_arguments() -> argparse.Namespace:
    """
    Parseia argumentos da linha de comando.

    Returns
    -------
    argparse.Namespace
        Argumentos parseados
    """
    try:
        parser = argparse.ArgumentParser(
            description='Clonagem de Banco de Dados PostgreSQL com Preservação de Permissões',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemplos:
  # Clonagem básica
  %(prog)s config.json

  # Clonagem com drop do banco existente
  %(prog)s config.json --drop-if-exists

  # Clonagem apenas estrutura (sem dados)
  %(prog)s config.json --no-data

  # Salvar metadados em arquivo
  %(prog)s config.json --save-metadata metadata.json

Formato do arquivo de configuração JSON:
{
  "host": "localhost",
  "port": 5432,
  "ssl_mode": "false",
  "possible_users": [
    {
      "username": "migration_user",
      "password": "senha_secreta"
    }
  ],
  "db_source": "banco_origem",
  "db_destiny": "banco_destino"
}
            """
        )

        # Argumento posicional (obrigatório)
        parser.add_argument(
            'config_file',
            type=str,
            help='Arquivo JSON com configuração de conexão'
        )

        # Argumentos opcionais
        parser.add_argument(
            '--drop-if-exists',
            action='store_true',
            help='Dropar banco de destino se já existir'
        )

        parser.add_argument(
            '--no-data',
            action='store_true',
            help='Copiar apenas estrutura (sem dados)'
        )

        parser.add_argument(
            '--no-verify',
            action='store_true',
            help='Não verificar clonagem ao final'
        )

        parser.add_argument(
            '--save-metadata',
            type=str,
            metavar='FILE',
            help='Salvar metadados extraídos em arquivo JSON'
        )

        parser.add_argument(
            '--log-file',
            type=str,
            metavar='FILE',
            help='Salvar logs em arquivo'
        )

        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Modo verboso (debug)'
        )

        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 2.0.0'
        )

        args = parser.parse_args()
        return args

    except Exception as e:
        print(f"ERRO ao parsear argumentos: {e}")
        sys.exit(1)


def validate_config_file(config_file: str) -> bool:
    """
    Valida se arquivo de configuração existe e é legível.

    Parameters
    ----------
    config_file : str
        Caminho do arquivo

    Returns
    -------
    bool
        True se válido, False caso contrário
    """
    try:
        if not isinstance(config_file, str) or not config_file:
            print("ERRO: Caminho do arquivo de configuração inválido")
            return False

        config_path = Path(config_file)

        if not config_path.exists():
            print(
                f"ERRO: Arquivo de configuração não encontrado: {config_file}")
            return False

        if not config_path.is_file():
            print(f"ERRO: Caminho não é um arquivo: {config_file}")
            return False

        if not os.access(config_path, os.R_OK):
            print(f"ERRO: Sem permissão de leitura no arquivo: {config_file}")
            return False

        return True

    except Exception as e:
        print(f"ERRO ao validar arquivo de configuração: {e}")
        return False


def load_configuration(config_file: str) -> Optional[PostgreSQLJsonConfig]:
    """
    Carrega configuração do arquivo JSON.

    Parameters
    ----------
    config_file : str
        Caminho do arquivo JSON

    Returns
    -------
    PostgreSQLJsonConfig or None
        Configuração carregada ou None em caso de erro
    """
    try:
        logging.info(f"Carregando configuração de: {config_file}")

        config = PostgreSQLJsonConfig.from_json_file(config_file)

        logging.info("✓ Configuração carregada com sucesso")
        logging.info(f"  Servidor: {config.host}:{config.port}")
        logging.info(f"  Origem: {config.db_source}")
        logging.info(f"  Destino: {config.db_destiny}")
        logging.info(f"  Usuários configurados: {len(config.possible_users)}")
        logging.info(f"  SSL Mode: {config.ssl_mode.value}")

        return config

    except FileNotFoundError as e:
        logging.error(f"✗ Arquivo não encontrado: {e}")
        return None
    except ValueError as e:
        logging.error(f"✗ Configuração inválida: {e}")
        return None
    except Exception as e:
        logging.error(f"✗ Erro ao carregar configuração: {e}")
        return None


def print_banner():
    """Imprime banner do sistema."""
    banner = """
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║           PostgreSQL Database Clone System v2.0.0                          ║
║                                                                            ║
║  Sistema Completo de Clonagem de Bancos de Dados PostgreSQL               ║
║  com Preservação de Permissões, Tablespaces e Estruturas                  ║
║                                                                            ║
║  Autor: yvesmarinho                                                        ║
║  Data: 2026-02-09                                                          ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_summary(
    config: PostgreSQLJsonConfig,
    cloner: DatabaseCloner,
    success: bool
):
    """
    Imprime resumo final da execução.

    Parameters
    ----------
    config : PostgreSQLJsonConfig
        Configuração utilizada
    cloner : DatabaseCloner
        Clonador utilizado
    success : bool
        Se execução foi bem-sucedida
    """
    try:
        print("\n" + "=" * 80)
        print("RESUMO FINAL DA EXECUÇÃO")
        print("=" * 80)

        if success:
            print("Status: ✓ SUCESSO")
        else:
            print("Status: ✗ FALHA")

        print("-" * 80)
        print(f"Servidor: {config.host}:{config.port}")
        print(f"Banco de Origem: {config.db_source}")
        print(f"Banco de Destino: {config.db_destiny}")
        print(
            f"Usuário Utilizado: {config.validated_user.username if config.validated_user else 'N/A'}")

        if cloner.clone_stats.get('start_time'):
            print("-" * 80)
            print(f"Início: {cloner.clone_stats['start_time']}")
            print(f"Fim: {cloner.clone_stats.get('end_time', 'N/A')}")
            print(
                f"Duração: {cloner.clone_stats.get('duration_seconds', 0):.2f} segundos")

        if cloner.clone_stats.get('roles_created') is not None:
            print("-" * 80)
            print("Estatísticas:")
            print(
                f"  Roles criadas: {cloner.clone_stats.get('roles_created', 0)}")
            print(
                f"  Tabelas copiadas: {cloner.clone_stats.get('tables_copied', 0)}")
            print(
                f"  Views criadas: {cloner.clone_stats.get('views_created', 0)}")
            print(
                f"  Functions criadas: {cloner.clone_stats.get('functions_created', 0)}")
            print(
                f"  Permissões aplicadas: {cloner.clone_stats.get('permissions_applied', 0)}")

        errors = cloner.clone_stats.get('errors', [])
        if errors:
            print("-" * 80)
            print(f"Erros Encontrados: {len(errors)}")
            for idx, error in enumerate(errors, 1):
                print(f"  {idx}. {error}")

        print("=" * 80)

    except Exception as e:
        logging.error(f"Erro ao imprimir resumo: {e}")


def main() -> int:
    """
    Função principal do script.

    Returns
    -------
    int
        Código de saída (0 = sucesso, 1 = erro)
    """
    manager = None
    success = False

    try:
        # Imprimir banner
        print_banner()

        # Parsear argumentos
        args = parse_arguments()

        # Configurar logging
        if not setup_logging(verbose=args.verbose, log_file=args.log_file):
            print("ERRO: Falha ao configurar logging")
            return 1

        logging.info("=" * 80)
        logging.info("INICIANDO SISTEMA DE CLONAGEM")
        logging.info("=" * 80)

        # Validar arquivo de configuração
        if not validate_config_file(args.config_file):
            return 1

        # Carregar configuração
        config = load_configuration(args.config_file)
        if not config:
            return 1

        # Criar gerenciador de conexões
        logging.info("\nCriando gerenciador de conexões...")
        manager = PostgreSQLConnectionManager(
            config,
            use_pool=True,
            auto_validate=True
        )

        if not manager.config.validated_user:
            logging.error("✗ Nenhuma credencial válida encontrada")
            return 1

        # Conectar aos bancos
        logging.info("\nEstabelecendo conexões...")
        if not manager.connect():
            logging.error("✗ Falha ao conectar aos bancos de dados")
            return 1

        # Criar analisador de metadados
        logging.info("\nCriando analisador de metadados...")
        analyzer = DatabaseMetadataAnalyzer(manager)

        # Criar clonador
        logging.info("\nCriando clonador de banco de dados...")
        cloner = DatabaseCloner(manager, analyzer)

        # Executar clonagem
        logging.info("\n" + "=" * 80)
        logging.info("INICIANDO PROCESSO DE CLONAGEM")
        logging.info("=" * 80)

        success = cloner.clone_database(
            drop_if_exists=args.drop_if_exists,
            copy_data=not args.no_data,
            verify_clone=not args.no_verify
        )

        # Salvar metadados se solicitado
        if args.save_metadata and analyzer.metadata:
            logging.info(f"\nSalvando metadados em: {args.save_metadata}")
            if analyzer.save_metadata_to_file(args.save_metadata):
                logging.info(f"✓ Metadados salvos com sucesso")
            else:
                logging.warning(f"⚠ Falha ao salvar metadados")

        # Imprimir resumo
        print_summary(config, cloner, success)

        if success:
            logging.info("\n✓ CLONAGEM CONCLUÍDA COM SUCESSO!")
            return 0
        else:
            logging.error("\n✗ CLONAGEM FALHOU")
            return 1

    except KeyboardInterrupt:
        logging.warning("\n\n⚠ INTERROMPIDO PELO USUÁRIO")
        return 1
    except Exception as e:
        logging.error(f"\n✗ ERRO FATAL: {e}", exc_info=True)
        return 1
    finally:
        # Desconectar
        if manager:
            try:
                logging.info("\nDesconectando...")
                manager.disconnect()
                logging.info("✓ Desconexão concluída")
            except Exception as e:
                logging.error(f"Erro ao desconectar: {e}")


if __name__ == "__main__":
    sys.exit(main())
