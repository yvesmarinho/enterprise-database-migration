# Guia de Configuração SSH para Git Push

**Situação Atual:** O push falhou com erro:
```
ERROR: Permission to yvesmarinho/enterprise-database-migration.git denied to deploy key
```

Isso indica que o repositório está usando uma **deploy key** que não tem permissão de escrita.

---

## 🔍 Diagnóstico

### 1. Verificar configuração atual

```bash
# Ver URL do repositório remoto
git remote -v

# Ver qual chave SSH está sendo usada
ssh -T git@github.com

# Listar chaves SSH disponíveis
ls -la ~/.ssh/
```

---

## ✅ Soluções (escolha uma)

### Opção 1: Usar sua Chave SSH Pessoal (Recomendado)

**Quando usar:** Para desenvolvimento pessoal, você precisa de acesso completo (leitura + escrita).

#### Passo 1: Verificar se você tem uma chave SSH

```bash
# Verificar chaves existentes
ls -la ~/.ssh/

# Procurar por:
# - id_rsa / id_rsa.pub (chave RSA - antiga)
# - id_ed25519 / id_ed25519.pub (chave Ed25519 - moderna, recomendada)
```

#### Passo 2: Criar uma nova chave SSH (se não tiver)

```bash
# Criar chave Ed25519 (recomendado)
ssh-keygen -t ed25519 -C "seu-email@example.com"

# OU criar chave RSA (se seu sistema não suportar Ed25519)
ssh-keygen -t rsa -b 4096 -C "seu-email@example.com"

# Pressione Enter para aceitar o local padrão (~/.ssh/id_ed25519)
# Digite uma senha forte (recomendado) ou deixe em branco
```

#### Passo 3: Adicionar chave ao SSH agent

```bash
# Iniciar o ssh-agent
eval "$(ssh-agent -s)"

# Adicionar sua chave privada
ssh-add ~/.ssh/id_ed25519
# OU
ssh-add ~/.ssh/id_rsa
```

#### Passo 4: Copiar chave pública e adicionar ao GitHub

```bash
# Copiar chave pública para clipboard
cat ~/.ssh/id_ed25519.pub
# OU
cat ~/.ssh/id_rsa.pub

# A saída será algo como:
# ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJl3... seu-email@example.com
```

**Adicionar ao GitHub:**
1. Acesse: https://github.com/settings/keys
2. Clique em "New SSH key"
3. Título: `Seu-Computador-$(date +%Y-%m-%d)`
4. Cole a chave pública completa
5. Clique em "Add SSH key"

#### Passo 5: Testar conexão

```bash
# Testar conexão com GitHub
ssh -T git@github.com

# Deve mostrar:
# Hi yvesmarinho! You've successfully authenticated...
```

#### Passo 6: Fazer push

```bash
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration
git push origin main
```

---

### Opção 2: Configurar Deploy Key com Permissão de Escrita

**Quando usar:** Se você quer usar uma deploy key específica para este projeto.

#### Passo 1: Criar chave específica para o projeto

```bash
# Criar chave dedicada
ssh-keygen -t ed25519 -f ~/.ssh/enterprise-db-migration -C "enterprise-db-deploy"

# Adicionar ao ssh-agent
ssh-add ~/.ssh/enterprise-db-migration
```

#### Passo 2: Configurar SSH para usar essa chave

Crie/edite `~/.ssh/config`:

```bash
# Abrir ou criar arquivo config
nano ~/.ssh/config
```

Adicione:

```ssh-config
# GitHub - Enterprise Database Migration
Host github-enterprise-migration
    HostName github.com
    User git
    IdentityFile ~/.ssh/enterprise-db-migration
    IdentitiesOnly yes
```

#### Passo 3: Adicionar chave como Deploy Key no GitHub

```bash
# Copiar chave pública
cat ~/.ssh/enterprise-db-migration.pub
```

**No GitHub:**
1. Vá para: https://github.com/yvesmarinho/enterprise-database-migration/settings/keys
2. Clique em "Add deploy key"
3. Título: `Deploy Key - $(hostname) - Write Access`
4. Cole a chave pública
5. ✅ **IMPORTANTE:** Marque "Allow write access"
6. Clique em "Add key"

#### Passo 4: Atualizar URL do repositório

```bash
# Atualizar remote para usar o host configurado
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration
git remote set-url origin github-enterprise-migration:yvesmarinho/enterprise-database-migration.git

# Verificar
git remote -v
```

#### Passo 5: Fazer push

```bash
git push origin main
```

---

### Opção 3: Usar HTTPS com Token (Alternativa)

**Quando usar:** Se você tem problemas com SSH ou prefere HTTPS.

#### Passo 1: Criar Personal Access Token no GitHub

1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token" → "Generate new token (classic)"
3. Nome: `Enterprise DB Migration - $(hostname)`
4. Selecione escopo: ✅ `repo` (acesso completo a repositórios privados)
5. Clique em "Generate token"
6. **COPIE O TOKEN** (você não verá novamente!)

#### Passo 2: Atualizar URL do repositório

```bash
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration

# Mudar para HTTPS
git remote set-url origin https://github.com/yvesmarinho/enterprise-database-migration.git

# Verificar
git remote -v
```

#### Passo 3: Fazer push (vai pedir credenciais)

```bash
git push origin main

# Username: yvesmarinho
# Password: [COLE SEU TOKEN AQUI]
```

#### Passo 4: Salvar credenciais (opcional)

```bash
# Salvar credenciais para não pedir sempre
git config --global credential.helper store

# Próximo push salvará as credenciais
```

---

## 🔧 Troubleshooting

### Erro: "Permission denied"

```bash
# Verificar qual chave está sendo usada
ssh -vT git@github.com 2>&1 | grep "identity file"

# Verificar se a chave está no ssh-agent
ssh-add -l

# Adicionar chave manualmente
ssh-add ~/.ssh/id_ed25519
```

### Erro: "Could not resolve hostname"

```bash
# Testar conectividade
ping github.com

# Verificar DNS
nslookup github.com
```

### Verificar permissões das chaves

```bash
# Chaves privadas devem ter permissão 600
chmod 600 ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_rsa

# Chaves públicas podem ter 644
chmod 644 ~/.ssh/id_ed25519.pub
chmod 644 ~/.ssh/id_rsa.pub

# Diretório .ssh deve ser 700
chmod 700 ~/.ssh
```

---

## 📋 Verificação Rápida

Execute este script para diagnóstico:

```bash
#!/bin/bash
echo "=== Diagnóstico SSH/Git ==="
echo ""
echo "1. URL do repositório:"
git remote -v | grep origin
echo ""
echo "2. Chaves SSH disponíveis:"
ls -lh ~/.ssh/ | grep -E "(id_|known)"
echo ""
echo "3. Chaves no ssh-agent:"
ssh-add -l 2>/dev/null || echo "ssh-agent não iniciado"
echo ""
echo "4. Teste de conexão GitHub:"
ssh -T git@github.com 2>&1 | grep -E "(Hi|successfully|Permission)"
echo ""
echo "5. Configuração Git:"
echo "   User: $(git config user.name)"
echo "   Email: $(git config user.email)"
echo ""
echo "=== Fim do diagnóstico ==="
```

Salve como `diagnose-ssh.sh`, dê permissão e execute:

```bash
chmod +x diagnose-ssh.sh
./diagnose-ssh.sh
```

---

## 🎯 Recomendação

Para uso pessoal neste projeto, recomendo:

1. **Use a Opção 1** (chave SSH pessoal)
2. **Ed25519** é mais moderna e segura que RSA
3. **Adicione senha** à sua chave privada para segurança extra
4. **Use ssh-agent** para não precisar digitar a senha toda hora

---

## 📚 Referências

- [Documentação oficial GitHub - SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Gerar nova chave SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
- [Deploy Keys](https://docs.github.com/en/developers/overview/managing-deploy-keys)

---

**Criado em:** 11 de março de 2026
**Projeto:** Enterprise Database Migration
