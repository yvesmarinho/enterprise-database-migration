#!/usr/bin/env python3
"""
Restaura backup do Metabase usando credenciais do projeto
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuração
PROJECT_HOME = Path(__file__).parent.parent
BACKUP_FILE = PROJECT_HOME / "temp" / \
    "20260116_093154_postgresql_metabase_db.sql"
SECRETS_DIR = PROJECT_HOME / "secrets"


def load_credentials():
    """Carrega credenciais do PostgreSQL"""
    config_file = SECRETS_DIR / "postgresql_destination_config.json"

    if not config_file.exists():
        config_file = SECRETS_DIR / "destination_config.json"

    if not config_file.exists():
        print("❌ Arquivo de configuração não encontrado em secrets/")
        sys.exit(1)

    with open(config_file, 'r') as f:
        data = json.load(f)

    config = {
        'host': data['server']['host'],
        'port': data['server']['port'],
        'user': data['authentication']['user'],
        'password': data['authentication']['password'],
        'database': 'metabase_db'
    }

    return config


def drop_database(config, db_name):
    """Dropa o banco de dados forçando desconexão"""
    print(f"🗑️  Dropando banco {db_name}...")

    conn = psycopg2.connect(
        host=config['host'],
        port=config.get('port', 5432),
        user=config['user'],
        password=config['password'],
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE);")
        print("✅ Banco dropado")
    finally:
        conn.close()


def create_database(config, db_name):
    """Cria banco de dados limpo"""
    print(f"📦 Criando banco {db_name}...")

    conn = psycopg2.connect(
        host=config['host'],
        port=config.get('port', 5432),
        user=config['user'],
        password=config['password'],
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                CREATE DATABASE {db_name}
                    WITH TEMPLATE = template0
                    OWNER = metabase_user
                    ENCODING = 'UTF8'
                    LC_COLLATE = 'en_US.utf8'
                    LC_CTYPE = 'en_US.utf8'
                    CONNECTION LIMIT = -1;
            """)
        print("✅ Banco criado")
    finally:
        conn.close()


def restore_backup(config, db_name, backup_file):
    """Restaura backup usando pg_restore"""
    print(f"📥 Restaurando {backup_file.name}...")

    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']

    cmd = [
        'pg_restore',
        '-h', config['host'],
        '-p', str(config.get('port', 5432)),
        '-U', config['user'],
        '-d', db_name,
        '--verbose',
        '--no-owner',
        '--no-acl',
        str(backup_file)
    ]

    result = subprocess.run(
        cmd, env=env, capture_output=True, text=True, check=False)

    if result.stderr:
        lines = [l for l in result.stderr.split(
            '\n') if 'processing' in l.lower() or 'creating' in l.lower()]
        for line in lines[-10:]:
            if line.strip():
                print(f"  {line}")

    print("✅ Backup restaurado")


def verify_restore(config, db_name):
    """Verifica se a restauração foi bem-sucedida"""
    print(f"\n📊 Verificando...")

    conn = psycopg2.connect(
        host=config['host'],
        port=config.get('port', 5432),
        user=config['user'],
        password=config['password'],
        database=db_name
    )

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)
            tables = cur.fetchone()[0]
            print(f"  📋 Tabelas: {tables}")

            cur.execute("""
                SELECT EXISTS (SELECT 1 FROM information_schema.tables
                WHERE table_name = 'databasechangelog');
            """)
            has_log = cur.fetchone()[0]

            if has_log:
                cur.execute("SELECT COUNT(*) FROM databasechangelog;")
                migrations = cur.fetchone()[0]
                print(f"  🔄 Migrações: {migrations}")

            cur.execute("""
                SELECT column_name, data_type FROM information_schema.columns
                WHERE table_name = 'auth_identity' AND column_name = 'user_id';
            """)
            result = cur.fetchone()
            if result:
                print(f"  🔑 auth_identity.user_id: {result[1]}")
    finally:
        conn.close()


def main():
    print("🔄 Restauração de Backup do Metabase")
    print("=" * 60)

    if not BACKUP_FILE.exists():
        print(f"❌ Backup não encontrado: {BACKUP_FILE}")
        sys.exit(1)

    print(f"📁 {BACKUP_FILE.name}")

    config = load_credentials()
    db_name = config.get('database', 'metabase_db')

    print(f"🗄️  {db_name} @ {config['host']}:{config.get('port', 5432)}")
    print(f"👤 {config['user']}")
    print()
    print("⚠️  AVISO: Banco será DROPADO e RECRIADO!")
    print("⚠️  Metabase deve estar PARADO!")
    print()

    response = input("Digite 'CONFIRMO' para continuar: ")
    if response != 'CONFIRMO':
        print("❌ Cancelado")
        sys.exit(0)

    print()

    try:
        drop_database(config, db_name)
        create_database(config, db_name)
        restore_backup(config, db_name, BACKUP_FILE)
        verify_restore(config, db_name)

        print("\n" + "=" * 60)
        print("✅ Restauração concluída!")
        print("\n🚀 Próximos passos:")
        print("   1. docker-compose start dashboard")
        print("   2. docker-compose logs -f dashboard")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
