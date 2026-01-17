#!/usr/bin/env python3
"""
Script simplificado para configurar permissões do usuário 'backup'.

Uso:
    python scripts/setup_backup_permissions_simple.py

    # Com modo dry-run (apenas verifica, não aplica):
    python scripts/setup_backup_permissions_simple.py --dry-run
"""

import json
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

from sqlalchemy import create_engine, text


def load_config(config_path: str) -> dict:
    """Carrega configuração do arquivo JSON."""
    with open(config_path, 'r') as f:
        return json.load(f)


def setup_logging(config: dict, project_root: Path) -> str:
    """
    Configura logging para console e arquivo.

    Args:
        config: Configuração carregada do JSON
        project_root: Diretório raiz do projeto

    Returns:
        Caminho do arquivo de log criado
    """
    logging_config = config.get("logging", {})
    log_level = logging_config.get("level", "INFO")
    log_format = logging_config.get("format", "%(asctime)s - %(levelname)s - %(message)s")
    log_file = logging_config.get("file", "reports/backup_permissions.log")

    # Cria caminho completo do log
    log_path = project_root / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Adiciona timestamp ao nome do arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = log_path.stem
    log_extension = log_path.suffix
    log_path_with_timestamp = log_path.parent / f"{log_filename}_{timestamp}{log_extension}"

    # Configura logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(log_path_with_timestamp, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("="*70)
    logger.info("SETUP DE PERMISSÕES - USUÁRIO BACKUP")
    logger.info("="*70)
    logger.info(f"Arquivo de log: {log_path_with_timestamp}")
    logger.info(f"Nível de log: {log_level}")

    return str(log_path_with_timestamp)


def create_engine_for_db(config: dict, database: str):
    """Cria engine SQLAlchemy para uma base de dados específica."""
    auth = config["authentication"]
    server = config["server"]

    conn_str = (
        f"postgresql://{auth['user']}:{auth['password']}"
        f"@{server['host']}:{server['port']}/{database}"
    )

    return create_engine(conn_str, pool_pre_ping=True)


def get_all_databases(engine) -> list:
    """Retorna lista de todas as bases de dados (exceto templates)."""
    query = text("""
        SELECT datname
        FROM pg_database
        WHERE datistemplate = false
          AND datname NOT IN ('postgres', 'template0', 'template1')
        ORDER BY datname
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        return [row[0] for row in result]


def ensure_backup_user_exists(engine) -> bool:
    """Garante que o usuário backup existe."""
    logger = logging.getLogger(__name__)
    check_query = text("SELECT 1 FROM pg_roles WHERE rolname = 'backup'")

    with engine.connect() as conn:
        result = conn.execute(check_query)

        if result.scalar():
            print("✓ Usuário 'backup' já existe")
            logger.info("Usuário 'backup' já existe no sistema")
            return True

        print("→ Criando usuário 'backup'...")
        logger.info("Criando usuário 'backup'...")
        create_query = text("""
            CREATE ROLE backup WITH
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION
        """)

        conn.execute(create_query)
        conn.commit()
        print("✓ Usuário 'backup' criado")
        logger.info("Usuário 'backup' criado com sucesso")
        return True


def check_database_permissions(engine, database: str) -> dict:
    """Verifica permissões do usuário backup em uma database."""
    query = text("""
        SELECT has_database_privilege('backup', :dbname, 'CONNECT') as can_connect
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"dbname": database})
        row = result.fetchone()
        return {"connect": row[0] if row else False}


def apply_backup_permissions(config: dict, database: str, dry_run: bool = False) -> bool:
    """Aplica todas as permissões necessárias para o usuário backup."""
    logger = logging.getLogger(__name__)

    try:
        engine = create_engine_for_db(config, database)

        with engine.connect() as conn:
            trans = conn.begin()

            try:
                statements = []

                # 1. CONNECT na database
                statements.append(f"GRANT CONNECT ON DATABASE {database} TO backup")

                # 2. Obter todos os schemas
                schema_query = text("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                """)
                result = conn.execute(schema_query)
                schemas = [row[0] for row in result]

                logger.debug(f"Database '{database}': encontrados {len(schemas)} schemas: {', '.join(schemas)}")

                # 3. Para cada schema, adicionar permissões
                for schema in schemas:
                    statements.extend([
                        f"GRANT USAGE ON SCHEMA {schema} TO backup",
                        f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO backup",
                        f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO backup",
                        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO backup",
                        f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON SEQUENCES TO backup"
                    ])

                if dry_run:
                    print(f"\n  [DRY-RUN] Comandos que seriam executados em '{database}':")
                    logger.info(f"[DRY-RUN] Database '{database}': {len(statements)} comandos seriam executados")
                    for stmt in statements[:5]:  # Mostra apenas os primeiros
                        print(f"    • {stmt}")
                        logger.debug(f"    {stmt}")
                    if len(statements) > 5:
                        print(f"    ... e mais {len(statements) - 5} comandos")
                        logger.debug(f"    ... e mais {len(statements) - 5} comandos")
                    trans.rollback()
                    return True

                # Executa os comandos
                logger.info(f"Aplicando {len(statements)} permissões em '{database}'")
                for stmt in statements:
                    logger.debug(f"Executando: {stmt}")
                    conn.execute(text(stmt))

                trans.commit()
                print(f"  ✓ {len(statements)} permissões aplicadas em '{database}'")
                logger.info(f"✓ {len(statements)} permissões aplicadas com sucesso em '{database}'")
                return True

            except Exception as e:
                trans.rollback()
                print(f"  ✗ Erro em '{database}': {e}")
                logger.error(f"Erro ao aplicar permissões em '{database}': {e}", exc_info=True)
                return False

        engine.dispose()

    except Exception as e:
        print(f"  ✗ Erro ao conectar em '{database}': {e}")
        logger.error(f"Erro de conexão em '{database}': {e}", exc_info=True)
        return False


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Configura permissões do usuário 'backup' em todas as bases de dados"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Apenas verifica, sem aplicar mudanças'
    )
    parser.add_argument(
        '--config',
        default='secrets/postgresql_destination_config.json',
        help='Caminho para o arquivo de configuração'
    )

    args = parser.parse_args()

    # Carrega configuração
    project_root = Path(__file__).parent.parent
    config_path = project_root / args.config

    if not config_path.exists():
        print(f"✗ Arquivo não encontrado: {config_path}")
        sys.exit(1)

    config = load_config(str(config_path))

    # Configura logging
    log_file = setup_logging(config, project_root)
    logger = logging.getLogger(__name__)

    print("="*70)
    print("SETUP DE PERMISSÕES - USUÁRIO BACKUP")
    print("="*70)
    print(f"Servidor: {config['server']['host']}")
    print(f"Modo: {'DRY-RUN (apenas verificação)' if args.dry_run else 'APLICAÇÃO'}")
    print(f"Log: {log_file}")
    print("="*70 + "\n")

    logger.info(f"Servidor: {config['server']['host']}")
    logger.info(f"Modo: {'DRY-RUN' if args.dry_run else 'APLICAÇÃO'}")

    # Conecta ao postgres para operações administrativas
    try:
        admin_engine = create_engine_for_db(config, "postgres")
        logger.info("Conexão administrativa estabelecida com sucesso")
    except Exception as e:
        logger.error(f"Erro ao conectar ao servidor: {e}", exc_info=True)
        print(f"✗ Erro ao conectar ao servidor: {e}")
        sys.exit(1)

    # Garante que usuário backup existe
    print("→ Verificando usuário 'backup'...")
    logger.info("Verificando existência do usuário 'backup'")
    if not ensure_backup_user_exists(admin_engine):
        logger.error("Falha ao criar/verificar usuário backup")
        print("✗ Falha ao criar/verificar usuário backup")
        sys.exit(1)

    # Obtém lista de databases
    print("\n→ Coletando bases de dados...")
    logger.info("Coletando lista de bases de dados")
    databases = get_all_databases(admin_engine)
    print(f"  ✓ Encontradas {len(databases)} bases de dados\n")
    logger.info(f"Encontradas {len(databases)} bases de dados: {', '.join(databases)}")

    # Processa cada database
    print("→ Processando permissões...\n")
    logger.info("Iniciando processamento de permissões")
    results = {}

    for i, database in enumerate(databases, 1):
        print(f"[{i}/{len(databases)}] {database}")
        logger.info(f"[{i}/{len(databases)}] Processando database: {database}")

        # Verifica permissões atuais
        perms = check_database_permissions(admin_engine, database)

        if perms['connect'] and not args.dry_run:
            print(f"  ✓ Permissões já configuradas")
            logger.info(f"Database '{database}': permissões já configuradas")
            results[database] = True
        else:
            # Aplica permissões
            success = apply_backup_permissions(config, database, args.dry_run)
            results[database] = success

    # Resumo
    print("\n" + "="*70)
    print("RESUMO")
    print("="*70)

    success_count = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"Total: {total}")
    print(f"Sucesso: {success_count}")
    print(f"Falhas: {total - success_count}")

    logger.info("="*70)
    logger.info("RESUMO FINAL")
    logger.info("="*70)
    logger.info(f"Total de databases processadas: {total}")
    logger.info(f"Sucessos: {success_count}")
    logger.info(f"Falhas: {total - success_count}")

    if success_count < total:
        print("\nDatabases com falha:")
        logger.warning("Databases com falha:")
        for db, success in results.items():
            if not success:
                print(f"  • {db}")
                logger.warning(f"  - {db}")

    print("="*70)

    admin_engine.dispose()
    logger.info("Conexões fechadas")

    if args.dry_run:
        print("\n💡 Execute sem --dry-run para aplicar as mudanças")
        logger.info("Execução em modo DRY-RUN concluída")
    else:
        logger.info("Execução concluída")

    logger.info(f"Log completo salvo em: {log_file}")
    logger.info("="*70)

    sys.exit(0 if success_count == total else 1)


if __name__ == "__main__":
    main()
