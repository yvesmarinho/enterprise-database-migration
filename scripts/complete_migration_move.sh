#!/bin/bash
#
# Complete Migration Files Move - Part 2
# ======================================
#
# Script complementar para mover arquivos restantes de teste
# que estavam na pasta test/ e não foram detectados no primeiro script.
#

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🔧 Migration Files - Complementary Move${NC}"
echo -e "${BLUE}================================================${NC}"

# Função para mover arquivo com log
move_file() {
    local source="$1"
    local destination="$2"
    local category="$3"

    if [ -f "$source" ]; then
        mv "$source" "$destination"
        echo -e "${GREEN}   ✅ $source → $destination${NC} ($category)"
        return 0
    else
        echo -e "${YELLOW}   ⚠️  $source não encontrado${NC}"
        return 1
    fi
}

echo -e "${YELLOW}🔍 Movendo arquivos de teste restantes...${NC}"

# VALIDATION - Arquivos da pasta test/
echo -e "\n${BLUE}🧪 VALIDATION - Arquivos de Teste${NC}"

move_file "test/test_wfdb02_connection.py" "src/migration/validation/test_wfdb02_connection.py" "VALIDATION"
move_file "test/test_wfdb02_minimal.py" "src/migration/validation/test_wfdb02_minimal.py" "VALIDATION"
move_file "test/test_wfdb02_simple.py" "src/migration/validation/test_wfdb02_simple.py" "VALIDATION"
move_file "test/tst_connection_psql.py" "src/migration/validation/tst_connection_psql.py" "VALIDATION"

# Arquivos adicionais em src/postgresql/
echo -e "\n${BLUE}📦 Arquivos Adicionais${NC}"

move_file "src/postgresql/test_wfdb02_only.py" "src/migration/validation/test_wfdb02_only.py" "VALIDATION"

# Verificar se há mais arquivos de migração
echo -e "\n${BLUE}🔍 Verificando arquivos restantes...${NC}"

# Procurar por arquivos relacionados à migração em src/postgresql/
remaining_migration_files=$(find src/postgresql/ -name "*migration*" -o -name "*migrate*" -o -name "*wfdb*" -o -name "*scram*" | grep -v __pycache__ | wc -l)

if [ "$remaining_migration_files" -gt 0 ]; then
    echo -e "${YELLOW}📋 Arquivos relacionados à migração ainda em src/postgresql/:${NC}"
    find src/postgresql/ -name "*migration*" -o -name "*migrate*" -o -name "*wfdb*" -o -name "*scram*" | grep -v __pycache__ | while read file; do
        if [ -f "$file" ]; then
            basename_file=$(basename "$file")
            echo -e "${YELLOW}   📄 $file${NC}"

            # Sugerir categoria baseada no nome
            if [[ "$basename_file" == *"test"* ]] || [[ "$basename_file" == *"check"* ]] || [[ "$basename_file" == *"validation"* ]]; then
                suggested_dir="validation"
            elif [[ "$basename_file" == *"config"* ]] || [[ "$basename_file" == *"setup"* ]]; then
                suggested_dir="config"
            elif [[ "$basename_file" == *"util"* ]] || [[ "$basename_file" == *"helper"* ]] || [[ "$basename_file" == *"debug"* ]]; then
                suggested_dir="utils"
            else
                suggested_dir="core"
            fi

            echo -e "${BLUE}      💡 Sugestão: mover para src/migration/${suggested_dir}/${NC}"
        fi
    done
fi

# Contar arquivos finais
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}📊 RELATÓRIO FINAL COMPLEMENTAR${NC}"
echo -e "${BLUE}================================================${NC}"

core_count=$(find src/migration/core/ -name "*.py" -not -name "__init__.py" | wc -l)
utils_count=$(find src/migration/utils/ -name "*.py" -not -name "__init__.py" | wc -l)
validation_count=$(find src/migration/validation/ -name "*.py" -not -name "__init__.py" | wc -l)
config_count=$(find src/migration/config/ -name "*.py" -not -name "__init__.py" | wc -l)
legacy_count=$(find src/migration/legacy/ -name "*.py" -not -name "__init__.py" | wc -l)

echo -e "${GREEN}✅ Estrutura final:${NC}"
echo "   src/migration/core/       - $core_count arquivos"
echo "   src/migration/utils/      - $utils_count arquivos"
echo "   src/migration/config/     - $config_count arquivos"
echo "   src/migration/validation/ - $validation_count arquivos"
echo "   src/migration/legacy/     - $legacy_count arquivos"

total_files=$((core_count + utils_count + validation_count + config_count + legacy_count))
echo ""
echo -e "${GREEN}🎯 Total de arquivos organizados: $total_files${NC}"

echo ""
echo -e "${BLUE}🏁 Reorganização complementar concluída!${NC}"
