#!/bin/bash
# =============================================================================
# Setup Script para PostgreSQL Migration Structure
# =============================================================================
#
# Script de configuração automática para o sistema de migração PostgreSQL
# enterprise-database-install-transfer-structure
#
# Autor: Enterprise Database Install Project
# Data: 02 de outubro de 2025
# Versão: 1.0.0
#
# Uso:
#   chmod +x setup_migration.sh
#   ./setup_migration.sh [--install-deps] [--test] [--help]
#
# =============================================================================

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configurações
PROJECT_NAME="PostgreSQL Migration Structure"
VERSION="1.0.0"
PYTHON_MIN_VERSION="3.8"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Função para logging
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
}

print_banner() {
    echo -e "${PURPLE}"
    echo "============================================================================="
    echo "🚀 $PROJECT_NAME - Setup Script"
    echo "============================================================================="
    echo "📅 Data: $TIMESTAMP"
    echo "🏗️ Projeto: enterprise-database-install-transfer-structure"
    echo "📍 Migração: wf004.vya.digital (PG14) → wfdb02.vya.digital (PG16)"
    echo "🔧 Versão: $VERSION"
    echo "============================================================================="
    echo -e "${NC}"
    echo
}

check_python_version() {
    log "🐍 Verificando versão do Python..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python3 não encontrado. Por favor, instale Python 3.8+"
        exit 1
    fi

    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python $python_version encontrado (>= $PYTHON_MIN_VERSION)"
    else
        log_error "Python $python_version encontrado, mas é necessário >= $PYTHON_MIN_VERSION"
        exit 1
    fi
}

check_pip_or_uv() {
    log "📦 Verificando gerenciador de pacotes..."

    if command -v uv &> /dev/null; then
        PACKAGE_MANAGER="uv"
        log_success "uv encontrado (recomendado)"
    elif command -v pip3 &> /dev/null; then
        PACKAGE_MANAGER="pip3"
        log_success "pip3 encontrado"
    else
        log_error "Nem uv nem pip3 encontrados. Por favor, instale um deles."
        exit 1
    fi
}

create_virtual_environment() {
    log "🏗️ Configurando ambiente virtual..."

    if [ -d ".venv" ]; then
        log_warning "Ambiente virtual já existe. Usando existente."
    else
        if [ "$PACKAGE_MANAGER" = "uv" ]; then
            uv venv .venv
        else
            python3 -m venv .venv
        fi
        log_success "Ambiente virtual criado"
    fi

    # Ativar ambiente virtual
    source .venv/bin/activate
    log_success "Ambiente virtual ativado"
}

install_dependencies() {
    log "📥 Instalando dependências..."

    if [ "$PACKAGE_MANAGER" = "uv" ]; then
        uv pip install -r requirements.migration.txt
    else
        pip3 install -r requirements.migration.txt
    fi

    log_success "Dependências instaladas"
}

verify_file_structure() {
    log "📁 Verificando estrutura de arquivos..."

    required_files=(
        "config/source_config.json"
        "config/destination_config.json"
        "config/migration_rules.json"
        "migration_structure.py"
        "test_migration.py"
        "requirements.migration.txt"
    )

    required_dirs=(
        "config"
        "sql"
        "reports"
    )

    all_ok=true

    # Verificar diretórios
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_success "Diretório: $dir/"
        else
            log_error "Diretório ausente: $dir/"
            all_ok=false
        fi
    done

    # Verificar arquivos
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "N/A")
            log_success "Arquivo: $file ($size bytes)"
        else
            log_error "Arquivo ausente: $file"
            all_ok=false
        fi
    done

    if [ "$all_ok" = true ]; then
        log_success "Estrutura de arquivos OK"
        return 0
    else
        log_error "Estrutura de arquivos incompleta"
        return 1
    fi
}

run_tests() {
    log "🧪 Executando testes do sistema..."

    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    fi

    if python3 test_migration.py --dry-run; then
        log_success "Todos os testes passaram!"
        return 0
    else
        log_error "Alguns testes falharam"
        return 1
    fi
}

show_usage_instructions() {
    echo
    echo -e "${CYAN}============================================================================="
    echo "📚 INSTRUÇÕES DE USO"
    echo "============================================================================="
    echo -e "${NC}"
    echo "1. 🔧 Para configurar credenciais:"
    echo "   Edite os arquivos config/*.json com suas credenciais reais"
    echo
    echo "2. 🧪 Para testar o sistema:"
    echo "   source .venv/bin/activate"
    echo "   python3 test_migration.py --dry-run    # Teste simulado"
    echo "   python3 test_migration.py              # Teste real (requer conectividade)"
    echo
    echo "3. 🚀 Para executar migração:"
    echo "   source .venv/bin/activate"
    echo "   python3 migration_structure.py"
    echo
    echo "4. 📊 Para ver logs detalhados:"
    echo "   ls -la reports/"
    echo "   tail -f reports/migration_execution_*.log"
    echo
    echo -e "${CYAN}============================================================================="
    echo -e "${NC}"
}

show_help() {
    echo "Uso: $0 [opções]"
    echo
    echo "Opções:"
    echo "  --install-deps    Instala dependências Python"
    echo "  --test           Executa testes após setup"
    echo "  --help           Mostra esta ajuda"
    echo
    echo "Exemplos:"
    echo "  $0                      # Setup básico"
    echo "  $0 --install-deps       # Setup + instalação de dependências"
    echo "  $0 --install-deps --test # Setup + deps + testes"
}

main() {
    local install_deps=false
    local run_test=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-deps)
                install_deps=true
                shift
                ;;
            --test)
                run_test=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Opção desconhecida: $1"
                show_help
                exit 1
                ;;
        esac
    done

    print_banner

    # Verificações básicas
    check_python_version

    if [ "$install_deps" = true ]; then
        check_pip_or_uv
    fi

    # Verificar estrutura de arquivos
    if ! verify_file_structure; then
        log_error "Setup não pode continuar devido a arquivos ausentes"
        exit 1
    fi

    # Instalar dependências se solicitado
    if [ "$install_deps" = true ]; then
        create_virtual_environment
        install_dependencies
    fi

    # Executar testes se solicitado
    if [ "$run_test" = true ]; then
        if ! run_tests; then
            log_warning "Testes falharam, mas setup continuou"
        fi
    fi

    # Instruções finais
    show_usage_instructions

    log_success "Setup concluído com sucesso!"
    echo
    echo -e "${GREEN}🎉 PostgreSQL Migration Structure está pronto para uso!${NC}"
}

# Executar função principal
main "$@"
