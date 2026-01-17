# Scripts de Correção - n8n Permissions

Este diretório contém scripts para corrigir o problema de permissões do usuário `n8n_admin` no banco de dados `n8n_db`.

## 🔴 Problema

O Docker do n8n está reportando erro de permissão:

```
ERROR: permission denied for schema public
ERROR: permission denied for table <table_name>
ERROR: must be owner of database n8n_db
```

**Causa:** O usuário `n8n_admin` foi criado sem os privilégios necessários para operações DDL (CREATE, ALTER, DROP) no banco `n8n_db`.

## ✅ Solução Rápida

### Opção 1: Script Automatizado (Recomendado)

```bash
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration

# Com senhas padrão (não recomendado para produção)
./scripts/apply_n8n_fix.sh

# Com senhas customizadas (RECOMENDADO)
export N8N_ADMIN_PASSWORD='sua_senha_admin_segura'
export N8N_USER_PASSWORD='sua_senha_user_segura'
./scripts/apply_n8n_fix.sh
```

O script irá:
- ✅ Verificar conexão com PostgreSQL
- ✅ Aplicar todas as correções necessárias
- ✅ Criar/atualizar senhas dos usuários
- ✅ Detectar containers n8n Docker
- ✅ Oferecer reiniciar os containers automaticamente
- ✅ Mostrar os próximos passos

### Opção 2: Manual

```bash
# Com senhas padrão (não recomendado)
psql -U postgres -d postgres -f scripts/fix_n8n_permissions.sql

# Com senhas customizadas (RECOMENDADO)
psql -U postgres -d postgres \
  -v n8n_admin_password='sua_senha_admin_segura' \
  -v n8n_user_password='sua_senha_user_segura' \
  -f scripts/fix_n8n_permissions.sql

# Reiniciar container n8n
docker restart <n8n-container-name>
```

### 🔐 Senhas Padrão

Se você **não** fornecer senhas customizadas, serão usadas:
- `n8n_admin`: `changeme_admin_n8n`
- `n8n_user`: `changeme_user_n8n`

⚠️ **ATENÇÃO:** Sempre use senhas fortes em produção!

## 📄 Arquivos

### 1. `fix_n8n_permissions.sql`
Script SQL completo que:
- Adiciona privilégio `CREATEDB` ao `n8n_admin`
- Altera OWNER do banco para `n8n_admin`
- Concede ALL PRIVILEGES no schema public ao `n8n_admin`
- Configura permissões em tabelas, sequences e funções para `n8n_admin`
- **Configura `n8n_user` como SOMENTE LEITURA** (SELECT apenas)
- Configura default privileges para objetos futuros
- Concede ALL PRIVILEGES no schema public
- Configura permissões em tabelas, sequences e funções
- Configura default privileges para objetos futuros

### 2. `apply_n8n_fix.sh`
Script bash automatizado que:
- Verifica conexão com PostgreSQL
- Executa o script SQL de correção
- Detecta e pode reiniciar containers n8n
- Fornece feedback colorido e próximos passos

### 3. `alter_evolution_api_db_only.sql`
Script genérico para alterações de databases (exemplo de referência).

## 🔍 Verificação

Após aplicar a correção, verifique:

```bash
# 1. Verificar privilégios do n8n_admin
psql -U postgres -d postgres -c "SELECT rolname, rolcreatedb FROM pg_roles WHERE rolname = 'n8n_admin';"

# 2. Verificar owner do banco
psql -U postgres -d postgres -c "SELECT datname, pg_catalog.pg_get_userbyid(datdba) AS owner FROM pg_database WHERE datname = 'n8n_db';"

# 3. Verificar permissões de n8n_user (deve ser readonly)
psql -U postgres -d n8n_db -c "SELECT grantee, privilege_type FROM information_schema.table_privileges WHERE grantee = 'n8n_user' AND table_schema = 'public' LIMIT 5;"

# 4. Verificar logs do n8n
docker logs -f <n8n-container-name>
```

**Resultado esperado:**
```
rolname   | rolcreatedb
----------+-------------
n8n_admin | t           ← Deve ser 't' (true)

datname | owner
--------+-----------
n8n_db  | n8n_admin  ← Deve ser 'n8n_admin'

grantee  | privilege_type
---------+----------------
n8n_user | SELECT        ← Apenas SELECT (readonly)
```

## 👥 Usuários n8n

### `n8n_admin` - Administrador (Leitura + Escrita)
- ✅ CREATEDB
- ✅ OWNER do banco n8n_db
- ✅ ALL PRIVILEGES no schema public
- ✅ CREATE, ALTER, DROP (DDL)
- ✅ INSERT, UPDATE, DELETE (DML)
- ✅ SELECT (leitura)

**Uso:** Aplicação n8n principal, migrations, administração

### `n8n_user` - Somente Leitura
- ✅ CONNECT no database
- ✅ USAGE no schema public
- ✅ SELECT em tabelas (apenas leitura)
- ✅ SELECT em sequences
- ❌ Sem CREATE, INSERT, UPDATE, DELETE
- ❌ Sem ALTER, DROP

**Uso:** Relatórios, dashboards, monitoramento, backups read-only

## 📚 Documentação Completa

Para análise técnica detalhada, consulte:
- [docs/FIX_N8N_PERMISSIONS_ANALYSIS.md](../docs/FIX_N8N_PERMISSIONS_ANALYSIS.md)

## ⚙️ Variáveis de Ambiente

### PostgreSQL Connection
```bash
export POSTGRES_HOST=localhost    # Padrão: localhost
export POSTGRES_PORT=5432         # Padrão: 5432
export POSTGRES_USER=postgres     # Padrão: postgres
```

### Senhas dos Usuários (IMPORTANTE)
```bash
export N8N_ADMIN_PASSWORD='sua_senha_admin_forte'    # Padrão: changeme_admin_n8n
export N8N_USER_PASSWORD='sua_senha_user_forte'      # Padrão: changeme_user_n8n
```

**⚠️ Senhas Padrão:**
- Se não definidas, serão usadas senhas padrão **INSEGURAS**
- **SEMPRE** defina senhas fortes em ambientes de produção
- As senhas padrão servem apenas para desenvolvimento/teste

**Exemplo completo:**
```bash
export POSTGRES_HOST=10.0.0.5
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export N8N_ADMIN_PASSWORD='M1nh@S3nh@F0rt3!Admin'
export N8N_USER_PASSWORD='M1nh@S3nh@F0rt3!User'

./scripts/apply_n8n_fix.sh
```

## 🆘 Troubleshooting

### Erro: "connection refused"
```bash
# Verificar se PostgreSQL está rodando
systemctl status postgresql
# ou
docker ps | grep postgres
```

### Erro: "permission denied"
```bash
# Executar como superuser (postgres)
sudo -u postgres psql -d postgres -f scripts/fix_n8n_permissions.sql
```

### n8n ainda com erro após correção
```bash
# 1. Limpar cache do n8n
docker exec <n8n-container> rm -rf /home/node/.n8n/cache/*

# 2. Reiniciar com logs
docker restart <n8n-container> && docker logs -f <n8n-container>

# 3. Verificar string de conexão do n8n
docker exec <n8n-container> env | grep DB_
```

## 📞 Suporte

Se o problema persistir:
1. Verifique os logs completos do n8n
2. Consulte a documentação completa em `docs/FIX_N8N_PERMISSIONS_ANALYSIS.md`
3. Verifique a string de conexão do n8n (deve usar `n8n_admin`)

---

**Criado em:** 12 de janeiro de 2026
**Autor:** GitHub Copilot
**Projeto:** enterprise-database-migration
