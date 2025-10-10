#!/usr/bin/env python3
"""
Script de Validação de Grants - PostgreSQL Migration System
Coleta grants da origem e valida se foram aplicados corretamente no destino
"""

import json
from datetime import datetime

from sqlalchemy import create_engine, text

from components.config_normalizer import get_sqlalchemy_url


class GrantsValidator:
    """Validador de grants entre origem e destino."""

    def __init__(self):
        self.source_engine = None
        self.dest_engine = None

    def load_configs(self):
        """Carrega configurações de origem e destino."""
        try:
            with open('secrets/postgresql_source_config.json', 'r') as f:
                self.source_config = json.load(f)

            with open('secrets/postgresql_destination_config.json', 'r') as f:
                self.dest_config = json.load(f)

            # Criar engines
            source_url = get_sqlalchemy_url(self.source_config, database='postgres')
            dest_url = get_sqlalchemy_url(self.dest_config, database='postgres')

            self.source_engine = create_engine(source_url)
            self.dest_engine = create_engine(dest_url)

            print("✅ Configurações carregadas e engines criadas")
            return True

        except Exception as e:
            print(f"❌ Erro ao carregar configurações: {e}")
            return False

    def get_database_grants(self, engine, db_name):
        """Coleta grants específicos de um banco de dados usando query corrigida."""
        grants_query = text("""
            SELECT
                :db_name AS database_name,
                SPLIT_PART(acl_item::text, '=', 1) AS grantee,
                SPLIT_PART(SPLIT_PART(acl_item::text, '=', 2), '/', 1) AS privileges
            FROM (
                SELECT unnest(datacl) AS acl_item
                FROM pg_database
                WHERE datname = :db_name AND datacl IS NOT NULL
            ) AS acl_items
            WHERE acl_item::text != ''
        """)

        try:
            with engine.connect() as conn:
                result = conn.execute(grants_query, {"db_name": db_name})
                grants = []

                for row in result:
                    grantee = row.grantee if row.grantee else 'public'
                    privileges_code = row.privileges

                    # Decode PostgreSQL privilege codes
                    privileges = self.decode_privilege_codes(privileges_code)

                    grants.append({
                        'database': db_name,
                        'grantee': grantee,
                        'privileges': privileges,
                        'raw_privileges': privileges_code
                    })

                return grants

        except Exception as e:
            print(f"❌ Erro ao coletar grants do banco {db_name}: {e}")
            return []

    def decode_privilege_codes(self, codes):
        """Decodifica códigos de privilégios PostgreSQL."""
        privilege_map = {
            'c': 'CONNECT',
            'C': 'CREATE',
            'T': 'TEMPORARY',
            'a': 'INSERT',
            'r': 'SELECT',
            'w': 'UPDATE',
            'd': 'DELETE',
            'D': 'TRUNCATE',
            'x': 'REFERENCES',
            't': 'TRIGGER'
        }

        if 'CTc' in codes:
            return ['ALL']

        privileges = []
        for code in codes:
            if code in privilege_map:
                privileges.append(privilege_map[code])

        return privileges if privileges else ['CONNECT']

    def get_top_databases(self):
        """Obtém as primeiras 10 bases de dados de usuário."""
        databases_query = text("""
            SELECT datname
            FROM pg_database
            WHERE datname NOT IN ('template0', 'template1', 'postgres')
            ORDER BY datname
            LIMIT 10
        """)

        try:
            with self.source_engine.connect() as conn:
                result = conn.execute(databases_query)
                databases = [row.datname for row in result]
                return databases

        except Exception as e:
            print(f"❌ Erro ao buscar bases de dados: {e}")
            return []

    def validate_grants(self):
        """Valida grants entre origem e destino."""
        if not self.load_configs():
            return False

        print("🔍 VALIDAÇÃO DE GRANTS - PostgreSQL Migration")
        print("=" * 60)

        # Obter top 10 bases de dados
        databases = self.get_top_databases()
        print(f"📋 Bases de dados a validar: {len(databases)}")
        for i, db in enumerate(databases, 1):
            print(f"   {i}. {db}")

        validation_results = []

        print(f"\n🔍 Iniciando validação...")

        for db_name in databases:
            print(f"\n📊 Validando: {db_name}")

            # Coletar grants da origem
            source_grants = self.get_database_grants(self.source_engine, db_name)
            print(f"   📤 Origem: {len(source_grants)} grants encontrados")

            # Coletar grants do destino
            dest_grants = self.get_database_grants(self.dest_engine, db_name)
            print(f"   📥 Destino: {len(dest_grants)} grants encontrados")

            # Comparar grants
            comparison = self.compare_grants(db_name, source_grants, dest_grants)
            validation_results.append(comparison)

            # Mostrar resultado da comparação
            if comparison['status'] == 'match':
                print(f"   ✅ CONFORMIDADE: Grants coincidem")
            else:
                print(f"   ⚠️ DIVERGÊNCIA: {comparison['differences']} diferenças")
                for diff in comparison['details'][:3]:  # Mostrar apenas 3 primeiras
                    print(f"      - {diff}")

        # Gerar relatório final
        self.generate_validation_report(validation_results)

        return True

    def compare_grants(self, db_name, source_grants, dest_grants):
        """Compara grants entre origem e destino."""
        # Normalizar grants para comparação
        source_normalized = {}
        for grant in source_grants:
            key = f"{grant['grantee']}:{grant['database']}"
            source_normalized[key] = set(grant['privileges'])

        dest_normalized = {}
        for grant in dest_grants:
            key = f"{grant['grantee']}:{grant['database']}"
            dest_normalized[key] = set(grant['privileges'])

        # Encontrar diferenças
        differences = []
        all_keys = set(source_normalized.keys()) | set(dest_normalized.keys())

        for key in all_keys:
            source_privs = source_normalized.get(key, set())
            dest_privs = dest_normalized.get(key, set())

            if source_privs != dest_privs:
                grantee = key.split(':')[0]
                missing_in_dest = source_privs - dest_privs
                extra_in_dest = dest_privs - source_privs

                if missing_in_dest:
                    differences.append(f"Falta no destino: {grantee} -> {', '.join(missing_in_dest)}")
                if extra_in_dest:
                    differences.append(f"Extra no destino: {grantee} -> {', '.join(extra_in_dest)}")

        status = 'match' if len(differences) == 0 else 'divergent'

        return {
            'database': db_name,
            'status': status,
            'source_count': len(source_grants),
            'dest_count': len(dest_grants),
            'differences': len(differences),
            'details': differences
        }

    def generate_validation_report(self, results):
        """Gera relatório de validação."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"\n📋 RELATÓRIO FINAL DE VALIDAÇÃO")
        print("=" * 50)

        total_dbs = len(results)
        conformant_dbs = len([r for r in results if r['status'] == 'match'])
        divergent_dbs = total_dbs - conformant_dbs

        print(f"📊 Total de bases validadas: {total_dbs}")
        print(f"✅ Bases conformes: {conformant_dbs}")
        print(f"⚠️ Bases com divergências: {divergent_dbs}")
        print(f"📈 Taxa de conformidade: {(conformant_dbs/total_dbs)*100:.1f}%")

        print(f"\n📋 Detalhes por base:")
        for result in results:
            status_icon = "✅" if result['status'] == 'match' else "⚠️"
            print(f"   {status_icon} {result['database']}: "
                  f"{result['source_count']}→{result['dest_count']} grants, "
                  f"{result['differences']} diferenças")

        # Salvar relatório em arquivo
        report_data = {
            'timestamp': timestamp,
            'summary': {
                'total_databases': total_dbs,
                'conformant_databases': conformant_dbs,
                'divergent_databases': divergent_dbs,
                'conformity_rate': f"{(conformant_dbs/total_dbs)*100:.1f}%"
            },
            'results': results
        }

        report_path = f"core/reports/grants_validation_{timestamp}.json"
        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\n💾 Relatório salvo: {report_path}")
        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {e}")


def main():
    """Função principal."""
    validator = GrantsValidator()
    validator.validate_grants()


if __name__ == "__main__":
    main()
