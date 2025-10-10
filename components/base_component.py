"""
Base Module for Migration Components
====================================

Módulo base para padronizar todos os componentes de migração.
Define interfaces comuns e logging padronizado.

Versão: 1.0.0
Data: 03/10/2025
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

class ComponentStatus(Enum):
    """Status de um componente."""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"

@dataclass
class ComponentResult:
    """Resultado de operação de componente."""
    success: bool
    message: str
    data: Optional[Dict] = None
    error_code: Optional[str] = None

class MigrationComponent(ABC):
    """Classe base para todos os componentes de migração."""

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.status = ComponentStatus.INACTIVE
        self.logger = logger or logging.getLogger(f"migration.{name}")
        self._initialize()

    def _initialize(self):
        """Inicialização do componente."""
        self.status = ComponentStatus.INITIALIZING
        self.log_info(f"Inicializando componente {self.name}")

        try:
            self._setup()
            self.status = ComponentStatus.READY
            self.log_success(f"Componente {self.name} pronto")
        except Exception as e:
            self.status = ComponentStatus.ERROR
            self.log_error(f"Erro na inicialização do {self.name}: {e}")
            raise

    @abstractmethod
    def _setup(self):
        """Setup específico do componente. Deve ser implementado pelas subclasses."""
        pass

    def log_debug(self, message: str):
        """Log debug."""
        self.logger.debug(f"[{self.name}] {message}")

    def log_info(self, message: str):
        """Log info."""
        self.logger.info(f"[{self.name}] {message}")

    def log_success(self, message: str):
        """Log success (usando info com prefixo)."""
        self.logger.info(f"[{self.name}] ✅ {message}")

    def log_warning(self, message: str):
        """Log warning."""
        self.logger.warning(f"[{self.name}] ⚠️ {message}")

    def log_error(self, message: str):
        """Log error."""
        self.logger.error(f"[{self.name}] ❌ {message}")

    def is_ready(self) -> bool:
        """Verifica se o componente está pronto."""
        return self.status == ComponentStatus.READY

    def get_status_info(self) -> Dict:
        """Retorna informações de status."""
        return {
            'name': self.name,
            'status': self.status.value,
            'ready': self.is_ready()
        }

class DatabaseComponent(MigrationComponent):
    """Classe base para componentes que trabalham com banco."""

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.connection = None
        self.config = {}
        super().__init__(name, logger)

    def load_config(self, config: Dict) -> ComponentResult:
        """Carrega configuração do componente."""
        try:
            self.config = config
            self.log_info("Configuração carregada")
            return ComponentResult(True, "Configuração carregada com sucesso", {"config_keys": list(config.keys())})
        except Exception as e:
            self.log_error(f"Erro ao carregar configuração: {e}")
            return ComponentResult(False, str(e), error_code="CONFIG_ERROR")

    @abstractmethod
    def connect(self) -> ComponentResult:
        """Conecta ao banco. Deve ser implementado pelas subclasses."""
        pass

    @abstractmethod
    def disconnect(self) -> ComponentResult:
        """Desconecta do banco. Deve ser implementado pelas subclasses."""
        pass

    def test_connection(self) -> ComponentResult:
        """Testa conexão com o banco."""
        try:
            self.log_info("Testando conexão...")
            connect_result = self.connect()

            if not connect_result.success:
                return ComponentResult(False, f"Falha na conexão: {connect_result.message}")

            # Realizar teste específico
            test_result = self._perform_connection_test()

            # Desconectar
            disconnect_result = self.disconnect()
            if not disconnect_result.success:
                self.log_warning(f"Aviso ao desconectar: {disconnect_result.message}")

            return test_result

        except Exception as e:
            self.log_error(f"Erro no teste de conexão: {e}")
            return ComponentResult(False, str(e), error_code="CONNECTION_TEST_ERROR")

    def _perform_connection_test(self) -> ComponentResult:
        """Executa teste específico de conexão. Pode ser sobrescrito."""
        return ComponentResult(True, "Conexão testada com sucesso")

class ValidationComponent(MigrationComponent):
    """Classe base para componentes de validação."""

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.validation_rules = {}
        super().__init__(name, logger)

    def add_validation_rule(self, rule_name: str, rule_function):
        """Adiciona regra de validação."""
        self.validation_rules[rule_name] = rule_function
        self.log_info(f"Regra de validação adicionada: {rule_name}")

    @abstractmethod
    def validate(self, data: Any) -> ComponentResult:
        """Executa validação. Deve ser implementado pelas subclasses."""
        pass

    def run_all_validations(self, data: Any) -> ComponentResult:
        """Executa todas as regras de validação."""
        results = {}
        overall_success = True

        for rule_name, rule_function in self.validation_rules.items():
            try:
                self.log_info(f"Executando validação: {rule_name}")
                result = rule_function(data)
                results[rule_name] = result

                if not result:
                    overall_success = False
                    self.log_error(f"Validação falhou: {rule_name}")
                else:
                    self.log_success(f"Validação passou: {rule_name}")

            except Exception as e:
                self.log_error(f"Erro na validação {rule_name}: {e}")
                results[rule_name] = False
                overall_success = False

        return ComponentResult(
            overall_success,
            f"Validação {'bem-sucedida' if overall_success else 'falhou'}",
            {"rule_results": results}
        )

class UtilityComponent(MigrationComponent):
    """Classe base para componentes utilitários."""

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.cache = {}
        super().__init__(name, logger)

    def cache_result(self, key: str, value: Any):
        """Armazena resultado no cache."""
        self.cache[key] = value
        self.log_debug(f"Resultado cacheado: {key}")

    def get_cached_result(self, key: str) -> Optional[Any]:
        """Recupera resultado do cache."""
        result = self.cache.get(key)
        if result is not None:
            self.log_debug(f"Resultado recuperado do cache: {key}")
        return result

    def clear_cache(self):
        """Limpa o cache."""
        self.cache.clear()
        self.log_info("Cache limpo")

# Decorador para padronizar métodos de componentes
def component_method(func):
    """Decorador para métodos de componentes."""
    def wrapper(self, *args, **kwargs):
        method_name = func.__name__
        self.log_debug(f"Executando método: {method_name}")

        try:
            self.status = ComponentStatus.RUNNING
            result = func(self, *args, **kwargs)
            self.status = ComponentStatus.SUCCESS
            return result
        except Exception as e:
            self.status = ComponentStatus.ERROR
            self.log_error(f"Erro em {method_name}: {e}")
            raise

    return wrapper

# Factory para criar componentes
class ComponentFactory:
    """Factory para criar componentes padronizados."""

    @staticmethod
    def create_database_component(name: str, component_class, logger: Optional[logging.Logger] = None):
        """Cria componente de banco."""
        if not issubclass(component_class, DatabaseComponent):
            raise ValueError(f"Classe {component_class} deve herdar de DatabaseComponent")

        return component_class(name, logger)

    @staticmethod
    def create_validation_component(name: str, component_class, logger: Optional[logging.Logger] = None):
        """Cria componente de validação."""
        if not issubclass(component_class, ValidationComponent):
            raise ValueError(f"Classe {component_class} deve herdar de ValidationComponent")

        return component_class(name, logger)

    @staticmethod
    def create_utility_component(name: str, component_class, logger: Optional[logging.Logger] = None):
        """Cria componente utilitário."""
        if not issubclass(component_class, UtilityComponent):
            raise ValueError(f"Classe {component_class} deve herdar de UtilityComponent")

        return component_class(name, logger)
