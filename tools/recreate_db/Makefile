.PHONY: help install test clean example list mysql postgres

help:
	@echo "Database Recreator - Comandos Disponíveis"
	@echo ""
	@echo "  make install      - Instala dependências Python"
	@echo "  make test         - Executa testes automatizados"
	@echo "  make example      - Executa exemplos interativos"
	@echo "  make list         - Lista arquivos de configuração"
	@echo "  make clean        - Remove arquivos temporários"
	@echo ""
	@echo "  make mysql DB=nome_db CONFIG=config.json       - Recria banco MySQL"
	@echo "  make postgres DB=nome_db CONFIG=config.json    - Recria banco PostgreSQL"
	@echo ""
	@echo "NOTA: Por padrão, conexões ativas SÃO terminadas (force=True)"
	@echo "      Para desabilitar, adicione NO_FORCE=1 ao comando"
	@echo ""
	@echo "Exemplos:"
	@echo "  make install"
	@echo "  make test"
	@echo "  make mysql DB=perfexcrm_db CONFIG=mysql_config.json"
	@echo "  make postgres DB=chatwoot_dev_db CONFIG=wfdb02_postgres.json"
	@echo "  make postgres DB=chatwoot_dev_db CONFIG=wfdb02_postgres.json NO_FORCE=1"

install:
	@echo "📦 Instalando dependências..."
	pip3 install -r requirements.txt
	@echo "✅ Dependências instaladas!"

test:
	@echo "🧪 Executando testes..."
	python3 test_recreator.py

example:
	@echo "📚 Executando exemplos..."
	python3 example_usage.py

list:
	@echo "📋 Arquivos de configuração disponíveis:"
	@ls -1 ../../secrets/*.json 2>/dev/null || echo "Nenhum arquivo encontrado"

clean:
	@echo "🧹 Limpando arquivos temporários..."
	rm -rf __pycache__
	rm -f *.pyc
	rm -f /tmp/test_*.json
	rm -f temp_config.json
	@echo "✅ Limpeza concluída!"

# Uso: make mysql DB=perfexcrm_db CONFIG=mysql_config.json
# Opcionalmente: make mysql DB=nome_db CONFIG=config.json NO_FORCE=1
mysql:
ifndef DB
	$(error DB não definido. Uso: make mysql DB=nome_db CONFIG=config.json)
endif
ifndef CONFIG
	$(error CONFIG não definido. Uso: make mysql DB=nome_db CONFIG=config.json)
endif
	@echo "🔄 Recriando banco MySQL '$(DB)'..."
	@echo "   Config: ../../secrets/$(CONFIG)"
	@echo "   Force: $(if $(NO_FORCE),NÃO (--no-force),SIM (padrão - termina conexões))"
	python3 recreate_database.py \
		--config ../../secrets/$(CONFIG) \
		--database $(DB) \
		--verbose \
		$(if $(NO_FORCE),--no-force,)

# Uso: make postgres DB=app_workforce CONFIG=postgresql_source_config.json
# Opcionalmente: make postgres DB=nome_db CONFIG=config.json NO_FORCE=1
postgres:
ifndef DB
	$(error DB não definido. Uso: make postgres DB=nome_db CONFIG=config.json)
endif
ifndef CONFIG
	$(error CONFIG não definido. Uso: make postgres DB=nome_db CONFIG=config.json)
endif
	@echo "🔄 Recriando banco PostgreSQL '$(DB)'..."
	@echo "   Config: ../../secrets/$(CONFIG)"
	@echo "   Force: $(if $(NO_FORCE),NÃO (--no-force),SIM (padrão - termina conexões))"
	python3 recreate_database.py \
		--config ../../secrets/$(CONFIG) \
		--database $(DB) \
		--verbose \
		$(if $(NO_FORCE),--no-force,)

# Alias
deps: install
tests: test
examples: example
ls: list
