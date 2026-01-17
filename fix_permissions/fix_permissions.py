#!/usr/bin/env python3
"""
Script para correção automatizada de permissões em bancos de dados PostgreSQL
Baseado nas configurações do fix_permissions.json

Autor: Sistema de Migração Enterprise
Data: 2026-01-16
Versão: 1.0.0

Uso:
    python3 fix_permissions.py --database metabase_db --dry-run
    python3 fix_permissions.py --database metabase_db --execute
    python3 fix_permissions.py --all --execute --verbose
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class PermissionsFixer:
    """Classe para corrigir permissões de bancos de dados PostgreSQL"""

    def __init__(self, config_path: str, verbose: bool = False):
        self.verbose = verbose
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.connection_config = self._load_connection_config()
        self.conn = None
        self.cur = None

    def _load_config(self) -> Dict:
        """Carrega configuração do JSON"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_connection_config(self) -> Dict:
        """Carrega configuração de conexão"""
        config_file = self.config['connection']['config_file']
        config_path = Path(__file__).parent.parent / config_file

        if not config_path.exists():
            raise FileNotFoundError(
                f"Arquivo de credenciais não encontrado: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def connect(self, database: str = 'postgres'):
        """Estabelece conexão com o banco de dados"""
        try:
            self.conn = psycopg2.connect(
                host=self.connection_config['server']['host'],
                port=self.connection_config['server']['port'],
                database=database,
                user=self.connection_config['authentication']['user'],
                password=self.connection_config['authentication']['password']
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cur = self.conn.cursor()

            if self.verbose:
                print(f"✓ Conectado ao banco: {database}")

            return True
        except Exception as e:
            print(f"✗ Erro ao conectar: {e}")
            return False

    def disconnect(self):
        """Fecha conexão com o banco"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def _log(self, message: str, level: str = 'INFO'):
        """Log de mensagens"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        symbols = {
            'INFO': '→',
            'SUCCESS': '✓',
            'ERROR': '✗',
            'WARNING': '⚠'
        }
        symbol = symbols.get(level, '•')

        if self.verbose or level in ['SUCCESS', 'ERROR', 'WARNING']:
            print(f"[{timestamp}] {symbol} {message}")

    def _execute_sql(self, sql: str, params: tuple = None, dry_run: bool = False) -> bool:
        """Executa SQL com tratamento de erros"""
        try:
            if dry_run:
                self._log(f"DRY-RUN: {sql}", 'INFO')
                return True

            if params:
                self.cur.execute(sql, params)
            else:
                self.cur.execute(sql)

            self._log(f"Executado: {sql[:100]}...", 'SUCCESS')
            return True
        except Exception as e:
            self._log(f"Erro ao executar SQL: {e}\nSQL: {sql}", 'ERROR')
            return False

    def transfer_table_ownership(self, database: str, from_user: str, to_user: str, dry_run: bool = False):
        """Transfere ownership de todas as tabelas"""
        self._log(
            f"Transferindo ownership de tabelas: {from_user} → {to_user}")

        # Obter lista de tabelas
        self.cur.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tableowner = %s;
        """, (from_user,))

        tables = self.cur.fetchall()
        count = 0

        for (table_name,) in tables:
            sql = f"ALTER TABLE public.{table_name} OWNER TO {to_user};"
            if self._execute_sql(sql, dry_run=dry_run):
                count += 1

        self._log(f"Ownership transferido para {count} tabelas", 'SUCCESS')
        return count

    def transfer_sequence_ownership(self, database: str, from_user: str, to_user: str, dry_run: bool = False):
        """Transfere ownership de todas as sequências"""
        self._log(
            f"Transferindo ownership de sequências: {from_user} → {to_user}")

        self.cur.execute("""
            SELECT sequencename
            FROM pg_sequences
            WHERE schemaname = 'public';
        """)

        sequences = self.cur.fetchall()
        count = 0

        for (seq_name,) in sequences:
            sql = f"ALTER SEQUENCE public.{seq_name} OWNER TO {to_user};"
            if self._execute_sql(sql, dry_run=dry_run):
                count += 1

        self._log(f"Ownership transferido para {count} sequências", 'SUCCESS')
        return count

    def transfer_view_ownership(self, database: str, from_user: str, to_user: str, dry_run: bool = False):
        """Transfere ownership de todas as views"""
        self._log(f"Transferindo ownership de views: {from_user} → {to_user}")

        self.cur.execute("""
            SELECT viewname
            FROM pg_views
            WHERE schemaname = 'public';
        """)

        views = self.cur.fetchall()
        count = 0

        for (view_name,) in views:
            sql = f"ALTER VIEW public.{view_name} OWNER TO {to_user};"
            if self._execute_sql(sql, dry_run=dry_run):
                count += 1

        self._log(f"Ownership transferido para {count} views", 'SUCCESS')
        return count

    def grant_schema_privileges(self, schema: str, user: str, privileges: List[str], dry_run: bool = False):
        """Concede privilégios no schema"""
        privs = ', '.join(privileges)
        sql = f"GRANT {privs} ON SCHEMA {schema} TO {user};"
        self._execute_sql(sql, dry_run=dry_run)

    def grant_all_tables_privileges(self, schema: str, user: str, privileges: List[str], dry_run: bool = False):
        """Concede privilégios em todas as tabelas"""
        privs = ', '.join(privileges)
        sql = f"GRANT {privs} ON ALL TABLES IN SCHEMA {schema} TO {user};"
        self._execute_sql(sql, dry_run=dry_run)

    def grant_all_sequences_privileges(self, schema: str, user: str, privileges: List[str], dry_run: bool = False):
        """Concede privilégios em todas as sequências"""
        privs = ', '.join(privileges)
        sql = f"GRANT {privs} ON ALL SEQUENCES IN SCHEMA {schema} TO {user};"
        self._execute_sql(sql, dry_run=dry_run)

    def set_default_privileges(self, schema: str, target: str, user: str, privileges: List[str], dry_run: bool = False):
        """Define privilégios padrão para objetos futuros"""
        privs = ', '.join(privileges)
        target_upper = target.upper()
        sql = f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT {privs} ON {target_upper} TO {user};"
        self._execute_sql(sql, dry_run=dry_run)

    def verify_user_exists(self, user: str) -> bool:
        """Verifica se usuário existe"""
        self.cur.execute("SELECT 1 FROM pg_user WHERE usename = %s;", (user,))
        exists = self.cur.fetchone() is not None

        if exists:
            self._log(f"Usuário '{user}' encontrado", 'SUCCESS')
        else:
            self._log(f"Usuário '{user}' NÃO EXISTE", 'ERROR')

        return exists

    def verify_ownership(self, database: str, expected_owner: str) -> Dict:
        """Verifica ownership das tabelas"""
        self.cur.execute("""
            SELECT tableowner, COUNT(*) as count
            FROM pg_tables
            WHERE schemaname = 'public'
            GROUP BY tableowner;
        """)

        results = {}
        for owner, count in self.cur.fetchall():
            results[owner] = count

        self._log(f"Ownership verificado: {results}")

        if expected_owner in results:
            self._log(
                f"Owner '{expected_owner}' possui {results[expected_owner]} tabelas", 'SUCCESS')
        else:
            self._log(
                f"Owner '{expected_owner}' não possui tabelas", 'WARNING')

        return results

    def verify_privileges(self, schema: str, user: str) -> int:
        """Verifica privilégios do usuário"""
        self.cur.execute("""
            SELECT COUNT(DISTINCT table_name)
            FROM information_schema.table_privileges
            WHERE table_schema = %s
            AND grantee = %s;
        """, (schema, user))

        count = self.cur.fetchone()[0]
        self._log(f"Usuário '{user}' tem privilégios em {count} tabelas",
                  'SUCCESS' if count > 0 else 'WARNING')

        return count

    def process_database(self, database_config: Dict, dry_run: bool = False):
        """Processa todas as operações de um banco de dados"""
        db_name = database_config['name']
        owner = database_config['owner']

        print(f"\n{'='*80}")
        print(f"PROCESSANDO: {db_name} ({database_config['description']})")
        print(f"Owner esperado: {owner}")
        print(f"Modo: {'DRY-RUN' if dry_run else 'EXECUÇÃO'}")
        print(f"{'='*80}\n")

        # Conectar ao banco específico
        if not self.connect(db_name):
            return False

        # Verificar se usuário existe
        if self.config['verification']['enabled'] and 'user_exists' in self.config['verification']['checks']:
            if not self.verify_user_exists(owner):
                self._log(f"Abortando: usuário '{owner}' não existe", 'ERROR')
                return False

        # Processar operações
        success_count = 0
        total_ops = len(database_config['operations'])

        for idx, operation in enumerate(database_config['operations'], 1):
            op_type = operation['type']
            self._log(f"\n[{idx}/{total_ops}] Operação: {op_type}", 'INFO')

            try:
                if op_type == 'transfer_ownership':
                    target = operation['target']
                    from_user = operation.get('from_user', 'postgres')
                    to_user = operation['to_user']

                    if target == 'tables':
                        self.transfer_table_ownership(
                            db_name, from_user, to_user, dry_run)
                    elif target == 'sequences':
                        self.transfer_sequence_ownership(
                            db_name, from_user, to_user, dry_run)
                    elif target == 'views':
                        self.transfer_view_ownership(
                            db_name, from_user, to_user, dry_run)

                    success_count += 1

                elif op_type == 'grant_privileges':
                    target = operation['target']
                    user = operation['user']
                    privileges = operation['privileges']

                    if target == 'schema':
                        schema = operation['schema']
                        self.grant_schema_privileges(
                            schema, user, privileges, dry_run)
                    elif target == 'all_tables':
                        schema = operation['schema']
                        self.grant_all_tables_privileges(
                            schema, user, privileges, dry_run)
                    elif target == 'all_sequences':
                        schema = operation['schema']
                        self.grant_all_sequences_privileges(
                            schema, user, privileges, dry_run)

                    success_count += 1

                elif op_type == 'set_default_privileges':
                    schema = operation['schema']
                    target = operation['target']
                    user = operation['user']
                    privileges = operation['privileges']

                    self.set_default_privileges(
                        schema, target, user, privileges, dry_run)
                    success_count += 1

            except Exception as e:
                self._log(f"Erro na operação {op_type}: {e}", 'ERROR')

        # Verificações finais
        if self.config['verification']['enabled'] and not dry_run:
            print(f"\n{'─'*80}")
            print("VERIFICAÇÕES FINAIS:")
            print(f"{'─'*80}\n")

            if 'ownership' in self.config['verification']['checks']:
                self.verify_ownership(db_name, owner)

            if 'privileges' in self.config['verification']['checks']:
                self.verify_privileges('public', owner)

        self.disconnect()

        print(f"\n{'='*80}")
        print(f"RESULTADO: {success_count}/{total_ops} operações concluídas")
        print(f"{'='*80}\n")

        return success_count == total_ops


def main():
    parser = argparse.ArgumentParser(
        description='Correção automatizada de permissões PostgreSQL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Modo dry-run (sem executar)
  python3 fix_permissions.py --database metabase_db --dry-run

  # Executar correções
  python3 fix_permissions.py --database metabase_db --execute

  # Processar todos os bancos
  python3 fix_permissions.py --all --execute --verbose

  # Apenas verificar
  python3 fix_permissions.py --database n8n_db --verify
        """
    )

    parser.add_argument(
        '--database',
        type=str,
        help='Nome do banco de dados a processar'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Processar todos os bancos de dados'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular sem executar (padrão)'
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Executar as correções de fato'
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Apenas verificar permissões atuais'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Modo verboso (mais detalhes)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='fix_permissions/fix_permissions.json',
        help='Caminho para o arquivo de configuração JSON'
    )

    args = parser.parse_args()

    # Validações
    if not args.database and not args.all:
        parser.error("Especifique --database <nome> ou --all")

    if args.execute and args.dry_run:
        parser.error("Use --execute OU --dry-run, não ambos")

    # Modo padrão é dry-run
    dry_run = not args.execute

    try:
        # Inicializar fixer
        fixer = PermissionsFixer(args.config, verbose=args.verbose)

        print("\n" + "="*80)
        print("FIX PERMISSIONS - PostgreSQL Permission Fixer")
        print(f"Versão: {fixer.config.get('version', '1.0.0')}")
        print(f"Configuração: {args.config}")
        print(
            f"Modo: {'DRY-RUN (simulação)' if dry_run else 'EXECUÇÃO (real)'}")
        print("="*80 + "\n")

        if args.verify:
            # Apenas verificar
            print("Modo: VERIFICAÇÃO\n")
            if args.database:
                db_config = next(
                    (db for db in fixer.config['databases'] if db['name'] == args.database), None)
                if not db_config:
                    print(
                        f"✗ Banco de dados '{args.database}' não encontrado no config")
                    sys.exit(1)

                fixer.connect(db_config['name'])
                fixer.verify_user_exists(db_config['owner'])
                fixer.verify_ownership(db_config['name'], db_config['owner'])
                fixer.verify_privileges('public', db_config['owner'])
                fixer.disconnect()

        else:
            # Processar bancos
            if args.all:
                # Processar todos
                for db_config in fixer.config['databases']:
                    fixer.process_database(db_config, dry_run=dry_run)
            else:
                # Processar apenas o especificado
                db_config = next(
                    (db for db in fixer.config['databases'] if db['name'] == args.database), None)

                if not db_config:
                    print(
                        f"✗ Banco de dados '{args.database}' não encontrado no config")
                    print(f"\nBancos disponíveis:")
                    for db in fixer.config['databases']:
                        print(f"  - {db['name']} ({db['description']})")
                    sys.exit(1)

                fixer.process_database(db_config, dry_run=dry_run)

        print("\n✓ Processo concluído com sucesso!\n")
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n✗ Erro: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠ Processo interrompido pelo usuário\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
