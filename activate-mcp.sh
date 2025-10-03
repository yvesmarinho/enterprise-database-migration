#!/bin/bash

# Script para ativar o contexto MCP no projeto de migração PostgreSQL
# Usage: ./activate-mcp.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_FILE="$PROJECT_ROOT/.vscode/mcp.json"

echo "🚀 Ativando contexto MCP do PostgreSQL Migration System..."

# Verificar se o arquivo MCP existe
if [ ! -f "$MCP_FILE" ]; then
    echo "❌ Erro: Arquivo mcp.json não encontrado em .vscode/"
    echo "💡 Execute 'make build-mcp' primeiro"
    exit 1
fi

# Validar JSON (se jq estiver disponível)
if command -v jq >/dev/null 2>&1; then
    if ! jq . "$MCP_FILE" > /dev/null 2>&1; then
        echo "❌ Erro: Arquivo mcp.json contém JSON inválido"
        exit 1
    fi
else
    echo "⚠️  jq não encontrado - pulando validação JSON"
fi

# Exibir informações do projeto
echo ""
echo "📋 Informações do Projeto:"
echo "  🏷️  Nome: PostgreSQL Migration System"
echo "  📁 Local: $PROJECT_ROOT"
echo "  🔧 Tipo: Sistema de Migração Enterprise"
echo "  📊 Versão: 1.0.0"

# Verificar estrutura de diretórios
echo ""
echo "📂 Verificando estrutura do projeto..."

# Diretórios essenciais
DIRS_TO_CHECK=(
    "core"
    "secrets"
    "config"
    "cleanup"
    "scripts"
    "docs"
    ".vscode"
)

for dir in "${DIRS_TO_CHECK[@]}"; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ (não encontrado)"
    fi
done

# Verificar arquivos principais
echo ""
echo "📄 Verificando arquivos principais..."

FILES_TO_CHECK=(
    "objetivo.yaml"
    "mcp-questions.yaml"
    "README.md"
    "Makefile"
    "source_config_template.json"
    "destination_config_template.json"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (não encontrado)"
    fi
done

# Verificar arquivos secrets
echo ""
echo "🔐 Verificando configurações secrets..."

SECRET_FILES=(
    "secrets/source_config.json"
    "secrets/destination_config.json"
    "secrets/postgresql_source_config.json"
    "secrets/postgresql_destination_config.json"
)

secrets_configured=0
for file in "${SECRET_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo "  ✅ $file"
        secrets_configured=$((secrets_configured + 1))
    else
        echo "  ⚠️  $file (não configurado)"
    fi
done

if [ $secrets_configured -eq 0 ]; then
    echo ""
    echo "⚠️  ATENÇÃO: Nenhum arquivo de configuração secrets encontrado!"
    echo "💡 Execute: make setup-secrets"
fi

# Verificar dependências Python
echo ""
echo "🐍 Verificando ambiente Python..."

if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  ✅ $PYTHON_VERSION"
else
    echo "  ❌ Python 3 não encontrado"
fi

if [ -d "$PROJECT_ROOT/venv" ]; then
    echo "  ✅ Ambiente virtual encontrado (venv/)"
else
    echo "  ⚠️  Ambiente virtual não encontrado"
    echo "     💡 Execute: make install-deps"
fi

# Verificar se há logs ou relatórios
echo ""
echo "📊 Verificando logs e relatórios..."

if [ -d "$PROJECT_ROOT/logs" ] && [ "$(ls -A $PROJECT_ROOT/logs 2>/dev/null)" ]; then
    LOG_COUNT=$(ls -1 "$PROJECT_ROOT/logs"/*.log 2>/dev/null | wc -l)
    echo "  📜 $LOG_COUNT arquivo(s) de log encontrado(s)"
else
    echo "  📜 Nenhum log encontrado"
fi

if [ -d "$PROJECT_ROOT/reports" ] && [ "$(ls -A $PROJECT_ROOT/reports 2>/dev/null)" ]; then
    REPORT_COUNT=$(ls -1 "$PROJECT_ROOT/reports" 2>/dev/null | wc -l)
    echo "  📊 $REPORT_COUNT relatório(s) encontrado(s)"
else
    echo "  📊 Nenhum relatório encontrado"
fi

# Sugestões de próximos passos
echo ""
echo "🎯 Próximos Passos Sugeridos:"

if [ $secrets_configured -eq 0 ]; then
    echo "  1️⃣  Configurar secrets: make setup-secrets"
fi

if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "  2️⃣  Instalar dependências: make install-deps"
fi

echo "  3️⃣  Testar conexões: make test-connection"
echo "  4️⃣  Executar migração: make migrate-interactive"
echo "  5️⃣  Validar resultados: make validate"

# Comandos úteis
echo ""
echo "💡 Comandos Úteis:"
echo "  make help              # Ver todos os comandos disponíveis"
echo "  make status            # Verificar status da migração"
echo "  make logs              # Ver logs recentes"
echo "  make monitor           # Monitor em tempo real"

echo ""
echo "✅ Contexto MCP ativado com sucesso!"
echo "📖 Consulte o README.md para documentação completa"

# Se estiver em ambiente de desenvolvimento, mostrar informações extras
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo ""
    echo "🛠️  Ambiente de desenvolvimento detectado"
    echo "   Use: source .env && make dev-setup"
fi

echo ""
echo "🚀 Sistema pronto para uso!"
