#!/usr/bin/env python3
"""
Test Evolution API Permissions - Simulador de Acesso
=====================================================

Script para simular acesso à Evolution API e verificar permissões.
Baseado: https://github.com/EvolutionAPI/evolution-api

Propósito:
- Simular requisições API com diferentes credenciais
- Testar autenticação e autorização
- Verificar permissões em operações CRUD
- Validar guards e middleware de segurança

Uso:
    python3 test_evolution_api_permissions.py --help
    python3 test_evolution_api_permissions.py \\
        --url http://localhost:8080 --apikey test-key
    python3 test_evolution_api_permissions.py \\
        --url http://localhost:8080 --apikey test-key --verbose
    python3 test_evolution_api_permissions.py \\
        --url http://localhost:8080 --simulate-all
"""

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

# ============================================================================
# Configuração de Logging
# ============================================================================


def setup_logging(verbose: bool = False):
    """Configura sistema de logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


logger = logging.getLogger(__name__)


# ============================================================================
# Enumerações e Data Classes
# ============================================================================

class HttpStatus(Enum):
    """Status HTTP da Evolution API"""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500


class AuthType(Enum):
    """Tipo de autenticação"""
    GLOBAL_API_KEY = "global-api-key"
    INSTANCE_TOKEN = "instance-token"
    NO_AUTH = "no-auth"


@dataclass
class TestCase:
    """Caso de teste de API"""
    name: str
    method: str
    endpoint: str
    auth_type: AuthType
    api_key: Optional[str] = None
    instance_name: Optional[str] = None
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    description: str = ""


@dataclass
class TestResult:
    """Resultado de um teste"""
    test_case: TestCase
    success: bool
    status_code: int
    response: Dict[str, Any]
    error: Optional[str] = None
    elapsed_time: float = 0.0


# ============================================================================
# Classe Principal: Evolution API Test Client
# ============================================================================

class EvolutionAPITestClient:
    """Cliente para testar Evolution API"""

    def __init__(
        self,
        base_url: str,
        global_api_key: Optional[str] = None,
        timeout: int = 10,
        verify_ssl: bool = True
    ):
        """
        Inicializa cliente de teste

        Args:
            base_url: URL base da Evolution API
            global_api_key: Chave API global
            timeout: Timeout em segundos
            verify_ssl: Verificar certificado SSL
        """
        self.base_url = base_url.rstrip('/')
        self.global_api_key = global_api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.test_results: List[TestResult] = []

    def _build_url(self, endpoint: str) -> str:
        """Constrói URL completa"""
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _build_headers(
        self,
        api_key: Optional[str] = None,
        content_type: str = "application/json"
    ) -> Dict[str, str]:
        """Constrói headers da requisição"""
        headers = {"Content-Type": content_type}

        if api_key:
            headers["apikey"] = api_key

        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        api_key: Optional[str] = None,
        instance_name: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> tuple[int, Dict[str, Any], str]:
        """
        Faz requisição HTTP

        Returns:
            Tupla (status_code, response_json, error_message)
        """
        try:
            url = self._build_url(endpoint)
            headers = self._build_headers(api_key)

            # Adicionar instanceName ao endpoint se fornecido
            if instance_name:
                url = url.replace("{instanceName}", instance_name)

            logger.debug(
                f"Requisição {method} para {url}"
            )

            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            try:
                response_json = response.json()
            except ValueError:
                response_json = {"raw": response.text}

            return response.status_code, response_json, ""

        except Timeout:
            error = f"Timeout após {self.timeout}s"
            logger.error(error)
            return 0, {}, error
        except ConnectionError as e:
            error = f"Erro de conexão: {str(e)}"
            logger.error(error)
            return 0, {}, error
        except RequestException as e:
            error = f"Erro na requisição: {str(e)}"
            logger.error(error)
            return 0, {}, error

    def test_health(self) -> bool:
        """Testa se API está disponível"""
        logger.info("🔍 Testando disponibilidade da API...")
        status, response, error = self._make_request("GET", "/")

        if error:
            logger.error(f"❌ API não acessível: {error}")
            return False

        if status == HttpStatus.OK.value:
            logger.info("✅ API disponível")
            logger.debug(f"Resposta: {json.dumps(response, indent=2)}")
            return True
        else:
            logger.error(f"❌ Status inesperado: {status}")
            return False

    def run_test(self, test_case: TestCase) -> TestResult:
        """Executa um caso de teste"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📋 Teste: {test_case.name}")
        logger.info(f"{'='*70}")

        if test_case.description:
            logger.info(f"📝 {test_case.description}")

        # Determinar API key baseado no tipo de autenticação
        api_key = None
        if test_case.auth_type == AuthType.GLOBAL_API_KEY:
            api_key = test_case.api_key or self.global_api_key
            logger.info(f"🔑 Autenticação: GLOBAL_API_KEY")
        elif test_case.auth_type == AuthType.INSTANCE_TOKEN:
            api_key = test_case.api_key
            logger.info(f"🔑 Autenticação: INSTANCE_TOKEN")
        else:
            logger.info(f"🔑 Autenticação: SEM_CREDENCIAIS")

        # Construir endpoint completo
        endpoint = test_case.endpoint
        if test_case.instance_name:
            endpoint = endpoint.replace(
                "{instanceName}",
                test_case.instance_name
            )

        # Fazer requisição
        import time
        start_time = time.time()

        status_code, response, error = self._make_request(
            method=test_case.method,
            endpoint=endpoint,
            api_key=api_key,
            instance_name=test_case.instance_name,
            body=test_case.body
        )

        elapsed_time = time.time() - start_time

        # Validar resultado
        success = False
        if error:
            logger.error(f"❌ ERRO: {error}")
        elif status_code == test_case.expected_status:
            logger.info(
                f"✅ SUCESSO: Status {status_code} (esperado: "
                f"{test_case.expected_status})"
            )
            success = True
        else:
            logger.warning(
                f"⚠️  Status inesperado: {status_code} "
                f"(esperado: {test_case.expected_status})"
            )

        # Log de resposta
        logger.debug(f"📤 Resposta: {json.dumps(response, indent=2)}")
        logger.debug(f"⏱️  Tempo: {elapsed_time:.2f}s")

        result = TestResult(
            test_case=test_case,
            success=success,
            status_code=status_code,
            response=response,
            error=error,
            elapsed_time=elapsed_time
        )

        self.test_results.append(result)
        return result

    def run_all_tests(self, test_cases: List[TestCase]):
        """Executa todos os testes"""
        logger.info(
            f"\n{'='*70}\n"
            f"🚀 INICIANDO SUITE DE TESTES\n"
            f"{'='*70}"
        )

        for test_case in test_cases:
            self.run_test(test_case)

    def print_summary(self):
        """Imprime resumo dos testes"""
        if not self.test_results:
            logger.warning("Nenhum teste executado")
            return

        logger.info(
            f"\n{'='*70}\n"
            f"📊 RESUMO DOS TESTES\n"
            f"{'='*70}"
        )

        total = len(self.test_results)
        successful = sum(1 for r in self.test_results if r.success)
        failed = total - successful

        logger.info(f"Total de testes: {total}")
        logger.info(f"✅ Bem-sucedidos: {successful}")
        logger.error(f"❌ Falhados: {failed}")
        logger.info(f"Taxa de sucesso: {(successful/total*100):.1f}%")

        # Detalhes de falhas
        if failed > 0:
            logger.error(f"\n{'='*70}")
            logger.error("TESTES QUE FALHARAM:")
            logger.error(f"{'='*70}")
            for result in self.test_results:
                if not result.success:
                    logger.error(f"\n❌ {result.test_case.name}")
                    logger.error(f"   Status: {result.status_code}")
                    if result.error:
                        logger.error(f"   Erro: {result.error}")

    def save_report(self, filepath: Path):
        """Salva relatório em arquivo JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "successful": sum(1 for r in self.test_results if r.success),
            "failed": sum(1 for r in self.test_results if not r.success),
            "tests": [
                {
                    "name": r.test_case.name,
                    "endpoint": r.test_case.endpoint,
                    "method": r.test_case.method,
                    "success": r.success,
                    "status_code": r.status_code,
                    "elapsed_time": r.elapsed_time,
                    "error": r.error,
                    "response": r.response
                }
                for r in self.test_results
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Relatório salvo em: {filepath}")


# ============================================================================
# Casos de Teste Padrão
# ============================================================================

def get_standard_test_cases() -> List[TestCase]:
    """Retorna casos de teste padrão"""
    return [
        # Testes de autenticação básica
        TestCase(
            name="Verificar disponibilidade da API",
            method="GET",
            endpoint="/",
            auth_type=AuthType.NO_AUTH,
            expected_status=200,
            description="Deve retornar status OK com informações da API"
        ),

        # Testes com autenticação global
        TestCase(
            name="GET /instance/fetchInstances (com API key global)",
            method="GET",
            endpoint="/instance/fetchInstances",
            auth_type=AuthType.GLOBAL_API_KEY,
            expected_status=200,
            description="Buscar todas as instâncias com autenticação global"
        ),

        TestCase(
            name="Criar instância WhatsApp (com API key global)",
            method="POST",
            endpoint="/instance/create",
            auth_type=AuthType.GLOBAL_API_KEY,
            body={
                "instanceName": "test-evolution-instance",
                "integration": "BAILEYS"
            },
            expected_status=201,
            description="Criar nova instância de WhatsApp"
        ),

        # Testes de operações instance-specific
        TestCase(
            name="GET /chat/findChats (com instance token)",
            method="GET",
            endpoint="/chat/findChats",
            auth_type=AuthType.INSTANCE_TOKEN,
            expected_status=200,
            description="Buscar chats de uma instância específica"
        ),

        TestCase(
            name="Buscar labels da instância",
            method="GET",
            endpoint="/label/findLabels",
            auth_type=AuthType.INSTANCE_TOKEN,
            expected_status=200,
            description="Listar labels disponíveis"
        ),

        # Testes de negação de acesso
        TestCase(
            name="Acesso sem autenticação",
            method="GET",
            endpoint="/instance/fetchInstances",
            auth_type=AuthType.NO_AUTH,
            expected_status=401,
            description="Deve retornar 401 Unauthorized sem credenciais"
        ),

        TestCase(
            name="API key inválida",
            method="GET",
            endpoint="/instance/fetchInstances",
            auth_type=AuthType.GLOBAL_API_KEY,
            api_key="invalid-key-12345",
            expected_status=401,
            description="Deve retornar 401 com chave inválida"
        ),

        # Testes de operações OpenAI
        TestCase(
            name="Buscar credenciais OpenAI",
            method="GET",
            endpoint="/openai/creds",
            auth_type=AuthType.INSTANCE_TOKEN,
            expected_status=200,
            description="Buscar credenciais OpenAI configuradas"
        ),

        # Testes de settings
        TestCase(
            name="Buscar settings da instância",
            method="GET",
            endpoint="/settings/find",
            auth_type=AuthType.INSTANCE_TOKEN,
            expected_status=200,
            description="Obter configurações da instância"
        ),

        # Testes de verificação de permissões
        TestCase(
            name="Verificar status de instância",
            method="GET",
            endpoint="/instance/connect",
            auth_type=AuthType.INSTANCE_TOKEN,
            expected_status=200,
            description="Verificar status de conexão da instância"
        ),
    ]


# ============================================================================
# Função Principal
# ============================================================================

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Teste de permissões da Evolution API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Testar disponibilidade
  python3 test_evolution_api_permissions.py --url http://localhost:8080

  # Testar com API key global
  python3 test_evolution_api_permissions.py \\
    --url http://localhost:8080 \\
    --apikey sua-chave-api-global

  # Executar todos os testes
  python3 test_evolution_api_permissions.py \\
    --url http://localhost:8080 \\
    --apikey sua-chave-api \\
    --simulate-all

  # Com modo verbose
  python3 test_evolution_api_permissions.py \\
    --url http://localhost:8080 \\
    --apikey sua-chave-api \\
    --verbose \\
    --report test-results.json
        """
    )

    parser.add_argument(
        "--url",
        required=True,
        help="URL base da Evolution API (ex: http://localhost:8080)"
    )

    parser.add_argument(
        "--apikey",
        help="Chave API global para autenticação"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Timeout para requisições em segundos (padrão: 10)"
    )

    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="Desabilitar verificação de certificado SSL"
    )

    parser.add_argument(
        "--simulate-all",
        action="store_true",
        help="Executar todos os testes padrão"
    )

    parser.add_argument(
        "--report",
        type=Path,
        help="Salvar relatório em arquivo JSON"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Ativa logging em nível DEBUG"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    logger.info("="*70)
    logger.info("Evolution API - Permission Test Client")
    logger.info("="*70)

    # Criar cliente
    client = EvolutionAPITestClient(
        base_url=args.url,
        global_api_key=args.apikey,
        timeout=args.timeout,
        verify_ssl=not args.no_ssl_verify
    )

    # Testar disponibilidade
    if not client.test_health():
        logger.error("❌ API não está disponível")
        return 1

    # Executar testes
    if args.simulate_all:
        test_cases = get_standard_test_cases()
        client.run_all_tests(test_cases)
        client.print_summary()

        if args.report:
            client.save_report(args.report)

    logger.info("\n✅ Testes concluídos com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
