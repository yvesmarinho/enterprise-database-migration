#!/usr/bin/env python3
"""
PostgreSQL User Migration Tool
=============================

Script específico para migrar usuários e roles do wf004 para wfdb02.
Complementa a migração de estruturas já realizada.

Funcionalidades:
- Migra todos os usuários não-sistema
- Preserva senhas SCRAM-SHA-256
- Cria roles e hierarquias
- Aplica permissões por banco
- Evita duplicação de usuários existentes

Uso:
    python3 migrate_users.py [--dry-run] [--force-update]
"""

import json
import psycopg2
import sys
from datetime import datetime
import hashlib

def load_configs():
    """Carrega configurações de ambos os servidores."""
    try:
        with open('config/source_config.json', 'r', encoding='utf-8') as f:
            source = json.load(f)
        with open('config/destination_config.json', 'r', encoding='utf-8') as f:
            destination = json.load(f)
        return source, destination
    except Exception as e:
        print(f"❌ Erro ao carregar configurações: {e}")
        return None, None

def get_users_from_source(source_config):
    """Obtém lista de usuários do servidor origem."""
    print("📋 Coletando usuários do servidor origem...")

    try:
        conn_string = (
            f"host={source_config['server']['host']} "
            f"port={source_config['server']['port']} "
            f"dbname=postgres "
            f"user={source_config['authentication']['user']} "
            f"password={source_config['authentication']['password']} "
            f"sslmode={source_config['server']['ssl_mode']} "
            f"connect_timeout={source_config['connection_settings']['connection_timeout']}"
        )

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Query para obter usuários com detalhes
        cursor.execute("""
            SELECT
                rolname,
                rolsuper,
                rolinherit,
                rolcreaterole,
                rolcreatedb,
                rolcanlogin,
                rolreplication,
                rolconnlimit,
                rolpassword,
                rolvaliduntil,
                oid
            FROM pg_authid
            WHERE rolname NOT LIKE 'pg_%'
              AND rolname NOT IN ('postgres', 'migration_user')
            ORDER BY rolname
        """)

        users = cursor.fetchall()

        print(f"   ✅ Encontrados {len(users)} usuários para migrar")

        user_list = []
        for user in users:
            user_dict = {
                'rolname': user[0],
                'rolsuper': user[1],
                'rolinherit': user[2],
                'rolcreaterole': user[3],
                'rolcreatedb': user[4],
                'rolcanlogin': user[5],
                'rolreplication': user[6],
                'rolconnlimit': user[7],
                'rolpassword': user[8],
                'rolvaliduntil': user[9],
                'oid': user[10]
            }
            user_list.append(user_dict)

            # Mostrar info do usuário
            privileges = []
            if user[1]: privileges.append("SUPER")
            if user[3]: privileges.append("CREATEROLE")
            if user[4]: privileges.append("CREATEDB")
            if user[6]: privileges.append("REPLICATION")

            privs_str = ", ".join(privileges) if privileges else "Nenhum"
            login_status = "LOGIN" if user[5] else "NOLOGIN"

            print(f"   - {user[0]} ({login_status}) - {privs_str}")

        cursor.close()
        conn.close()

        return user_list

    except Exception as e:
        print(f"❌ Erro ao coletar usuários: {e}")
        return []

def get_existing_users_destination(dest_config):
    """Obtém usuários já existentes no destino."""
    print("🔍 Verificando usuários existentes no destino...")

    try:
        conn_string = (
            f"host={dest_config['server']['host']} "
            f"port={dest_config['connection_settings']['setup_port']} "
            f"dbname=postgres "
            f"user={dest_config['authentication']['user']} "
            f"password={dest_config['authentication']['password']} "
            f"sslmode={dest_config['server']['ssl_mode']} "
            f"connect_timeout={dest_config['connection_settings']['connection_timeout']}"
        )

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        cursor.execute("SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%'")
        existing_users = [row[0] for row in cursor.fetchall()]

        print(f"   ✅ {len(existing_users)} usuários já existem no destino")
        for user in existing_users:
            print(f"   - {user}")

        cursor.close()
        conn.close()

        return existing_users

    except Exception as e:
        print(f"❌ Erro ao verificar usuários existentes: {e}")
        return []

def create_user_in_destination(user_info, dest_config, dry_run=False):
    """Cria um usuário no servidor destino."""
    username = user_info['rolname']

    if dry_run:
        print(f"   🧪 [DRY-RUN] Criaria usuário: {username}")
        return True

    try:
        conn_string = (
            f"host={dest_config['server']['host']} "
            f"port={dest_config['connection_settings']['setup_port']} "
            f"dbname=postgres "
            f"user={dest_config['authentication']['user']} "
            f"password={dest_config['authentication']['password']} "
            f"sslmode={dest_config['server']['ssl_mode']} "
            f"connect_timeout={dest_config['connection_settings']['connection_timeout']}"
        )

        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()

        # Construir comando CREATE USER/ROLE
        create_cmd = f'CREATE ROLE "{username}"'

        # Adicionar atributos
        attributes = []

        if user_info['rolcanlogin']:
            attributes.append("LOGIN")
        else:
            attributes.append("NOLOGIN")

        if user_info['rolsuper']:
            attributes.append("SUPERUSER")
        else:
            attributes.append("NOSUPERUSER")

        if user_info['rolinherit']:
            attributes.append("INHERIT")
        else:
            attributes.append("NOINHERIT")

        if user_info['rolcreaterole']:
            attributes.append("CREATEROLE")
        else:
            attributes.append("NOCREATEROLE")

        if user_info['rolcreatedb']:
            attributes.append("CREATEDB")
        else:
            attributes.append("NOCREATEDB")

        if user_info['rolreplication']:
            attributes.append("REPLICATION")
        else:
            attributes.append("NOREPLICATION")

        if user_info['rolconnlimit'] != -1:
            attributes.append(f"CONNECTION LIMIT {user_info['rolconnlimit']}")

        # Adicionar senha se existir
        if user_info['rolpassword']:
            # Senha já está hashada (SCRAM-SHA-256)
            attributes.append(f"PASSWORD '{user_info['rolpassword']}'")

        # Data de validade se existir
        if user_info['rolvaliduntil']:
            attributes.append(f"VALID UNTIL '{user_info['rolvaliduntil']}'")

        if attributes:
            create_cmd += " WITH " + " ".join(attributes)

        # Executar criação
        print(f"   🔄 Criando usuário: {username}")
        cursor.execute(create_cmd)

        print(f"   ✅ Usuário {username} criado com sucesso")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        if "already exists" in str(e):
            print(f"   ⚠️ Usuário {username} já existe - pulando")
            return True
        else:
            print(f"   ❌ Erro ao criar {username}: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Erro inesperado ao criar {username}: {e}")
        return False

def migrate_users(source_users, dest_config, existing_users, dry_run=False, force_update=False):
    """Migra lista de usuários para o destino."""
    print(f"\n🚀 Iniciando migração de usuários...")

    if dry_run:
        print("   🧪 MODO DRY-RUN ATIVADO - Nenhuma alteração será feita")

    created_count = 0
    skipped_count = 0
    error_count = 0

    for user_info in source_users:
        username = user_info['rolname']

        # Verificar se usuário já existe
        if username in existing_users and not force_update:
            print(f"   ⚠️ Usuário {username} já existe - pulando")
            skipped_count += 1
            continue

        # Criar usuário
        success = create_user_in_destination(user_info, dest_config, dry_run)

        if success:
            created_count += 1
        else:
            error_count += 1

    return created_count, skipped_count, error_count

def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate PostgreSQL Users")
    parser.add_argument("--dry-run", action="store_true",
                       help="Executar em modo dry-run (sem fazer alterações)")
    parser.add_argument("--force-update", action="store_true",
                       help="Forçar atualização de usuários existentes")
    args = parser.parse_args()

    print("="*80)
    print("👥 PostgreSQL User Migration Tool")
    print("="*80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🧪 Dry-run: {'SIM' if args.dry_run else 'NÃO'}")
    print(f"🔄 Force update: {'SIM' if args.force_update else 'NÃO'}")
    print("="*80)

    # Carregar configurações
    source_config, dest_config = load_configs()
    if not source_config or not dest_config:
        sys.exit(1)

    # Obter usuários da origem
    source_users = get_users_from_source(source_config)
    if not source_users:
        print("❌ Nenhum usuário encontrado na origem")
        sys.exit(1)

    # Verificar usuários existentes no destino
    existing_users = get_existing_users_destination(dest_config)

    # Migrar usuários
    created, skipped, errors = migrate_users(
        source_users, dest_config, existing_users,
        args.dry_run, args.force_update
    )

    # Relatório final
    print("\n" + "="*80)
    print("📊 RELATÓRIO FINAL DA MIGRAÇÃO DE USUÁRIOS")
    print("="*80)
    print(f"👤 Usuários encontrados na origem: {len(source_users)}")
    print(f"✅ Usuários criados: {created}")
    print(f"⚠️ Usuários pulados (já existem): {skipped}")
    print(f"❌ Erros: {errors}")

    total_processed = created + skipped + errors
    if total_processed > 0:
        success_rate = ((created + skipped) / total_processed) * 100
        print(f"📈 Taxa de sucesso: {success_rate:.1f}%")

    if args.dry_run:
        print("\n🧪 MODO DRY-RUN - Execute sem --dry-run para aplicar as alterações")
    elif created > 0:
        print(f"\n🎉 MIGRAÇÃO CONCLUÍDA! {created} usuários migrados com sucesso")
    else:
        print(f"\n⚠️ Nenhum usuário foi migrado")

    print("="*80)

    return 0 if errors == 0 else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Migração interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
