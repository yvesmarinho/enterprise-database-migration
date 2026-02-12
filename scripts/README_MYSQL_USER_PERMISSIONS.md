# Setup de Usuários MySQL/MariaDB

Script Python 3.11 para criar e configurar usuários MySQL/MariaDB com permissões específicas usando SQLAlchemy.

## 📋 Descrição

Este script automatiza a criação de usuários MySQL/MariaDB com diferentes níveis de permissão:

- ✅ **Modo Interativo**: Solicita todas as informações necessárias
- ✅ **Modo CLI**: Aceita parâmetros via linha de comando
- ✅ **Tipos de Usuário**: write, read, backup, migration
- ✅ **Escopo Global ou Específico**: Permissões em todas as databases ou apenas uma
- ✅ **SQLAlchemy**: Código reutilizável e compatível com o projeto
- ✅ **Validação**: Verifica usuário existente antes de criar
- ✅ **Visualização**: Mostra os grants concedidos

## 🎯 Tipos de Usuário

### 1. **read** (Somente Leitura)
Permissões: `SELECT`, `SHOW VIEW`

Ideal para:
- Relatórios e dashboards
- Usuários de análise
- Ferramentas de BI

### 2. **write** (Leitura e Escrita)
Permissões: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `EXECUTE`, `SHOW VIEW`

Ideal para:
- Aplicações web
- APIs
- Sistemas CRUD

### 3. **backup** (Backup e Replicação)
Permissões: `SELECT`, `SHOW VIEW`, `LOCK TABLES`, `RELOAD`, `REPLICATION CLIENT`

Ideal para:
- Sistemas de backup
- Ferramentas de sincronização
- Replicação de dados

### 4. **migration** (Administração Completa)
Permissões: `ALL PRIVILEGES`

Ideal para:
- Migrações de schema
- Administração de database
- Deployment de aplicações

## 🚀 Como Usar

### Pré-requisitos

```bash
# Instalar dependências
pip install sqlalchemy pymysql

# Ou usando requirements.txt do projeto
pip install -r requirements.txt
```

### Modo Interativo (Recomendado)

```bash
python scripts/setup_mysql_user_permissions.py
```

O script solicitará:
1. **Servidor**: Host, porta, usuário admin e senha
2. **Novo Usuário**: Nome, senha e padrão de host
3. **Tipo**: read, write, backup ou migration
4. **Database**: Nome específico ou vazio para global

**Exemplo de execução:**

```
══════════════════════════════════════════════════════════════════════
GERENCIADOR DE USUÁRIOS MYSQL/MARIADB
══════════════════════════════════════════════════════════════════════

📡 CONEXÃO COM O SERVIDOR
──────────────────────────────────────────────────────────────────────
Host do servidor MySQL [localhost]: wfdb02.vya.digital
Porta [3306]: 3306
Usuário administrativo [root]: migration_user
Senha do usuário administrativo: ********

👤 NOVO USUÁRIO
──────────────────────────────────────────────────────────────────────
Nome do novo usuário: backup_user
Senha do novo usuário: ********
Confirme a senha: ********
Padrão de host [% (qualquer host)]: %

🔐 TIPO DE USUÁRIO E PERMISSÕES
──────────────────────────────────────────────────────────────────────
Tipos disponíveis:
  • write        - Permissões de leitura e escrita (sem DDL)
    SELECT, INSERT, UPDATE, DELETE, EXECUTE, SHOW VIEW
  • read         - Apenas permissões de leitura
    SELECT, SHOW VIEW
  • backup       - Permissões otimizadas para backup
    SELECT, SHOW VIEW, LOCK TABLES, RELOAD, REPLICATION CLIENT
  • migration    - Permissões completas incluindo DDL
    ALL PRIVILEGES

Tipo de usuário [read]: backup

💾 BASE DE DADOS
──────────────────────────────────────────────────────────────────────
Nome da database (deixe vazio para global):

✅ Conectado ao MySQL/MariaDB: 8.0.35
✅ Usuário 'backup_user'@'%' criado com sucesso
✅ Permissões concedidas com sucesso para 'backup_user'@'%'

📜 Privilégios de 'backup_user'@'%':
──────────────────────────────────────────────────────────────────────
  GRANT SELECT, RELOAD, LOCK TABLES, REPLICATION CLIENT ON *.* TO `backup_user`@`%`
──────────────────────────────────────────────────────────────────────

✅ PROCESSO CONCLUÍDO COM SUCESSO!
```

### Modo CLI (Não-Interativo)

#### Exemplo 1: Usuário Global de Backup

```bash
python scripts/setup_mysql_user_permissions.py \
  --host wfdb02.vya.digital \
  --admin-user root \
  --admin-password "senha_admin" \
  --username backup_user \
  --password "senha_backup" \
  --type backup \
  --show-grants
```

#### Exemplo 2: Usuário Read-Only para Database Específica

```bash
python scripts/setup_mysql_user_permissions.py \
  --host localhost \
  --admin-user root \
  --admin-password "senha_admin" \
  --username reports_viewer \
  --password "senha_viewer" \
  --type read \
  --database perfexcrm_db \
  --show-grants
```

#### Exemplo 3: Usuário de Aplicação (Write)

```bash
python scripts/setup_mysql_user_permissions.py \
  --host wfdb02.vya.digital \
  --admin-user migration_user \
  --admin-password "senha_migration" \
  --username app_user \
  --password "senha_app" \
  --type write \
  --database myapp_db \
  --host-pattern "10.0.%.%"
```

#### Exemplo 4: Usuário de Migração

```bash
python scripts/setup_mysql_user_permissions.py \
  --host localhost \
  --admin-user root \
  --admin-password "senha_admin" \
  --username migration_user \
  --password "senha_migration" \
  --type migration
```

### Listar Databases Disponíveis

```bash
python scripts/setup_mysql_user_permissions.py \
  --host localhost \
  --admin-user root \
  --admin-password "senha_admin" \
  --list-databases
```

## 📝 Parâmetros CLI

| Parâmetro | Descrição | Padrão | Obrigatório |
|-----------|-----------|--------|-------------|
| `--host` | Host do servidor MySQL | - | Sim* |
| `--port` | Porta do servidor | 3306 | Não |
| `--admin-user` | Usuário administrativo | - | Sim* |
| `--admin-password` | Senha do admin | - | Sim* |
| `--username` | Nome do novo usuário | - | Sim* |
| `--password` | Senha do novo usuário | - | Sim* |
| `--host-pattern` | Padrão de host | % | Não |
| `--type` | Tipo de usuário | - | Sim* |
| `--database` | Database específica | global | Não |
| `--show-grants` | Mostrar privilégios | false | Não |
| `--list-databases` | Listar databases | false | Não |

\* Obrigatório no modo CLI. No modo interativo, o script solicita estas informações.

## 🔍 Padrões de Host

O parâmetro `--host-pattern` define de onde o usuário pode se conectar:

| Padrão | Descrição |
|--------|-----------|
| `%` | Qualquer host (padrão) |
| `localhost` | Apenas conexões locais |
| `192.168.1.%` | Subnet específica |
| `%.example.com` | Domínio específico |
| `10.0.%.%` | Range de IPs |

## 🔐 Comparação de Permissões

| Operação | read | write | backup | migration |
|----------|------|-------|--------|-----------|
| SELECT | ✅ | ✅ | ✅ | ✅ |
| INSERT | ❌ | ✅ | ❌ | ✅ |
| UPDATE | ❌ | ✅ | ❌ | ✅ |
| DELETE | ❌ | ✅ | ❌ | ✅ |
| CREATE TABLE | ❌ | ❌ | ❌ | ✅ |
| DROP TABLE | ❌ | ❌ | ❌ | ✅ |
| ALTER TABLE | ❌ | ❌ | ❌ | ✅ |
| EXECUTE | ❌ | ✅ | ❌ | ✅ |
| LOCK TABLES | ❌ | ❌ | ✅ | ✅ |
| REPLICATION | ❌ | ❌ | ✅ | ✅ |

## 🔍 Verificação Manual

### Verificar se usuário existe

```sql
SELECT User, Host FROM mysql.user WHERE User = 'backup_user';
```

### Verificar privilégios

```sql
SHOW GRANTS FOR 'backup_user'@'%';
```

### Verificar conexões ativas

```sql
SELECT user, host, db, command, time, state
FROM information_schema.processlist
WHERE user = 'backup_user';
```

### Listar todas as databases

```sql
SHOW DATABASES;
```

## ⚠️ Notas Importantes

1. **Usuário Administrativo**: O script usa um usuário com privilégios suficientes para criar usuários e conceder permissões (geralmente `root` ou um usuário com `GRANT OPTION`).

2. **Senhas Seguras**: Use senhas fortes para usuários de produção. O script não valida força de senha.

3. **Host Pattern**: O padrão `%` permite conexão de qualquer host. Em produção, restrinja a hosts específicos.

4. **Usuário Global vs Específico**:
   - **Global** (`*.*`): Permissões em todas as databases
   - **Específico** (`` `database`.* ``): Apenas uma database

5. **Recreação de Usuário**: Se o usuário já existe, o script pergunta se deseja recriar (modo interativo) ou mantém o existente.

## 🐛 Troubleshooting

### Erro: "Access denied"

**Causa**: Usuário administrativo sem privilégios suficientes.

**Solução**:
```sql
-- Verificar privilégios do admin
SHOW GRANTS FOR 'admin_user'@'%';

-- Conceder privilégios necessários
GRANT CREATE USER, GRANT OPTION ON *.* TO 'admin_user'@'%';
FLUSH PRIVILEGES;
```

### Erro: "User already exists"

**Causa**: Usuário já existe no sistema.

**Solução**:
- Modo interativo: Responda 's' para recriar
- Modo CLI: Remova manualmente antes:
```sql
DROP USER 'username'@'%';
```

### Erro: "Unknown database"

**Causa**: Database especificada não existe.

**Solução**:
```sql
-- Criar a database primeiro
CREATE DATABASE myapp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Erro: "Can't connect to MySQL server"

**Causa**: Problema de conectividade ou firewall.

**Solução**:
1. Verificar se o servidor está rodando: `systemctl status mysql`
2. Testar conexão: `mysql -h host -u user -p`
3. Verificar firewall: `sudo ufw status`

## 💡 Casos de Uso Comuns

### Caso 1: Usuário para Sistema de Backup

```bash
python scripts/setup_mysql_user_permissions.py \
  --host wfdb02.vya.digital \
  --admin-user root \
  --admin-password "senha" \
  --username backup \
  --password "senha_backup" \
  --type backup
```

### Caso 2: Usuário Read-Only para Metabase

```bash
python scripts/setup_mysql_user_permissions.py \
  --host localhost \
  --admin-user root \
  --admin-password "senha" \
  --username metabase_viewer \
  --password "senha_metabase" \
  --type read \
  --database analytics_db
```

### Caso 3: Usuário de Aplicação Web

```bash
python scripts/setup_mysql_user_permissions.py \
  --host localhost \
  --admin-user root \
  --admin-password "senha" \
  --username webapp_user \
  --password "senha_webapp" \
  --type write \
  --database webapp_db \
  --host-pattern "10.0.1.%"
```

### Caso 4: Usuário para Migrações

```bash
python scripts/setup_mysql_user_permissions.py \
  --host localhost \
  --admin-user root \
  --admin-password "senha" \
  --username flyway_user \
  --password "senha_flyway" \
  --type migration \
  --database app_db
```

## 🔄 Integração com Scripts Existentes

### Usando como Módulo Python

```python
from scripts.setup_mysql_user_permissions import MySQLUserManager

# Criar gerenciador
manager = MySQLUserManager(
    host="localhost",
    port=3306,
    admin_user="root",
    admin_password="senha_admin"
)

# Conectar
if manager.connect():
    # Criar usuário
    manager.create_user(
        username="app_user",
        password="senha_app",
        host_pattern="%"
    )

    # Conceder privilégios
    manager.grant_privileges(
        username="app_user",
        user_type="write",
        database="app_db"
    )

    # Mostrar grants
    manager.show_user_grants("app_user")

    # Fechar
    manager.close()
```

### Pipeline de Migração

```bash
#!/bin/bash
# Script de migração completo

# 1. Criar usuários
python scripts/setup_mysql_user_permissions.py \
  --host wfdb02.vya.digital \
  --admin-user root \
  --admin-password "$ADMIN_PASS" \
  --username backup \
  --password "$BACKUP_PASS" \
  --type backup

# 2. Migrar dados
python scripts/migrate_perfexcrm_mysql.sh

# 3. Validar
python scripts/validate_migration.py
```

## 📊 Comparação com PostgreSQL

| Recurso | MySQL (Este Script) | PostgreSQL (Projeto) |
|---------|---------------------|----------------------|
| Criação de Usuário | ✅ | ✅ |
| Tipos de Permissão | 4 tipos | Configurável |
| Escopo Global | ✅ | ✅ |
| Escopo por Database | ✅ | ✅ |
| Escopo por Schema | ❌ (MySQL não tem) | ✅ |
| Permissões Futuras | ❌ (MySQL não tem) | ✅ |
| SQLAlchemy | ✅ | ✅ |
| Modo Interativo | ✅ | ❌ |
| Modo CLI | ✅ | ✅ |

## 🔐 Segurança

### Boas Práticas

1. **Não armazene senhas em arquivos**: Use variáveis de ambiente ou secret managers
2. **Restrinja host patterns**: Evite `%` em produção
3. **Princípio do menor privilégio**: Use o tipo de usuário apropriado
4. **Rotação de senhas**: Altere senhas periodicamente
5. **Auditoria**: Monitore conexões e acessos

### Exemplo com Variáveis de Ambiente

```bash
export MYSQL_ADMIN_PASS="senha_admin"
export MYSQL_NEW_USER_PASS="senha_nova"

python scripts/setup_mysql_user_permissions.py \
  --host localhost \
  --admin-user root \
  --admin-password "$MYSQL_ADMIN_PASS" \
  --username app_user \
  --password "$MYSQL_NEW_USER_PASS" \
  --type write \
  --database app_db
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verificar os logs de erro do MySQL: `/var/log/mysql/error.log`
2. Consultar a seção de Troubleshooting acima
3. Executar verificação manual com as queries SQL fornecidas
4. Usar `--show-grants` para visualizar permissões aplicadas

---

**Versão:** 1.0.0
**Data:** 27/01/2026
**Python:** 3.11+
**Dependências:** SQLAlchemy 2.x, PyMySQL
**Compatibilidade:** MySQL 5.7+, MariaDB 10.3+
