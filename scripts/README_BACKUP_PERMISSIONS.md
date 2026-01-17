# Setup de Permissões do Usuário Backup

Scripts Python 3.11 para configurar permissões do usuário `backup` em todas as bases de dados PostgreSQL.

## 📋 Descrição

Estes scripts automatizam a configuração de permissões do usuário `backup` em todas as bases de dados do servidor PostgreSQL, garantindo que:

- O usuário `backup` tenha acesso de leitura a todas as bases de dados
- Permissões sejam concedidas em todos os schemas (exceto system schemas)
- Permissões futuras sejam configuradas automaticamente
- Nenhuma permissão existente seja alterada

## 🎯 Funcionalidades

### Script Principal: `setup_backup_user_permissions.py`

**Recursos:**
- ✅ Cria o usuário `backup` se não existir
- ✅ Coleta todas as bases de dados automaticamente
- ✅ Verifica permissões existentes
- ✅ Aplica apenas permissões faltantes
- ✅ Preserva permissões existentes
- ✅ Suporte a múltiplos schemas por database
- ✅ Configura permissões para objetos futuros
- ✅ Relatório detalhado com resumo
- ✅ Tratamento robusto de erros

**Permissões Concedidas:**
```sql
-- Database level
GRANT CONNECT ON DATABASE <database> TO backup;

-- Schema level (para cada schema não-sistema)
GRANT USAGE ON SCHEMA <schema> TO backup;

-- Objetos existentes
GRANT SELECT ON ALL TABLES IN SCHEMA <schema> TO backup;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA <schema> TO backup;

-- Objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA <schema>
    GRANT SELECT ON TABLES TO backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA <schema>
    GRANT SELECT ON SEQUENCES TO backup;
```

### Script Simplificado: `setup_backup_permissions_simple.py`

Versão mais simples e direta, com suporte a modo dry-run.

## 🚀 Como Usar

### Pré-requisitos

```bash
# Instalar dependências
pip install sqlalchemy psycopg2-binary

# Ou usando requirements.txt do projeto
pip install -r requirements.txt
```

### Execução

#### 1. Script Principal (Recomendado)

```bash
# Executar configuração completa
python scripts/setup_backup_user_permissions.py
```

**Saída esperada:**
```
======================================================================
CONFIGURAÇÃO DE PERMISSÕES DO USUÁRIO BACKUP
======================================================================
Servidor: wfdb02.vya.digital
Usuário: backup
======================================================================

✅ Conectado ao PostgreSQL: PostgreSQL 16...
✅ Usuário 'backup' existe
📊 Encontradas 15 bases de dados

======================================================================
PROCESSAMENTO DE PERMISSÕES DO USUÁRIO BACKUP
======================================================================

[1/15] Processando: app_workforce
----------------------------------------------------------------------
✅ Tem permissão CONNECT
✅ Tem USAGE em 3 schemas
✅ Permissões já estão corretas

[2/15] Processando: botpress_db
----------------------------------------------------------------------
⚠️  Falta permissão CONNECT
🔧 Aplicando permissões...
✅ Permissões concedidas em 'botpress_db' (2 schemas)

...

======================================================================
RESUMO DO PROCESSAMENTO
======================================================================

✅ Sucesso: 15/15

======================================================================

✅ Processo concluído com sucesso!
```

#### 2. Script Simplificado

```bash
# Modo dry-run (apenas verifica, não aplica)
python scripts/setup_backup_permissions_simple.py --dry-run

# Aplicar permissões
python scripts/setup_backup_permissions_simple.py

# Com arquivo de configuração customizado
python scripts/setup_backup_permissions_simple.py --config /path/to/config.json
```

## 📁 Configuração

Os scripts leem automaticamente o arquivo de configuração:
```
secrets/postgresql_destination_config.json
```

**Estrutura esperada:**
```json
{
  "server": {
    "host": "wfdb02.vya.digital",
    "port": 5432
  },
  "authentication": {
    "user": "migration_user",
    "password": "senha_admin"
  },
  "connection_settings": {
    "connection_timeout": 30
  }
}
```

## 🔍 Verificação Manual

Para verificar as permissões manualmente:

```sql
-- Verificar se usuário backup existe
SELECT * FROM pg_roles WHERE rolname = 'backup';

-- Verificar permissão CONNECT em uma database
SELECT has_database_privilege('backup', 'nome_database', 'CONNECT');

-- Verificar permissões em um schema
SELECT has_schema_privilege('backup', 'public', 'USAGE');

-- Listar todas as permissões do usuário backup
SELECT
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'backup'
ORDER BY table_schema, table_name;
```

## ⚠️ Notas Importantes

1. **Usuário Administrativo**: Os scripts usam o usuário `migration_user` configurado no arquivo JSON, que deve ter privilégios de SUPERUSER ou GRANT OPTION.

2. **Tablespaces**: O script considera que cada base de dados tem sua própria tablespace, conforme especificado.

3. **Schemas Sistema**: Os schemas `pg_catalog`, `information_schema` e `pg_toast` são automaticamente excluídos do processamento.

4. **Transações**: Cada database é processada em uma transação separada. Se houver erro em uma database, as outras não são afetadas.

5. **Permissões Existentes**: O script NÃO revoga ou altera permissões existentes, apenas adiciona as faltantes.

## 🐛 Troubleshooting

### Erro: "permission denied"

**Causa**: Usuário `migration_user` não tem privilégios suficientes.

**Solução**:
```sql
-- Conceder privilégios ao migration_user
ALTER USER migration_user WITH SUPERUSER;

-- Ou apenas o necessário:
GRANT CREATE ON DATABASE nome_database TO migration_user;
```

### Erro: "could not connect to server"

**Causa**: Problema de conectividade ou credenciais incorretas.

**Solução**:
1. Verificar se o servidor está acessível
2. Testar conexão manual: `psql -h wfdb02.vya.digital -U migration_user -d postgres`
3. Verificar firewall e regras de pg_hba.conf

### Erro: "role backup already exists"

**Causa**: Usuário já existe mas com configurações diferentes.

**Solução**: O script detecta automaticamente e não tenta recriar.

## 📊 Logs e Auditoria

Para auditar as mudanças:

```sql
-- Ver últimas mudanças de privilégios (se logging estiver habilitado)
SELECT * FROM pg_stat_activity
WHERE query LIKE '%GRANT%'
ORDER BY query_start DESC
LIMIT 20;
```

## 🔐 Segurança

- O usuário `backup` é criado com privilégios mínimos (LOGIN, sem SUPERUSER)
- Apenas permissões de leitura (SELECT) são concedidas
- Nenhum privilégio de escrita (INSERT, UPDATE, DELETE) é concedido
- O usuário não pode criar databases ou roles

## 📝 Exemplos de Uso

### Caso 1: Setup Inicial

```bash
# Primeira execução - verifica e configura tudo
python scripts/setup_backup_user_permissions.py
```

### Caso 2: Adicionar Permissões em Nova Database

```bash
# Após criar uma nova database, re-execute o script
# Ele detectará a nova database e configurará automaticamente
python scripts/setup_backup_user_permissions.py
```

### Caso 3: Verificação sem Mudanças

```bash
# Usar versão simplificada com dry-run
python scripts/setup_backup_permissions_simple.py --dry-run
```

## 🔄 Integração com Pipeline

Adicionar ao processo de migração:

```python
# No seu script de migração
from scripts.setup_backup_user_permissions import BackupUserPermissionManager

manager = BackupUserPermissionManager("secrets/postgresql_destination_config.json")
manager.run()
```

## 📞 Suporte

Para problemas ou dúvidas:
1. Verificar os logs no console
2. Consultar a seção de Troubleshooting acima
3. Executar verificação manual com as queries SQL fornecidas

---

**Versão:** 1.0.0
**Data:** 22/12/2025
**Python:** 3.11+
**Dependências:** SQLAlchemy 2.x, psycopg2-binary
