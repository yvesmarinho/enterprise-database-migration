#!/bin/bash

# ================================================================
# Script: apply_n8n_fix.sh
# Propósito: Aplicar correção de permissões do n8n_admin automaticamente
# ================================================================

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações (ajuste conforme necessário)
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
N8N_ADMIN_PASSWORD="${N8N_ADMIN_PASSWORD:-}"
N8N_USER_PASSWORD="${N8N_USER_PASSWORD:-}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FIX_SCRIPT="${SCRIPT_DIR}/fix_n8n_permissions.sql"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Correção de Permissões n8n_admin${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Verificar se o script SQL existe
if [ ! -f "$FIX_SCRIPT" ]; then
    echo -e "${RED}❌ ERRO: Script fix_n8n_permissions.sql não encontrado em:${NC}"
    echo -e "${RED}   $FIX_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Script de correção encontrado${NC}"
echo ""

# Função para verificar se o PostgreSQL está acessível
check_postgres() {
    echo -e "${YELLOW}🔍 Verificando conexão com PostgreSQL...${NC}"
    if psql -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d postgres -c "SELECT version();" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL acessível${NC}"
        return 0
    else
        echo -e "${RED}❌ ERRO: Não foi possível conectar ao PostgreSQL${NC}"
        echo -e "${YELLOW}   Host: $POSTGRES_HOST${NC}"
        echo -e "${YELLOW}   Port: $POSTGRES_PORT${NC}"
        echo -e "${YELLOW}   User: $POSTGRES_USER${NC}"
        echo ""
        echo -e "${YELLOW}💡 Dica: Configure as variáveis de ambiente:${NC}"
        echo -e "${YELLOW}   export POSTGRES_HOST=seu_host${NC}"
        echo -e "${YELLOW}   export POSTGRES_PORT=sua_porta${NC}"
        echo -e "${YELLOW}   export POSTGRES_USER=seu_usuario${NC}"
        return 1
    fi
}

# Função para executar o script de correção
apply_fix() {
    echo ""
    echo -e "${YELLOW}🔧 Aplicando correções de permissões...${NC}"
    echo ""

    # Construir comando com variáveis de senha se fornecidas
    PSQL_CMD="psql -U \"$POSTGRES_USER\" -h \"$POSTGRES_HOST\" -p \"$POSTGRES_PORT\" -d postgres"

    if [ -n "$N8N_ADMIN_PASSWORD" ]; then
        echo -e "${GREEN}✅ Usando senha customizada para n8n_admin${NC}"
        PSQL_CMD="$PSQL_CMD -v n8n_admin_password=\"$N8N_ADMIN_PASSWORD\""
    else
        echo -e "${YELLOW}⚠️  Usando senha padrão para n8n_admin (changeme_admin_n8n)${NC}"
    fi

    if [ -n "$N8N_USER_PASSWORD" ]; then
        echo -e "${GREEN}✅ Usando senha customizada para n8n_user${NC}"
        PSQL_CMD="$PSQL_CMD -v n8n_user_password=\"$N8N_USER_PASSWORD\""
    else
        echo -e "${YELLOW}⚠️  Usando senha padrão para n8n_user (changeme_user_n8n)${NC}"
    fi

    echo ""

    if eval "$PSQL_CMD -f \"$FIX_SCRIPT\""; then
        echo ""
        echo -e "${GREEN}✅ Correções aplicadas com sucesso!${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}❌ ERRO ao aplicar correções${NC}"
        return 1
    fi
}

# Função para verificar se n8n está rodando em Docker
check_n8n_docker() {
    echo ""
    echo -e "${YELLOW}🐳 Verificando containers Docker do n8n...${NC}"

    N8N_CONTAINERS=$(docker ps --filter "name=n8n" --format "{{.Names}}" 2>/dev/null || echo "")

    if [ -z "$N8N_CONTAINERS" ]; then
        echo -e "${YELLOW}⚠️  Nenhum container n8n encontrado rodando${NC}"
        echo -e "${YELLOW}   Você precisará reiniciar o n8n manualmente após a correção${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Containers n8n encontrados:${NC}"
        echo "$N8N_CONTAINERS" | while read container; do
            echo -e "${GREEN}   - $container${NC}"
        done
        return 0
    fi
}

# Função para reiniciar containers n8n
restart_n8n() {
    N8N_CONTAINERS=$(docker ps --filter "name=n8n" --format "{{.Names}}" 2>/dev/null || echo "")

    if [ -n "$N8N_CONTAINERS" ]; then
        echo ""
        echo -e "${YELLOW}🔄 Deseja reiniciar os containers n8n agora? [S/n]${NC}"
        read -r response

        if [[ "$response" =~ ^([sS]|[yY]|)$ ]]; then
            echo "$N8N_CONTAINERS" | while read container; do
                echo -e "${YELLOW}   Reiniciando $container...${NC}"
                docker restart "$container"
            done
            echo -e "${GREEN}✅ Containers reiniciados${NC}"
        else
            echo -e "${YELLOW}⚠️  Lembre-se de reiniciar o n8n manualmente:${NC}"
            echo -e "${YELLOW}   docker restart <n8n-container-name>${NC}"
        fi
    fi
}

# Função para mostrar próximos passos
show_next_steps() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Próximos Passos${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo -e "${GREEN}1.${NC} Verifique os logs do n8n:"
    echo -e "   ${YELLOW}docker logs -f <n8n-container-name>${NC}"
    echo ""
    echo -e "${GREEN}2.${NC} Procure por mensagens de sucesso:"
    echo -e "   ${GREEN}✅ Database migration successful${NC}"
    echo -e "   ${GREEN}✅ n8n ready on port...${NC}"
    echo ""
    echo -e "${GREEN}3.${NC} Se ainda houver erros, execute:"
    echo -e "   ${YELLOW}psql -U $POSTGRES_USER -h $POSTGRES_HOST -d n8n_db -c \"\\\\du n8n_admin\"${NC}"
    echo -e "   ${YELLOW}psql -U $POSTGRES_USER -h $POSTGRES_HOST -d postgres -c \"\\\\l n8n_db\"${NC}"
    echo ""
    echo -e "${GREEN}4.${NC} Para mais detalhes, consulte:"
    echo -e "   ${YELLOW}docs/FIX_N8N_PERMISSIONS_ANALYSIS.md${NC}"
    echo ""
}

# Main execution
main() {
    # Verificar conexão
    if ! check_postgres; then
        exit 1
    fi

    # Verificar Docker
    check_n8n_docker
    HAS_DOCKER=$?

    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANTE: Este script irá:${NC}"
    echo -e "${YELLOW}   1. Adicionar privilégio CREATEDB ao usuário n8n_admin${NC}"
    echo -e "${YELLOW}   2. Alterar o OWNER do banco n8n_db para n8n_admin${NC}"
    echo -e "${YELLOW}   3. Conceder ALL PRIVILEGES no schema public${NC}"
    echo -e "${YELLOW}   4. Configurar default privileges${NC}"
    echo ""
    echo -e "${YELLOW}Deseja continuar? [S/n]${NC}"
    read -r response

    if [[ ! "$response" =~ ^([sS]|[yY]|)$ ]]; then
        echo -e "${RED}❌ Operação cancelada${NC}"
        exit 0
    fi

    # Aplicar correções
    if apply_fix; then
        # Reiniciar n8n se encontrado
        if [ $HAS_DOCKER -eq 0 ]; then
            restart_n8n
        fi

        # Mostrar próximos passos
        show_next_steps

        echo -e "${GREEN}============================================${NC}"
        echo -e "${GREEN}  ✅ Correção concluída com sucesso!${NC}"
        echo -e "${GREEN}============================================${NC}"
        exit 0
    else
        echo -e "${RED}============================================${NC}"
        echo -e "${RED}  ❌ Erro na aplicação da correção${NC}"
        echo -e "${RED}============================================${NC}"
        exit 1
    fi
}

# Executar main
main "$@"
