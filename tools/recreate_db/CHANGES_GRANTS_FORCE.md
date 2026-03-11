# Correções Implementadas no Database Recreator

> ⚠️ **ATENÇÃO:** Este arquivo documenta a implementação INICIAL de coleta de grants.
>
> **VERSÃO ATUALIZADA:** A coleta de grants foi EXPANDIDA em 2026-03-11.
> **Consulte:** `GRANTS_COLLECTION_FIX.md` para a implementação completa e atualizada.
>
> ### Principais melhorias na versão atual:
> - ✅ PostgreSQL: Agora coleta grants de schemas, tabelas e views
> - ✅ MySQL: Agora coleta grants de tabelas e colunas
> - ✅ Estrutura expandida com contador `total_grants`
> - ✅ Conexão temporária ao banco específico (PostgreSQL)

## ✅ Mudanças Realizadas (Versão Inicial)

### 1. Coleta de Grants (Permissões)

#### MySQL - `_collect_mysql_grants()`
Coleta permissões usando `information_schema.SCHEMA_PRIVILEGES`:
```python
def _collect_mysql_grants(self, cursor) -> list:
    """Coleta grants/permissões do MySQL para o banco de dados"""
    cursor.execute("""
        SELECT
            GRANTEE,
            PRIVILEGE_TYPE,
            IS_GRANTABLE
        FROM information_schema.SCHEMA_PRIVILEGES
        WHERE TABLE_SCHEMA = %s
        ORDER BY GRANTEE, PRIVILEGE_TYPE
    """, (self.database_name,))
    grants = cursor.fetchall()
    return [dict(g) for g in grants] if grants else []
```

**Informações coletadas:**
- `GRANTEE` - Usuário/Role que tem a permissão
- `PRIVILEGE_TYPE` - Tipo de permissão (SELECT, INSERT, UPDATE, etc.)
- `IS_GRANTABLE` - Se pode repassar a permissão

#### PostgreSQL - `_collect_postgresql_grants()`
Coleta permissões usando `pg_database` e ACLs:
```python
def _collect_postgresql_grants(self, cursor) -> dict:
    """Coleta grants/permissões do PostgreSQL para o banco de dados"""
    cursor.execute("""
        SELECT
            datname,
            datacl,
            pg_catalog.pg_get_userbyid(datdba) as owner
        FROM pg_database
        WHERE datname = %s
    """, (self.database_name,))
    db_acl = cursor.fetchone()

    return {
        'database': db_acl['datname'],
        'owner': db_acl['owner'],
        'acl': db_acl['datacl'],
        'acl_list': db_acl['datacl'] if db_acl['datacl'] else []
    }
```

**Informações coletadas:**
- `database` - Nome do banco
- `owner` - Dono do banco
- `acl` - Lista de ACLs (Access Control List)
- `acl_list` - ACLs em array

### 2. Force por Padrão (Sempre Termina Conexões)

#### Mudança no `drop_database()`
```python
def drop_database(self, force: bool = True) -> bool:  # ← PADRÃO AGORA É True
    """
    Apaga o banco de dados

    Args:
        force: Se True, força a exclusão terminando conexões ativas (padrão: True)
    """
```

**MySQL - Termina conexões:**
```python
if force:
    cursor.execute(f"""
        SELECT CONCAT('KILL ', id, ';') as kill_cmd
        FROM information_schema.PROCESSLIST
        WHERE DB = '{self.database_name}' AND id != CONNECTION_ID()
    """)
    kill_commands = cursor.fetchall()
    for cmd in kill_commands:
        cursor.execute(cmd['kill_cmd'])
    logger.info(f"Terminadas {len(kill_commands)} conexões MySQL ativas")
```

**PostgreSQL - SEMPRE termina conexões:**
```python
cursor.execute(f"""
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = '{self.database_name}'
    AND pid <> pg_backend_pid()
""")
logger.info("Conexões ativas PostgreSQL terminadas (force)")
```

#### Mudança no `execute_full_recreation()`
```python
def execute_full_recreation(self, force: bool = True, save_report: bool = True):
    # ↑ PADRÃO MUDOU DE False PARA True
```

### 3. Novo Argumento CLI: `--no-force`

**ANTES:**
```bash
--force  # Para ATIVAR force
```

**AGORA:**
```bash
--no-force  # Para DESATIVAR force (padrão é ATIVO)
```

**Código CLI:**
```python
parser.add_argument(
    '--no-force',
    action='store_true',
    help='NÃO força a exclusão de conexões ativas (padrão é sempre forçar)'
)

# Uso
result = recreator.execute_full_recreation(
    force=not args.no_force,  # Padrão é True
    save_report=not args.no_report
)
```

### 4. Metadados Ampliados

**ANTES:**
```json
{
  "database_name": "perfexcrm_db",
  "charset": "utf8mb4",
  "collation": "utf8mb4_unicode_ci",
  "table_count": 42
}
```

**AGORA:**
```json
{
  "database_name": "perfexcrm_db",
  "charset": "utf8mb4",
  "collation": "utf8mb4_unicode_ci",
  "table_count": 42,
  "grants": [
    {
      "GRANTEE": "'perfexcrm_user'@'%'",
      "PRIVILEGE_TYPE": "SELECT",
      "IS_GRANTABLE": "NO"
    },
    {
      "GRANTEE": "'perfexcrm_user'@'%'",
      "PRIVILEGE_TYPE": "INSERT",
      "IS_GRANTABLE": "NO"
    }
  ]
}
```

---

## 🎯 Uso Atualizado

### Comportamento Padrão (Force = True)
```bash
# SEMPRE termina conexões ativas
python3 recreate_database.py \
  --config ../../secrets/wfdb02_postgres.json \
  --database chatwoot_dev_db
```

### Desabilitar Force (se necessário)
```bash
# NÃO termina conexões (pode falhar se banco estiver em uso)
python3 recreate_database.py \
  --config ../../secrets/wfdb02_postgres.json \
  --database chatwoot_dev_db \
  --no-force
```

### Modo Programático
```python
from recreate_database import DatabaseRecreator

recreator = DatabaseRecreator('config.json', 'database_name')

# Padrão: force=True (recomendado)
result = recreator.execute_full_recreation()

# Sem força (não recomendado)
result = recreator.execute_full_recreation(force=False)
```

---

## 📊 Relatórios Gerados

Agora incluem grants/permissões:

```json
{
  "operation": "database_recreation",
  "database": "chatwoot_dev_db",
  "type": "postgresql",
  "metadata_before": {
    "database_name": "chatwoot_dev_db",
    "exists": true,
    "encoding": "UTF8",
    "collate": "pt_BR.UTF-8",
    "ctype": "pt_BR.UTF-8",
    "size": "150 MB",
    "table_count": 78,
    "grants": {
      "database": "chatwoot_dev_db",
      "owner": "chatwoot_user",
      "acl": "{chatwoot_user=CTc/chatwoot_user,readonly=r/chatwoot_user}",
      "acl_list": [...]
    },
    "timestamp": "2026-03-05T10:30:00"
  },
  "config_file": "secrets/wfdb02_postgres.json",
  "timestamp": "20260305_103000"
}
```

---

## ⚠️ Benefícios das Mudanças

### 1. Evita Erros de Permissão
- ✅ Grants são coletados antes de apagar
- ✅ Permite recriar permissões depois (manual ou automático)
- ✅ Auditoria completa de quem tinha acesso

### 2. Sempre Funciona (Force por Padrão)
- ✅ Não falha por "database is being accessed by other users"
- ✅ Termina conexões automaticamente
- ✅ Operação confiável e previsível
- ✅ Menos intervenção manual necessária

### 3. Segurança
- ✅ Confirmação continua obrigatória (digite 'SIM')
- ✅ Logs mostram quantas conexões foram terminadas
- ✅ Relatório completo salvo antes de qualquer ação
- ✅ Opção --no-force disponível se precisar

---

## 🧪 Validação

Execute os testes:
```bash
cd tools/recreate_db
python3 test_recreator.py
```

**Testes adicionados:**
- ✅ Método `_collect_mysql_grants()` existe
- ✅ Método `_collect_postgresql_grants()` existe
- ✅ `drop_database(force=True)` por padrão
- ✅ `execute_full_recreation(force=True)` por padrão

---

## 📋 Checklist de Funcionalidades

- [x] Coleta grants MySQL
- [x] Coleta grants PostgreSQL
- [x] Termina conexões MySQL quando force=True
- [x] Termina conexões PostgreSQL quando force=True
- [x] Force=True por padrão no drop_database
- [x] Force=True por padrão no execute_full_recreation
- [x] Argumento CLI --no-force (inverso do --force)
- [x] Logs informativos sobre conexões terminadas
- [x] Grants salvos no relatório JSON
- [x] Documentação atualizada
- [x] Testes validando mudanças

---

**Status:** ✅ Todas as mudanças implementadas e testadas!
