#!/usr/bin/env python3
"""
Debug Script para Investigar Problema de Privilégios - Fase 3
============================================================

Baseado na análise do pgAdmin4, este script investiga por que a verificação
de usuários existentes está falhando durante a aplicação de privilégios.

Análise pgAdmin4 descobriu:
- Verificação via: SELECT rolname FROM pg_roles
- Apply via: conn.execute_dict(sql_data)
- Templates SQL para GRANT statements
- Status/success flags para tratamento de erros

Investigará:
1. Conexão com servidor destino
2. Lista real de usuários no destino
3. Timing entre Fase 1 (criação) e Fase 3 (verificação)
4. Diferenças entre engines/conexões usadas
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text


class PrivilegeDebugger:
    def __init__(self):
        self.source_engine = None
        self.dest_engine = None
        self.source_config = None
        self.dest_config = None
        self.debug_log = []

    def log(self, message, level="INFO"):
        """Log com timestamp para debug."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"{timestamp} | {level:5s} | {message}"
        print(log_entry)
        self.debug_log.append(log_entry)

    def load_configs(self):
        """Carrega configurações do sistema."""
        try:
            # Usar paths relativos baseados na estrutura do projeto
            base_path = Path(__file__).parent

            source_path = base_path / "secrets" / "postgresql_source_config.json"
            dest_path = base_path / "secrets" / "postgresql_destination_config.json"

            if not source_path.exists():
                self.log(f"❌ Arquivo não encontrado: {source_path}", "ERROR")
                return False

            if not dest_path.exists():
                self.log(f"❌ Arquivo não encontrado: {dest_path}", "ERROR")
                return False

            with open(source_path, 'r', encoding='utf-8') as f:
                self.source_config = json.load(f)

            with open(dest_path, 'r', encoding='utf-8') as f:
                self.dest_config = json.load(f)

            self.log("✅ Configurações carregadas com sucesso")
            return True

        except Exception as e:
            self.log(f"❌ Erro ao carregar configurações: {e}", "ERROR")
            return False

    def create_engines(self):
        """Cria engines usando a mesma lógica do sistema principal."""
        try:
            # Criar URLs de conexão (similar ao get_sqlalchemy_url)
            def build_url(config):
                server = config.get('server', {})
                auth = config.get('authentication', {})

                host = server.get('host', 'localhost')
                port = server.get('port', 5432)
                database = server.get('database', 'postgres')
                user = auth.get('user', 'postgres')
                password = auth.get('password', '')

                return f"postgresql://{user}:{password}@{host}:{port}/{database}"

            # Engine origem
            source_url = build_url(self.source_config)
            self.source_engine = create_engine(
                source_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                echo=False
            )

            # Engine destino
            dest_url = build_url(self.dest_config)
            self.dest_engine = create_engine(
                dest_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                echo=False
            )

            # Testar conexões
            with self.source_engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                self.log(f"✅ Conexão origem OK: {version[:50]}...")

            with self.dest_engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                self.log(f"✅ Conexão destino OK: {version[:50]}...")

            return True

        except Exception as e:
            self.log(f"❌ Erro ao criar engines: {e}", "ERROR")
            return False

    def get_users_with_method(self, engine, method_name):
        """Busca usuários usando diferentes métodos para comparação."""
        try:
            with engine.connect() as conn:
                if method_name == "pg_roles":
                    # Método atual do sistema
                    result = conn.execute(text("SELECT rolname FROM pg_roles ORDER BY rolname"))
                    users = {row.rolname for row in result}

                elif method_name == "pg_roles_detailed":
                    # Método detalhado similar ao pgAdmin4
                    result = conn.execute(text("""
                        SELECT rolname, rolcanlogin, rolsuper, rolcreaterole, rolcreatedb
                        FROM pg_roles
                        ORDER BY rolname
                    """))
                    users = {row.rolname for row in result if row.rolcanlogin or row.rolsuper}

                elif method_name == "pg_user":
                    # Método alternativo (apenas usuários de login)
                    result = conn.execute(text("SELECT usename FROM pg_user ORDER BY usename"))
                    users = {row.usename for row in result}

                elif method_name == "information_schema":
                    # Método via information_schema
                    result = conn.execute(text("""
                        SELECT grantee FROM information_schema.applicable_roles
                        WHERE grantee != 'PUBLIC'
                        GROUP BY grantee
                        ORDER BY grantee
                    """))
                    users = {row.grantee for row in result}

                return users

        except Exception as e:
            self.log(f"❌ Erro no método {method_name}: {e}", "ERROR")
            return set()

    def compare_user_lists(self):
        """Compara listas de usuários entre origem e destino usando diferentes métodos."""
        self.log("🔍 === COMPARANDO LISTAS DE USUÁRIOS ===")

        methods = [
            "pg_roles",
            "pg_roles_detailed",
            "pg_user",
            "information_schema"
        ]

        for method in methods:
            self.log(f"\n📋 Método: {method}")

            source_users = self.get_users_with_method(self.source_engine, method)
            dest_users = self.get_users_with_method(self.dest_engine, method)

            self.log(f"   📤 Origem: {len(source_users)} usuários")
            self.log(f"   📥 Destino: {len(dest_users)} usuários")

            # Usuários apenas na origem
            only_source = source_users - dest_users
            if only_source:
                self.log(f"   ⚠️  Apenas na origem ({len(only_source)}): {', '.join(sorted(list(only_source)))}")

            # Usuários apenas no destino
            only_dest = dest_users - source_users
            if only_dest:
                self.log(f"   ✅ Apenas no destino ({len(only_dest)}): {', '.join(sorted(list(only_dest)))}")

            # Usuários comuns
            common = source_users & dest_users
            self.log(f"   🔗 Comuns ({len(common)}): {len(list(common))} usuários")

    def test_user_verification_timing(self):
        """Testa timing entre criação e verificação de usuários."""
        self.log("\n🕐 === TESTE DE TIMING DE VERIFICAÇÃO ===")

        test_user = f"test_debug_user_{datetime.now().strftime('%H%M%S')}"

        try:
            # 1. Verificar se usuário NÃO existe
            with self.dest_engine.connect() as conn:
                result = conn.execute(text("SELECT rolname FROM pg_roles WHERE rolname = :username"),
                                    {"username": test_user})
                exists_before = result.fetchone() is not None
                self.log(f"   📍 Usuário {test_user} existe ANTES: {exists_before}")

            # 2. Criar usuário
            with self.dest_engine.connect() as conn:
                conn = conn.execution_options(autocommit=True)
                conn.execute(text(f'CREATE USER "{test_user}"'))
                self.log(f"   ✅ Usuário {test_user} criado")

            # 3. Verificar IMEDIATAMENTE após criação (sem nova conexão)
            with self.dest_engine.connect() as conn:
                result = conn.execute(text("SELECT rolname FROM pg_roles WHERE rolname = :username"),
                                    {"username": test_user})
                exists_immediate = result.fetchone() is not None
                self.log(f"   📍 Usuário existe IMEDIATAMENTE: {exists_immediate}")

            # 4. Verificar com nova conexão (simulando Fase 3)
            with self.dest_engine.connect() as conn:
                result = conn.execute(text("SELECT rolname FROM pg_roles WHERE rolname = :username"),
                                    {"username": test_user})
                exists_new_conn = result.fetchone() is not None
                self.log(f"   📍 Usuário existe com NOVA CONEXÃO: {exists_new_conn}")

            # 5. Buscar na lista geral (método usado pelo sistema)
            with self.dest_engine.connect() as conn:
                result = conn.execute(text("SELECT rolname FROM pg_roles"))
                all_users = {row.rolname for row in result}
                exists_in_list = test_user in all_users
                self.log(f"   📍 Usuário na LISTA GERAL: {exists_in_list}")

            # 6. Cleanup
            with self.dest_engine.connect() as conn:
                conn = conn.execution_options(autocommit=True)
                conn.execute(text(f'DROP USER "{test_user}"'))
                self.log(f"   🗑️ Usuário {test_user} removido")

        except Exception as e:
            self.log(f"❌ Erro no teste de timing: {e}", "ERROR")

    def test_privilege_application(self):
        """Testa aplicação de privilégios simulando o sistema real."""
        self.log("\n🔐 === TESTE DE APLICAÇÃO DE PRIVILÉGIOS ===")

        test_user = f"test_priv_user_{datetime.now().strftime('%H%M%S')}"
        test_db = "postgres"  # Usar banco que já existe

        try:
            # 1. Criar usuário de teste
            with self.dest_engine.connect() as conn:
                conn = conn.execution_options(autocommit=True)
                conn.execute(text(f'CREATE USER "{test_user}"'))
                self.log(f"   ✅ Usuário {test_user} criado")

            # 2. Buscar usuários existentes (método do sistema)
            with self.dest_engine.connect() as conn:
                result = conn.execute(text("SELECT rolname FROM pg_roles"))
                existing_users = {row.rolname for row in result}
                user_exists = test_user in existing_users
                self.log(f"   📍 Usuário encontrado na verificação: {user_exists}")

            # 3. Tentar aplicar privilégio (método do sistema)
            if user_exists:
                try:
                    with self.dest_engine.connect() as conn:
                        conn = conn.execution_options(autocommit=True)
                        grant_sql = text(f'GRANT CONNECT ON DATABASE "{test_db}" TO "{test_user}"')
                        conn.execute(grant_sql)
                        self.log(f"   ✅ Privilégio CONNECT aplicado com sucesso")

                        # Verificar se privilégio foi aplicado
                        check_sql = text("""
                            SELECT has_database_privilege(:username, :dbname, 'CONNECT') as has_connect
                        """)
                        result = conn.execute(check_sql, {"username": test_user, "dbname": test_db})
                        has_privilege = result.scalar()
                        self.log(f"   📍 Privilégio verificado: {has_privilege}")

                except Exception as e:
                    self.log(f"   ❌ Erro ao aplicar privilégio: {e}", "ERROR")
            else:
                self.log(f"   ⚠️ Usuário não encontrado - não foi possível aplicar privilégio")

            # 4. Cleanup
            with self.dest_engine.connect() as conn:
                conn = conn.execution_options(autocommit=True)
                conn.execute(text(f'DROP USER "{test_user}"'))
                self.log(f"   🗑️ Usuário {test_user} removido")

        except Exception as e:
            self.log(f"❌ Erro no teste de privilégios: {e}", "ERROR")

    def analyze_migration_state(self):
        """Analisa o estado atual da migração."""
        self.log("\n🔍 === ANÁLISE DO ESTADO DA MIGRAÇÃO ===")

        try:
            # Contar usuários por tipo no destino
            with self.dest_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN rolsuper THEN 1 END) as superusers,
                        COUNT(CASE WHEN rolcanlogin AND NOT rolsuper THEN 1 END) as regular_users,
                        COUNT(CASE WHEN NOT rolcanlogin AND NOT rolsuper THEN 1 END) as role_only
                    FROM pg_roles
                """))
                stats = result.fetchone()

                self.log(f"   📊 Total de usuários: {stats.total_users}")
                self.log(f"   👑 Superusuários: {stats.superusers}")
                self.log(f"   👤 Usuários regulares: {stats.regular_users}")
                self.log(f"   🏷️ Apenas roles: {stats.role_only}")

            # Buscar usuários criados recentemente (possível indicação de migração)
            with self.dest_engine.connect() as conn:
                # Listar usuários não-sistema
                result = conn.execute(text("""
                    SELECT rolname, rolcanlogin, rolsuper
                    FROM pg_roles
                    WHERE rolname NOT IN ('postgres', 'pg_signal_backend', 'pg_read_server_files',
                                         'pg_write_server_files', 'pg_execute_server_program',
                                         'pg_read_all_settings', 'pg_read_all_stats', 'pg_stat_scan_tables',
                                         'pg_monitor', 'pg_database_owner', 'pg_checkpoint')
                    AND rolname NOT LIKE 'pg_%'
                    ORDER BY rolname
                """))

                user_list = result.fetchall()
                self.log(f"   👥 Usuários não-sistema encontrados ({len(user_list)}):")
                for user in user_list:
                    login_status = "LOGIN" if user.rolcanlogin else "NOLOGIN"
                    super_status = "SUPER" if user.rolsuper else "REGULAR"
                    self.log(f"      - {user.rolname} ({login_status}, {super_status})")

        except Exception as e:
            self.log(f"❌ Erro na análise do estado: {e}", "ERROR")

    def save_debug_report(self):
        """Salva relatório completo de debug."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"debug_privileges_report_{timestamp}.log"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("RELATÓRIO DE DEBUG - PROBLEMA DE PRIVILÉGIOS FASE 3\n")
                f.write("=" * 80 + "\n")
                f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Sistema: PostgreSQL Migration Orchestrator v3.0.0\n")
                f.write("=" * 80 + "\n\n")

                for log_entry in self.debug_log:
                    f.write(log_entry + "\n")

            self.log(f"📄 Relatório salvo: {report_file}")
            return report_file

        except Exception as e:
            self.log(f"❌ Erro ao salvar relatório: {e}", "ERROR")
            return None

    def run_full_diagnosis(self):
        """Executa diagnóstico completo."""
        self.log("🚀 INICIANDO DIAGNÓSTICO COMPLETO DO PROBLEMA DE PRIVILÉGIOS")
        self.log("=" * 80)

        if not self.load_configs():
            return False

        if not self.create_engines():
            return False

        # Executar todas as análises
        self.compare_user_lists()
        self.test_user_verification_timing()
        self.test_privilege_application()
        self.analyze_migration_state()

        # Salvar relatório
        report_file = self.save_debug_report()

        self.log("\n🎯 === DIAGNÓSTICO CONCLUÍDO ===")
        if report_file:
            self.log(f"📄 Relatório completo disponível em: {report_file}")

        return True


if __name__ == "__main__":
    debugger = PrivilegeDebugger()
    success = debugger.run_full_diagnosis()

    if not success:
        sys.exit(1)

    print(f"\n✅ Debug concluído. Execute o arquivo de log gerado para ver detalhes completos.")
