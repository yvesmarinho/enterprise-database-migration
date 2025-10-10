#!/bin/bash

# Script para limpar a raiz do projeto, movendo arquivos de versão para history
# Uso: ./clean-root.sh

# Diretório para onde os arquivos serão movidos
HISTORY_DIR="development/history"
mkdir -p $HISTORY_DIR

# Move arquivos de versão para history
echo "🔍 Procurando arquivos de versão na raiz..."
count=0

# Arquivos com padrão -v00*.md
for file in *-v00*.md; do
    if [ -f "$file" ]; then
        echo "  Movendo $file para $HISTORY_DIR/"
        mv "$file" "$HISTORY_DIR/"
        count=$((count + 1))
    fi
done

# Arquivos com padrão -v00*.yaml
for file in *-v00*.yaml; do
    if [ -f "$file" ]; then
        echo "  Movendo $file para $HISTORY_DIR/"
        mv "$file" "$HISTORY_DIR/"
        count=$((count + 1))
    fi
done

# Arquivos com padrão .config-v00*
for file in .config-v00*; do
    if [ -f "$file" ]; then
        echo "  Movendo $file para $HISTORY_DIR/"
        mv "$file" "$HISTORY_DIR/"
        count=$((count + 1))
    fi
done

# Arquivos com padrão .pre-commit-config-v00*
for file in .pre-commit-config-v00*; do
    if [ -f "$file" ]; then
        echo "  Movendo $file para $HISTORY_DIR/"
        mv "$file" "$HISTORY_DIR/"
        count=$((count + 1))
    fi
done

echo "✅ Movidos $count arquivos de versão para $HISTORY_DIR/"

# Verificar arquivos TEMPLATE
echo "🔍 Verificando arquivos de template..."
template_count=0

# Lista de arquivos padrão de template
TEMPLATE_FILES=(
    "README-TEMPLATE.md"
    "TODO-TEMPLATE.md"
    "ROADMAP-TEMPLATE.md"
)

for file in "${TEMPLATE_FILES[@]}"; do
    if [ -f "$file" ]; then
        if [ ! -f "template/$file" ]; then
            echo "  Copiando $file para template/"
            cp "$file" "template/"
        else 
            echo "  $file já existe em template/"
        fi
        template_count=$((template_count + 1))
    fi
done

echo "✅ Verificados $template_count arquivos de template"

echo "🧹 Limpeza da raiz concluída!"
