#!/bin/bash
# Script de diagnóstico SSH/Git
# Verifica configuração atual e sugere correções

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     DIAGNÓSTICO SSH/GIT - Enterprise Database Migration        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Verificar URL do repositório
echo -e "${BLUE}1️⃣  URL do Repositório Remoto:${NC}"
echo "─────────────────────────────────────────────────────────────────"
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ${GREEN}✓${NC} $REMOTE_URL"

    if [[ $REMOTE_URL == git@* ]]; then
        echo "   📌 Usando SSH"
    elif [[ $REMOTE_URL == https://* ]]; then
        echo "   📌 Usando HTTPS"
    fi
else
    echo "   ${RED}✗${NC} Repositório remoto não encontrado"
fi
echo ""

# 2. Verificar chaves SSH disponíveis
echo -e "${BLUE}2️⃣  Chaves SSH Disponíveis:${NC}"
echo "─────────────────────────────────────────────────────────────────"
SSH_DIR="$HOME/.ssh"

if [ -d "$SSH_DIR" ]; then
    KEYS_FOUND=0

    # Verificar chaves Ed25519
    if [ -f "$SSH_DIR/id_ed25519" ]; then
        echo "   ${GREEN}✓${NC} id_ed25519 (Ed25519 - Recomendada)"
        KEYS_FOUND=$((KEYS_FOUND + 1))
    fi

    # Verificar chaves RSA
    if [ -f "$SSH_DIR/id_rsa" ]; then
        echo "   ${GREEN}✓${NC} id_rsa (RSA)"
        KEYS_FOUND=$((KEYS_FOUND + 1))
    fi

    # Verificar outras chaves
    for key in "$SSH_DIR"/id_*; do
        if [ -f "$key" ] && [[ ! "$key" =~ \.pub$ ]]; then
            keyname=$(basename "$key")
            if [[ "$keyname" != "id_ed25519" ]] && [[ "$keyname" != "id_rsa" ]]; then
                echo "   ${GREEN}✓${NC} $keyname"
                KEYS_FOUND=$((KEYS_FOUND + 1))
            fi
        fi
    done

    if [ $KEYS_FOUND -eq 0 ]; then
        echo "   ${YELLOW}⚠${NC}  Nenhuma chave SSH encontrada"
        echo "   ${YELLOW}→${NC}  Execute: ssh-keygen -t ed25519 -C \"seu-email@example.com\""
    fi
else
    echo "   ${RED}✗${NC} Diretório ~/.ssh não existe"
    echo "   ${YELLOW}→${NC}  Execute: mkdir -p ~/.ssh && chmod 700 ~/.ssh"
fi
echo ""

# 3. Verificar permissões das chaves
echo -e "${BLUE}3️⃣  Permissões das Chaves:${NC}"
echo "─────────────────────────────────────────────────────────────────"
if [ -d "$SSH_DIR" ]; then
    PERMS_OK=true

    # Verificar permissão do diretório
    DIR_PERMS=$(stat -c %a "$SSH_DIR" 2>/dev/null || stat -f %A "$SSH_DIR" 2>/dev/null)
    if [ "$DIR_PERMS" = "700" ]; then
        echo "   ${GREEN}✓${NC} ~/.ssh/ ($DIR_PERMS) - OK"
    else
        echo "   ${YELLOW}⚠${NC}  ~/.ssh/ ($DIR_PERMS) - Deveria ser 700"
        echo "   ${YELLOW}→${NC}  Execute: chmod 700 ~/.ssh"
        PERMS_OK=false
    fi

    # Verificar permissões das chaves privadas
    for key in "$SSH_DIR"/id_*; do
        if [ -f "$key" ] && [[ ! "$key" =~ \.pub$ ]]; then
            KEY_PERMS=$(stat -c %a "$key" 2>/dev/null || stat -f %A "$key" 2>/dev/null)
            keyname=$(basename "$key")
            if [ "$KEY_PERMS" = "600" ]; then
                echo "   ${GREEN}✓${NC} $keyname ($KEY_PERMS) - OK"
            else
                echo "   ${YELLOW}⚠${NC}  $keyname ($KEY_PERMS) - Deveria ser 600"
                echo "   ${YELLOW}→${NC}  Execute: chmod 600 $key"
                PERMS_OK=false
            fi
        fi
    done

    if [ "$PERMS_OK" = true ]; then
        echo "   ${GREEN}✓${NC} Todas as permissões estão corretas"
    fi
else
    echo "   ${RED}✗${NC} Diretório ~/.ssh não existe"
fi
echo ""

# 4. Verificar SSH agent
echo -e "${BLUE}4️⃣  SSH Agent:${NC}"
echo "─────────────────────────────────────────────────────────────────"
if [ -n "$SSH_AUTH_SOCK" ]; then
    echo "   ${GREEN}✓${NC} SSH Agent está rodando"

    # Listar chaves carregadas
    KEYS_LOADED=$(ssh-add -l 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   ${GREEN}✓${NC} Chaves carregadas no agent:"
        echo "$KEYS_LOADED" | while read line; do
            echo "      • $line"
        done
    else
        echo "   ${YELLOW}⚠${NC}  Nenhuma chave carregada no agent"
        echo "   ${YELLOW}→${NC}  Execute: ssh-add ~/.ssh/id_ed25519"
    fi
else
    echo "   ${YELLOW}⚠${NC}  SSH Agent não está rodando"
    echo "   ${YELLOW}→${NC}  Execute: eval \"\$(ssh-agent -s)\" && ssh-add ~/.ssh/id_ed25519"
fi
echo ""

# 5. Testar conexão com GitHub
echo -e "${BLUE}5️⃣  Conexão com GitHub:${NC}"
echo "─────────────────────────────────────────────────────────────────"
SSH_TEST=$(ssh -T git@github.com 2>&1)

if echo "$SSH_TEST" | grep -q "successfully authenticated"; then
    USERNAME=$(echo "$SSH_TEST" | grep -oP "Hi \K[^!]+")
    echo "   ${GREEN}✓${NC} Autenticado com sucesso como: $USERNAME"
elif echo "$SSH_TEST" | grep -q "Permission denied"; then
    echo "   ${RED}✗${NC} Permissão negada"
    echo "   ${YELLOW}→${NC}  Chave SSH não está configurada no GitHub"
    echo "   ${YELLOW}→${NC}  Acesse: https://github.com/settings/keys"
elif echo "$SSH_TEST" | grep -q "Could not resolve"; then
    echo "   ${RED}✗${NC} Não foi possível conectar ao GitHub"
    echo "   ${YELLOW}→${NC}  Verifique sua conexão com a internet"
else
    echo "   ${YELLOW}⚠${NC}  Resposta inesperada:"
    echo "      $SSH_TEST"
fi
echo ""

# 6. Configuração Git
echo -e "${BLUE}6️⃣  Configuração Git:${NC}"
echo "─────────────────────────────────────────────────────────────────"
GIT_USER=$(git config user.name)
GIT_EMAIL=$(git config user.email)

if [ -n "$GIT_USER" ]; then
    echo "   ${GREEN}✓${NC} Nome: $GIT_USER"
else
    echo "   ${YELLOW}⚠${NC}  Nome não configurado"
    echo "   ${YELLOW}→${NC}  Execute: git config --global user.name \"Seu Nome\""
fi

if [ -n "$GIT_EMAIL" ]; then
    echo "   ${GREEN}✓${NC} Email: $GIT_EMAIL"
else
    echo "   ${YELLOW}⚠${NC}  Email não configurado"
    echo "   ${YELLOW}→${NC}  Execute: git config --global user.email \"seu-email@example.com\""
fi
echo ""

# 7. Status do repositório
echo -e "${BLUE}7️⃣  Status do Repositório:${NC}"
echo "─────────────────────────────────────────────────────────────────"
BRANCH=$(git branch --show-current 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   ${GREEN}✓${NC} Branch atual: $BRANCH"

    # Verificar commits à frente
    AHEAD=$(git rev-list --count @{u}..HEAD 2>/dev/null)
    if [ $? -eq 0 ] && [ "$AHEAD" -gt 0 ]; then
        echo "   ${YELLOW}⚠${NC}  $AHEAD commit(s) não enviado(s) para o remoto"
        echo "   ${YELLOW}→${NC}  Execute: git push origin $BRANCH"
    fi
else
    echo "   ${RED}✗${NC} Não está em um repositório git"
fi
echo ""

# Resumo e Recomendações
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    RESUMO E RECOMENDAÇÕES                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar o que precisa ser feito
ISSUES=0

if [ ! -d "$SSH_DIR" ] || [ $KEYS_FOUND -eq 0 ]; then
    echo "${YELLOW}🔑 Criar chave SSH:${NC}"
    echo "   ssh-keygen -t ed25519 -C \"seu-email@example.com\""
    echo ""
    ISSUES=$((ISSUES + 1))
fi

if echo "$SSH_TEST" | grep -q "Permission denied"; then
    echo "${YELLOW}📤 Adicionar chave ao GitHub:${NC}"
    echo "   1. Copie a chave: cat ~/.ssh/id_ed25519.pub"
    echo "   2. Acesse: https://github.com/settings/keys"
    echo "   3. Clique em 'New SSH key' e cole a chave"
    echo ""
    ISSUES=$((ISSUES + 1))
fi

if [ -n "$SSH_AUTH_SOCK" ] && ! ssh-add -l &>/dev/null; then
    echo "${YELLOW}🔐 Adicionar chave ao SSH agent:${NC}"
    echo "   ssh-add ~/.ssh/id_ed25519"
    echo ""
    ISSUES=$((ISSUES + 1))
fi

if [ "$PERMS_OK" = false ]; then
    echo "${YELLOW}🔒 Corrigir permissões:${NC}"
    echo "   chmod 700 ~/.ssh"
    echo "   chmod 600 ~/.ssh/id_*"
    echo "   chmod 644 ~/.ssh/id_*.pub"
    echo ""
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo "${GREEN}✨ Tudo certo! Você pode fazer push:${NC}"
    echo "   git push origin main"
    echo ""
else
    echo "${YELLOW}⚠  Encontrados $ISSUES problema(s) para resolver.${NC}"
    echo ""
    echo "📚 Consulte o guia completo: GUIA_CONFIGURACAO_SSH.md"
fi

echo "═══════════════════════════════════════════════════════════════════"
echo ""
