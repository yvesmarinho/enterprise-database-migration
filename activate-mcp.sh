#!/bin/bash

# Script para ativar o contexto MCP no projeto de migração PostgreSQL
# Usage: ./activate-mcp.sh OU source ./activate-mcp.sh

# Detectar se está sendo executado via source
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Executado diretamente - pode usar exit
    SOURCED=false
    set -e
else
    # Executado via source - não pode usar exit
    SOURCED=true
    set -e
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_FILE="$PROJECT_ROOT/.vscode/mcp.json"

# Função para sair adequadamente dependendo do modo de execução
safe_exit() {
    if [ "$SOURCED" = true ]; then
        echo "❌ Erro detectado. Retornando ao terminal..."
        return 1
    else
        exit 1
    fi
}

echo "🚀 Ativando contexto MCP do PostgreSQL Migration System..."

# Verificar se o arquivo MCP existe
if [ ! -f "$MCP_FILE" ]; then
    echo "❌ Erro: Arquivo mcp.json não encontrado em .vscode/"
    echo "💡 Execute 'make build-mcp' primeiro"
    safe_exit
fi

# Validar JSON (se jq estiver disponível)
if command -v jq >/dev/null 2>&1; then
    if ! jq . "$MCP_FILE" > /dev/null 2>&1; then
        echo "❌ Erro: Arquivo mcp.json contém JSON inválido"
        safe_exit
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

# Configurar ambiente Python
echo ""
echo "🐍 Configurando ambiente Python..."

if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "  ✅ $PYTHON_VERSION"
else
    echo "  ❌ Python 3 não encontrado"
    safe_exit
fi

# Desativar ambiente virtual atual se houver
if [ -n "$VIRTUAL_ENV" ]; then
    echo "  🔄 Desativando ambiente virtual atual: $(basename $VIRTUAL_ENV)"
    unset VIRTUAL_ENV
    unset PYTHONPATH
fi

# Configurar ambiente virtual do projeto
VENV_PATHS=(
    "$PROJECT_ROOT/.venv"
    "$PROJECT_ROOT/venv"
)

VENV_ACTIVATED=0
for venv_path in "${VENV_PATHS[@]}"; do
    if [ -d "$venv_path" ] && [ -f "$venv_path/bin/activate" ]; then
        echo "  ✅ Ativando ambiente virtual: $venv_path"
        source "$venv_path/bin/activate"
        export VIRTUAL_ENV="$venv_path"
        export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
        VENV_ACTIVATED=1
        break
    fi
done

if [ $VENV_ACTIVATED -eq 0 ]; then
    echo "  ⚠️  Ambiente virtual não encontrado"
    echo "     💡 Criando ambiente virtual com uv..."

    if command -v uv >/dev/null 2>&1; then
        cd "$PROJECT_ROOT"
        uv venv
        source ".venv/bin/activate"
        export VIRTUAL_ENV="$PROJECT_ROOT/.venv"
        export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
        echo "  ✅ Ambiente virtual criado e ativado: $PROJECT_ROOT/.venv"
    else
        echo "     💡 Execute: make install-deps ou instale uv primeiro"
    fi
fi

# Verificar se ambiente está ativo
if [ -n "$VIRTUAL_ENV" ]; then
    echo "  🎯 Ambiente ativo: $VIRTUAL_ENV"
    echo "  📁 Python path: $PYTHONPATH"
else
    echo "  ❌ Nenhum ambiente virtual ativo"
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
echo ""

if [ "$SOURCED" = true ]; then
    echo "✅ Ambiente configurado no terminal atual!"
    echo "🎯 Agora você pode usar diretamente:"
    echo "   python main.py status"
    echo "   uv run main.py status"
else
    echo "🔧 Para aplicar as configurações no terminal atual, execute:"
    echo "   source ./activate-mcp.sh"
    echo ""
    echo "🎯 Ou simplesmente use uv que gerencia automaticamente:"
    echo "   uv run main.py status"
fi
