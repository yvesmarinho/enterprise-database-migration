# ===========================================================================
# tools/Makefile — Utilitários PostgreSQL
# Executar a partir da RAIZ do projeto:  make -f tools/Makefile <alvo>
# Ou entre na pasta tools/ e execute:    make <alvo>
# ===========================================================================

PYTHON   := ../.venv/bin/python
SECRETS  := ../secrets

MIGRATE  := migrate_users/migrate_targeted_users_and_db.py
FIX      := fix_permissions/fix_permissions.py
VERIFY   := fix_permissions/verify_metabase_permissions.py

# Valores padrão (sobrescreva na linha de comando)
SOURCE  ?=
DESTINY ?=
SERVER  ?=
DB      ?=
CONFIG  ?= fix_permissions.json

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Ajuda
# ---------------------------------------------------------------------------
.PHONY: help
help:
	@echo ""
	@echo "  tools/ — Utilitários PostgreSQL"
	@echo "  ================================"
	@echo ""
	@echo "  MIGRATE USERS"
	@echo "  -------------"
	@echo "  make migrate-list                        Lista configs disponíveis em secrets/"
	@echo "  make migrate-dry   SOURCE=x DESTINY=y   Dry-run da migração de usuários"
	@echo "  make migrate       SOURCE=x DESTINY=y   Executa migração de usuários"
	@echo "  make migrate-verbose SOURCE=x DESTINY=y Migração com log detalhado"
	@echo ""
	@echo "  FIX PERMISSIONS"
	@echo "  ---------------"
	@echo "  make fix-list                                   Lista servidores e configs disponíveis"
	@echo "  make fix-dry    SERVER=x DB=nome               Dry-run para um banco"
	@echo "  make fix        SERVER=x DB=nome               Corrige permissões de um banco"
	@echo "  make fix-all    SERVER=x                       Corrige todos os bancos do config"
	@echo "  make fix        SERVER=x DB=nome CONFIG=file   Usa config alternativa"
	@echo "  make fix-interactive                            Modo interativo (pede servidor/banco)"
	@echo "  make fix-verify                                 Verifica permissões do metabase"
	@echo ""
	@echo "  GERAL"
	@echo "  -----"
	@echo "  make list-secrets                              Lista arquivos JSON em secrets/"
	@echo ""

# ---------------------------------------------------------------------------
# Listar configs
# ---------------------------------------------------------------------------
.PHONY: list-secrets migrate-list
list-secrets migrate-list:
	@$(PYTHON) $(MIGRATE) --list-configs

# ---------------------------------------------------------------------------
# migrate_users
# ---------------------------------------------------------------------------
.PHONY: migrate-dry
migrate-dry:
	@[ -n "$(SOURCE)" ]  || (echo "Erro: informe SOURCE=<arquivo>"; exit 1)
	@[ -n "$(DESTINY)" ] || (echo "Erro: informe DESTINY=<arquivo>"; exit 1)
	$(PYTHON) $(MIGRATE) \
		--source  $(SOURCE) \
		--destiny $(DESTINY) \
		--dry-run

.PHONY: migrate
migrate:
	@[ -n "$(SOURCE)" ]  || (echo "Erro: informe SOURCE=<arquivo>"; exit 1)
	@[ -n "$(DESTINY)" ] || (echo "Erro: informe DESTINY=<arquivo>"; exit 1)
	$(PYTHON) $(MIGRATE) \
		--source  $(SOURCE) \
		--destiny $(DESTINY)

.PHONY: migrate-verbose
migrate-verbose:
	@[ -n "$(SOURCE)" ]  || (echo "Erro: informe SOURCE=<arquivo>"; exit 1)
	@[ -n "$(DESTINY)" ] || (echo "Erro: informe DESTINY=<arquivo>"; exit 1)
	$(PYTHON) $(MIGRATE) \
		--source  $(SOURCE) \
		--destiny $(DESTINY) \
		--verbose

# Modo interativo (pede os arquivos ao executar)
.PHONY: migrate-interactive
migrate-interactive:
	$(PYTHON) $(MIGRATE)

# ---------------------------------------------------------------------------
# fix_permissions
# ---------------------------------------------------------------------------
.PHONY: fix-list
fix-list:
	$(PYTHON) $(FIX) --list-configs

.PHONY: fix-dry
fix-dry:
	@[ -n "$(SERVER)" ] || (echo "Erro: informe SERVER=<arquivo>"; exit 1)
	@[ -n "$(DB)" ]     || (echo "Erro: informe DB=<nome_do_banco>"; exit 1)
	$(PYTHON) $(FIX) \
		--server   $(SERVER) \
		--config   $(CONFIG) \
		--database $(DB) \
		--dry-run

.PHONY: fix
fix:
	@[ -n "$(SERVER)" ] || (echo "Erro: informe SERVER=<arquivo>"; exit 1)
	@[ -n "$(DB)" ]     || (echo "Erro: informe DB=<nome_do_banco>"; exit 1)
	$(PYTHON) $(FIX) \
		--server   $(SERVER) \
		--config   $(CONFIG) \
		--database $(DB) \
		--execute

.PHONY: fix-verbose
fix-verbose:
	@[ -n "$(SERVER)" ] || (echo "Erro: informe SERVER=<arquivo>"; exit 1)
	@[ -n "$(DB)" ]     || (echo "Erro: informe DB=<nome_do_banco>"; exit 1)
	$(PYTHON) $(FIX) \
		--server   $(SERVER) \
		--config   $(CONFIG) \
		--database $(DB) \
		--execute \
		--verbose

.PHONY: fix-all
fix-all:
	@[ -n "$(SERVER)" ] || (echo "Erro: informe SERVER=<arquivo>"; exit 1)
	$(PYTHON) $(FIX) \
		--server $(SERVER) \
		--config $(CONFIG) \
		--all \
		--execute

.PHONY: fix-all-verbose
fix-all-verbose:
	@[ -n "$(SERVER)" ] || (echo "Erro: informe SERVER=<arquivo>"; exit 1)
	$(PYTHON) $(FIX) \
		--server $(SERVER) \
		--config $(CONFIG) \
		--all \
		--execute \
		--verbose

# Modo interativo (pede servidor, config e banco ao executar)
.PHONY: fix-interactive
fix-interactive:
	$(PYTHON) $(FIX) --execute

.PHONY: fix-verify
fix-verify:
	$(PYTHON) $(VERIFY)
