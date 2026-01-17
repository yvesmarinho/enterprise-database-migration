#!/bin/bash
# ================================================================
# Arquivo: migrate_perfexcrm_mysql.sh
# Propósito: Migrar banco de dados PerfexCRM do MySQL
#            do servidor wf004 para wfdb02
# Sistema: PerfexCRM
# Database: perfexcrm_db (MySQL)
# Usuários: perfexcrm_user (RW), perfexcrm_view (RO)
#
# Execução:
#   bash scripts/migrate_perfexcrm_mysql.sh
# ================================================================

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
SOURCE_HOST="wf004.vya.digital"
DEST_HOST="wfdb02.vya.digital"
DATABASE="perfexcrm_db"
BACKUP_DIR="./backup/perfexcrm_$(date +%Y%m%d_%H%M%S)"
DUMP_FILE="${BACKUP_DIR}/${DATABASE}_dump.sql"
LOG_FILE="${BACKUP_DIR}/migration.log"

# Credenciais (serão solicitadas interativamente)
SOURCE_USER=""
SOURCE_PASS=""
DEST_USER=""
DEST_PASS=""
PERFEX_USER_PASS=""
PERFEX_VIEW_PASS=""

# Funções auxiliares
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║     Migração MySQL - PerfexCRM                             ║
║     Origem: wf004.vya.digital                              ║
║     Destino: wfdb02.vya.digital                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"
log "Diretório de backup criado: $BACKUP_DIR"

# Solicitar credenciais
echo ""
log "Configurando credenciais..."
echo ""

read -p "Usuário MySQL no servidor ORIGEM (wf004) [root]: " SOURCE_USER
SOURCE_USER=${SOURCE_USER:-root}

read -sp "Senha do usuário $SOURCE_USER no wf004: " SOURCE_PASS
echo ""

read -p "Usuário MySQL no servidor DESTINO (wfdb02) [root]: " DEST_USER
DEST_USER=${DEST_USER:-root}

read -sp "Senha do usuário $DEST_USER no wfdb02: " DEST_PASS
echo ""

read -sp "Nova senha para perfexcrm_user no wfdb02: " PERFEX_USER_PASS
echo ""

read -sp "Nova senha para perfexcrm_view no wfdb02: " PERFEX_VIEW_PASS
echo ""
echo ""

# ================================================================
# ETAPA 1: Verificação do ambiente de origem
# ================================================================
log "═══════════════════════════════════════════════════════════"
log "ETAPA 1: Verificando ambiente de origem (wf004)"
log "═══════════════════════════════════════════════════════════"

if ! mysql -h "$SOURCE_HOST" -u "$SOURCE_USER" -p"$SOURCE_PASS" -e "USE $DATABASE;" 2>/dev/null; then
    log_error "Não foi possível conectar ao banco $DATABASE no servidor $SOURCE_HOST"
    exit 1
fi
log_success "Conexão com banco de origem verificada"

# Verificar tamanho do banco
DB_SIZE=$(mysql -h "$SOURCE_HOST" -u "$SOURCE_USER" -p"$SOURCE_PASS" -e \
    "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
     FROM information_schema.tables
     WHERE table_schema = '$DATABASE';" -N)
log "Tamanho do banco: ${DB_SIZE} MB"

# Contar tabelas
TABLE_COUNT=$(mysql -h "$SOURCE_HOST" -u "$SOURCE_USER" -p"$SOURCE_PASS" -e \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$DATABASE';" -N)
log "Número de tabelas: ${TABLE_COUNT}"

# ================================================================
# ETAPA 2: Backup do banco de origem
# ================================================================
log ""
log "═══════════════════════════════════════════════════════════"
log "ETAPA 2: Criando backup do banco de origem"
log "═══════════════════════════════════════════════════════════"

log "Iniciando dump do banco $DATABASE..."
if mysqldump -h "$SOURCE_HOST" \
    -u "$SOURCE_USER" \
    -p"$SOURCE_PASS" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --set-gtid-purged=OFF \
    --skip-lock-tables \
    --quick \
    "$DATABASE" > "$DUMP_FILE" 2>> "$LOG_FILE"; then
    log_success "Dump criado com sucesso: $DUMP_FILE"

    DUMP_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
    log "Tamanho do arquivo de dump: $DUMP_SIZE"
else
    log_error "Falha ao criar dump do banco"
    exit 1
fi

# Criar backup compactado
log "Compactando backup..."
if gzip -c "$DUMP_FILE" > "${DUMP_FILE}.gz"; then
    log_success "Backup compactado criado: ${DUMP_FILE}.gz"
    COMPRESSED_SIZE=$(du -h "${DUMP_FILE}.gz" | cut -f1)
    log "Tamanho compactado: $COMPRESSED_SIZE"
fi

# ================================================================
# ETAPA 3: Verificação do ambiente de destino
# ================================================================
log ""
log "═══════════════════════════════════════════════════════════"
log "ETAPA 3: Verificando ambiente de destino (wfdb02)"
log "═══════════════════════════════════════════════════════════"

if ! mysql -h "$DEST_HOST" -u "$DEST_USER" -p"$DEST_PASS" -e "SELECT 1;" 2>/dev/null; then
    log_error "Não foi possível conectar ao servidor $DEST_HOST"
    exit 1
fi
log_success "Conexão com servidor de destino verificada"

# Verificar se o banco já existe
if mysql -h "$DEST_HOST" -u "$DEST_USER" -p"$DEST_PASS" -e "USE $DATABASE;" 2>/dev/null; then
    log_warning "Banco $DATABASE já existe no servidor de destino!"
    read -p "Deseja SOBRESCREVER o banco existente? (digite 'SIM' para confirmar): " CONFIRM
    if [ "$CONFIRM" != "SIM" ]; then
        log_error "Operação cancelada pelo usuário"
        exit 1
    fi
    log_warning "Banco existente será sobrescrito"
fi

# ================================================================
# ETAPA 4: Criação do banco no destino
# ================================================================
log ""
log "═══════════════════════════════════════════════════════════"
log "ETAPA 4: Criando banco de dados no destino"
log "═══════════════════════════════════════════════════════════"

log "Criando banco $DATABASE no servidor $DEST_HOST..."
mysql -h "$DEST_HOST" -u "$DEST_USER" -p"$DEST_PASS" << EOF 2>> "$LOG_FILE"
DROP DATABASE IF EXISTS \`$DATABASE\`;
CREATE DATABASE \`$DATABASE\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

if [ $? -eq 0 ]; then
    log_success "Banco $DATABASE criado com sucesso"
else
    log_error "Falha ao criar banco de dados"
    exit 1
fi

# ================================================================
# ETAPA 5: Restauração dos dados
# ================================================================
log ""
log "═══════════════════════════════════════════════════════════"
log "ETAPA 5: Restaurando dados no destino"
log "═══════════════════════════════════════════════════════════"

log "Iniciando importação dos dados..."
if mysql -h "$DEST_HOST" \
    -u "$DEST_USER" \
    -p"$DEST_PASS" \
    "$DATABASE" < "$DUMP_FILE" 2>> "$LOG_FILE"; then
    log_success "Dados importados com sucesso"
else
    log_error "Falha ao importar dados"
    exit 1
fi

# ================================================================
# ETAPA 6: Criação e configuração de usuários
# ================================================================
log ""
log "═══════════════════════════════════════════════════════════"
log "ETAPA 6: Configurando usuários e permissões"
log "═══════════════════════════════════════════════════════════"

log "Criando usuário perfexcrm_user (Read/Write)..."
mysql -h "$DEST_HOST" -u "$DEST_USER" -p"$DEST_PASS" << EOF 2>> "$LOG_FILE"
-- Remover usuários existentes se houver
DROP USER IF EXISTS 'perfexcrm_user'@'%';
DROP USER IF EXISTS 'perfexcrm_view'@'%';

-- Criar usuário perfexcrm_user com permissões completas
CREATE USER 'perfexcrm_user'@'%' IDENTIFIED BY '${PERFEX_USER_PASS}';
GRANT ALL PRIVILEGES ON \`${DATABASE}\`.* TO 'perfexcrm_user'@'%';

-- Criar usuário perfexcrm_view com permissões somente leitura
CREATE USER 'perfexcrm_view'@'%' IDENTIFIED BY '${PERFEX_VIEW_PASS}';
GRANT SELECT ON \`${DATABASE}\`.* TO 'perfexcrm_view'@'%';

-- Aplicar privilégios
FLUSH PRIVILEGES;
EOF

if [ $? -eq 0 ]; then
    log_success "Usuários criados e configurados com sucesso"
else
    log_error "Falha ao configurar usuários"
    exit 1
fi

# ================================================================
# ETAPA 7: Validação da migração
# ================================================================
log ""
log "═══════════════════════════════════════════════════════════"
log "ETAPA 7: Validando migração"
log "═══════════════════════════════════════════════════════════"

# Contar tabelas no destino
DEST_TABLE_COUNT=$(mysql -h "$DEST_HOST" -u "$DEST_USER" -p"$DEST_PASS" -e \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$DATABASE';" -N)

log "Tabelas na origem: $TABLE_COUNT"
log "Tabelas no destino: $DEST_TABLE_COUNT"

if [ "$TABLE_COUNT" -eq "$DEST_TABLE_COUNT" ]; then
    log_success "Número de tabelas confere"
else
    log_warning "Número de tabelas diferente!"
fi

# Verificar tamanho do banco no destino
DEST_DB_SIZE=$(mysql -h "$DEST_HOST" -u "$DEST_USER" -p"$DEST_PASS" -e \
    "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
     FROM information_schema.tables
     WHERE table_schema = '$DATABASE';" -N)

log "Tamanho na origem: ${DB_SIZE} MB"
log "Tamanho no destino: ${DEST_DB_SIZE} MB"

# Testar conexão com perfexcrm_user
log ""
log "Testando conexão com perfexcrm_user..."
if mysql -h "$DEST_HOST" -u "perfexcrm_user" -p"$PERFEX_USER_PASS" -e "USE $DATABASE; SHOW TABLES;" > /dev/null 2>&1; then
    log_success "perfexcrm_user pode acessar o banco"
else
    log_error "perfexcrm_user não consegue acessar o banco"
fi

# Testar conexão com perfexcrm_view
log "Testando conexão com perfexcrm_view..."
if mysql -h "$DEST_HOST" -u "perfexcrm_view" -p"$PERFEX_VIEW_PASS" -e "USE $DATABASE; SHOW TABLES;" > /dev/null 2>&1; then
    log_success "perfexcrm_view pode acessar o banco"
else
    log_error "perfexcrm_view não consegue acessar o banco"
fi

# ================================================================
# RELATÓRIO FINAL
# ================================================================
log ""
log "═══════════════════════════════════════════════════════════"
log "MIGRAÇÃO CONCLUÍDA COM SUCESSO!"
log "═══════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}✓ Resumo da Migração:${NC}"
echo -e "  Banco de dados: ${BLUE}${DATABASE}${NC}"
echo -e "  Origem: ${BLUE}${SOURCE_HOST}${NC}"
echo -e "  Destino: ${BLUE}${DEST_HOST}${NC}"
echo -e "  Tabelas migradas: ${BLUE}${DEST_TABLE_COUNT}${NC}"
echo -e "  Tamanho: ${BLUE}${DEST_DB_SIZE} MB${NC}"
echo ""
echo -e "${GREEN}✓ Usuários configurados:${NC}"
echo -e "  ${BLUE}perfexcrm_user${NC} - Leitura e Escrita"
echo -e "  ${BLUE}perfexcrm_view${NC} - Somente Leitura"
echo ""
echo -e "${YELLOW}⚠ Arquivos salvos em:${NC}"
echo -e "  Dump SQL: ${BLUE}${DUMP_FILE}${NC}"
echo -e "  Dump compactado: ${BLUE}${DUMP_FILE}.gz${NC}"
echo -e "  Log: ${BLUE}${LOG_FILE}${NC}"
echo ""
echo -e "${YELLOW}⚠ PRÓXIMOS PASSOS:${NC}"
echo -e "  1. Atualize a configuração do PerfexCRM para apontar para:"
echo -e "     Host: ${BLUE}${DEST_HOST}${NC}"
echo -e "     Database: ${BLUE}${DATABASE}${NC}"
echo -e "     User: ${BLUE}perfexcrm_user${NC}"
echo -e "     Password: ${BLUE}[senha configurada]${NC}"
echo ""
echo -e "  2. Teste a aplicação PerfexCRM"
echo -e "  3. Verifique os logs da aplicação"
echo -e "  4. Após confirmar que tudo está funcionando:"
echo -e "     - Guarde o backup em local seguro"
echo -e "     - Considere desativar o banco no servidor antigo"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
