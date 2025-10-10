#!/usr/bin/env python3
"""
PostgreSQL User Discovery Tool
==============================

Script para descobrir usuários existentes nos servidores PostgreSQL
e sugerir credenciais alternativas para migração.

Testa diferentes combinações de usuários comuns:
- postgres (superuser padrão)
- migration_user (usuário configurado)
- enterprise_user (usuário do projeto)
- admin, root, etc.

Uso:
    python3 discover_users.py [--server wf004|wfdb02|both]
"""

import json
import psycopg2
import sys
from datetime import datetime

def load_configs():
    """Carrega configurações de ambos os servidores."""
    try:
        from components.config_manager import get_db_config_path
        source_config_path = get_db_config_path('postgresql_source_config')
        dest_config_path = get_db_config_path('postgresql_destination_config')
        with open(source_config_path, 'r', encoding='utf-8') as f:
            source = json.load(f)
        with open(dest_config_path, 'r', encoding='utf-8') as f:
            destination = json.load(f)
        return source, destination
    except Exception as e:
        print(f"❌ Erro ao carregar configurações: {e}")
        return None, None

def test_user_combinations(host, port, ssl_mode, target_users=None):
    """Testa diferentes combinações de usuário/senha."""
    print(f"\n🔍 Descobrindo usuários em {host}:{port}...")

    # Usuários comuns para testar
    common_users = [
        ("postgres", "postgres"),
        ("postgres", ""),
        ("postgres", "admin"),
        ("postgres", "password"),
        ("migration_user", "-5FRifRucho3wudu&re2opafa+tuFr8#"),
        ("enterprise_user", "enterprise_pass123!"),
        ("admin", "admin"),
        ("root", "root"),
        ("user", "user"),
    ]

    # Se usuários específicos foram fornecidos, testar esses também
    if target_users:
        for user in target_users:
            common_users.append((user, ""))
            common_users.append((user, user))
            common_users.append((user, "password"))

    successful_connections = []

    for username, password in common_users:
        try:
            conn_string = (
                f"host={host} "
                f"port={port} "
                f"dbname=postgres "
                f"user={username} "
                f"password={password} "
                f"sslmode={ssl_mode} "
                f"connect_timeout=10"
            )

            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()

            # Obter informações do usuário
            cursor.execute("""
                SELECT
                    current_user,
                    session_user,
                    version(),
                    current_database()
            """)
            current_user, session_user, version, database = cursor.fetchone()

            # Obter privilégios
            cursor.execute("""
                SELECT rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
                FROM pg_roles
                WHERE rolname = current_user
            """)
            privileges = cursor.fetchone()

            success_info = {
                'username': username,
                'password': password,
                'current_user': current_user,
                'session_user': session_user,
                'version': version.split()[1] if version else 'Unknown',
                'database': database,
                'is_superuser': privileges[0] if privileges else False,
                'can_create_role': privileges[1] if privileges else False,
                'can_create_db': privileges[2] if privileges else False,
                'can_login': privileges[3] if privileges else False
            }

            successful_connections.append(success_info)

            print(f"   ✅ {username} - Conectado como: {current_user}")
            if privileges and privileges[0]:  # is superuser
                print(f"      🔑 SUPERUSER - Todos os privilégios")
            elif privileges and privileges[2]:  # can create db
                print(f"      🔑 CREATEDB - Pode criar bancos")
            else:
                print(f"      ⚠️ Privilégios limitados")

            cursor.close()
            conn.close()

        except psycopg2.OperationalError as e:
            # Não mostrar erros de autenticação (esperado)
            if "authentication failed" not in str(e) and "does not exist" not in str(e):
                print(f"   ❌ {username}: {e}")
        except Exception as e:
            print(f"   ❓ {username}: Erro inesperado - {e}")

    return successful_connections

def list_existing_users(host, port, ssl_mode, username, password):
    """Lista usuários existentes no servidor."""
    try:
        conn_string = (
            f"host={host} "
            f"port={port} "
            f"dbname=postgres "
            f"user={username} "
            f"password={password} "
            f"sslmode={ssl_mode} "
            f"connect_timeout=10"
        )

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                rolname,
                rolsuper,
                rolcreaterole,
                rolcreatedb,
                rolcanlogin,
                rolreplication
            FROM pg_roles
            WHERE rolname NOT LIKE 'pg_%'
            ORDER BY rolname
        """)

        users = cursor.fetchall()

        print(f"\n👥 Usuários existentes em {host}:")
        for user_info in users:
            name, is_super, can_create_role, can_create_db, can_login, can_replicate = user_info

            status = "ATIVO" if can_login else "INATIVO"
            privileges = []
            if is_super: privileges.append("SUPER")
            if can_create_role: privileges.append("CREATEROLE")
            if can_create_db: privileges.append("CREATEDB")
            if can_replicate: privileges.append("REPLICATION")

            privs_str = ", ".join(privileges) if privileges else "Nenhum"
            print(f"   - {name} ({status}) - {privs_str}")

        cursor.close()
        conn.close()

        return users

    except Exception as e:
        print(f"   ❌ Erro ao listar usuários: {e}")
        return []

def suggest_migration_credentials(wf004_users, wfdb02_users):
    """Sugere credenciais para migração baseado nos usuários encontrados."""
    print("\n" + "="*80)
    print("💡 SUGESTÕES PARA CREDENCIAIS DE MIGRAÇÃO")
    print("="*80)

    # Encontrar usuários em comum com privilégios adequados
    wf004_suitable = []
    wfdb02_suitable = []

    for user in wf004_users:
        if user['can_create_db'] or user['is_superuser']:
            wf004_suitable.append(user)

    for user in wfdb02_users:
        if user['can_create_db'] or user['is_superuser']:
            wfdb02_suitable.append(user)

    print("🎯 Usuários adequados para migração:")
    print("\nServidor wf004:")
    for user in wf004_suitable:
        privs = "SUPERUSER" if user['is_superuser'] else "CREATEDB"
        print(f"   ✅ {user['username']} ({privs})")

    print("\nServidor wfdb02:")
    for user in wfdb02_suitable:
        privs = "SUPERUSER" if user['is_superuser'] else "CREATEDB"
        print(f"   ✅ {user['username']} ({privs})")

    # Encontrar match exato
    print("\n🔗 Credenciais matching (mesmo usuário em ambos servidores):")
    matches_found = False

    for wf004_user in wf004_suitable:
        for wfdb02_user in wfdb02_suitable:
            if (wf004_user['username'] == wfdb02_user['username'] and
                wf004_user['password'] == wfdb02_user['password']):
                matches_found = True
                print(f"   🎉 PERFEITO: {wf004_user['username']}")
                print(f"      Senha: {'*' * len(wf004_user['password'])}")
                print(f"      wf004: {wf004_user['current_user']} ({'SUPER' if wf004_user['is_superuser'] else 'CREATEDB'})")
                print(f"      wfdb02: {wfdb02_user['current_user']} ({'SUPER' if wfdb02_user['is_superuser'] else 'CREATEDB'})")

    if not matches_found:
        print("   ⚠️ Nenhum usuário matching encontrado")
        print("\n🔧 RECOMENDAÇÕES:")
        if wf004_suitable:
            best_wf004 = wf004_suitable[0]
            print(f"   1. Usar {best_wf004['username']} para wf004")
            print(f"      Senha testada: {'*' * len(best_wf004['password'])}")

        if wfdb02_suitable:
            best_wfdb02 = wfdb02_suitable[0]
            print(f"   2. Usar {best_wfdb02['username']} para wfdb02")
            print(f"      Senha testada: {'*' * len(best_wfdb02['password'])}")

        print(f"\n   3. 🔄 Atualizar arquivos de configuração:")
        print(f"      - secrets/postgresql_source_config.json")
        print(f"      - secrets/postgresql_destination_config.json")

def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Discover PostgreSQL Users")
    parser.add_argument("--server", choices=['wf004', 'wfdb02', 'both'],
                       default='both', help="Servidor para testar")
    args = parser.parse_args()

    print("="*80)
    print("🔍 PostgreSQL User Discovery Tool")
    print("="*80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🎯 Servidor(es): {args.server}")
    print("="*80)

    # Carregar configurações
    source_config, dest_config = load_configs()
    if not source_config or not dest_config:
        sys.exit(1)

    wf004_users = []
    wfdb02_users = []

    # Testar wf004
    if args.server in ['wf004', 'both']:
        print("\n🌐 TESTANDO SERVIDOR WF004 (PostgreSQL 14)")
        print("-" * 50)
        wf004_users = test_user_combinations(
            source_config['server']['host'],
            source_config['server']['port'],
            source_config['server']['ssl_mode']
        )

        # Se encontrou usuários, listar todos os usuários existentes
        if wf004_users:
            working_user = wf004_users[0]  # Usar o primeiro que funcionou
            list_existing_users(
                source_config['server']['host'],
                source_config['server']['port'],
                source_config['server']['ssl_mode'],
                working_user['username'],
                working_user['password']
            )

    # Testar wfdb02
    if args.server in ['wfdb02', 'both']:
        print("\n🎯 TESTANDO SERVIDOR WFDB02 (PostgreSQL 16)")
        print("-" * 50)
        wfdb02_users = test_user_combinations(
            dest_config['server']['host'],
            dest_config['server']['port_direct'],
            dest_config['server']['ssl_mode']
        )

        # Se encontrou usuários, listar todos os usuários existentes
        if wfdb02_users:
            working_user = wfdb02_users[0]  # Usar o primeiro que funcionou
            list_existing_users(
                dest_config['server']['host'],
                dest_config['server']['port_direct'],
                dest_config['server']['ssl_mode'],
                working_user['username'],
                working_user['password']
            )

    # Gerar sugestões se testou ambos os servidores
    if args.server == 'both' and (wf004_users or wfdb02_users):
        suggest_migration_credentials(wf004_users, wfdb02_users)

    # Relatório final
    print("\n" + "="*80)
    print("📊 RESUMO DA DESCOBERTA")
    print("="*80)

    if args.server in ['wf004', 'both']:
        print(f"wf004: {len(wf004_users)} credenciais funcionais encontradas")

    if args.server in ['wfdb02', 'both']:
        print(f"wfdb02: {len(wfdb02_users)} credenciais funcionais encontradas")

    total_found = len(wf004_users) + len(wfdb02_users)
    if total_found > 0:
        print(f"\n🎉 Total: {total_found} conexões bem-sucedidas!")
        print("🔄 Use as credenciais encontradas para atualizar os arquivos de configuração")
    else:
        print("\n❌ Nenhuma credencial funcional encontrada")
        print("🔧 Verifique conectividade de rede e configurações dos servidores")

    print("="*80)

    return 0 if total_found > 0 else 1

# ============================================================================
# CLASSE MODULAR - Para integração com orquestrador
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from components.base_component import UtilityComponent, ComponentResult, component_method
except ImportError:
    # Fallback se base_component não estiver disponível
    class UtilityComponent:
        def __init__(self, name, logger=None):
            self.name = name
            self.logger = logger
            self.cache = {}
        def log_info(self, msg): print(f"[{self.name}] {msg}")
        def log_success(self, msg): print(f"[{self.name}] ✅ {msg}")
        def log_error(self, msg): print(f"[{self.name}] ❌ {msg}")
        def _setup(self): pass

    class ComponentResult:
        def __init__(self, success, message, data=None):
            self.success = success
            self.message = message
            self.data = data

    def component_method(func):
        return func

class UserDiscoverer(UtilityComponent):
    """Classe modular para descoberta de usuários PostgreSQL."""

    def __init__(self, logger=None):
        super().__init__("user_discoverer", logger)
        self.discovered_users = {}

    def _setup(self):
        """Setup do componente."""
        self.log_info("Inicializando descobridor de usuários")

    @component_method
    def discover_server_users(self, server_config, server_name="servidor"):
        """Descobre usuários de um servidor específico."""
        try:
            self.log_info(f"Descobrindo usuários em {server_name}...")

            # Usar normalização de configuração
            from components.config_normalizer import normalize_server_config
            norm_config = normalize_server_config(server_config)

            # Usar função existente
            users_found = test_user_combinations(
                norm_config['host'],
                norm_config['port'],
                norm_config['ssl_mode'],
                server_config.get('possible_users', [])
            )

            if users_found:
                self.log_success(f"{len(users_found)} usuários encontrados em {server_name}")
                self.discovered_users[server_name] = users_found
                return ComponentResult(True, f"Usuários descobertos em {server_name}", {
                    "server": server_name,
                    "users_count": len(users_found),
                    "users": users_found
                })
            else:
                self.log_error(f"Nenhum usuário encontrado em {server_name}")
                return ComponentResult(False, f"Nenhum usuário em {server_name}")

        except Exception as e:
            self.log_error(f"Erro na descoberta em {server_name}: {e}")
            return ComponentResult(False, f"Erro em {server_name}: {e}")

    @component_method
    def discover_all_users(self, source_config=None, dest_config=None):
        """Descobre usuários em todos os servidores configurados."""
        try:
            self.log_info("Iniciando descoberta de usuários em todos os servidores")

            all_results = {}
            total_users = 0

            # Se não receber configs, tentar carregar
            if not source_config or not dest_config:
                try:
                    configs = load_configs()
                    source_config = source_config or configs[0]
                    dest_config = dest_config or configs[1]
                except:
                    self.log_error("Configurações não disponíveis")
                    return ComponentResult(False, "Configurações não encontradas")

            # Descobrir no servidor origem
            if source_config:
                source_result = self.discover_server_users(source_config, "origem")
                all_results["origem"] = source_result
                if source_result.success:
                    total_users += source_result.data.get("users_count", 0) if source_result.data else 0

            # Descobrir no servidor destino
            if dest_config:
                dest_result = self.discover_server_users(dest_config, "destino")
                all_results["destino"] = dest_result
                if dest_result.success:
                    total_users += dest_result.data.get("users_count", 0) if dest_result.data else 0

            success = any(result.success for result in all_results.values())

            if success:
                self.log_success(f"Descoberta concluída: {total_users} usuários total")
            else:
                self.log_error("Falha na descoberta de usuários")

            return ComponentResult(success, "Descoberta de usuários concluída", {
                "total_users": total_users,
                "servers": all_results,
                "discovered_users": self.discovered_users
            })

        except Exception as e:
            self.log_error(f"Erro na descoberta geral: {e}")
            return ComponentResult(False, f"Erro geral: {e}")

    def get_discovered_users(self):
        """Retorna usuários descobertos."""
        return self.discovered_users

    def clear_discovered_users(self):
        """Limpa cache de usuários descobertos."""
        self.discovered_users = {}
        self.log_info("Cache de usuários limpo")

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Descoberta interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
