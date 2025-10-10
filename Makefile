#!/usr/bin/make -f

# Makefile para PostgreSQL Migration System
# Fluxo: objetivo.yaml → configuração → migração → validação → relatórios
# Usage: make <target>

.PHONY: help setup clean install-deps test lint format validate migrate migrate-auto migrate-interactive cleanup-db reports status monitor logs backup rollback dev-setup production-setup docker-setup

# Configurações
OBJETIVO_FILE := objetivo.yaml
CONFIG_FILE := mcp-questions.yaml
MCP_CONFIG := .vscode/mcp.json
VSCODE_DIR := .vscode
SRC_DIR := core
TEST_DIR := test
DOCS_DIR := docs
SECRETS_DIR := secrets
LOG_DIR := logs
REPORTS_DIR := reports

# Cores para output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m # No Color

# Python e ambiente
PYTHON := python3
PIP := pip3
VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# Target padrão
help: ## Mostra esta ajuda com fluxo de trabalho
	@echo "$(BLUE)PostgreSQL Migration System - Fluxo de Migração$(NC)"
	@echo "$(CYAN)objetivo.yaml → configuração → migração → validação$(NC)"
	@echo ""
	@echo "$(YELLOW)🚀 FLUXO PRINCIPAL:$(NC)"
	@echo "  $(GREEN)1. setup$(NC)              - Setup completo do projeto"
	@echo "  $(GREEN)2. migrate-interactive$(NC) - Migração interativa"
	@echo "  $(GREEN)3. migrate-auto$(NC)        - Migração automática"
	@echo "  $(GREEN)4. validate$(NC)            - Validar dados migrados"
	@echo "  $(GREEN)5. reports$(NC)             - Gerar relatórios"
	@echo ""
	@echo "$(YELLOW)⚙️  CONFIGURAÇÃO:$(NC)"
	@echo "  $(GREEN)install-deps$(NC)           - Instalar dependências"
	@echo "  $(GREEN)setup-secrets$(NC)          - Configurar arquivos secrets"
	@echo "  $(GREEN)test-connection$(NC)        - Testar conexões de banco"
	@echo ""
	@echo "$(YELLOW)🔧 DESENVOLVIMENTO:$(NC)"
	@echo "  $(GREEN)dev-setup$(NC)              - Setup ambiente desenvolvimento"
	@echo "  $(GREEN)test$(NC)                   - Executar testes"
	@echo "  $(GREEN)lint$(NC)                   - Verificar qualidade código"
	@echo "  $(GREEN)format$(NC)                 - Formatar código"
	@echo ""
	@echo "$(YELLOW)🗄️  MIGRAÇÃO:$(NC)"
	@echo "  $(GREEN)migrate$(NC)                - Migração padrão"
	@echo "  $(GREEN)migrate-parallel$(NC)       - Migração paralela"
	@echo "  $(GREEN)migrate-incremental$(NC)    - Migração incremental"
	@echo "  $(GREEN)rollback$(NC)               - Rollback da migração"
	@echo ""
	@echo "$(YELLOW)📊 MONITORAMENTO:$(NC)"
	@echo "  $(GREEN)status$(NC)                 - Status da migração"
	@echo "  $(GREEN)monitor$(NC)                - Monitor em tempo real"
	@echo "  $(GREEN)logs$(NC)                   - Visualizar logs"
	@echo "  $(GREEN)metrics$(NC)                - Métricas de performance"
	@echo ""
	@echo "$(YELLOW)🛠️  MANUTENÇÃO:$(NC)"
	@echo "  $(GREEN)cleanup-db$(NC)             - Limpeza de banco"
	@echo "  $(GREEN)backup$(NC)                 - Backup dos dados"
	@echo "  $(GREEN)clean$(NC)                  - Limpeza do projeto"
	@echo ""

# === SETUP E CONFIGURAÇÃO ===

setup: ## Setup completo do projeto
	@echo "$(YELLOW)🚀 Iniciando setup do PostgreSQL Migration System...$(NC)"
	$(MAKE) install-deps
	$(MAKE) setup-directories
	$(MAKE) setup-secrets
	$(MAKE) build-mcp
	@echo "$(GREEN)✅ Setup concluído com sucesso!$(NC)"

setup-directories: ## Criar diretórios necessários
	@echo "$(CYAN)📁 Criando estrutura de diretórios...$(NC)"
	@mkdir -p $(LOG_DIR) $(REPORTS_DIR) $(TEST_DIR)
	@mkdir -p $(SECRETS_DIR) || true
	@echo "$(GREEN)✅ Diretórios criados$(NC)"

install-deps: ## Instalar dependências
	@echo "$(CYAN)📦 Instalando dependências...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
	fi
	@$(VENV_PIP) install --upgrade pip
	@if [ -f "requirements.txt" ]; then \
		$(VENV_PIP) install -r requirements.txt; \
	else \
		$(VENV_PIP) install sqlalchemy asyncpg psycopg2-binary pytest pylint black; \
	fi
	@echo "$(GREEN)✅ Dependências instaladas$(NC)"

setup-secrets: ## Configurar arquivos secrets
	@echo "$(CYAN)🔐 Configurando arquivos secrets...$(NC)"
	@if [ ! -f "$(SECRETS_DIR)/source_config.json" ]; then \
		echo "$(YELLOW)⚠️  Copiando template para source_config.json$(NC)"; \
		cp source_config_template.json $(SECRETS_DIR)/source_config.json; \
		echo "$(RED)❗ Configure $(SECRETS_DIR)/source_config.json$(NC)"; \
	fi
	@if [ ! -f "$(SECRETS_DIR)/destination_config.json" ]; then \
		echo "$(YELLOW)⚠️  Copiando template para destination_config.json$(NC)"; \
		cp destination_config_template.json $(SECRETS_DIR)/destination_config.json; \
		echo "$(RED)❗ Configure $(SECRETS_DIR)/destination_config.json$(NC)"; \
	fi
	@echo "$(GREEN)✅ Arquivos secrets configurados$(NC)"

# === MIGRAÇÃO ===

migrate: migrate-interactive ## Migração padrão (interativa)

migrate-interactive: ## Migração interativa
	@echo "$(YELLOW)🔄 Iniciando migração interativa...$(NC)"
	@$(VENV_PYTHON) cli/run_migration.py || $(PYTHON) cli/run_migration.py
	@echo "$(GREEN)✅ Migração interativa concluída$(NC)"

migrate-auto: ## Migração automática
	@echo "$(YELLOW)🤖 Iniciando migração automática...$(NC)"
	@$(VENV_PYTHON) cli/run_migration.py --auto --verbose || $(PYTHON) cli/run_migration.py --auto --verbose
	@echo "$(GREEN)✅ Migração automática concluída$(NC)"

migrate-parallel: ## Migração paralela
	@echo "$(YELLOW)⚡ Iniciando migração paralela...$(NC)"
	@$(VENV_PYTHON) $(SRC_DIR)/orchestrator_pure_python.py --parallel || $(PYTHON) $(SRC_DIR)/orchestrator_pure_python.py --parallel
	@echo "$(GREEN)✅ Migração paralela concluída$(NC)"

migrate-incremental: ## Migração incremental
	@echo "$(YELLOW)📈 Iniciando migração incremental...$(NC)"
	@$(VENV_PYTHON) $(SRC_DIR)/orchestrator_pure_python.py --incremental || $(PYTHON) $(SRC_DIR)/orchestrator_pure_python.py --incremental
	@echo "$(GREEN)✅ Migração incremental concluída$(NC)"

# === VALIDAÇÃO E RELATÓRIOS ===

validate: ## Validar dados migrados
	@echo "$(YELLOW)🔍 Validando dados migrados...$(NC)"
	@$(VENV_PYTHON) $(SRC_DIR)/validator.py --validate-all || $(PYTHON) $(SRC_DIR)/validator.py --validate-all
	@echo "$(GREEN)✅ Validação concluída$(NC)"

reports: ## Gerar relatórios de migração
	@echo "$(YELLOW)📊 Gerando relatórios...$(NC)"
	@$(VENV_PYTHON) -c "from $(SRC_DIR).monitor import generate_reports; generate_reports()" || \
	 $(PYTHON) -c "from $(SRC_DIR).monitor import generate_reports; generate_reports()"
	@echo "$(GREEN)✅ Relatórios gerados em $(REPORTS_DIR)/$(NC)"

status: ## Verificar status da migração
	@echo "$(YELLOW)📋 Verificando status da migração...$(NC)"
	@$(VENV_PYTHON) -c "from $(SRC_DIR).monitor import check_migration_status; check_migration_status()" || \
	 $(PYTHON) -c "from $(SRC_DIR).monitor import check_migration_status; check_migration_status()"

# === TESTES E QUALIDADE ===

test: ## Executar todos os testes
	@echo "$(YELLOW)🧪 Executando testes...$(NC)"
	@$(VENV_PYTHON) -m pytest $(TEST_DIR)/ -v || $(PYTHON) -m pytest $(TEST_DIR)/ -v
	@echo "$(GREEN)✅ Testes concluídos$(NC)"

test-connection: ## Testar conexões de banco
	@echo "$(YELLOW)🔌 Testando conexões...$(NC)"
	@$(VENV_PYTHON) -c "from $(SRC_DIR).validator import test_connections; test_connections()" || \
	 $(PYTHON) -c "from $(SRC_DIR).validator import test_connections; test_connections()"
	@echo "$(GREEN)✅ Teste de conexões concluído$(NC)"

lint: ## Verificar qualidade do código
	@echo "$(YELLOW)🔍 Verificando qualidade do código...$(NC)"
	@$(VENV_PYTHON) -m pylint $(SRC_DIR)/ || $(PYTHON) -m pylint $(SRC_DIR)/ || true
	@echo "$(GREEN)✅ Verificação de qualidade concluída$(NC)"

format: ## Formatar código
	@echo "$(YELLOW)✨ Formatando código...$(NC)"
	@$(VENV_PYTHON) -m black $(SRC_DIR)/ || $(PYTHON) -m black $(SRC_DIR)/ || true
	@echo "$(GREEN)✅ Código formatado$(NC)"

# === MONITORAMENTO ===

monitor: ## Monitor em tempo real
	@echo "$(YELLOW)📺 Iniciando monitor em tempo real...$(NC)"
	@echo "$(CYAN)Pressione Ctrl+C para sair$(NC)"
	@$(VENV_PYTHON) -c "from $(SRC_DIR).monitor import start_realtime_monitor; start_realtime_monitor()" || \
	 $(PYTHON) -c "from $(SRC_DIR).monitor import start_realtime_monitor; start_realtime_monitor()"

logs: ## Visualizar logs
	@echo "$(YELLOW)📜 Logs de migração:$(NC)"
	@if [ -f "$(LOG_DIR)/migration.log" ]; then \
		tail -n 50 $(LOG_DIR)/migration.log; \
	else \
		echo "$(RED)❌ Arquivo de log não encontrado$(NC)"; \
	fi

logs-follow: ## Seguir logs em tempo real
	@echo "$(YELLOW)📜 Seguindo logs em tempo real...$(NC)"
	@echo "$(CYAN)Pressione Ctrl+C para sair$(NC)"
	@tail -f $(LOG_DIR)/migration.log

metrics: ## Exibir métricas de performance
	@echo "$(YELLOW)📈 Métricas de performance:$(NC)"
	@$(VENV_PYTHON) -c "from $(SRC_DIR).monitor import show_metrics; show_metrics()" || \
	 $(PYTHON) -c "from $(SRC_DIR).monitor import show_metrics; show_metrics()"

# === MANUTENÇÃO ===

cleanup-db: ## Limpeza de banco de dados
	@echo "$(YELLOW)🧹 Executando limpeza de banco...$(NC)"
	@$(VENV_PYTHON) cleanup/cleanup_database.py || $(PYTHON) cleanup/cleanup_database.py
	@echo "$(GREEN)✅ Limpeza de banco concluída$(NC)"

backup: ## Backup dos dados
	@echo "$(YELLOW)💾 Executando backup...$(NC)"
	@$(VENV_PYTHON) -c "from $(SRC_DIR).backup import create_backup; create_backup()" || \
	 $(PYTHON) -c "from $(SRC_DIR).backup import create_backup; create_backup()"
	@echo "$(GREEN)✅ Backup concluído$(NC)"

rollback: ## Rollback da migração
	@echo "$(YELLOW)⏪ Executando rollback...$(NC)"
	@echo "$(RED)⚠️  ATENÇÃO: Esta operação irá reverter a migração$(NC)"
	@read -p "Deseja continuar? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(VENV_PYTHON) $(SRC_DIR)/orchestrator_pure_python.py --rollback || \
		$(PYTHON) $(SRC_DIR)/orchestrator_pure_python.py --rollback; \
	else \
		echo "$(YELLOW)Rollback cancelado$(NC)"; \
	fi

# === MCP E VS CODE ===

build-mcp: ## Construir configuração MCP
	@echo "$(YELLOW)🔧 Construindo configuração MCP...$(NC)"
	@if [ ! -d "$(VSCODE_DIR)" ]; then mkdir -p $(VSCODE_DIR); fi
	@if [ -f "$(MCP_CONFIG)" ]; then \
		echo "$(GREEN)✅ Configuração MCP encontrada$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Criando configuração MCP básica$(NC)"; \
		echo '{"project": {"name": "postgresql-migration-system"}}' > $(MCP_CONFIG); \
	fi
	@echo "$(GREEN)✅ Configuração MCP preparada$(NC)"

activate-context: ## Ativar contexto MCP
	@echo "$(YELLOW)🚀 Ativando contexto MCP...$(NC)"
	@if [ -f "./activate-mcp.sh" ]; then \
		./activate-mcp.sh; \
	else \
		echo "$(RED)❌ Script activate-mcp.sh não encontrado$(NC)"; \
		echo "$(YELLOW)💡 Execute: make setup-mcp-script$(NC)"; \
	fi

setup-mcp-script: ## Criar script de ativação MCP
	@echo "$(YELLOW)📝 Criando script de ativação MCP...$(NC)"
	@cat > activate-mcp.sh << 'EOF'
#!/bin/bash
set -e
PROJECT_ROOT="$$(cd "$$(dirname "$${BASH_SOURCE[0]}")" && pwd)"
MCP_FILE="$$PROJECT_ROOT/.vscode/mcp.json"
echo "🚀 Ativando contexto MCP do PostgreSQL Migration System..."
if [ ! -f "$$MCP_FILE" ]; then
    echo "❌ Erro: Arquivo mcp.json não encontrado em .vscode/"
    echo "💡 Execute 'make build-mcp' primeiro"
    exit 1
fi
echo "✅ Contexto MCP ativado com sucesso!"
echo "📁 Projeto: postgresql-migration-system"
echo "📍 Local: $$PROJECT_ROOT"
EOF
	@chmod +x activate-mcp.sh
	@echo "$(GREEN)✅ Script activate-mcp.sh criado$(NC)"

# === AMBIENTES ===

dev-setup: ## Setup ambiente de desenvolvimento
	@echo "$(YELLOW)🛠️  Configurando ambiente de desenvolvimento...$(NC)"
	$(MAKE) install-deps
	$(MAKE) setup-directories
	@echo "export MIGRATION_LOG_LEVEL=DEBUG" > .env
	@echo "export PYTHONPATH=." >> .env
	@echo "$(GREEN)✅ Ambiente de desenvolvimento configurado$(NC)"
	@echo "$(CYAN)💡 Execute: source .env$(NC)"

production-setup: ## Setup ambiente de produção
	@echo "$(YELLOW)🏭 Configurando ambiente de produção...$(NC)"
	$(MAKE) install-deps
	$(MAKE) setup-directories
	$(MAKE) setup-secrets
	@echo "export MIGRATION_LOG_LEVEL=INFO" > .env.production
	@echo "export PYTHONPATH=." >> .env.production
	@echo "$(GREEN)✅ Ambiente de produção configurado$(NC)"

docker-setup: ## Setup com Docker
	@echo "$(YELLOW)🐳 Configurando ambiente Docker...$(NC)"
	@if [ ! -f "docker-compose.yml" ]; then \
		echo "$(RED)❌ docker-compose.yml não encontrado$(NC)"; \
		echo "$(YELLOW)💡 Criando docker-compose.yml básico...$(NC)"; \
		$(MAKE) create-docker-compose; \
	fi
	@docker-compose up -d
	@echo "$(GREEN)✅ Ambiente Docker configurado$(NC)"

create-docker-compose: ## Criar docker-compose.yml
	@cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  migration-system:
    build: .
    volumes:
      - .:/app
      - ./logs:/app/logs
      - ./reports:/app/reports
    environment:
      - MIGRATION_LOG_LEVEL=INFO
      - PYTHONPATH=/app
    networks:
      - migration-network

  postgres-source:
    image: postgres:14
    environment:
      POSTGRES_DB: source_db
      POSTGRES_USER: migration_user
      POSTGRES_PASSWORD: migration_pass
    networks:
      - migration-network

  postgres-destination:
    image: postgres:16
    environment:
      POSTGRES_DB: destination_db
      POSTGRES_USER: migration_user
      POSTGRES_PASSWORD: migration_pass
    networks:
      - migration-network

networks:
  migration-network:
    driver: bridge
EOF

# === LIMPEZA ===

clean: ## Limpeza completa do projeto
	@echo "$(YELLOW)🧹 Executando limpeza completa...$(NC)"
	@rm -rf __pycache__/
	@rm -rf $(SRC_DIR)/__pycache__/
	@rm -rf .pytest_cache/
	@rm -rf *.pyc
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Limpeza concluída$(NC)"

clean-logs: ## Limpar logs
	@echo "$(YELLOW)🗑️  Limpando logs...$(NC)"
	@rm -rf $(LOG_DIR)/*.log
	@echo "$(GREEN)✅ Logs limpos$(NC)"

clean-reports: ## Limpar relatórios
	@echo "$(YELLOW)🗑️  Limpando relatórios...$(NC)"
	@rm -rf $(REPORTS_DIR)/*
	@echo "$(GREEN)✅ Relatórios limpos$(NC)"

clean-all: clean clean-logs clean-reports ## Limpeza total

# === HELP DETALHADO ===

help-migration: ## Ajuda detalhada sobre migração
	@echo "$(BLUE)Guia Detalhado de Migração$(NC)"
	@echo ""
	@echo "$(YELLOW)1. PREPARAÇÃO:$(NC)"
	@echo "   make setup              # Setup inicial"
	@echo "   make test-connection    # Testar conexões"
	@echo ""
	@echo "$(YELLOW)2. MIGRAÇÃO:$(NC)"
	@echo "   make migrate-interactive # Para ambiente de teste"
	@echo "   make migrate-auto       # Para produção"
	@echo ""
	@echo "$(YELLOW)3. VALIDAÇÃO:$(NC)"
	@echo "   make validate          # Validar dados"
	@echo "   make reports           # Gerar relatórios"
	@echo ""
	@echo "$(YELLOW)4. MONITORAMENTO:$(NC)"
	@echo "   make status            # Status atual"
	@echo "   make logs              # Ver logs"
	@echo "   make monitor           # Monitor em tempo real"

# Mostrar ajuda como padrão
.DEFAULT_GOAL := help
