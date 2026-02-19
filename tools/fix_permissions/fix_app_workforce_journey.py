#!/usr/bin/env python3
"""
Script para corrigir permissões do journey_system no banco app_workforce do WF008
Conecta diretamente ao servidor WF008 usando credenciais configuradas
"""

import json
import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def load_wf008_credentials():
    """Carrega credenciais do arquivo de configuração wf008"""
    config_file = Path(__file__).parent.parent / "secrets" / \
        "wf008-postgresql_source_config.json"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {config_file}")

    with open(config_file, 'r') as f:
        config = json.load(f)

    return {
        "host": config["server"]["host"],
        "port": config["server"]["port"],
        "user": config["authentication"]["user"],
        "password": config["authentication"]["password"],
        "database": "app_workforce"
    }


def fix_journey_permissions():
    """Executa correção de permissões para journey_system no app_workforce"""

    print("\n" + "="*80)
    print("FIX PERMISSIONS - WF008 app_workforce (journey_system)")
    print("="*80 + "\n")

    try:
        # Carregar credenciais
        print("→ Carregando credenciais do WF008...")
        creds = load_wf008_credentials()
        print(
            f"✓ Credenciais carregadas: {creds['user']}@{creds['host']}:{creds['port']}")

        # Conectar
        print(f"\n→ Conectando ao banco {creds['database']}...")
        conn = psycopg2.connect(**creds)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        print(f"✓ Conectado com sucesso!")

        # Executar correções
        operations = [
            ("Concedendo CONNECT no banco de dados",
             "GRANT CONNECT ON DATABASE app_workforce TO journey_system;"),

            ("Concedendo CREATE no banco de dados",
             "GRANT CREATE ON DATABASE app_workforce TO journey_system;"),

            ("Concedendo TEMPORARY no banco de dados",
             "GRANT TEMPORARY ON DATABASE app_workforce TO journey_system;"),

            ("Concedendo USAGE no schema public",
             "GRANT USAGE ON SCHEMA public TO journey_system;"),

            ("Concedendo CREATE no schema public",
             "GRANT CREATE ON SCHEMA public TO journey_system;"),

            ("Concedendo SELECT, INSERT, UPDATE, DELETE em todas as tabelas",
             "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO journey_system;"),

            ("Concedendo USAGE, SELECT, UPDATE em todas as sequências",
             "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO journey_system;"),

            ("Configurando privilégios padrão para tabelas futuras",
             "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO journey_system;"),

            ("Configurando privilégios padrão para sequências futuras",
             "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO journey_system;"),
        ]

        print("\n" + "-"*80)
        print("EXECUTANDO OPERAÇÕES:")
        print("-"*80 + "\n")

        success_count = 0
        for idx, (description, sql) in enumerate(operations, 1):
            try:
                print(f"[{idx}/{len(operations)}] {description}...")
                cur.execute(sql)
                print(f"    ✓ OK\n")
                success_count += 1
            except Exception as e:
                print(f"    ✗ ERRO: {e}\n")

        # Verificações
        print("\n" + "-"*80)
        print("VERIFICAÇÕES:")
        print("-"*80 + "\n")

        # Verificar privilégios no schema
        print("→ Verificando privilégios no schema public...")
        cur.execute("""
            SELECT
                schemaname,
                has_schema_privilege('journey_system', schemaname, 'USAGE') as "USAGE",
                has_schema_privilege('journey_system', schemaname, 'CREATE') as "CREATE"
            FROM pg_namespace
            WHERE schemaname = 'public';
        """)

        for row in cur.fetchall():
            schema, usage, create = row
            print(f"  Schema: {schema}")
            print(f"    - USAGE: {'✓' if usage else '✗'}")
            print(f"    - CREATE: {'✓' if create else '✗'}")

        # Verificar privilégios em tabelas
        print("\n→ Verificando privilégios em tabelas...")
        cur.execute("""
            SELECT
                count(*) as total_tables,
                sum(CASE WHEN has_table_privilege('journey_system', schemaname||'.'||tablename, 'SELECT') THEN 1 ELSE 0 END) as can_select,
                sum(CASE WHEN has_table_privilege('journey_system', schemaname||'.'||tablename, 'INSERT') THEN 1 ELSE 0 END) as can_insert,
                sum(CASE WHEN has_table_privilege('journey_system', schemaname||'.'||tablename, 'UPDATE') THEN 1 ELSE 0 END) as can_update,
                sum(CASE WHEN has_table_privilege('journey_system', schemaname||'.'||tablename, 'DELETE') THEN 1 ELSE 0 END) as can_delete
            FROM pg_tables
            WHERE schemaname = 'public';
        """)

        result = cur.fetchone()
        if result:
            total, select_priv, insert_priv, update_priv, delete_priv = result
            print(f"  Total de tabelas: {total}")
            print(f"    - SELECT: {select_priv}/{total}")
            print(f"    - INSERT: {insert_priv}/{total}")
            print(f"    - UPDATE: {update_priv}/{total}")
            print(f"    - DELETE: {delete_priv}/{total}")

        # Verificar privilégios em sequências
        print("\n→ Verificando privilégios em sequências...")
        cur.execute("""
            SELECT
                count(*) as total_sequences,
                sum(CASE WHEN has_sequence_privilege('journey_system', schemaname||'.'||sequencename, 'USAGE') THEN 1 ELSE 0 END) as can_usage,
                sum(CASE WHEN has_sequence_privilege('journey_system', schemaname||'.'||sequencename, 'SELECT') THEN 1 ELSE 0 END) as can_select,
                sum(CASE WHEN has_sequence_privilege('journey_system', schemaname||'.'||sequencename, 'UPDATE') THEN 1 ELSE 0 END) as can_update
            FROM pg_sequences
            WHERE schemaname = 'public';
        """)

        result = cur.fetchone()
        if result:
            total, usage_priv, select_priv, update_priv = result
            print(f"  Total de sequências: {total}")
            if total > 0:
                print(f"    - USAGE: {usage_priv}/{total}")
                print(f"    - SELECT: {select_priv}/{total}")
                print(f"    - UPDATE: {update_priv}/{total}")

        # Fechar conexão
        cur.close()
        conn.close()

        # Resumo final
        print("\n" + "="*80)
        print(
            f"RESULTADO: {success_count}/{len(operations)} operações executadas com sucesso")
        print("="*80 + "\n")

        return success_count == len(operations)

    except Exception as e:
        print(f"\n✗ ERRO: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = fix_journey_permissions()
    sys.exit(0 if success else 1)
