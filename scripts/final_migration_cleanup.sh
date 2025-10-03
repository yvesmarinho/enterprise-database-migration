#!/bin/bash
#
# Final Migration Cleanup - Part 3
# =================================
#
# Script final para mover arquivos restantes importantes
# e ignorar arquivos de dependências/venv.
#

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🧹 Final Migration Cleanup${NC}"
echo -e "${BLUE}================================================${NC}"

# Função para mover arquivo com log
move_file() {
    local source="$1"
    local destination="$2"
    local category="$3"

    if [ -f "$source" ]; then
        # Criar diretório se não existir
        mkdir -p "$(dirname "$destination")"
        mv "$source" "$destination"
        echo -e "${GREEN}   ✅ $source → $destination${NC} ($category)"
        return 0
    else
        echo -e "${YELLOW}   ⚠️  $source não encontrado${NC}"
        return 1
    fi
}

echo -e "${YELLOW}🔧 Movendo arquivos críticos restantes...${NC}"

# CORE - Scripts principais e logs
echo -e "\n${BLUE}📦 CORE - Scripts e Logs${NC}"

move_file "src/postgresql/complete_migration.py" "src/migration/core/complete_migration.py" "CORE"
move_file "src/postgresql/requirements.migration.txt" "src/migration/core/requirements.migration.txt" "CORE"

# Criar pasta de reports e mover logs
if [ -d "src/postgresql/reports" ]; then
    echo -e "${GREEN}   📁 Movendo logs de migração...${NC}"
    mkdir -p "src/migration/core/reports"

    for log_file in src/postgresql/reports/migration_execution_*.log; do
        if [ -f "$log_file" ]; then
            basename_log=$(basename "$log_file")
            move_file "$log_file" "src/migration/core/reports/$basename_log" "LOGS"
        fi
    done
fi

# CONFIG - Configurações
echo -e "\n${BLUE}⚙️  CONFIG - Configurações${NC}"

move_file "src/postgresql/config/migration_rules.json" "src/migration/config/migration_rules.json" "CONFIG"
move_file "src/postgresql/setup_migration.sh" "src/migration/config/setup_migration.sh" "CONFIG"

# VALIDATION - Testes adicionais
echo -e "\n${BLUE}🧪 VALIDATION - Testes Adicionais${NC}"

move_file "src/postgresql/test_migration.py" "src/migration/validation/test_migration.py" "VALIDATION"
move_file "src/postgresql/check_wfdb02_status.py" "src/migration/validation/check_wfdb02_status.py" "VALIDATION"

# Copiar configurações originais se existirem
echo -e "\n${BLUE}📋 Copiando configurações originais...${NC}"

if [ -d "config" ]; then
    echo -e "${GREEN}   📁 Copiando config/ para src/migration/config/...${NC}"
    cp -r config/* src/migration/config/ 2>/dev/null || true
    echo -e "${GREEN}   ✅ Configurações copiadas${NC}"
fi

# Verificar estrutura final
echo -e "\n${BLUE}📊 Verificando estrutura final...${NC}"

core_count=$(find src/migration/core/ -name "*.py" -not -name "__init__.py" | wc -l)
utils_count=$(find src/migration/utils/ -name "*.py" -not -name "__init__.py" | wc -l)
validation_count=$(find src/migration/validation/ -name "*.py" -not -name "__init__.py" | wc -l)
config_count=$(find src/migration/config/ -type f | wc -l)
reports_count=$(find src/migration/core/reports/ -name "*.log" 2>/dev/null | wc -l || echo 0)

echo -e "${GREEN}✅ Estrutura final completa:${NC}"
echo "   src/migration/core/          - $core_count scripts + $reports_count logs"
echo "   src/migration/utils/         - $utils_count utilitários"
echo "   src/migration/config/        - $config_count configurações"
echo "   src/migration/validation/    - $validation_count testes"

# Criar arquivo de índice
echo -e "\n${YELLOW}📝 Criando índice de arquivos...${NC}"

cat > "src/migration/FILE_INDEX.md" << 'EOF'
# Migration Files Index

## 📦 Core Scripts
- `sqlalchemy_migration.py` - Migração principal usando SQLAlchemy ⭐
- `complete_migration_fixed.py` - Migração com psycopg2 corrigida
- `migration_structure.py` - Migração estruturas apenas
- `migrate_users.py` - Migração específica usuários
- `complete_migration.py` - Script de migração completa
- `requirements.migration.txt` - Dependências específicas

### Reports
- `reports/migration_execution_*.log` - Logs de execução históricos

## 🔧 Utils
- `discover_users.py` - Descoberta de usuários
- `analyze_password.py` - Análise senhas SCRAM
- `debug_connection.py` - Debug conexões

## ⚙️ Config
- `migration_rules.json` - Regras de migração
- `setup_migration.sh` - Setup inicial
- `source_config.json` - Config servidor origem
- `destination_config.json` - Config servidor destino

## 🧪 Validation
- `check_scram_auth.py` - Validação SCRAM-SHA-256
- `test_wfdb02_*.py` - Testes conexão WFDB02 (5 arquivos)
- `test_migration.py` - Teste migração
- `check_wfdb02_status.py` - Status WFDB02
- `tst_connection_psql.py` - Teste conexão PostgreSQL

## 🚀 Uso Recomendado

### Migração Completa
```bash
python3 src/migration/core/sqlalchemy_migration.py
```

### Validação
```bash
python3 src/migration/validation/check_scram_auth.py
```
EOF

echo -e "${GREEN}   ✅ src/migration/FILE_INDEX.md criado${NC}"

# Verificar arquivos restantes em src/postgresql/
echo -e "\n${BLUE}🔍 Verificando sobras em src/postgresql/...${NC}"

remaining_py_files=$(find src/postgresql/ -name "*.py" -not -path "*/.venv/*" -not -path "*/__pycache__/*" | wc -l)
remaining_important=$(find src/postgresql/ -name "*.py" -o -name "*.json" -o -name "*.sh" | grep -v ".venv" | grep -v "__pycache__" | wc -l)

if [ "$remaining_important" -gt 0 ]; then
    echo -e "${YELLOW}📋 Arquivos restantes importantes:${NC}"
    find src/postgresql/ -name "*.py" -o -name "*.json" -o -name "*.sh" | grep -v ".venv" | grep -v "__pycache__" | head -10 | while read file; do
        echo -e "${YELLOW}   📄 $file${NC}"
    done

    if [ "$remaining_important" -gt 10 ]; then
        echo -e "${YELLOW}   ... e mais $((remaining_important - 10)) arquivos${NC}"
    fi
else
    echo -e "${GREEN}   ✅ Nenhum arquivo importante restante${NC}"
fi

# Relatório final
total_organized=$((core_count + utils_count + validation_count + config_count))

echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}🎉 REORGANIZAÇÃO COMPLETA FINALIZADA${NC}"
echo -e "${BLUE}================================================${NC}"

echo -e "${GREEN}📊 ESTATÍSTICAS FINAIS:${NC}"
echo "   🚀 Total organizado: $total_organized arquivos"
echo "   📦 Core: $core_count scripts + $reports_count logs"
echo "   🔧 Utils: $utils_count utilitários"
echo "   ⚙️  Config: $config_count configurações"
echo "   🧪 Validation: $validation_count testes"

echo ""
echo -e "${GREEN}✅ SISTEMA DE MIGRAÇÃO 100% ORGANIZADO!${NC}"
echo -e "${BLUE}🎯 Pronto para uso em produção${NC}"
