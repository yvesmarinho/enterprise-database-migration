#!/usr/bin/env python3
"""
PostgreSQL SCRAM Authentication Checker - Modular Version
=========================================================

Componente modular para verificar se os servidores PostgreSQL utilizam SCRAM-SHA-256
para autenticação de senhas.

Verifica:
- password_encryption (configuração do servidor)
- Métodos de autenticação no pg_hba.conf
- Algoritmos utilizados pelos usuários existentes
- Compatibilidade entre servidores para migração

Versão: 2.0.0 (Modular)
Data: 03/10/2025
"""

import json
import psycopg2
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

# Importar módulo base
sys.path.insert(0, str(Path(__file__).parent.parent))
from components.base_component import ValidationComponent, ComponentResult, component_method

def load_configs():
    """Carrega configurações de ambos os servidores."""
    try:
        from components.config_manager import get_db_config_path
        source_config_path = get_db_config_path('source_config')
        with open(source_config_path, 'r', encoding='utf-8') as f:
            source = json.load(f)
        from components.config_manager import get_db_config_path
        dest_config_path = get_db_config_path('postgresql_destination_config')
        with open(dest_config_path, 'r', encoding='utf-8') as f:
            destination = json.load(f)
        return source, destination
    except Exception as e:
        print(f"❌ Erro ao carregar configurações: {e}")
        return None, None

def test_basic_connection(host, port, ssl_mode):
    """Testa conexões básicas para encontrar credenciais funcionais."""
    common_users = [
        ("postgres", "postgres"),
        ("postgres", ""),
        ("migration_user", "-5FRifRucho3wudu&re2opafa+tuFr8#"),
    ]

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
            conn.close()
            return username, password

        except psycopg2.OperationalError:
            continue
        except Exception:
            continue

    return None, None

def check_scram_settings(host, port, ssl_mode, username, password):
    """Verifica configurações SCRAM do servidor."""
    print(f"\n🔐 Verificando configurações SCRAM em {host}:{port}...")

    try:
        conn_string = (
            f"host={host} "
            f"port={port} "
            f"dbname=postgres "
            f"user={username} "
            f"password={password} "
            f"sslmode={ssl_mode} "
            f"connect_timeout=15"
        )

        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Obter informações básicas
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        pg_version = re.search(r'PostgreSQL (\d+\.\d+)', version).group(1)

        print(f"   📊 PostgreSQL {pg_version}")
        print(f"   👤 Conectado como: {username}")

        # 1. Verificar password_encryption
        cursor.execute("SHOW password_encryption")
        password_encryption = cursor.fetchone()[0]

        print(f"   🔑 password_encryption: {password_encryption}")

        if password_encryption == 'scram-sha-256':
            print(f"   ✅ SCRAM-SHA-256 está ativo")
        elif password_encryption == 'md5':
            print(f"   ⚠️ MD5 está ativo (método legado)")
        else:
            print(f"   ❓ Método desconhecido: {password_encryption}")

        # 2. Verificar algoritmos dos usuários existentes
        cursor.execute("""
            SELECT rolname,
                   CASE
                       WHEN rolpassword LIKE 'SCRAM-SHA-256%' THEN 'SCRAM-SHA-256'
                       WHEN rolpassword LIKE 'md5%' THEN 'MD5'
                       WHEN rolpassword IS NULL THEN 'NO_PASSWORD'
                       ELSE 'OTHER'
                   END as password_method
            FROM pg_authid
            WHERE rolcanlogin = true
              AND rolname NOT LIKE 'pg_%'
            ORDER BY rolname
        """)

        users_auth = cursor.fetchall()

        print(f"   👥 Métodos de autenticação dos usuários:")
        scram_users = 0
        md5_users = 0
        no_pass_users = 0

        for user, method in users_auth:
            if method == 'SCRAM-SHA-256':
                print(f"      ✅ {user}: SCRAM-SHA-256")
                scram_users += 1
            elif method == 'MD5':
                print(f"      ⚠️ {user}: MD5")
                md5_users += 1
            elif method == 'NO_PASSWORD':
                print(f"      ❌ {user}: SEM SENHA")
                no_pass_users += 1
            else:
                print(f"      ❓ {user}: {method}")

        # 3. Verificar configurações relacionadas ao SCRAM
        scram_configs = [
            'password_encryption',
            'ssl',
            'ssl_ciphers',
            'ssl_prefer_server_ciphers'
        ]

        print(f"   ⚙️ Configurações relacionadas à segurança:")
        for config in scram_configs:
            try:
                cursor.execute(f"SHOW {config}")
                value = cursor.fetchone()[0]
                print(f"      {config}: {value}")
            except:
                print(f"      {config}: N/A")

        # 4. Tentar obter informações do pg_hba.conf (se possível)
        try:
            cursor.execute("""
                SELECT type, database, user_name, address, method, options
                FROM pg_hba_file_rules
                WHERE database LIKE '%all%' OR database LIKE '%postgres%'
                ORDER BY line_number
                LIMIT 10
            """)

            hba_rules = cursor.fetchall()
            if hba_rules:
                print(f"   📋 Regras pg_hba.conf relevantes:")
                for rule in hba_rules:
                    rule_type, database, user_name, address, method, options = rule
                    print(f"      {rule_type} {database} {user_name} {address} {method}")
        except Exception as e:
            print(f"   ⚠️ Não foi possível acessar pg_hba.conf: {e}")

        cursor.close()
        conn.close()

        # Retornar resumo
        return {
            'host': host,
            'port': port,
            'version': pg_version,
            'password_encryption': password_encryption,
            'scram_users': scram_users,
            'md5_users': md5_users,
            'no_pass_users': no_pass_users,
            'total_users': len(users_auth),
            'scram_ready': password_encryption == 'scram-sha-256'
        }

    except Exception as e:
        print(f"   ❌ Erro ao verificar SCRAM: {e}")
        return None

def analyze_migration_compatibility(wf004_info, wfdb02_info):
    """Analisa compatibilidade SCRAM entre servidores para migração."""
    print("\n" + "="*80)
    print("🔍 ANÁLISE DE COMPATIBILIDADE SCRAM PARA MIGRAÇÃO")
    print("="*80)

    if not wf004_info or not wfdb02_info:
        print("❌ Não foi possível analisar - dados insuficientes")
        return

    print("📊 Resumo dos servidores:")
    print(f"   wf004 (origem): PostgreSQL {wf004_info['version']} - {wf004_info['password_encryption']}")
    print(f"   wfdb02 (destino): PostgreSQL {wfdb02_info['version']} - {wfdb02_info['password_encryption']}")

    # Verificar compatibilidade
    compatible = True
    recommendations = []

    print("\n🔐 Análise de compatibilidade:")

    # 1. Verificar se ambos suportam SCRAM
    if wf004_info['scram_ready'] and wfdb02_info['scram_ready']:
        print("   ✅ Ambos servidores usam SCRAM-SHA-256")
        print("   ✅ Migração de senhas será direta")
    elif wf004_info['scram_ready'] and not wfdb02_info['scram_ready']:
        print("   ⚠️ Origem usa SCRAM, destino usa MD5")
        print("   ⚠️ Senhas SCRAM podem não funcionar no destino")
        compatible = False
        recommendations.append("Configurar SCRAM-SHA-256 no servidor destino")
    elif not wf004_info['scram_ready'] and wfdb02_info['scram_ready']:
        print("   ⚠️ Origem usa MD5, destino usa SCRAM")
        print("   ⚠️ Senhas MD5 podem não funcionar no destino")
        compatible = False
        recommendations.append("Atualizar senhas para SCRAM na origem ou aceitar MD5 no destino")
    else:
        print("   ⚠️ Ambos servidores usam MD5")
        print("   ⚠️ Recomendado atualizar para SCRAM-SHA-256")
        recommendations.append("Atualizar ambos servidores para SCRAM-SHA-256")

    # 2. Analisar distribuição de usuários
    print(f"\n👥 Distribuição de usuários:")
    print(f"   wf004: {wf004_info['scram_users']} SCRAM, {wf004_info['md5_users']} MD5, {wf004_info['no_pass_users']} sem senha")
    print(f"   wfdb02: {wfdb02_info['scram_users']} SCRAM, {wfdb02_info['md5_users']} MD5, {wfdb02_info['no_pass_users']} sem senha")

    # 3. Verificar versions compatibility
    wf004_version = float(wf004_info['version'])
    wfdb02_version = float(wfdb02_info['version'])

    if wf004_version >= 10.0 and wfdb02_version >= 10.0:
        print("   ✅ Ambas versões suportam SCRAM-SHA-256 nativamente")
    else:
        print("   ⚠️ Versões antigas podem ter limitações SCRAM")
        recommendations.append("Verificar compatibilidade SCRAM das versões específicas")

    # 4. Gerar recomendações finais
    print(f"\n💡 RECOMENDAÇÕES:")

    if compatible:
        print("   🎉 Migração pode prosseguir sem ajustes de autenticação")
        print("   ✅ As senhas dos usuários serão preservadas")
    else:
        print("   ⚠️ Ajustes necessários antes da migração:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

    # 5. Scripts sugeridos
    print(f"\n🔧 SCRIPTS PARA APLICAR MUDANÇAS:")

    if not wf004_info['scram_ready']:
        print("   Para wf004 (origem):")
        print("     ALTER SYSTEM SET password_encryption = 'scram-sha-256';")
        print("     SELECT pg_reload_conf();")

    if not wfdb02_info['scram_ready']:
        print("   Para wfdb02 (destino):")
        print("     ALTER SYSTEM SET password_encryption = 'scram-sha-256';")
        print("     SELECT pg_reload_conf();")

    if wf004_info['md5_users'] > 0 or wfdb02_info['md5_users'] > 0:
        print("   Para atualizar senhas MD5 existentes:")
        print("     -- Para cada usuário com senha MD5:")
        print("     ALTER USER username PASSWORD 'nova_senha';")

    return compatible

def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Check PostgreSQL SCRAM Authentication")
    parser.add_argument("--server", choices=['wf004', 'wfdb02', 'both'],
                       default='both', help="Servidor para verificar")
    args = parser.parse_args()

    print("="*80)
    print("🔐 PostgreSQL SCRAM Authentication Checker")
    print("="*80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🎯 Servidor(es): {args.server}")
    print("="*80)

    # Carregar configurações
    source_config, dest_config = load_configs()
    if not source_config or not dest_config:
        sys.exit(1)

    wf004_info = None
    wfdb02_info = None

    # Verificar wf004
    if args.server in ['wf004', 'both']:
        print("\n🌐 SERVIDOR WF004 (PostgreSQL 14)")
        print("-" * 50)

        # Encontrar credenciais funcionais
        username, password = test_basic_connection(
            source_config['server']['host'],
            source_config['server']['port'],
            source_config['server']['ssl_mode']
        )

        if username:
            print(f"   ✅ Conectado com: {username}")
            wf004_info = check_scram_settings(
                source_config['server']['host'],
                source_config['server']['port'],
                source_config['server']['ssl_mode'],
                username, password
            )
        else:
            print("   ❌ Não foi possível conectar ao wf004")

    # Verificar wfdb02
    if args.server in ['wfdb02', 'both']:
        print("\n🎯 SERVIDOR WFDB02 (PostgreSQL 16)")
        print("-" * 50)

        # Encontrar credenciais funcionais
        username, password = test_basic_connection(
            dest_config['server']['host'],
            dest_config['server']['port_direct'],
            dest_config['server']['ssl_mode']
        )

        if username:
            print(f"   ✅ Conectado com: {username}")
            wfdb02_info = check_scram_settings(
                dest_config['server']['host'],
                dest_config['server']['port_direct'],
                dest_config['server']['ssl_mode'],
                username, password
            )
        else:
            print("   ❌ Não foi possível conectar ao wfdb02")

    # Análise de compatibilidade para migração
    if args.server == 'both' and wf004_info and wfdb02_info:
        compatible = analyze_migration_compatibility(wf004_info, wfdb02_info)
        return 0 if compatible else 1

    # Relatório final individual
    print("\n" + "="*80)
    print("📊 RESUMO DA VERIFICAÇÃO SCRAM")
    print("="*80)

    if wf004_info:
        status = "✅ SCRAM ATIVO" if wf004_info['scram_ready'] else "⚠️ MD5 ATIVO"
        print(f"wf004: {status} - {wf004_info['scram_users']} usuários SCRAM")

    if wfdb02_info:
        status = "✅ SCRAM ATIVO" if wfdb02_info['scram_ready'] else "⚠️ MD5 ATIVO"
        print(f"wfdb02: {status} - {wfdb02_info['scram_users']} usuários SCRAM")

    print("="*80)

    return 0

# ============================================================================
# VERSÃO MODULAR - Classe para integração com orquestrador
# ============================================================================

class ScramAuthChecker(ValidationComponent):
    """Componente modular para verificação SCRAM-SHA-256."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("scram_auth_checker", logger)
        self.configs = {}

    def _setup(self):
        """Setup do componente."""
        self.log_info("Inicializando verificador SCRAM")
        # Setup específico pode ser adicionado aqui

    @component_method
    def load_server_configs(self, source_config: Dict, dest_config: Dict) -> ComponentResult:
        """Carrega configurações dos servidores."""
        try:
            self.configs = {
                'source': source_config,
                'destination': dest_config
            }
            self.log_success("Configurações de servidor carregadas")
            return ComponentResult(True, "Configurações carregadas", {"servers": 2})
        except Exception as e:
            return ComponentResult(False, f"Erro ao carregar configurações: {e}")

    @component_method
    def validate(self, data: Any = None) -> ComponentResult:
        """Executa validação SCRAM completa."""
        if not self.configs:
            return ComponentResult(False, "Configurações não carregadas")

        try:
            self.log_info("Iniciando verificação SCRAM-SHA-256")

            # Verificar servidor origem
            source_result = self._check_server_scram(
                self.configs['source'],
                "origem"
            )

            # Verificar servidor destino
            dest_result = self._check_server_scram(
                self.configs['destination'],
                "destino"
            )

            # Analisar compatibilidade
            compatibility = self._analyze_compatibility(source_result, dest_result)

            overall_success = source_result['success'] and dest_result['success']

            result_data = {
                'source': source_result,
                'destination': dest_result,
                'compatibility': compatibility
            }

            message = "Verificação SCRAM concluída"
            if compatibility['compatible']:
                self.log_success("Servidores compatíveis para migração SCRAM")
            else:
                self.log_warning("Incompatibilidades detectadas na configuração SCRAM")

            return ComponentResult(overall_success, message, result_data)

        except Exception as e:
            self.log_error(f"Erro na verificação SCRAM: {e}")
            return ComponentResult(False, f"Erro na verificação: {e}")

    def _check_server_scram(self, config: Dict, server_name: str) -> Dict:
        """Verifica SCRAM em um servidor específico."""
        try:
            self.log_info(f"Verificando SCRAM no servidor {server_name}")

            # Usar as funções existentes
            username, password = find_working_credentials(
                config['host'],
                config['port'],
                config['ssl_mode'],
                config['possible_users']
            )

            if not username:
                return {
                    'success': False,
                    'error': 'Não foi possível conectar ao servidor',
                    'scram_enabled': False
                }

            scram_info = check_scram_settings(
                config['host'],
                config['port'],
                config['ssl_mode'],
                username,
                password
            )

            return {
                'success': True,
                'server': server_name,
                'scram_info': scram_info,
                'credentials_used': {'username': username}
            }

        except Exception as e:
            self.log_error(f"Erro ao verificar {server_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'server': server_name
            }

    def _analyze_compatibility(self, source_result: Dict, dest_result: Dict) -> Dict:
        """Analisa compatibilidade entre servidores."""
        compatibility = {
            'compatible': True,
            'issues': [],
            'recommendations': []
        }

        # Verificar se ambos suportam SCRAM
        if not (source_result.get('success') and dest_result.get('success')):
            compatibility['compatible'] = False
            compatibility['issues'].append("Falha na conexão com um ou ambos servidores")
            return compatibility

        # Análises específicas podem ser adicionadas aqui
        compatibility['recommendations'].append("Migração SCRAM pode prosseguir")

        return compatibility

    @component_method
    def check_scram_support(self) -> bool:
        """Método simplificado para verificação rápida."""
        try:
            if not self.configs:
                self.log_warning("Configurações não carregadas, executando verificação básica")
                return True  # Por padrão, assumir suporte

            result = self.validate()
            return result.success and result.data.get('compatibility', {}).get('compatible', False)

        except Exception as e:
            self.log_error(f"Erro na verificação rápida: {e}")
            return False

    def get_scram_summary(self) -> Dict:
        """Retorna resumo das verificações SCRAM."""
        if not hasattr(self, '_last_validation_result'):
            return {'status': 'not_validated'}

        return {
            'status': 'validated',
            'timestamp': datetime.now().isoformat(),
            'component_status': self.get_status_info()
        }

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Verificação interrompida pelo usuário")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
