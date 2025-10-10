#!/bin/bash

# Script para realizar uma reorganização completa do projeto
# Uso: ./reorganize-full.sh

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando reorganização completa do projeto...${NC}"

# 1. Verificar pré-requisitos
echo -e "${CYAN}📋 Verificando pré-requisitos...${NC}"
if [ ! -f scripts/smart-copy.sh ] || [ ! -f scripts/clean-root.sh ]; then
  echo -e "${RED}❌ Scripts necessários não encontrados${NC}"
  exit 1
fi

# 2. Criar estrutura de diretórios
echo -e "${CYAN}📋 Criando estrutura de diretórios...${NC}"
mkdir -p template/{scripts,docs,.vscode,pattern_code}
mkdir -p development/{.vscode,history,session}
mkdir -p transfer/{protocolos,scripts,melhorias}/versions

# 3. Realizar análise de conteúdo
echo -e "${CYAN}📋 Analisando conteúdo dos arquivos...${NC}"
# README e documentação
./scripts/smart-copy.sh README.md template/README.md
./scripts/smart-copy.sh README-TEMPLATE.md template/README-TEMPLATE.md
./scripts/smart-copy.sh TODO.md development/TODO.md
./scripts/smart-copy.sh TODO-TEMPLATE.md template/TODO-TEMPLATE.md
./scripts/smart-copy.sh ROADMAP-TEMPLATE.md template/ROADMAP-TEMPLATE.md
./scripts/smart-copy.sh CONTRIBUTING.md template/CONTRIBUTING.md
./scripts/smart-copy.sh SECURITY.md template/SECURITY.md

# Configurações
./scripts/smart-copy.sh mcp-questions.yaml template/mcp-questions.yaml
./scripts/smart-copy.sh mcp-questions.example.yaml template/mcp-questions.example.yaml
./scripts/smart-copy.sh objetivo.yaml template/objetivo.yaml

# Arquivos de desenvolvimento
./scripts/smart-copy.sh .vscode/mcp.json development/.vscode/mcp.json
./scripts/smart-copy.sh HISTORICO.md development/HISTORICO.md
./scripts/smart-copy.sh VERSION_REPORT.md development/VERSION_REPORT.md
if [ -f .session-current ]; then 
  cp .session-current development/session/
fi

# 4. Mover arquivos de script
echo -e "${CYAN}📋 Organizando scripts...${NC}"
for script in scripts/*.py; do
  if [ -f "$script" ]; then
    base=$(basename "$script")
    case "$base" in
      generate-mcp-config.py|generate-vscode-config.py|generate-docs.py|generate-project.py)
        ./scripts/smart-copy.sh "$script" "template/scripts/$base"
        ;;
      generate-session-init.py|generate-history.py|generate-versions.py)
        ./scripts/smart-copy.sh "$script" "transfer/scripts/$base"
        ;;
      *)
        echo "  Script não categorizado: $base"
        ;;
    esac
  fi
done

# 5. Mover arquivos de pattern_code
echo -e "${CYAN}📋 Organizando pattern_code...${NC}"
if [ -d pattern_code ]; then
  find pattern_code -type f -print0 | while IFS= read -r -d '' file; do
    dest="template/$file"
    mkdir -p "$(dirname "$dest")"
    ./scripts/smart-copy.sh "$file" "$dest"
  done
fi

# 6. Limpar a raiz
echo -e "${CYAN}📋 Limpando a raiz do projeto...${NC}"
./scripts/clean-root.sh

# 7. Atualizar README principal se existir
if [ -f README-NEW.md ]; then
  echo -e "${CYAN}📋 Atualizando README principal...${NC}"
  ./scripts/smart-copy.sh README-NEW.md README.md true
fi

echo -e "${GREEN}✅ Reorganização completa concluída!${NC}"
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo "  1. Revisar a nova estrutura de diretórios"
echo "  2. Verificar a integridade dos arquivos após a migração"
echo "  3. Executar make test para garantir que tudo funciona corretamente"
