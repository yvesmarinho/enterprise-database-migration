"""
Módulo de Extração de Dados WF004
Extraí usuários, bases de dados e grants do servidor PostgreSQL origem
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2


class WF004DataExtractor:
    """Extrator de dados do servidor PostgreSQL WF004."""

    def __init__(self, config_file: str = "secrets/postgresql_source_config.json"):
        """
        Inicializa o extrator de dados.

        Args:
            config_file: Caminho para arquivo de configuração do servidor origem
        """
        self.config_file = config_file
        self.config = None
        self.connection = None
        self.extracted_data = {
            'extraction_info': {
                'timestamp': None,
                'source_server': None,
                'extractor_version': '4.0.0'
            },
            'users': [],
            'databases': [],
            'grants': {},
            'summary': {}
        }

    def load_config(self) -> bool:
        """Carrega configuração do servidor origem."""
        try:
            with open(self.config_file, 'r') as f:
                raw_config = json.load(f)

            # Extrair dados da estrutura aninhada
            self.config = {
                'host': raw_config['server']['host'],
                'port': raw_config['server']['port'],
                'user': raw_config['authentication']['user'],
                'password': raw_config['authentication']['password']
            }

            print(f"✅ Configuração carregada: {self.config['host']}:{self.config['port']}")
            return True

        except Exception as e:
            print(f"❌ Erro carregando configuração: {e}")
            return False

    def connect_to_source(self) -> bool:
        """Conecta ao servidor de origem."""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database='postgres',
                user=self.config['user'],
                password=self.config['password']
            )

            print(f"✅ Conectado ao {self.config['host']}:{self.config['port']}")

            # Verificar versão e configurar extraction_info
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                print(f"   📊 Versão: {version.split(',')[0]}")

                self.extracted_data['extraction_info']['source_server'] = f"{self.config['host']}:{self.config['port']}"
                self.extracted_data['extraction_info']['timestamp'] = datetime.now().isoformat()

            return True

        except Exception as e:
            print(f"❌ Erro conectando: {e}")
            return False

    def extract_users(self) -> bool:
        """Extrai usuários do servidor."""
        try:
            print("\n👥 Extraindo usuários...")

            query = """
                SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb,
                       rolcanlogin, rolreplication, rolconnlimit, rolpassword,
                       rolvaliduntil
                FROM pg_roles
                WHERE rolname NOT LIKE 'pg_%'
                ORDER BY rolname
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                users_data = cursor.fetchall()

                for user_row in users_data:
                    user_info = {
                        'rolname': user_row[0],
                        'rolsuper': user_row[1],
                        'rolinherit': user_row[2],
                        'rolcreaterole': user_row[3],
                        'rolcreatedb': user_row[4],
                        'rolcanlogin': user_row[5],
                        'rolreplication': user_row[6],
                        'rolconnlimit': user_row[7],
                        'rolpassword': user_row[8],
                        'rolvaliduntil': user_row[9].isoformat() if user_row[9] else None
                    }

                    self.extracted_data['users'].append(user_info)

                print(f"   ✅ {len(self.extracted_data['users'])} usuários extraídos")
                return True

        except Exception as e:
            print(f"❌ Erro extraindo usuários: {e}")
            return False

    def extract_databases(self) -> bool:
        """Extrai bases de dados do servidor."""
        try:
            print("\n🏗️ Extraindo bases de dados...")

            query = """
                SELECT d.datname, d.datdba, r.rolname as owner,
                       d.encoding, d.datcollate, d.datctype, d.datconnlimit,
                       pg_database_size(d.datname) / (1024*1024) as size_mb
                FROM pg_database d
                JOIN pg_roles r ON d.datdba = r.oid
                ORDER BY d.datname
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                databases_data = cursor.fetchall()

                system_databases = ['postgres', 'template0', 'template1']
                user_db_count = 0

                for db_row in databases_data:
                    is_system = db_row[0] in system_databases
                    if not is_system:
                        user_db_count += 1

                    db_info = {
                        'datname': db_row[0],
                        'datdba': db_row[1],
                        'owner': db_row[2],
                        'encoding': db_row[3],
                        'datcollate': db_row[4],
                        'datctype': db_row[5],
                        'datconnlimit': db_row[6],
                        'size_mb': float(db_row[7]),
                        'is_system': is_system
                    }

                    self.extracted_data['databases'].append(db_info)

                print(f"   ✅ {len(self.extracted_data['databases'])} bases extraídas ({user_db_count} de usuário)")
                return True

        except Exception as e:
            print(f"❌ Erro extraindo bases: {e}")
            # Fazer rollback da transação para permitir outras queries
            try:
                if self.connection:
                    self.connection.rollback()
            except Exception:
                pass
            return False

    def extract_grants(self) -> bool:
        """Extrai grants das bases de dados."""
        try:
            print("\n🔐 Extraindo grants...")

            query = """
                SELECT d.datname,
                       grantee::regrole::text AS grantee,
                       privilege_type
                FROM pg_database d,
                     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
                WHERE d.datname NOT IN ('postgres', 'template0', 'template1')
                  AND grantee::regrole::text != '-'
                  AND grantee::regrole::text IS NOT NULL
                ORDER BY d.datname, grantee::regrole::text, privilege_type
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                grants_data = cursor.fetchall()

                # Organizar grants por base de dados
                for grant_row in grants_data:
                    db_name, grantee, privilege = grant_row

                    if db_name not in self.extracted_data['grants']:
                        self.extracted_data['grants'][db_name] = []

                    # Procurar grant existente para o grantee
                    existing_grant = None
                    for grant in self.extracted_data['grants'][db_name]:
                        if grant['grantee'] == grantee:
                            existing_grant = grant
                            break

                    if existing_grant:
                        existing_grant['privileges'].append(privilege)
                    else:
                        self.extracted_data['grants'][db_name].append({
                            'grantee': grantee,
                            'privileges': [privilege]
                        })

                total_grants = sum(
                    len(grants) for grants in self.extracted_data['grants'].values()
                )

                print(f"   ✅ {total_grants} grants extraídos para {len(self.extracted_data['grants'])} bases")
                return True

        except Exception as e:
            print(f"❌ Erro extraindo grants: {e}")
            return False

    def generate_summary(self) -> None:
        """Gera resumo dos dados extraídos."""
        user_databases = len([db for db in self.extracted_data['databases'] if not db['is_system']])
        total_grants = sum(len(grants) for grants in self.extracted_data['grants'].values())

        self.extracted_data['summary'] = {
            'total_users': len(self.extracted_data['users']),
            'total_databases': len(self.extracted_data['databases']),
            'user_databases': user_databases,
            'system_databases': len(self.extracted_data['databases']) - user_databases,
            'total_grants': total_grants,
            'databases_with_grants': len(self.extracted_data['grants'])
        }

    def save_to_json(self, output_file: Optional[str] = None) -> str:
        """Salva dados extraídos em arquivo JSON."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"extracted_data_{timestamp}.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Dados salvos: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ Erro salvando arquivo: {e}")
            return ""

    def run_extraction(self, output_file: Optional[str] = None) -> str:
        """Executa extração completa de dados."""
        print("🚀 INICIANDO EXTRAÇÃO DE DADOS WF004")
        print("=" * 50)

        if not self.load_config():
            return ""

        if not self.connect_to_source():
            return ""

        success = True
        success &= self.extract_users()
        success &= self.extract_databases()
        success &= self.extract_grants()

        if success:
            self.generate_summary()
            output_path = self.save_to_json(output_file)

            summary = self.extracted_data['summary']
            print(f"\n✅ EXTRAÇÃO CONCLUÍDA!")
            print(f"   👥 {summary['total_users']} usuários")
            print(f"   🏗️ {summary['user_databases']} bases de usuário")
            print(f"   🔐 {summary['total_grants']} grants")

            return output_path
        else:
            print(f"\n❌ EXTRAÇÃO FALHOU!")
            return ""

    def close_connection(self) -> None:
        """Fecha conexão com servidor."""
        if self.connection:
            self.connection.close()
            print("🔌 Conexão fechada")


if __name__ == "__main__":
    import sys

    extractor = WF004DataExtractor()

    try:
        output_file = sys.argv[1] if len(sys.argv) > 1 else None
        result = extractor.run_extraction(output_file)

        if result:
            print(f"\n🎯 Arquivo gerado: {result}")
            sys.exit(0)
        else:
            sys.exit(1)

    finally:
        extractor.close_connection()
