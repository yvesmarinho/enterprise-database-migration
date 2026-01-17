#!/usr/bin/env python3
"""
FASE 1: EXTRAÇÃO COMPLETA DE DADOS DO WF004
Coleta usuários, bancos e grants em formato JSON
"""

import json
import sys
from datetime import datetime

from sqlalchemy import create_engine, text

sys.path.append('/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration')
from components.config_normalizer import get_sqlalchemy_url


class WF004DataExtractor:
    def __init__(self):
        self.source_engine = None
        self.extracted_data = {
            'extraction_timestamp': datetime.now().isoformat(),
            'source_server': 'wf004.vya.digital:5432',
            'users': [],
            'databases': [],
            'grants': {},
            'summary': {}
        }

    def connect_source(self):
        """Conecta ao servidor origem (wf004)."""
        try:
            with open('secrets/postgresql_source_config.json', 'r') as f:
                source_config = json.load(f)

            source_url = get_sqlalchemy_url(source_config, database='postgres')
            self.source_engine = create_engine(source_url)

            # Testar conexão
            with self.source_engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✅ Conectado ao wf004: {version}")

            return True

        except Exception as e:
            print(f"❌ Erro conectando ao wf004: {e}")
            return False

    def extract_users(self):
        """Extrai todos os usuários do wf004."""
        print("\n👥 EXTRAINDO USUÁRIOS...")

        users_query = text("""
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

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(users_query)

                for row in result:
                    user_data = {
                        'rolname': row.rolname,
                        'rolsuper': row.rolsuper,
                        'rolinherit': row.rolinherit,
                        'rolcreaterole': row.rolcreaterole,
                        'rolcreatedb': row.rolcreatedb,
                        'rolcanlogin': row.rolcanlogin,
                        'rolreplication': row.rolreplication,
                        'rolconnlimit': row.rolconnlimit,
                        'rolpassword': row.rolpassword,
                        'rolvaliduntil': row.rolvaliduntil.isoformat() if row.rolvaliduntil else None,
                        'oid': row.oid
                    }
                    self.extracted_data['users'].append(user_data)

                print(f"   ✅ {len(self.extracted_data['users'])} usuários extraídos")

        except Exception as e:
            print(f"   ❌ Erro extraindo usuários: {e}")

    def extract_databases(self):
        """Extrai todas as bases de dados do wf004."""
        print("\n🏗️ EXTRAINDO BASES DE DADOS...")

        databases_query = text("""
            SELECT
                d.datname,
                r.rolname as owner,
                d.encoding,
                d.datcollate,
                d.datctype,
                d.datconnlimit,
                d.datistemplate,
                pg_database_size(d.datname) as size_bytes,
                d.oid
            FROM pg_database d
            JOIN pg_roles r ON d.datdba = r.oid
            WHERE d.datallowconn = true
            ORDER BY d.datname
        """)

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(databases_query)

                for row in result:
                    db_data = {
                        'datname': row.datname,
                        'owner': row.owner,
                        'encoding': row.encoding,
                        'datcollate': row.datcollate,
                        'datctype': row.datctype,
                        'datconnlimit': row.datconnlimit,
                        'datistemplate': row.datistemplate,
                        'size_bytes': row.size_bytes,
                        'size_mb': round(row.size_bytes / (1024 * 1024), 2),
                        'oid': row.oid,
                        'is_system': row.datname in ['postgres', 'template0', 'template1'] or row.datistemplate
                    }
                    self.extracted_data['databases'].append(db_data)

                user_dbs = [db for db in self.extracted_data['databases'] if not db['is_system']]
                system_dbs = [db for db in self.extracted_data['databases'] if db['is_system']]

                print(f"   ✅ {len(self.extracted_data['databases'])} bases extraídas")
                print(f"      ├─ 👤 Bases de usuário: {len(user_dbs)}")
                print(f"      └─ ⚙️ Bases do sistema: {len(system_dbs)}")

        except Exception as e:
            print(f"   ❌ Erro extraindo bases: {e}")

    def extract_grants(self):
        """Extrai todos os grants usando query completa e confiável."""
        print("\n🔐 EXTRAINDO GRANTS...")

        # Query robusta para extrair TODOS os grants
        grants_query = text("""
            SELECT
                d.datname,
                CASE
                    WHEN split_part(aclitem::text, '=', 1) = '' THEN 'public'
                    ELSE split_part(aclitem::text, '=', 1)
                END as grantee,
                split_part(split_part(aclitem::text, '=', 2), '/', 1) as privileges,
                split_part(split_part(aclitem::text, '=', 2), '/', 2) as grantor
            FROM pg_database d, unnest(COALESCE(d.datacl, ARRAY[]::aclitem[])) as aclitem
            WHERE d.datname NOT LIKE 'template%'

            UNION ALL

            -- Adicionar owners implícitos quando não há ACL explícita
            SELECT
                d.datname,
                r.rolname as grantee,
                'CTc' as privileges,
                r.rolname as grantor
            FROM pg_database d
            JOIN pg_roles r ON d.datdba = r.oid
            WHERE d.datname NOT LIKE 'template%'
              AND (d.datacl IS NULL OR NOT EXISTS (
                  SELECT 1 FROM unnest(d.datacl) as acl
                  WHERE split_part(acl::text, '=', 1) = r.rolname
              ))

            ORDER BY datname, grantee
        """)

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(grants_query)

                for row in result:
                    db_name = row.datname
                    grantee = row.grantee
                    priv_codes = row.privileges
                    grantor = row.grantor

                    # Inicializar grants do banco se não existe
                    if db_name not in self.extracted_data['grants']:
                        self.extracted_data['grants'][db_name] = []

                    # Decodificar privilégios
                    decoded_privileges = self.decode_privileges(priv_codes)

                    grant_entry = {
                        'grantee': grantee,
                        'privileges': decoded_privileges,
                        'privilege_codes': priv_codes,
                        'grantor': grantor,
                        'is_owner': grantor == grantee and priv_codes == 'CTc'
                    }

                    self.extracted_data['grants'][db_name].append(grant_entry)

                total_grants = sum(len(grants) for grants in self.extracted_data['grants'].values())
                print(f"   ✅ {total_grants} grants extraídos de {len(self.extracted_data['grants'])} bases")

        except Exception as e:
            print(f"   ❌ Erro extraindo grants: {e}")

    def decode_privileges(self, codes):
        """Decodifica códigos de privilégios PostgreSQL."""
        if not codes:
            return []

        # Se tem todos os códigos principais, é ALL
        if codes == 'CTc':
            return ['ALL']

        privileges = []
        if 'C' in codes:  # CONNECT
            privileges.append('CONNECT')
        if 'T' in codes:  # TEMPORARY
            privileges.append('TEMPORARY')
        if 'c' in codes:  # CREATE
            privileges.append('CREATE')

        return privileges if privileges else ['CONNECT']

    def generate_summary(self):
        """Gera resumo dos dados extraídos."""
        users = self.extracted_data['users']
        databases = self.extracted_data['databases']
        grants = self.extracted_data['grants']

        user_dbs = [db for db in databases if not db['is_system']]
        system_dbs = [db for db in databases if db['is_system']]

        total_grants = sum(len(db_grants) for db_grants in grants.values())

        self.extracted_data['summary'] = {
            'total_users': len(users),
            'total_databases': len(databases),
            'user_databases': len(user_dbs),
            'system_databases': len(system_dbs),
            'total_grants': total_grants,
            'databases_with_grants': len(grants),
            'largest_db': max(user_dbs, key=lambda x: x['size_bytes']) if user_dbs else None,
            'total_size_gb': round(sum(db['size_bytes'] for db in databases) / (1024**3), 2)
        }

    def save_to_json(self, filename=None):
        """Salva dados extraídos em JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extracted_data_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Dados salvos em: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Erro salvando JSON: {e}")
            return None

    def run_extraction(self):
        """Executa extração completa."""
        print("🔍 INICIANDO EXTRAÇÃO COMPLETA DO WF004")
        print("=" * 50)

        if not self.connect_source():
            return False

        self.extract_users()
        self.extract_databases()
        self.extract_grants()
        self.generate_summary()

        # Mostrar resumo
        summary = self.extracted_data['summary']
        print(f"\n📊 RESUMO DA EXTRAÇÃO:")
        print(f"   👥 Usuários: {summary['total_users']}")
        print(f"   🏗️ Bases total: {summary['total_databases']}")
        print(f"      ├─ 👤 Bases usuário: {summary['user_databases']}")
        print(f"      └─ ⚙️ Bases sistema: {summary['system_databases']}")
        print(f"   🔐 Total de grants: {summary['total_grants']}")
        print(f"   💾 Tamanho total: {summary['total_size_gb']} GB")

        if summary['largest_db']:
            largest = summary['largest_db']
            print(f"   📈 Maior base: {largest['datname']} ({largest['size_mb']} MB)")

        filename = self.save_to_json()

        if filename:
            print(f"\n✅ EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
            print(f"📁 Arquivo: {filename}")
            return filename
        else:
            print(f"\n❌ EXTRAÇÃO FALHOU")
            return None


if __name__ == "__main__":
    extractor = WF004DataExtractor()
    result = extractor.run_extraction()

    if result:
        print(f"\n🎯 PRÓXIMO PASSO: Gerar scripts SQL baseados em {result}")
    else:
        print(f"\n❌ Falha na extração - verificar logs")
