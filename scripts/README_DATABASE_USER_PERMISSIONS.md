# Setup Universal de Usuários - MySQL/MariaDB e PostgreSQL

Script Python 3.11 universal para criar e configurar usuários em **MySQL/MariaDB** e **PostgreSQL** com permissões específicas usando SQLAlchemy.

## 🎯 Características Principais

- ✅ **Suporte Multi-Banco**: MySQL/MariaDB e PostgreSQL no mesmo script
- ✅ **Modo Interativo**: Solicita todas as informações necessárias
- ✅ **Modo CLI**: Aceita parâmetros via linha de comando
- ✅ **4 Tipos de Usuário**: write, read, backup, migration
- ✅ **Escopo Flexível**: Global (todas as databases) ou específico
- ✅ **SQLAlchemy**: Código reutilizável e compatível
- ✅ **Validação**: Verifica usuário existente antes de criar
- ✅ **Visualização**: Mostra os grants concedidos

## 🗄️ Bancos Suportados

| Banco | Aliases Aceitos | Porta Padrão |
|-------|----------------|--------------|
| MySQL/MariaDB | `mysql`, `mariadb` | 3306 |
| PostgreSQL | `postgresql`, `postgres`, `pg` | 5432 |

## 🎯 Tipos de Usuário

### 1. **read** (Somente Leitura)

**MySQL**: `SELECT`, `SHOW VIEW`
**PostgreSQL**: `CONNECT`, `SELECT`, `USAGE`

Ideal para:
- Relatórios e dashboards
- Usuários de análise
- Ferramentas de BI (Metabase, PowerBI)

### 2. **write** (Leitura e Escrita)

**MySQL**: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `EXECUTE`, `SHOW VIEW`
**PostgreSQL**: `CONNECT`, `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `USAGE`

Ideal para:
- Aplicações web
- APIs REST/GraphQL
- Sistemas CRUD

### 3. **backup** (Backup e Replicação)

**MySQL**: `SELECT`, `SHOW VIEW`, `LOCK TABLES`, `RELOAD`, `REPLICATION CLIENT`
**PostgreSQL**: `CONNECT`, `SELECT`, `USAGE`

Ideal para:
- Sistemas de backup automatizado
- Ferramentas de sincronização
- Replicação de dados

### 4. **migration** (Administração Completa)

**MySQL**: `ALL PRIVILEGES`
**PostgreSQL**: `ALL` (incluindo DDL em schemas)

Ideal para:
- Migrações de schema (Flyway, Liquibase)
- Administração de database
- Deployment de aplicações

## 🚀 Como Usar

### Pré-requisitos

```bash
# Instalar dependências
pip install sqlalchemy pymysql psycopg2-binary

# Ou usando requirements.txt do projeto
pip install -r requirements.txt
```

### Modo Interativo (Recomendado)

```bash
python scripts/setup_database_user_permissions.py
```

O script solicitará:
1. **Tipo de Banco**: MySQL ou PostgreSQL
2. **Servidor**: Host, porta, usuário admin e senha
3. **Novo Usuário**: Nome, senha e padrão de host (MySQL)
4. **Tipo**: read, write, backup ou migration
5. **Database**: Nome específico ou vazio para global

**Exemplo de execução:**

```
══════════════════════════════════════════════════════════════════════
GERENCIADOR UNIVERSAL DE USUÁRIOS DE BANCO DE DADOS
══════════════════════════════════════════════════════════════════════

🗄️  TIPO DE BANCO DE DADOS
──────────────────────────────────────────────────────────────────────
Tipos suportados:
  1. MySQL/MariaDB
  2. PostgreSQL

Escolha o tipo [1]: 2

📡 CONEXÃO COM O SERVIDOR
──────────────────────────────────────────────────────────────────────
Host do servidor [localhost]: wfdb02.vya.digital
Porta [5432]: 5432
Usuário administrativo [root]: postgres
Senha do usuário administrativo: ********

👤 NOVO USUÁRIO
──────────────────────────────────────────────────────────────────────
Nome do novo usuário: backup_user
Senha do novo usuário: ********
Confirme a senha: ********

🔐 TIPO DE USUÁRIO E PERMISSÕES
──────────────────────────────────────────────────────────────────────
Tipos disponíveis:
  • write        - Permissões de leitura e escrita (sem DDL)
  • read         - Apenas permissões de leitura
  • backup       - Permissões otimizadas para backup
  • migration    - Permissões completas incluindo DDL

Tipo de usuário [read]: backup

💾 BASE DE DADOS
──────────────────────────────────────────────────────────────────────
Nome da database (deixe vazio para global):

✅ Conectado ao PostgreSQL: PostgreSQL 16.1...
✅ Usuário 'backup_user' criado com sucesso

📋 Concedendo permissões de 'backup' em 15 databases...
   ✓ app_workforce (3 schemas)
   ✓ botpress_db (1 schemas)
   ✓ evolution_api_db (1 schemas)
   ... (mais databases)

✅ Permissões concedidas com sucesso!
✅ PROCESSO CONCLUÍDO COM SUCESSO!
```

## 📝 Modo CLI (Não-Interativo)

### Exemplo 1: MySQL - Usuário Global de Backup

```bash
python scripts/setup_database_user_permissions.py \
  --db-type mysql \
  --host wfdb02.vya.digital \
  --admin-user root \
  --admin-password "senha_admin" \
  --username backup_user \
  --password "senha_backup" \
  --type backup \
  --show-grants
```

### Exemplo 2: PostgreSQL - Usuário Read-Only Global

```bash
python scripts/setup_database_user_permissions.py \
  --db-type postgresql \
  --host localhost \
  --admin-user postgres \
  --admin-password "senha_admin" \
  --username reports_viewer \
  --password "senha_viewer" \
  --type read \
  --show-grants
```

### Exemplo 3: MySQL - Usuário de Aplicação (Database Específica)

```bash
python scripts/setup_database_user_permissions.py \
  --db-type mysql \
  --host localhost \
  --admin-user root \
  --admin-password "senha_admin" \
  --username app_user \
  --password "senha_app" \
  --type write \
  --database myapp_db \
  --host-pattern "10.0.%.%"
```

### Exemplo 4: PostgreSQL - Usuário de Migração

```bash
python scripts/setup_database_user_permissions.py \
  --db-type postgresql \
  --host wfdb02.vya.digital \
  --admin-user postgres \
  --admin-password "senha_admin" \
  --username migration_user \
  --password "senha_migration" \
  --type migration \
  --database app_db
```

### Listar Databases Disponíveis

```bash
# MySQL
python scripts/setup_database_user_permissions.py \
  --db-type mysql \
  --host localhost \
  --admin-user root \
  --admin-password "senha" \
  --list-databases

# PostgreSQL
python scripts/setup_database_user_permissions.py \
  --db-type postgresql \
  --host localhost \
  --admin-user postgres \
  --admin-password "senha" \
  --list-databases
```

## 📝 Parâmetros CLI

| Parâmetro | Descrição | Valores | Obrigatório |
|-----------|-----------|---------|-------------|
| `--db-type` | Tipo de banco | mysql, mariadb, postgresql, postgres | Sim* |
| `--host` | Host do servidor | hostname ou IP | Sim* |
| `--port` | Porta do servidor | número | Não** |
| `--admin-user` | Usuário administrativo | nome | Sim* |
| `--admin-password` | Senha do admin | senha | Sim* |
| `--username` | Nome do novo usuário | nome | Sim* |
| `--password` | Senha do novo usuário | senha | Sim* |
| `--host-pattern` | Padrão de host (MySQL) | %, localhost, etc | Não (% padrão) |
| `--type` | Tipo de usuário | write, read, backup, migration | Sim* |
| `--database` | Database específica | nome | Não (global) |
| `--show-grants` | Mostrar privilégios | flag | Não |
| `--list-databases` | Listar databases | flag | Não |

\* Obrigatório no modo CLI. No modo interativo, o script solicita estas informações.
\** Usa porta padrão se não especificado (3306 para MySQL, 5432 para PostgreSQL)

## 🔐 Comparação de Permissões por Tipo

### MySQL/MariaDB

| Operação | read | write | backup | migration |
|----------|------|-------|--------|-----------|
| SELECT | ✅ | ✅ | ✅ | ✅ |
| INSERT | ❌ | ✅ | ❌ | ✅ |
| UPDATE | ❌ | ✅ | ❌ | ✅ |
| DELETE | ❌ | ✅ | ❌ | ✅ |
| CREATE TABLE | ❌ | ❌ | ❌ | ✅ |
| DROP TABLE | ❌ | ❌ | ❌ | ✅ |
| LOCK TABLES | ❌ | ❌ | ✅ | ✅ |
| REPLICATION | ❌ | ❌ | ✅ | ✅ |

### PostgreSQL

| Operação | read | write | backup | migration |
|----------|------|-------|--------|-----------|
| CONNECT | ✅ | ✅ | ✅ | ✅ |
| SELECT | ✅ | ✅ | ✅ | ✅ |
| INSERT | ❌ | ✅ | ❌ | ✅ |
| UPDATE | ❌ | ✅ | ❌ | ✅ |
| DELETE | ❌ | ✅ | ❌ | ✅ |
| CREATE TABLE | ❌ | ❌ | ❌ | ✅ |
| ALTER TABLE | ❌ | ❌ | ❌ | ✅ |
| DROP TABLE | ❌ | ❌ | ❌ | ✅ |

## 🔍 Padrões de Host (MySQL)

O parâmetro `--host-pattern` é **específico do MySQL** e define de onde o usuário pode se conectar:

| Padrão | Descrição |
|--------|-----------|
| `%` | Qualquer host (padrão) |
| `localhost` | Apenas conexões locais |
| `192.168.1.%` | Subnet específica |
| `%.example.com` | Domínio específico |
| `10.0.%.%` | Range de IPs |

**Nota**: PostgreSQL gerencia isso via `pg_hba.conf`, não no usuário.

## 🔍 Verificação Manual

### MySQL

```sql
-- Verificar se usuário existe
SELECT User, Host FROM mysql.user WHERE User = 'backup_user';

-- Ver privilégios
SHOW GRANTS FOR 'backup_user'@'%';

-- Ver conexões ativas
SELECT user, host, db FROM information_schema.processlist
WHERE user = 'backup_user';
```

### PostgreSQL

```sql
-- Verificar se usuário existe
SELECT * FROM pg_roles WHERE rolname = 'backup_user';

-- Ver permissões em database
SELECT has_database_privilege('backup_user', 'app_workforce', 'CONNECT');

-- Ver permissões em schema
SELECT has_schema_privilege('backup_user', 'public', 'USAGE');

-- Ver conexões ativas
SELECT usename, datname, client_addr, state
FROM pg_stat_activity
WHERE usename = 'backup_user';
```

## 💡 Casos de Uso Comuns

### Caso 1: Usuário de Backup para Ambos os Bancos

```bash
# MySQL
python scripts/setup_database_user_permissions.py \
  --db-type mysql \
  --host wfdb02.vya.digital \
  --admin-user root \
  --admin-password "$MYSQL_ROOT_PASS" \
  --username backup \
  --password "$BACKUP_PASS" \
  --type backup

# PostgreSQL
python scripts/setup_database_user_permissions.py \
  --db-type postgresql \
  --host wfdb02.vya.digital \
  --admin-user postgres \
  --admin-password "$PG_ADMIN_PASS" \
  --username backup \
  --password "$BACKUP_PASS" \
  --type backup
```

### Caso 2: Usuário Read-Only para Metabase

```bash
# PostgreSQL - Leitura em todas as databases
python scripts/setup_database_user_permissions.py \
  --db-type postgresql \
  --host localhost \
  --admin-user postgres \
  --admin-password "senha" \
  --username metabase_reader \
  --password "senha_metabase" \
  --type read
```

### Caso 3: Usuário de Aplicação Web

```bash
# MySQL - Write em database específica
python scripts/setup_database_user_permissions.py \
  --db-type mysql \
  --host localhost \
  --admin-user root \
  --admin-password "senha" \
  --username webapp_user \
  --password "senha_webapp" \
  --type write \
  --database webapp_db \
  --host-pattern "10.0.1.%"
```

## 🔄 Integração com Scripts Existentes

### Usando como Módulo Python

```python
from scripts.setup_database_user_permissions import create_manager

# MySQL
mysql_manager = create_manager(
    db_type="mysql",
    host="localhost",
    port=3306,
    admin_user="root",
    admin_password="senha_admin"
)

if mysql_manager.connect():
    mysql_manager.create_user("app_user", "senha_app", "%")
    mysql_manager.grant_privileges("app_user", "write", "app_db")
    mysql_manager.close()

# PostgreSQL
pg_manager = create_manager(
    db_type="postgresql",
    host="localhost",
    port=5432,
    admin_user="postgres",
    admin_password="senha_admin"
)

if pg_manager.connect():
    pg_manager.create_user("backup", "senha_backup")
    pg_manager.grant_privileges("backup", "backup")
    pg_manager.close()
```

### Pipeline Completo de Migração

```bash
#!/bin/bash
# setup_migration_users.sh

# 1. Criar usuário backup no MySQL origem
python scripts/setup_database_user_permissions.py \
  --db-type mysql \
  --host wf004.vya.digital \
  --admin-user root \
  --admin-password "$MYSQL_ROOT_PASS" \
  --username backup \
  --password "$BACKUP_PASS" \
  --type backup

# 2. Criar usuário backup no PostgreSQL destino
python scripts/setup_database_user_permissions.py \
  --db-type postgresql \
  --host wfdb02.vya.digital \
  --admin-user postgres \
  --admin-password "$PG_ADMIN_PASS" \
  --username backup \
  --password "$BACKUP_PASS" \
  --type backup

# 3. Criar usuário de migração no destino
python scripts/setup_database_user_permissions.py \
  --db-type postgresql \
  --host wfdb02.vya.digital \
  --admin-user postgres \
  --admin-password "$PG_ADMIN_PASS" \
  --username migration_user \
  --password "$MIGRATION_PASS" \
  --type migration

echo "✅ Todos os usuários configurados!"
```

## ⚠️ Notas Importantes

### MySQL/MariaDB

1. **Host Pattern**: Use `%` apenas em ambientes de desenvolvimento. Em produção, restrinja a IPs específicos.
2. **FLUSH PRIVILEGES**: O script executa automaticamente após cada GRANT.
3. **Usuário Admin**: Necessita privilégios `CREATE USER` e `GRANT OPTION`.

### PostgreSQL

1. **Schemas**: O script concede permissões em todos os schemas exceto os do sistema.
2. **Default Privileges**: Configura permissões para objetos futuros automaticamente.
3. **pg_hba.conf**: Configure separadamente para controlar acesso por IP/rede.
4. **Conexões por Database**: Conecta em cada database para aplicar permissões.

### Ambos

1. **Senhas Seguras**: Use senhas fortes para usuários de produção.
2. **Princípio do Menor Privilégio**: Use o tipo de usuário apropriado.
3. **Rotação de Senhas**: Altere senhas periodicamente.
4. **Auditoria**: Monitore conexões e acessos.

## 🐛 Troubleshooting

### Erro: "Access denied" (MySQL)

```sql
-- Verificar privilégios do admin
SHOW GRANTS FOR 'root'@'%';

-- Conceder privilégios necessários
GRANT CREATE USER, GRANT OPTION ON *.* TO 'root'@'%';
FLUSH PRIVILEGES;
```

### Erro: "permission denied" (PostgreSQL)

```sql
-- Verificar se admin é superuser
SELECT rolname, rolsuper FROM pg_roles WHERE rolname = 'postgres';

-- Conceder superuser se necessário
ALTER USER postgres WITH SUPERUSER;
```

### Erro: "Can't connect to server"

**Soluções**:
1. Verificar se o servidor está rodando
2. Testar conexão manualmente
3. Verificar firewall e portas
4. Conferir pg_hba.conf (PostgreSQL) ou bind-address (MySQL)

### Erro: "Unknown database"

```sql
-- Criar database se não existe
-- MySQL
CREATE DATABASE myapp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- PostgreSQL
CREATE DATABASE myapp_db WITH ENCODING 'UTF8';
```

## 📊 Diferenças entre MySQL e PostgreSQL

| Recurso | MySQL | PostgreSQL |
|---------|-------|------------|
| Host Pattern | ✅ Sim (`user@host`) | ❌ Não (usa pg_hba.conf) |
| Schemas | ❌ Não (equivalente a databases) | ✅ Sim (múltiplos por database) |
| Default Privileges | ❌ Não | ✅ Sim |
| GRANT Syntax | `GRANT ... ON db.* TO 'user'@'host'` | `GRANT ... ON ... TO user` |
| Roles | Limitado | Completo (herança) |

## 🔐 Segurança

### Boas Práticas

1. **Variáveis de Ambiente**: Não armazene senhas em scripts
2. **Conexões SSL**: Configure TLS/SSL para conexões
3. **Auditoria**: Habilite logging de conexões
4. **Backup de Usuários**: Documente usuários criados
5. **Revisão Periódica**: Remova usuários não utilizados

### Exemplo com Variáveis de Ambiente

```bash
# Definir variáveis
export DB_TYPE="postgresql"
export DB_HOST="wfdb02.vya.digital"
export ADMIN_USER="postgres"
export ADMIN_PASS="senha_segura"
export NEW_USER="backup"
export NEW_PASS="senha_backup_segura"

# Executar script
python scripts/setup_database_user_permissions.py \
  --db-type "$DB_TYPE" \
  --host "$DB_HOST" \
  --admin-user "$ADMIN_USER" \
  --admin-password "$ADMIN_PASS" \
  --username "$NEW_USER" \
  --password "$NEW_PASS" \
  --type backup
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verificar os logs de erro do banco
2. Consultar a seção de Troubleshooting acima
3. Executar verificação manual com as queries SQL fornecidas
4. Usar `--show-grants` para visualizar permissões aplicadas

---

**Versão:** 2.0.0 (Universal)
**Data:** 27/01/2026
**Python:** 3.11+
**Dependências**: SQLAlchemy 2.x, PyMySQL, psycopg2-binary
**Compatibilidade**:
- MySQL 5.7+, MariaDB 10.3+
- PostgreSQL 12+
