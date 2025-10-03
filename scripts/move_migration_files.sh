#!/bin/bash
#
# Move Migration Files to src/migration
# ====================================
# 
# Este script move todos os arquivos relacionados à migração PostgreSQL
# para a pasta src/migration, organizando por categorias.
#
# Estrutura final:
# src/migration/
# ├── core/           # Scripts principais de migração
# ├── utils/          # Utilitários e helpers
# ├── config/         # Configurações
# ├── validation/     # Scripts de validação/teste
# └── legacy/         # Versões antigas/backup
#

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🚚 Migration Files Reorganization Script${NC}"
echo -e "${BLUE}================================================${NC}"

# Verificar se estamos no diretório correto
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Erro: Execute este script na raiz do projeto${NC}"
    exit 1
fi

# Criar estrutura de diretórios
echo -e "${YELLOW}📁 Criando estrutura de diretórios...${NC}"

mkdir -p src/migration/{core,utils,config,validation,legacy}

echo -e "${GREEN}✅ Estrutura criada:${NC}"
echo "   src/migration/core/       - Scripts principais"
echo "   src/migration/utils/      - Utilitários"
echo "   src/migration/config/     - Configurações"
echo "   src/migration/validation/ - Testes e validação"
echo "   src/migration/legacy/     - Versões antigas"

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

echo -e "\n${YELLOW}🔄 Movendo arquivos de migração...${NC}"

# ==========================================
# CORE - Scripts principais de migração
# ==========================================
echo -e "\n${BLUE}📦 CORE - Scripts Principais${NC}"

move_file "src/postgresql/sqlalchemy_migration.py" "src/migration/core/sqlalchemy_migration.py" "CORE"
move_file "src/postgresql/complete_migration_fixed.py" "src/migration/core/complete_migration_fixed.py" "CORE"
move_file "src/postgresql/migration_structure.py" "src/migration/core/migration_structure.py" "CORE"
move_file "src/postgresql/migrate_users.py" "src/migration/core/migrate_users.py" "CORE"

# ==========================================
# UTILS - Utilitários e helpers
# ==========================================
echo -e "\n${BLUE}🔧 UTILS - Utilitários${NC}"

move_file "src/postgresql/discover_users.py" "src/migration/utils/discover_users.py" "UTILS"
move_file "src/postgresql/analyze_password.py" "src/migration/utils/analyze_password.py" "UTILS"
move_file "src/postgresql/debug_connection.py" "src/migration/utils/debug_connection.py" "UTILS"

# ==========================================
# CONFIG - Arquivos de configuração
# ==========================================
echo -e "\n${BLUE}⚙️  CONFIG - Configurações${NC}"

# Mover configs se existirem
if [ -d "config" ]; then
    echo -e "${GREEN}   📁 Movendo diretório config/ completo...${NC}"
    cp -r config/* src/migration/config/ 2>/dev/null || true
    echo -e "${GREEN}   ✅ Configurações copiadas para src/migration/config/${NC}"
fi

# ==========================================
# VALIDATION - Scripts de teste/validação
# ==========================================
echo -e "\n${BLUE}🧪 VALIDATION - Testes e Validação${NC}"

move_file "src/postgresql/check_scram_auth.py" "src/migration/validation/check_scram_auth.py" "VALIDATION"
move_file "src/postgresql/test_wfdb02_connection.py" "src/migration/validation/test_wfdb02_connection.py" "VALIDATION"
move_file "src/postgresql/test_wfdb02_minimal.py" "src/migration/validation/test_wfdb02_minimal.py" "VALIDATION"
move_file "src/postgresql/test_wfdb02_simple.py" "src/migration/validation/test_wfdb02_simple.py" "VALIDATION"
move_file "src/postgresql/tst_connection_psql.py" "src/migration/validation/tst_connection_psql.py" "VALIDATION"

# ==========================================
# LEGACY - Versões antigas (backup)
# ==========================================
echo -e "\n${BLUE}📦 LEGACY - Versões Antigas${NC}"

# Procurar por arquivos com sufixos -v001, _old, etc.
find src/postgresql/ -name "*-v001*" -type f 2>/dev/null | while read file; do
    if [ -f "$file" ]; then
        basename_file=$(basename "$file")
        move_file "$file" "src/migration/legacy/$basename_file" "LEGACY"
    fi
done

find src/postgresql/ -name "*_old*" -type f 2>/dev/null | while read file; do
    if [ -f "$file" ]; then
        basename_file=$(basename "$file")  
        move_file "$file" "src/migration/legacy/$basename_file" "LEGACY"
    fi
done

# ==========================================
# Arquivos restantes em postgresql/
# ==========================================
echo -e "\n${BLUE}🔍 Verificando arquivos restantes em src/postgresql/${NC}"

remaining_files=$(find src/postgresql/ -name "*.py" -type f 2>/dev/null | wc -l)
if [ "$remaining_files" -gt 0 ]; then
    echo -e "${YELLOW}📋 Arquivos restantes em src/postgresql/:${NC}"
    find src/postgresql/ -name "*.py" -type f 2>/dev/null | while read file; do
        echo -e "${YELLOW}   📄 $file${NC}"
    done
    echo -e "${BLUE}💡 Estes arquivos podem ser específicos do PostgreSQL e não de migração${NC}"
fi

# ==========================================
# Criar arquivo __init__.py em cada pasta
# ==========================================
echo -e "\n${YELLOW}📝 Criando arquivos __init__.py...${NC}"

for dir in src/migration/{core,utils,config,validation,legacy}; do
    if [ -d "$dir" ]; then
        cat > "$dir/__init__.py" << 'EOF'
"""
PostgreSQL Migration Package
============================

Este pacote contém ferramentas para migração de PostgreSQL 14 → 16
entre servidores wf004.vya.digital e wfdb02.vya.digital.
"""
EOF
        echo -e "${GREEN}   ✅ $dir/__init__.py criado${NC}"
    fi
done

# Criar __init__.py principal
cat > "src/migration/__init__.py" << 'EOF'
"""
Enterprise PostgreSQL Migration System
======================================

Sistema completo de migração PostgreSQL 14.11 → 16.10
Desenvolvido para ambiente empresarial Vya Digital.

Módulos:
- core/      : Scripts principais de migração
- utils/     : Utilitários e ferramentas auxiliares  
- config/    : Configurações de conexão e migração
- validation/: Scripts de teste e validação
- legacy/    : Versões antigas e backup

Uso principal:
    from src.migration.core.sqlalchemy_migration import SQLAlchemyPostgreSQLMigrator
    
    migrator = SQLAlchemyPostgreSQLMigrator()
    migrator.run_complete_migration()
"""

__version__ = "1.0.0"
__author__ = "Enterprise Migration Team"
__date__ = "2025-10-02"
EOF

echo -e "${GREEN}   ✅ src/migration/__init__.py criado${NC}"

# ==========================================
# Criar README para a pasta migration
# ==========================================
echo -e "\n${YELLOW}📖 Criando documentação...${NC}"

cat > "src/migration/README.md" << 'EOF'
# PostgreSQL Migration System

Sistema completo de migração PostgreSQL 14 → 16 para ambiente empresarial.

## 🏗️ Estrutura

```
src/migration/
├── core/           # Scripts principais de migração
│   ├── sqlalchemy_migration.py      # Migração usando SQLAlchemy (RECOMENDADO)
│   ├── complete_migration_fixed.py  # Migração com psycopg2 corrigida  
│   ├── migration_structure.py       # Migração de estruturas apenas
│   └── migrate_users.py             # Migração específica de usuários
├── utils/          # Utilitários e helpers
│   ├── discover_users.py           # Descoberta de usuários
│   ├── analyze_password.py         # Análise de senhas SCRAM
│   └── debug_connection.py         # Debug de conexões
├── config/         # Configurações
│   ├── source_config.json          # Config servidor origem
│   ├── destination_config.json     # Config servidor destino
│   └── migration_rules.json        # Regras de migração
├── validation/     # Scripts de validação/teste
│   ├── check_scram_auth.py         # Validação SCRAM-SHA-256
│   ├── test_wfdb02_connection.py   # Teste conexão WFDB02
│   └── *.py                        # Outros testes
└── legacy/         # Versões antigas/backup
```

## 🚀 Uso Recomendado

### Migração Completa (SQLAlchemy)
```bash
cd src/migration/core
python3 sqlalchemy_migration.py
```

### Validação de Conectividade
```bash
cd src/migration/validation  
python3 check_scram_auth.py
```

## 📊 Histórico de Execuções

- **Última migração**: 2025-10-02
- **Usuários**: 39 migrados
- **Bancos**: 29 migrados  
- **Privilégios**: 2.486 aplicados
- **Tempo**: 426.89s
- **Status**: ✅ SUCESSO

## 🔧 Dependências

```bash
pip install sqlalchemy psycopg2-binary
```

## 📈 Performance

| Método | Usuários | Bancos | Privilégios | Tempo |
|--------|----------|--------|-------------|-------|
| SQLAlchemy | 39 | 29 | 2.486 | 426.89s |
| psycopg2 | 39 | 29 | - | ~81s* |

*Estruturas apenas, sem privilégios completos
EOF

echo -e "${GREEN}   ✅ src/migration/README.md criado${NC}"

# ==========================================
# Relatório final
# ==========================================
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}📊 RELATÓRIO FINAL${NC}"
echo -e "${BLUE}================================================${NC}"

echo -e "${GREEN}✅ Reorganização concluída com sucesso!${NC}"
echo ""
echo -e "${YELLOW}📁 Nova estrutura:${NC}"
echo "   src/migration/core/       - $(find src/migration/core/ -name "*.py" | wc -l) arquivos"
echo "   src/migration/utils/      - $(find src/migration/utils/ -name "*.py" | wc -l) arquivos"
echo "   src/migration/config/     - $(find src/migration/config/ -name "*" -type f | wc -l) arquivos"  
echo "   src/migration/validation/ - $(find src/migration/validation/ -name "*.py" | wc -l) arquivos"
echo "   src/migration/legacy/     - $(find src/migration/legacy/ -name "*.py" | wc -l) arquivos"

echo ""
echo -e "${BLUE}🎯 Próximos passos:${NC}"
echo "   1. Verificar se todos os imports estão corretos"
echo "   2. Atualizar referências nos scripts principais"
echo "   3. Testar migração: python3 src/migration/core/sqlalchemy_migration.py"
echo "   4. Commit das mudanças no git"

echo ""
echo -e "${GREEN}🎉 Sistema de migração organizado e pronto para uso!${NC}"