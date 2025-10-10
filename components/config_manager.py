#!/usr/bin/env python3
"""
Configuration Manager - Gerenciador de Configurações Centralizado
===============================================================

Este módulo centraliza o acesso às configurações do projeto usando
PROJECT_HOME como base e config.ini como fonte de configurações.

Uso:
    from components.config_manager import config, get_project_path, get_db_config_path

    # Obter path absoluto para qualquer diretório do projeto
    config_dir = get_project_path('config')

    # Obter path para arquivo de configuração de banco
    source_config = get_db_config_path('source_config')

    # Acessar configurações do config.ini
    batch_size = config.getint('MIGRATION_SETTINGS', 'default_batch_size')
"""

import os
import configparser
from pathlib import Path
from typing import Optional

def get_project_home() -> Path:
    """Retorna o diretório raiz do projeto usando PROJECT_HOME."""
    project_home = os.environ.get('PROJECT_HOME')
    if not project_home:
        # Fallback: tentar detectar pela localização atual
        current_file = Path(__file__)
        for parent in [current_file.parent] + list(current_file.parents):
            if (parent / 'main.py').exists() and (parent / 'config.ini').exists():
                project_home = str(parent)
                os.environ['PROJECT_HOME'] = project_home
                break
        else:
            raise RuntimeError("PROJECT_HOME não encontrado. Execute através do main.py")

    return Path(project_home)

def get_project_path(relative_path: str) -> Path:
    """
    Retorna path absoluto para um caminho relativo ao projeto.

    Args:
        relative_path: Caminho relativo ao PROJECT_HOME (ex: 'config', 'secrets/source_config.json')

    Returns:
        Path absoluto do arquivo/diretório
    """
    return get_project_home() / relative_path

def get_db_config_path(config_name: str) -> Path:
    """
    Retorna path absoluto para arquivo de configuração de banco.

    Args:
        config_name: Nome da configuração (ex: 'source_config', 'destination_config')

    Returns:
        Path absoluto do arquivo de configuração
    """
    config_filename = config.get('DATABASE_CONFIGS', config_name, fallback=f"{config_name}.json")
    secrets_dir = config.get('PATHS', 'secrets_dir', fallback='secrets')
    return get_project_path(f"{secrets_dir}/{config_filename}")

def load_config() -> configparser.ConfigParser:
    """Carrega o arquivo config.ini do projeto."""
    config_parser = configparser.ConfigParser()
    config_file = get_project_home() / 'config.ini'

    if not config_file.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_file}")

    config_parser.read(config_file, encoding='utf-8')
    return config_parser

# Instância global de configuração (carregada uma vez)
config = load_config()

def get_log_file_path() -> Path:
    """Retorna path para arquivo de log atual."""
    from datetime import datetime

    logs_dir = config.get('PATHS', 'logs_dir', fallback='logs')
    log_pattern = config.get('LOGGING', 'log_file_pattern', fallback='migration_%Y%m%d_%H%M%S.log')

    timestamp = datetime.now().strftime(log_pattern.replace('%Y%m%d_%H%M%S', '%Y%m%d_%H%M%S'))
    return get_project_path(f"{logs_dir}/{timestamp}")

def get_reports_dir() -> Path:
    """Retorna diretório de relatórios."""
    reports_dir = config.get('PATHS', 'reports_dir', fallback='core/reports')
    reports_path = get_project_path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    return reports_path

def validate_project_structure() -> bool:
    """
    Valida se a estrutura do projeto está correta.

    Returns:
        True se estrutura válida, False caso contrário
    """
    try:
        project_home = get_project_home()

        # Verificar arquivos essenciais
        essential_files = ['main.py', 'config.ini']
        for file in essential_files:
            if not (project_home / file).exists():
                print(f"❌ Arquivo essencial não encontrado: {file}")
                return False

        # Verificar diretórios essenciais
        essential_dirs = ['config', 'secrets', 'core', 'utils', 'validation']
        for dir_name in essential_dirs:
            dir_path = get_project_path(dir_name)
            if not dir_path.exists():
                print(f"❌ Diretório essencial não encontrado: {dir_path}")
                return False

        # Verificar configurações de banco
        try:
            source_config = get_db_config_path('source_config')
            if not source_config.exists():
                print(f"❌ Configuração de banco não encontrada: {source_config}")
                return False
        except Exception as e:
            print(f"❌ Erro ao verificar configurações de banco: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Erro na validação da estrutura: {e}")
        return False

def print_project_info():
    """Imprime informações do projeto para debug."""
    try:
        project_home = get_project_home()
        print(f"\n📁 PROJECT_HOME: {project_home}")
        print(f"📁 Config dir: {get_project_path('config')}")
        print(f"📁 Secrets dir: {get_project_path('secrets')}")
        print(f"📁 Reports dir: {get_reports_dir()}")
        print(f"📄 Source config: {get_db_config_path('source_config')}")
        print(f"📄 Destination config: {get_db_config_path('destination_config')}")

        # Verificar se arquivos existem
        if validate_project_structure():
            print("✅ Estrutura do projeto válida")
        else:
            print("❌ Problemas na estrutura do projeto")

    except Exception as e:
        print(f"❌ Erro ao obter informações do projeto: {e}")

# Utilitários de conveniência
def get_config_value(section: str, key: str, fallback: str = None):
    """Utilitário para obter valor de configuração com fallback."""
    return config.get(section, key, fallback=fallback)

def get_config_int(section: str, key: str, fallback: int = 0):
    """Utilitário para obter valor inteiro de configuração."""
    return config.getint(section, key, fallback=fallback)

def get_config_bool(section: str, key: str, fallback: bool = False):
    """Utilitário para obter valor booleano de configuração."""
    return config.getboolean(section, key, fallback=fallback)

if __name__ == "__main__":
    # Teste do módulo
    print("🧪 Testando Configuration Manager...")
    print_project_info()
