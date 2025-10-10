#!/bin/bash
# PostgreSQL Enterprise Migration System v4.0.0
# Script de inicialização e setup

echo "🚀 PostgreSQL Enterprise Migration System v4.0.0"
echo "================================================"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.8+"
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"

# Verificar/instalar dependências
echo "📦 Verificando dependências..."

if ! python3 -c "import psycopg2" &> /dev/null; then
    echo "⚠️ psycopg2 não encontrado. Instalando..."
    pip3 install psycopg2-binary
    if [ $? -eq 0 ]; then
        echo "✅ psycopg2 instalado com sucesso"
    else
        echo "❌ Falha na instalação do psycopg2"
        exit 1
    fi
else
    echo "✅ psycopg2 já instalado"
fi

# Criar estrutura de diretórios
echo "📁 Criando estrutura de diretórios..."

directories=(
    "logs"
    "reports"
    "extracted_data"
    "generated_scripts"
    "config"
    "secrets"
    "core/modules"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "  📂 Criado: $dir/"
    else
        echo "  ✅ Existe: $dir/"
    fi
done

# Verificar arquivos de configuração
echo "⚙️ Verificando configurações..."

if [ ! -f "config/migration_config.json" ]; then
    echo "⚠️ Arquivo de configuração principal não encontrado"
    echo "   Será criado automaticamente na primeira execução"
fi

if [ ! -f "secrets/postgresql_source_config.json" ]; then
    echo "⚠️ Configuração do servidor origem não encontrada"
    echo "   Configure secrets/postgresql_source_config.json"
fi

if [ ! -f "secrets/postgresql_destination_config.json" ]; then
    echo "⚠️ Configuração do servidor destino não encontrada"
    echo "   Configure secrets/postgresql_destination_config.json"
fi

# Tornar executável
chmod +x migration_orchestrator.py
chmod +x exemplo_uso.py

echo "✅ Arquivos tornados executáveis"

# Verificar sistema
echo "🔍 Verificando sistema..."
if python3 -c "
import sys
import os
sys.path.append('.')
sys.path.append('core')

try:
    from migration_orchestrator import MigrationOrchestrator
    print('✅ Orquestrador principal: OK')
except ImportError as e:
    print(f'❌ Erro importando orquestrador: {e}')
    sys.exit(1)

try:
    from core.modules.data_extractor import WF004DataExtractor
    print('✅ Módulo extrator: OK')
except ImportError as e:
    print(f'❌ Erro importando extrator: {e}')
    sys.exit(1)

try:
    from core.modules.script_generator import SQLScriptGenerator
    print('✅ Módulo gerador: OK')
except ImportError as e:
    print(f'❌ Erro importando gerador: {e}')
    sys.exit(1)

try:
    from core.modules.migration_executor import ControlledMigrationExecutor
    print('✅ Módulo executor: OK')
except ImportError as e:
    print(f'❌ Erro importando executor: {e}')
    sys.exit(1)

print('✅ Todos os módulos carregados com sucesso')
"; then
    echo "✅ Sistema verificado e funcionando"
else
    echo "❌ Problema na verificação do sistema"
    exit 1
fi

# Informações finais
echo ""
echo "🎉 SETUP CONCLUÍDO COM SUCESSO!"
echo "================================"
echo ""
echo "💡 Próximos passos:"
echo "   1. Configure os arquivos em secrets/"
echo "   2. Execute: python3 migration_orchestrator.py --help"
echo "   3. Para exemplos: python3 exemplo_uso.py"
echo ""
echo "📚 Documentação: README_v4.md"
echo "⚙️ Configuração: config/migration_config.json"
echo "📝 Logs em: logs/"
echo "📊 Relatórios em: reports/"
echo ""
echo "🚀 Sistema pronto para uso!"
