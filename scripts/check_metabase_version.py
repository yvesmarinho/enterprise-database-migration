#!/usr/bin/env python3
"""
Script para verificar a versão do Metabase no backup restaurado
e identificar o problema de downgrade
"""

import json

import psycopg2


def main():
    # Carregar credenciais
    with open('secrets/postgresql_destination_config.json', 'r') as f:
        config = json.load(f)

    conn_params = {
        'host': config['server']['host'],
        'port': config['server']['port'],
        'database': 'metabase_db',
        'user': config['authentication']['user'],
        'password': config['authentication']['password']
    }

    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    print('=' * 80)
    print('ANÁLISE DA VERSÃO DO METABASE NO BACKUP')
    print('=' * 80)
    print()

    # 1. Verificar última migração
    print('1. ÚLTIMAS MIGRAÇÕES EXECUTADAS:')
    print('-' * 80)
    cur.execute("""
        SELECT
            filename,
            id,
            orderexecuted,
            dateexecuted
        FROM databasechangelog
        ORDER BY dateexecuted DESC
        LIMIT 15;
    """)

    for filename, migration_id, order, date in cur.fetchall():
        print(f'  {date} | Order: {order:4} | {filename}')
        print(f'    └─ ID: {migration_id}')

    # 2. Verificar maior ordem executada
    print()
    print('2. INFORMAÇÕES GERAIS DAS MIGRAÇÕES:')
    print('-' * 80)
    cur.execute("""
        SELECT
            MAX(orderexecuted) as max_order,
            COUNT(*) as total_migrations,
            MIN(dateexecuted) as first_migration,
            MAX(dateexecuted) as last_migration
        FROM databasechangelog;
    """)

    max_order, total, first_date, last_date = cur.fetchone()
    print(f'  Maior ordem executada: {max_order}')
    print(f'  Total de migrações: {total}')
    print(f'  Primeira migração: {first_date}')
    print(f'  Última migração: {last_date}')

    # 3. Verificar versão pela tabela setting
    print()
    print('3. SETTINGS RELACIONADAS À VERSÃO:')
    print('-' * 80)
    cur.execute("""
        SELECT key, value
        FROM setting
        WHERE key LIKE '%version%'
        ORDER BY key;
    """)

    settings = cur.fetchall()
    if settings:
        for key, value in settings:
            print(f'  {key}: {value}')
    else:
        print('  Nenhuma setting de versão encontrada')

    # 4. Buscar migrações da v56 (causa do erro)
    print()
    print('4. MIGRAÇÕES DA VERSÃO 56 (CAUSANDO DOWNGRADE):')
    print('-' * 80)
    cur.execute("""
        SELECT
            id,
            filename,
            orderexecuted,
            dateexecuted
        FROM databasechangelog
        WHERE filename LIKE '%056%' OR filename LIKE '%v56%'
        ORDER BY orderexecuted DESC
        LIMIT 20;
    """)

    v56_migrations = cur.fetchall()
    if v56_migrations:
        print(f'  Encontradas {len(v56_migrations)} migrações da v56:')
        for migration_id, filename, order, date in v56_migrations:
            print(f'    Order {order:4}: {migration_id}')
    else:
        print('  Nenhuma migração da v56 encontrada')

    # 5. Verificar arquivos de migração únicos
    print()
    print('5. ARQUIVOS DE MIGRAÇÃO POR VERSÃO:')
    print('-' * 80)
    cur.execute("""
        SELECT
            filename,
            COUNT(*) as migration_count,
            MAX(orderexecuted) as max_order
        FROM databasechangelog
        GROUP BY filename
        ORDER BY max_order DESC
        LIMIT 10;
    """)

    for filename, count, max_order in cur.fetchall():
        print(f'  {filename:50} | {count:3} migrações | '
              f'Max Order: {max_order}')

    # 6. Conclusão
    print()
    print('=' * 80)
    print('DIAGNÓSTICO:')
    print('=' * 80)

    if v56_migrations:
        print('❌ PROBLEMA IDENTIFICADO:')
        print('  O backup contém migrações da versão 56+ do Metabase')
        print('  Você está tentando executar v0.54.9 (downgrade)')
        print()
        print('SOLUÇÕES POSSÍVEIS:')
        print('  1. Usar backup ANTERIOR (sem migrações v56)')
        print('  2. Usar Metabase v0.56.0 ou superior')
        print('  3. Executar downgrade manual das migrações')
    else:
        print('✓ Backup parece compatível com versões antigas')
        print('  Não foram encontradas migrações v56')

    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
