# Análise e Correção: Problema de Permissões n8n_admin

**Data:** 12 de janeiro de 2026
**Problema:** Docker do n8n reclamando que n8n_admin não tem permissão para fazer alteração no banco n8n_db

---

## 🔍 Diagnóstico do Problema

### 1. Situação Atual

#### Usuário `n8n_admin`:
```sql
CREATE ROLE "n8n_admin" WITH LOGIN INHERIT PASSWORD '********';
```

**Problemas identificados:**
- ❌ **NÃO tem** privilégio `CREATEDB`
- ❌ **NÃO tem** privilégios administrativos suficientes
- ❌ **NÃO é** OWNER do banco `n8n_db`
- ✅ Tem apenas `LOGIN INHERIT` (insuficiente para operações DDL)

#### Banco `n8n_db`:
```sql
CREATE DATABASE "n8n_db"
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    TABLESPACE = pg_default
    TEMPLATE = template0
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;
```

**Problemas identificados:**
- ❌ Owner é `postgres`, não `n8n_admin`
- ✅ Banco existe e está configurado corretamente
- ⚠️ Grants existem mas são insuficientes:
  ```sql
  GRANT CONNECT ON DATABASE "n8n_db" TO "n8n_admin";
  GRANT CREATE ON DATABASE "n8n_db" TO "n8n_admin";
  GRANT TEMPORARY ON DATABASE "n8n_db" TO "n8n_admin";
  ```

### 2. Permissões Detectadas

De acordo com os dados extraídos em `extracted_data_20251006_142153.json`:

```json
"n8n_db": [
  {
    "grantee": "n8n_admin",
    "privileges": [
      "CONNECT",
      "CREATE",
      "TEMPORARY"
    ]
  },
  {
    "grantee": "n8n_user",
    "privileges": [
      "CONNECT",
      "CREATE",
      "TEMPORARY"
    ]
  },
  {
    "grantee": "postgres",
    "privileges": [
      "CONNECT",
      "CREATE",
      "TEMPORARY"
    ]
  }
]
```

**Análise:**
- `n8n_admin` tem apenas permissões de DATABASE level
- **NÃO TEM** permissões de SCHEMA level (public)
- **NÃO TEM** permissões em TABLES, SEQUENCES, FUNCTIONS
- **NÃO TEM** DEFAULT PRIVILEGES configuradas

---

## ⚠️ Impacto

### O que o n8n NÃO consegue fazer:

1. **CREATE TABLE** - Criar novas tabelas
2. **ALTER TABLE** - Modificar estrutura de tabelas
3. **DROP TABLE** - Remover tabelas
4. **CREATE INDEX** - Criar índices
5. **CREATE SEQUENCE** - Criar sequences
6. **CREATE FUNCTION** - Criar funções/procedures
7. **INSERT/UPDATE/DELETE** - Operações DML em tabelas existentes
8. **Migrações automáticas** - Sistema de migrations do n8n falha

### Erro típico do Docker n8n:

```
ERROR: permission denied for schema public
ERROR: permission denied for table <table_name>
ERROR: must be owner of database n8n_db
```

---

## ✅ Solução Implementada

### Arquivo: `scripts/fix_n8n_permissions.sql`

Este script implementa uma solução completa em múltiplas camadas:

### 1. **Ajuste do Role n8n_admin**
```sql
ALTER ROLE "n8n_admin" WITH CREATEDB;
```
- Adiciona privilégio CREATEDB ao usuário

### 2. **Transferência de Ownership**
```sql
ALTER DATABASE "n8n_db" OWNER TO "n8n_admin";
```
- Torna n8n_admin o dono do banco (controle total)

### 3. **Privilégios Explícitos no Database**
```sql
GRANT ALL PRIVILEGES ON DATABASE "n8n_db" TO "n8n_admin";
```

### 4. **Privilégios no Schema Public**
```sql
GRANT ALL ON SCHEMA public TO "n8n_admin";
```

### 5. **Privilégios em Objetos Existentes**
```sql
-- Tabelas
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "n8n_admin";

-- Sequences
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "n8n_admin";

-- Funções
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "n8n_admin";
```

### 6. **Default Privileges (Objetos Futuros)**
```sql
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO "n8n_admin";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO "n8n_admin";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO "n8n_admin";
```

---

## 🚀 Como Aplicar a Correção

### Passo 1: Executar o script de correção
```bash
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration

# Executar como superuser (postgres)
psql -U postgres -d postgres -f scripts/fix_n8n_permissions.sql
```

### Passo 2: Verificar as permissões
```bash
# O script já faz verificação automática, mas você pode conferir:
psql -U postgres -d postgres -c "SELECT rolname, rolcreatedb FROM pg_roles WHERE rolname = 'n8n_admin';"

psql -U postgres -d postgres -c "SELECT datname, pg_catalog.pg_get_userbyid(datdba) AS owner FROM pg_database WHERE datname = 'n8n_db';"
```

### Passo 3: Reiniciar o container n8n
```bash
# Identifique o container
docker ps | grep n8n

# Reinicie
docker restart <n8n-container-id>

# Ou se estiver usando docker-compose
cd /path/to/n8n
docker-compose restart n8n
```

### Passo 4: Verificar logs do n8n
```bash
docker logs -f <n8n-container-id>

# Procure por:
# ✅ "Database migration successful"
# ✅ "n8n ready on port..."
# ❌ NÃO deve ter "permission denied"
```

---

## 📋 Checklist de Verificação Pós-Correção

- [ ] Script executado sem erros
- [ ] `n8n_admin` tem `CREATEDB = true`
- [ ] `n8n_db` tem `OWNER = n8n_admin`
- [ ] Container n8n reiniciado
- [ ] Logs do n8n sem erros de permissão
- [ ] n8n consegue criar workflows
- [ ] n8n consegue executar workflows
- [ ] Migrações automáticas funcionando

---

## 🔧 Correção Preventiva para Novos Bancos

### Atualizar `generated_scripts/01_create_users.sql`:

```sql
-- ANTES (INCORRETO):
-- Usuário: n8n_admin
CREATE ROLE "n8n_admin" WITH LOGIN INHERIT PASSWORD '********';

-- DEPOIS (CORRETO):
-- Usuário: n8n_admin
-- NOTA: CREATEDB necessário para operações DDL no banco n8n_db
CREATE ROLE "n8n_admin" WITH LOGIN INHERIT CREATEDB PASSWORD '********';
```

### Atualizar `generated_scripts/02_create_databases.sql`:

```sql
-- ANTES (INCORRETO):
CREATE DATABASE "n8n_db"
    WITH
    OWNER = postgres
    ...

-- DEPOIS (CORRETO):
CREATE DATABASE "n8n_db"
    WITH
    OWNER = n8n_admin  -- Usar n8n_admin como owner
    ...
```

### Atualizar `generated_scripts/03_apply_grants.sql`:

Adicionar após os grants existentes:

```sql
-- =====================================================
-- GRANTS EXTRAS PARA BASE: n8n_db
-- Garantir permissões completas para n8n_admin
-- =====================================================

-- Conectar ao banco para ajustar schema e objetos
\c n8n_db

GRANT ALL ON SCHEMA public TO "n8n_admin";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "n8n_admin";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "n8n_admin";
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "n8n_admin";

-- Configurar default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO "n8n_admin";
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO "n8n_admin";
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO "n8n_admin";

\c postgres
```

---

## 📊 Comparação: Antes vs Depois

| Aspecto | ANTES ❌ | DEPOIS ✅ |
|---------|---------|-----------|
| **Role Privileges** | `LOGIN INHERIT` | `LOGIN INHERIT CREATEDB` |
| **Database Owner** | `postgres` | `n8n_admin` |
| **Schema Privileges** | ❌ Nenhum | `ALL ON SCHEMA public` |
| **Table Privileges** | ❌ Nenhum | `ALL ON ALL TABLES` |
| **Sequence Privileges** | ❌ Nenhum | `ALL ON ALL SEQUENCES` |
| **Function Privileges** | ❌ Nenhum | `EXECUTE ON ALL FUNCTIONS` |
| **Default Privileges** | ❌ Não configurado | ✅ Configurado |
| **n8n Funcionalidade** | ❌ Quebrado | ✅ Funcionando |

---

## 🎯 Conclusão

### Causa Raiz:
O sistema de migração gerou scripts que criaram o usuário `n8n_admin` **sem privilégios suficientes** e o banco `n8n_db` com owner incorreto.

### Solução:
1. ✅ Script de correção criado: `scripts/fix_n8n_permissions.sql`
2. ✅ Documentação completa do problema e solução
3. ⚠️ Recomendação: Atualizar scripts de geração para evitar recorrência

### Próximos Passos:
1. Executar `fix_n8n_permissions.sql`
2. Reiniciar container n8n
3. Validar funcionamento
4. (Opcional) Atualizar scripts gerados com as correções preventivas

---

## 📚 Referências

- PostgreSQL Documentation: [GRANT](https://www.postgresql.org/docs/current/sql-grant.html)
- PostgreSQL Documentation: [ALTER ROLE](https://www.postgresql.org/docs/current/sql-alterrole.html)
- PostgreSQL Documentation: [ALTER DATABASE](https://www.postgresql.org/docs/current/sql-alterdatabase.html)
- PostgreSQL Documentation: [ALTER DEFAULT PRIVILEGES](https://www.postgresql.org/docs/current/sql-alterdefaultprivileges.html)
- n8n Documentation: [Database Configuration](https://docs.n8n.io/hosting/configuration/configuration-methods/)

---

**Arquivo criado por:** GitHub Copilot
**Script de correção:** `/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration/scripts/fix_n8n_permissions.sql`
