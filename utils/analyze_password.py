#!/usr/bin/env python3
"""
Análise de Senha - Debug Detalhado
=================================

Verifica se há problemas de encoding, caracteres especiais ou
diferenças na senha entre os métodos que funcionam e os que falham.
"""

import json
import psycopg2

def analyze_password_issue():
    print("🔍 ANÁLISE DETALHADA DA SENHA")
    print("="*50)

    # Senha que funciona (hardcoded)
    working_password = "REDACTED_WFDB02_PASSWORD"
    print(f"💚 Senha funcional (hardcoded):")
    print(f"   Conteúdo: {repr(working_password)}")
    print(f"   Tamanho: {len(working_password)} chars")
    print(f"   Encoding: {working_password.encode('utf-8')}")

    # Senha do arquivo JSON
    from components.config_manager import get_db_config_path
    source_config_path = get_db_config_path('source_config')
    with open(source_config_path, 'r', encoding='utf-8') as f:
        source_data = json.load(f)

    json_password = source_data['authentication']['password']
    print(f"\n📋 Senha do JSON:")
    print(f"   Conteúdo: {repr(json_password)}")
    print(f"   Tamanho: {len(json_password)} chars")
    print(f"   Encoding: {json_password.encode('utf-8')}")

    # Comparação
    print(f"\n🔍 Comparação:")
    print(f"   São iguais? {working_password == json_password}")
    print(f"   Diff bytes: {working_password.encode('utf-8') == json_password.encode('utf-8')}")

    if working_password != json_password:
        print(f"   ❌ DIFERENÇA ENCONTRADA!")
        print(f"   Char por char:")
        for i, (c1, c2) in enumerate(zip(working_password, json_password)):
            if c1 != c2:
                print(f"      Posição {i}: '{c1}' vs '{c2}' (ord: {ord(c1)} vs {ord(c2)})")
    else:
        print(f"   ✅ Senhas são idênticas!")

    # Teste de conexão com ambas
    print(f"\n🧪 TESTE DE CONEXÃO:")

    # Teste 1: Senha hardcoded
    try:
        conn1 = psycopg2.connect(
            host="wf004.vya.digital",
            port=5432,
            dbname="postgres",
            user="migration_user",
            password=working_password,
            sslmode="prefer",
            connect_timeout=10
        )
        conn1.close()
        print(f"   ✅ Senha hardcoded: SUCESSO")
    except Exception as e:
        print(f"   ❌ Senha hardcoded: {e}")

    # Teste 2: Senha do JSON
    try:
        conn2 = psycopg2.connect(
            host="wf004.vya.digital",
            port=5432,
            dbname="postgres",
            user="migration_user",
            password=json_password,
            sslmode="prefer",
            connect_timeout=10
        )
        conn2.close()
        print(f"   ✅ Senha do JSON: SUCESSO")
    except Exception as e:
        print(f"   ❌ Senha do JSON: {e}")

    # Teste 3: String de conexão completa
    try:
        conn_string = (
            f"host=wf004.vya.digital "
            f"port=5432 "
            f"dbname=postgres "
            f"user=migration_user "
            f"password={json_password} "
            f"sslmode=prefer "
            f"connect_timeout=30"
        )
        print(f"\n📡 String de conexão testada:")
        print(f"   {conn_string.replace(json_password, '***')}")

        conn3 = psycopg2.connect(conn_string)
        conn3.close()
        print(f"   ✅ String completa: SUCESSO")
    except Exception as e:
        print(f"   ❌ String completa: {e}")

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

class PasswordAnalyzer(UtilityComponent):
    """Classe modular para análise de senhas PostgreSQL."""

    def __init__(self, logger=None):
        super().__init__("password_analyzer", logger)
        self.analysis_results = {}

    def _setup(self):
        """Setup do componente."""
        self.log_info("Inicializando analisador de senhas")

    @component_method
    def analyze_password_encoding(self, password, password_source="unknown"):
        """Analisa encoding e características de uma senha."""
        try:
            self.log_info(f"Analisando senha de {password_source}")

            analysis = {
                "source": password_source,
                "content": repr(password),
                "length": len(password),
                "encoding_utf8": password.encode('utf-8'),
                "has_special_chars": any(char in password for char in "!@#$%^&*()+-=[]{}|;:,.<>?"),
                "has_unicode": any(ord(char) > 127 for char in password)
            }

            self.analysis_results[password_source] = analysis
            self.log_success(f"Análise de {password_source} concluída")

            return ComponentResult(True, f"Senha de {password_source} analisada", analysis)

        except Exception as e:
            self.log_error(f"Erro na análise de {password_source}: {e}")
            return ComponentResult(False, f"Erro na análise: {e}")

    @component_method
    def compare_passwords(self, password1, password2, source1="senha1", source2="senha2"):
        """Compara duas senhas para identificar diferenças."""
        try:
            self.log_info(f"Comparando {source1} vs {source2}")

            comparison = {
                "identical": password1 == password2,
                "length_diff": len(password1) - len(password2),
                "encoding_diff": password1.encode('utf-8') != password2.encode('utf-8'),
                "char_differences": []
            }

            # Identificar diferenças de caracteres
            min_len = min(len(password1), len(password2))
            for i in range(min_len):
                if password1[i] != password2[i]:
                    comparison["char_differences"].append({
                        "position": i,
                        "char1": password1[i],
                        "char2": password2[i],
                        "ord1": ord(password1[i]),
                        "ord2": ord(password2[i])
                    })

            if comparison["identical"]:
                self.log_success("Senhas são idênticas")
            else:
                self.log_error(f"Senhas diferem em {len(comparison['char_differences'])} posições")

            return ComponentResult(True, "Comparação concluída", comparison)

        except Exception as e:
            self.log_error(f"Erro na comparação: {e}")
            return ComponentResult(False, f"Erro na comparação: {e}")

    @component_method
    def test_password_connection(self, host, port, database, username, password, password_source="test"):
        """Testa conexão com uma senha específica."""
        try:
            self.log_info(f"Testando conexão com senha de {password_source}")

            conn_string = (
                f"host={host} "
                f"port={port} "
                f"dbname={database} "
                f"user={username} "
                f"password={password} "
                f"sslmode=prefer "
                f"connect_timeout=10"
            )

            conn = psycopg2.connect(conn_string)
            conn.close()

            self.log_success(f"Conexão com {password_source} bem-sucedida")
            return ComponentResult(True, f"Conexão {password_source} OK", {
                "connection_successful": True,
                "password_source": password_source
            })

        except Exception as e:
            self.log_error(f"Falha na conexão com {password_source}: {e}")
            return ComponentResult(False, f"Conexão {password_source} falhou: {e}")

    @component_method
    def analyze_password_issue(self, config_file_path=None):
        """Executa análise completa baseada na função original."""
        try:
            self.log_info("Executando análise completa de senha")

            # Executar função original
            analyze_password_issue()

            self.log_info("Análise detalhada concluída (verifique output)")
            return ComponentResult(True, "Análise completa executada")

        except Exception as e:
            self.log_error(f"Erro na análise completa: {e}")
            return ComponentResult(False, f"Erro na análise: {e}")

    def get_analysis_results(self):
        """Retorna resultados das análises."""
        return self.analysis_results

    def clear_analysis_results(self):
        """Limpa resultados das análises."""
        self.analysis_results = {}
        self.log_info("Resultados de análise limpos")

if __name__ == "__main__":
    analyze_password_issue()
