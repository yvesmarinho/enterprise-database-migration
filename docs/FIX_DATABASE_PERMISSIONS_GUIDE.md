# Fix Database Permissions - Guia Completo

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Estruturas de Dados](#estruturas-de-dados)
4. [Tipos de Permissão](#tipos-de-permissão)
5. [Fluxo de Execução](#fluxo-de-execução)
6. [Configuração via JSON](#configuração-via-json)
7. [Funções Principais](#funções-principais)
8. [Exemplos de Uso](#exemplos-de-uso)
9. [Troubleshooting](#troubleshooting)

---

## Visão Geral

**Script**: `validation/fix_database_permissions.py`
**Propósito**: Ferramenta automatizada para análise e correção de permissões de usuários em bancos de dados PostgreSQL 18.

### Funcionalidades Principais

- ✅ **Análise de Permissões**: Verifica permissões de usuários em todos os objetos do banco
- ✅ **Correção Automática**: Aplica permissões corretas baseadas no tipo de usuário
- ✅ **Suporte a 3 Tipos de Usuário**: Admin, User (CRUD), Readonly
- ✅ **Configuração via JSON**: Define banco e usuários em arquivo estruturado
- ✅ **Modo Interativo**: Prompt para entrada manual de configurações
- ✅ **Relatórios Detalhados**: Exporta análise em JSON para auditoria
- ✅ **Criação de Usuários**: Pode criar usuários automaticamente se não existirem

### Casos de Uso

1. **Auditoria de Segurança**: Verificar se usuários têm apenas as permissões necessárias
2. **Correção de Acesso**: Restaurar permissões após migração ou erro
3. **Provisionamento**: Configurar usuários novos com permissões corretas
4. **Compliance**: Garantir segregação de privilégios (admin/user/readonly)

---

## Arquitetura

### Componentes do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    fix_database_permissions.py               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │ Configuração │    │   Análise    │    │   Correção   │ │
│  ├──────────────┤    ├──────────────┤    ├──────────────┤ │
│  │ • JSON       │───▶│ • Conexão    │───▶│ • GRANT      │ │
│  │ • Interativo │    │ • Validação  │    │ • REVOKE     │ │
│  │ • Credenciais│    │ • Relatório  │    │ • CREATE USER│ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                     │                    │        │
│         └─────────────────────┴────────────────────┘        │
│                              │                               │
└──────────────────────────────┼───────────────────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │   PostgreSQL 18      │
                    │   wfdb02.vya.digital │
                    └──────────────────────┘
```

### Dependências

- **Python 3.10+**
- **SQLAlchemy**: ORM para conexão e queries
- **PostgreSQL 18**: Banco de dados alvo
- **secrets/postgresql_destination_config.json**: Credenciais de admin

---

## Estruturas de Dados

### 1. UserPermissions (Dataclass)

Armazena o estado completo das permissões de um usuário.

```python
@dataclass
class UserPermissions:
    username: str                      # Nome do usuário
    exists: bool                        # Se usuário existe no PostgreSQL
    can_login: bool                     # Se pode fazer login
    is_superuser: bool                  # Se é superusuário
    connect_privilege: bool             # Privilégio CONNECT no banco
    usage_on_schema: bool               # Privilégio USAGE no schema public
    tables_with_select: int             # Quantas tabelas com SELECT
    tables_with_insert: int             # Quantas tabelas com INSERT
    tables_with_update: int             # Quantas tabelas com UPDATE
    tables_with_delete: int             # Quantas tabelas com DELETE
    total_tables: int                   # Total de tabelas no banco
    missing_permissions: List[str]      # Lista de permissões faltando
```

**Exemplo de Uso:**
```python
perms = analyze_user_permissions(session, "metabase_user", "metabase_db", 159)
if perms.tables_with_select < perms.total_tables:
    print("Usuário não tem SELECT em todas as tabelas")
```

### 2. DatabaseInfo (Dataclass)

Informações sobre o banco de dados.

```python
@dataclass
class DatabaseInfo:
    name: str                # Nome do banco
    exists: bool             # Se banco existe
    owner: str               # Dono do banco
    encoding: str            # Encoding (UTF8, etc)
    tablespace: str          # Tablespace utilizado
    size: str                # Tamanho formatado (145 MB)
    total_tables: int        # Total de tabelas
    total_schemas: int       # Total de schemas
```

### 3. PermissionFix (Dataclass)

Registro de cada correção aplicada.

```python
@dataclass
class PermissionFix:
    username: str                      # Usuário afetado
    action: str                        # GRANT_SELECT, CREATE_USER, etc
    sql_command: str                   # SQL executado
    success: bool                      # Se operação foi bem-sucedida
    error_message: Optional[str]       # Mensagem de erro (se houver)
```

### 4. AnalysisReport (Dataclass)

Relatório completo da execução.

```python
@dataclass
class AnalysisReport:
    timestamp: str                              # ISO 8601 timestamp
    database_name: str                          # Nome do banco analisado
    database_info: Optional[DatabaseInfo]       # Detalhes do banco
    expected_users: List[str]                   # Usuários esperados
    user_permissions: Dict[str, UserPermissions]# Permissões por usuário
    fixes_applied: List[PermissionFix]          # Correções aplicadas
    summary: str                                # Resumo textual
```

**Exportação:**
```json
{
  "timestamp": "2026-01-16T16:30:30.142092",
  "database_name": "metabase_db",
  "expected_users": ["metabase_user", "metabase_viewer"],
  "fixes_applied": [],
  "summary": "Análise concluída. 0 correções aplicadas"
}
```

---

## Tipos de Permissão

O sistema suporta 3 tipos de usuário com diferentes níveis de acesso:

### 1. 🔴 ADMIN (Administrador)

**Permissões Concedidas:**
- ✅ `ALL PRIVILEGES ON ALL TABLES` **WITH GRANT OPTION**
- ✅ `ALL PRIVILEGES ON ALL SEQUENCES` **WITH GRANT OPTION**
- ✅ `ALL PRIVILEGES ON ALL FUNCTIONS` **WITH GRANT OPTION**
- ✅ `CREATE ON SCHEMA public`
- ✅ `ALTER DEFAULT PRIVILEGES` (para novos objetos)

**Quando Usar:**
- Administradores de banco de dados
- Aplicações que gerenciam schema
- ETL/migração de dados

**Detecção Automática:**
- Nome termina com `_admin`
- Nome contém "admin" (case-insensitive)
- `permission_type: "admin"` no JSON

### 2. 🟢 USER (CRUD Completo)

**Permissões Concedidas:**
- ✅ `SELECT` em todas as tabelas
- ✅ `INSERT` em todas as tabelas
- ✅ `UPDATE` em todas as tabelas
- ✅ `DELETE` em todas as tabelas
- ✅ `USAGE` em sequences
- ✅ `EXECUTE` em functions
- ✅ `USAGE` no schema public
- ✅ `CONNECT` no banco

**Quando Usar:**
- Aplicações backend
- Usuários que precisam escrever dados
- APIs de serviço

**Detecção Automática:**
- Nome termina com `_user`
- `permission_type: "user"` no JSON
- Padrão para usuários não-readonly/admin

### 3. 🔵 READONLY/VIEWER (Somente Leitura)

**Permissões Concedidas:**
- ✅ `SELECT` em todas as tabelas (SOMENTE)
- ✅ `USAGE` no schema public
- ✅ `CONNECT` no banco

**Quando Usar:**
- Ferramentas de BI (Metabase, Grafana)
- Usuários de análise
- Aplicações de relatórios
- Auditoria

**Detecção Automática:**
- Nome termina com `_readonly` ou `_viewer`
- Nome contém "readonly" ou "viewer" (case-insensitive)
- `permission_type: "readonly"` no JSON

---

## Fluxo de Execução

### Diagrama de Fluxo Geral

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INICIALIZAÇÃO                                            │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────────┐                                        │
│ │ Parse Arguments  │                                        │
│ └────────┬─────────┘                                        │
│          │                                                   │
│          ├─────────▶ Modo JSON? ──Yes──▶ Load JSON Config  │
│          │                                                   │
│          └─────────▶ Modo Interativo ──▶ Prompt User Input │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 2. CONEXÃO E VALIDAÇÃO                                       │
├──────────────────────────────────────────────────────────────┤
│ • Carregar credenciais admin (migration_user)                │
│ • Conectar a PostgreSQL (banco postgres)                     │
│ • Verificar se banco alvo existe                             │
│ • Obter informações do banco (owner, size, tables)           │
│ • Determinar usuários esperados                              │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 3. ANÁLISE DE PERMISSÕES                                     │
├──────────────────────────────────────────────────────────────┤
│ Para cada usuário:                                           │
│   • Reconectar ao banco alvo (importante!)                   │
│   • Verificar se usuário existe                              │
│   • Obter info básica (can_login, is_superuser)             │
│   • Verificar privilégio CONNECT                             │
│   • Verificar privilégio USAGE no schema                     │
│   • Contar permissões SELECT/INSERT/UPDATE/DELETE            │
│   • Identificar permissões faltando                          │
│   • Detectar tipo de usuário (admin/user/readonly)           │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 4. EXIBIR RELATÓRIO                                          │
├──────────────────────────────────────────────────────────────┤
│ • Mostrar resumo do banco                                    │
│ • Listar usuários e suas permissões                          │
│ • Indicar tipo de cada usuário (cores)                       │
│ • Destacar permissões faltando                               │
└──────────────────────────┬───────────────────────────────────┘
                           │
                    auto_fix? ───No──▶ END
                           │
                          Yes
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 5. APLICAR CORREÇÕES                                         │
├──────────────────────────────────────────────────────────────┤
│ Para cada usuário com problemas:                             │
│   • Create user se não existe (se create_users=True)         │
│   • Detectar tipo de usuário (admin/user/readonly)           │
│   • Aplicar permissões apropriadas:                          │
│     - admin    ─▶ grant_admin_privileges()                   │
│     - readonly ─▶ grant_readonly_privileges()                │
│     - user     ─▶ grant_full_permissions()                   │
│   • Registrar cada ação (PermissionFix)                      │
│   • Commit transações                                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│ 6. EXPORTAR RELATÓRIO                                        │
├──────────────────────────────────────────────────────────────┤
│ • Gerar JSON com todos os detalhes                           │
│ • Salvar em reports/fix_permissions_{db}_{timestamp}.json    │
│ • Exibir sumário final (total de correções, sucessos/falhas) │
└──────────────────────────────────────────────────────────────┘
```

### Fluxo de Análise de Permissões (Detalhado)

```python
def analyze_user_permissions(session, username, db_name, total_tables, permission_type):
    """
    1. Obter info básica do usuário (pg_roles)
       ├─ exists, can_login, is_superuser
       └─ Se não existe: return UserPermissions com exists=False

    2. Verificar privilégios de conexão
       ├─ CONNECT no banco (has_database_privilege)
       └─ USAGE no schema public (has_schema_privilege)

    3. Contar permissões em tabelas (para cada permissão)
       ├─ SELECT: contar tabelas com has_table_privilege()
       ├─ INSERT: contar tabelas
       ├─ UPDATE: contar tabelas
       └─ DELETE: contar tabelas

    4. Detectar tipo de usuário
       ├─ Se permission_type fornecido: usar explicitamente
       └─ Senão: detectar por nome (_admin, _readonly, _viewer)

    5. Identificar permissões faltando
       ├─ Se !CONNECT: missing.append("CONNECT")
       ├─ Se !USAGE: missing.append("USAGE_ON_SCHEMA")
       ├─ Se readonly:
       │   └─ Se SELECT < total: missing.append("SELECT_ON_TABLES")
       └─ Se user/admin:
           ├─ Se SELECT < total: missing.append("SELECT_ON_TABLES")
           ├─ Se INSERT < total: missing.append("INSERT_ON_TABLES")
           ├─ Se UPDATE < total: missing.append("UPDATE_ON_TABLES")
           └─ Se DELETE < total: missing.append("DELETE_ON_TABLES")

    6. Return UserPermissions com todos os dados
    """
```

---

## Configuração via JSON

### Estrutura do Arquivo

**Arquivo**: `validation/permissions_config.json` (ou qualquer nome)

```json
{
  "database": "nome_do_banco",
  "users": [
    {
      "username": "usuario1",
      "permission_type": "admin|user|readonly",
      "description": "Opcional - descrição do usuário"
    }
  ]
}
```

### Campos Obrigatórios

| Campo | Tipo | Descrição | Obrigatório |
|-------|------|-----------|-------------|
| `database` | string | Nome do banco de dados no PostgreSQL | ✅ Sim |
| `users` | array | Lista de usuários a configurar | ✅ Sim |
| `users[].username` | string | Nome do usuário PostgreSQL | ✅ Sim |
| `users[].permission_type` | enum | Tipo de permissão: `admin`, `user`, `readonly` | ✅ Sim |
| `users[].description` | string | Descrição opcional | ❌ Não |

### Exemplo Completo

```json
{
  "database": "metabase_db",
  "users": [
    {
      "username": "metabase_admin",
      "permission_type": "admin",
      "description": "Administrador com permissões totais e GRANT OPTION"
    },
    {
      "username": "metabase_user",
      "permission_type": "user",
      "description": "Aplicação principal com CRUD completo"
    },
    {
      "username": "metabase_viewer",
      "permission_type": "readonly",
      "description": "BI e relatórios com apenas SELECT"
    }
  ]
}
```

### Validação

O script valida automaticamente:

1. ✅ Campo `database` presente e não-vazio
2. ✅ Campo `users` é um array
3. ✅ Cada usuário tem `username`
4. ✅ Cada usuário tem `permission_type`
5. ✅ `permission_type` é um dos valores válidos: `admin`, `user`, `readonly`

Se alguma validação falhar, o script para e exibe o erro.

---

## Funções Principais

### Configuração e Validação

#### `load_permissions_config(config_file: str) -> Dict[str, Any]`

Carrega e valida arquivo JSON de configuração.

**Parâmetros:**
- `config_file`: Caminho do arquivo JSON

**Retorna:**
- Dict com `database` e `users`

**Exceções:**
- `FileNotFoundError`: Arquivo não existe
- `json.JSONDecodeError`: JSON malformado
- `ValueError`: Estrutura inválida

**Exemplo:**
```python
config = load_permissions_config("permissions_config.json")
# config = {"database": "metabase_db", "users": [...]}
```

#### `load_admin_credentials() -> Dict[str, Any]`

Carrega credenciais do usuário admin (migration_user) de `secrets/postgresql_destination_config.json`.

**Retorna:**
```python
{
    "user": "migration_user",
    "password": "***",
    "host": "wfdb02.vya.digital",
    "port": 5432
}
```

### Análise

#### `analyze_user_permissions(session, username, db_name, total_tables, permission_type=None) -> UserPermissions`

Analisa permissões completas de um usuário.

**⚠️ IMPORTANTE**: A `session` deve estar conectada ao banco de dados alvo (não ao `postgres`), caso contrário `has_table_privilege()` falhará.

**Parâmetros:**
- `session`: SQLAlchemy Session **conectada ao banco alvo**
- `username`: Nome do usuário a analisar
- `db_name`: Nome do banco (usado para CONNECT check)
- `total_tables`: Total de tabelas no banco
- `permission_type`: Tipo explícito (`"admin"`, `"user"`, `"readonly"`) ou `None` para auto-detectar

**Retorna:**
- `UserPermissions` dataclass com estado completo

**Exemplo:**
```python
# Conectar ao banco CORRETO
engine_db = create_engine(f"postgresql://.../{db_name}")
with Session(engine_db) as session:
    perms = analyze_user_permissions(
        session,
        "metabase_user",
        "metabase_db",
        159,
        "admin"  # Explícito
    )
    print(f"SELECT: {perms.tables_with_select}/{perms.total_tables}")
```

#### `count_table_permissions(session, username, db_name, permission) -> int`

Conta quantas tabelas o usuário tem uma permissão específica.

**Algoritmo:**
1. Lista todas as tabelas em `pg_tables` (schema public, não-sistema)
2. Para cada tabela, verifica `has_table_privilege(user, table, permission)`
3. Conta quantas retornam `True`

**Exceção Handling:**
- Erros em tabelas individuais são ignorados (continua)
- Retorna 0 se erro geral

#### `get_total_tables(session, db_name) -> int`

Obtém total de tabelas no schema public (excluindo pg_*).

**Query:**
```sql
SELECT COUNT(*)
FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT LIKE 'pg_%'
```

### Correção de Permissões

#### `grant_admin_privileges(session, username, db_name) -> PermissionFix`

Concede privilégios de administrador completo.

**SQL Executado:**
```sql
-- Todas as tabelas + GRANT OPTION
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public
TO username WITH GRANT OPTION;

-- Todas as sequences + GRANT OPTION
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public
TO username WITH GRANT OPTION;

-- Todas as functions + GRANT OPTION
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public
TO username WITH GRANT OPTION;

-- Permissão de criar objetos
GRANT CREATE ON SCHEMA public TO username;

-- Permissões em objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO username WITH GRANT OPTION;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON SEQUENCES TO username WITH GRANT OPTION;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON FUNCTIONS TO username WITH GRANT OPTION;
```

#### `grant_readonly_privileges(session, username, db_name) -> PermissionFix`

Concede apenas privilégios de leitura.

**SQL Executado:**
```sql
-- SOMENTE SELECT
GRANT SELECT ON ALL TABLES IN SCHEMA public TO username;

-- USAGE no schema
GRANT USAGE ON SCHEMA public TO username;

-- CONNECT no banco
GRANT CONNECT ON DATABASE db_name TO username;

-- Permissões em tabelas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO username;
```

#### `grant_full_permissions(session, username, db_name) -> PermissionFix`

Concede permissões CRUD completas (user padrão).

**SQL Executado:**
```sql
-- CRUD em todas as tabelas
GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public TO username;

-- USAGE em sequences e schema
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO username;
GRANT USAGE ON SCHEMA public TO username;

-- EXECUTE em functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO username;

-- CONNECT no banco
GRANT CONNECT ON DATABASE db_name TO username;

-- Permissões em objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO username;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE ON SEQUENCES TO username;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT EXECUTE ON FUNCTIONS TO username;
```

#### `create_user_if_not_exists(session, username, password=None) -> PermissionFix`

Cria usuário se não existir.

**Funcionalidade:**
- Se `password` é `None`, gera senha aleatória com `secrets.token_urlsafe(16)`
- Exibe senha gerada (IMPORTANTE: salvar!)
- Cria usuário com `LOGIN` habilitado

**SQL:**
```sql
CREATE USER username WITH PASSWORD 'senha' LOGIN;
```

### Orquestração

#### `analyze_and_fix_database(db_name, auto_fix, create_users, custom_users, user_types) -> AnalysisReport`

Função principal que orquestra todo o processo.

**Parâmetros:**
- `db_name`: Nome do banco
- `auto_fix`: Se True, aplica correções automaticamente
- `create_users`: Se True, cria usuários que não existem
- `custom_users`: Lista de usernames customizados (ou None para usar padrão)
- `user_types`: Dict `{username: permission_type}` (ou None)

**Fluxo:**
1. Conectar a `postgres` como admin
2. Verificar se banco existe
3. Obter informações do banco
4. Determinar usuários esperados
5. **Reconectar ao banco alvo** (crítico!)
6. Analisar permissões de cada usuário
7. Se `auto_fix`:
   - Criar usuários se necessário
   - Aplicar correções de permissões
8. Exportar relatório

**Retorna:**
- `AnalysisReport` com todos os detalhes

### Exportação

#### `export_report(report: AnalysisReport) -> Optional[str]`

Exporta relatório para JSON.

**Filename**: `reports/fix_permissions_{db_name}_{timestamp}.json`

**Estrutura:**
```json
{
  "timestamp": "2026-01-16T16:30:30",
  "database_name": "metabase_db",
  "database_info": { ... },
  "expected_users": ["user1", "user2"],
  "user_permissions": {
    "user1": { ... },
    "user2": { ... }
  },
  "fixes_applied": [
    {
      "username": "user1",
      "action": "GRANT_SELECT",
      "sql_command": "GRANT ...",
      "success": true
    }
  ],
  "summary": "Análise concluída. 2 correções aplicadas (2 sucesso, 0 falhas)"
}
```

---

## Exemplos de Uso

### Exemplo 1: Modo Interativo

```bash
$ python3 validation/fix_database_permissions.py

================================================================================
FIX DATABASE PERMISSIONS - PostgreSQL 18 wfdb02
================================================================================

Digite o nome do banco de dados:
> metabase_db

Usuários sugeridos para o banco metabase_db:
  • metabase_db_admin (admin - permissões totais)
  • metabase_db_user (user - CRUD completo)
  • metabase_db_readonly (readonly - apenas SELECT)

Digite os nomes dos usuários a analisar:
(Separados por vírgula para múltiplos usuários)
(Enter para usar os usuários sugeridos)
> metabase_user, metabase_viewer

Aplicar correções automaticamente? (s/n):
> n

# ... análise executada ...
```

### Exemplo 2: Modo JSON Somente Leitura

```bash
# Apenas analisa, não corrige
python3 validation/fix_database_permissions.py \
  --config validation/permissions_config.json
```

### Exemplo 3: Modo JSON com Auto-Fix

```bash
# Analisa e corrige automaticamente
python3 validation/fix_database_permissions.py \
  --config validation/permissions_config.json \
  --auto-fix
```

### Exemplo 4: Criar Usuários e Corrigir Permissões

```bash
# Cria usuários se não existem + corrige permissões
python3 validation/fix_database_permissions.py \
  --config validation/permissions_config.json \
  --auto-fix \
  --create-users
```

### Exemplo 5: Pipeline de CI/CD

```bash
#!/bin/bash
# deploy_permissions.sh

CONFIG_FILE="config/production_permissions.json"

# Validar JSON
if ! python3 -c "import json; json.load(open('$CONFIG_FILE'))"; then
  echo "JSON inválido!"
  exit 1
fi

# Aplicar permissões
python3 validation/fix_database_permissions.py \
  --config "$CONFIG_FILE" \
  --auto-fix

# Verificar relatório
REPORT=$(ls -t reports/fix_permissions_*.json | head -1)
FIXES=$(jq '.fixes_applied | length' "$REPORT")

echo "Total de correções aplicadas: $FIXES"
```

### Exemplo 6: Configuração Multi-Banco

```bash
# production_dbs.json
{
  "databases": [
    {
      "database": "app_db",
      "users": [
        {"username": "app_admin", "permission_type": "admin"},
        {"username": "app_backend", "permission_type": "user"},
        {"username": "app_readonly", "permission_type": "readonly"}
      ]
    },
    {
      "database": "analytics_db",
      "users": [
        {"username": "etl_user", "permission_type": "user"},
        {"username": "bi_viewer", "permission_type": "readonly"}
      ]
    }
  ]
}
```

```bash
# Script para processar múltiplos bancos
for db_config in $(jq -c '.databases[]' production_dbs.json); do
  echo "$db_config" > /tmp/db_config.json

  python3 validation/fix_database_permissions.py \
    --config /tmp/db_config.json \
    --auto-fix
done
```

---

## Troubleshooting

### Problema 1: "cross-database references are not implemented"

**Erro:**
```
ERROR: cross-database references are not implemented: "metabase_db.public.table"
```

**Causa:**
A session está conectada ao banco `postgres`, mas tenta verificar permissões em tabelas de `metabase_db`. PostgreSQL não permite referências cross-database.

**Solução:**
O script **já corrige isso** reconectando ao banco alvo antes de analisar permissões:

```python
# ERRADO: conectado ao postgres
with Session(engine_postgres) as session:
    perms = analyze_user_permissions(session, "user", "metabase_db", 159)
    # ❌ Falha!

# CORRETO: reconectar ao banco alvo
conn_str_db = build_connection_string(creds, "metabase_db")
engine_db = create_engine(conn_str_db)
with Session(engine_db) as session:
    perms = analyze_user_permissions(session, "user", "metabase_db", 159)
    # ✅ Funciona!
```

### Problema 2: Total de tabelas = 0

**Sintoma:**
```
Tabelas (public): 0
SELECT: 159/0  # Deveria ser 159/159
```

**Causa:**
Query de contagem exclui tabelas onde `tableowner = 'postgres'`, mas no banco todas as tabelas pertencem ao postgres.

**Solução:**
Versão corrigida já implementada:

```python
# ERRADO (versão antiga)
WHERE tableowner != 'postgres'  # Exclui todas!

# CORRETO (versão atual)
WHERE tablename NOT LIKE 'pg_%'  # Exclui apenas tabelas de sistema
```

### Problema 3: Usuário não detectado como ADMIN

**Sintoma:**
```json
{
  "username": "metabase_user",
  "permission_type": "admin"  // No JSON
}
```

```
Analisando: metabase_user
  Tipo: USUÁRIO NORMAL (CRUD completo)  ❌ Deveria ser ADMIN
```

**Causa:**
O código detectava tipo apenas pelo nome (`_admin` suffix), ignorando o `permission_type` do JSON.

**Solução:**
Passar `user_types` dict para `analyze_and_fix_database()`:

```python
# Extrair tipos do JSON
user_types = {u['username']: u['permission_type'] for u in config['users']}

# Passar para análise
report = analyze_and_fix_database(
    db_name, auto_fix, create_users, custom_users,
    user_types  # ✅ Agora respeita JSON
)
```

### Problema 4: Arquivo de credenciais não encontrado

**Erro:**
```
FileNotFoundError: secrets/postgresql_destination_config.json
```

**Solução:**
Criar arquivo de credenciais:

```json
{
  "authentication": {
    "user": "migration_user",
    "password": "sua_senha_aqui"
  },
  "server": {
    "host": "wfdb02.vya.digital",
    "port": 5432
  }
}
```

**Permissões requeridas para migration_user:**
- `SUPERUSER` ou `CREATEDB` + `CREATEROLE`
- Acesso a `pg_roles`, `pg_database`, `pg_tables`

### Problema 5: "Permission denied for relation pg_roles"

**Causa:**
Usuário admin não tem permissão de ler `pg_roles`.

**Solução:**
```sql
-- Como postgres
GRANT SELECT ON pg_roles TO migration_user;
GRANT SELECT ON pg_database TO migration_user;
```

### Problema 6: Senha do usuário criado perdida

**Problema:**
Script criou usuário com senha aleatória mas você não salvou.

**Solução:**
```sql
-- Resetar senha manualmente
ALTER USER username WITH PASSWORD 'nova_senha_segura';
```

### Problema 7: JSON inválido

**Erro:**
```
json.JSONDecodeError: Expecting ',' delimiter: line 5 column 3
```

**Solução:**
Validar JSON antes de usar:

```bash
# Validar sintaxe
python3 -m json.tool permissions_config.json

# Ou com jq
jq empty permissions_config.json
```

### Problema 8: "Database does not exist"

**Causa:**
Banco especificado no JSON não existe no PostgreSQL.

**Solução:**
```sql
-- Listar bancos disponíveis
SELECT datname FROM pg_database WHERE datistemplate = false;

-- Criar banco se necessário
CREATE DATABASE metabase_db
  WITH OWNER = postgres
  ENCODING = 'UTF8'
  TABLESPACE = ts_enterprise_data;
```

---

## Segurança e Boas Práticas

### ✅ Recomendações

1. **Credenciais Seguras**
   - Nunca commitar `secrets/` no Git
   - Usar `.gitignore` para excluir credenciais
   - Considerar usar vault (HashiCorp Vault, AWS Secrets Manager)

2. **Princípio do Menor Privilégio**
   - Preferir `readonly` quando possível
   - Usar `user` apenas se CRUD for necessário
   - Reservar `admin` para DBAs e ferramentas de migração

3. **Auditoria**
   - Sempre exportar relatórios (--config gera JSON)
   - Versionar arquivos de configuração
   - Manter histórico de mudanças de permissões

4. **Validação**
   - Testar em ambiente staging primeiro
   - Usar modo somente leitura (sem --auto-fix) para preview
   - Revisar relatório antes de aplicar correções

5. **Automação**
   - Integrar no pipeline de CI/CD
   - Executar periodicamente para detectar drift
   - Alertar sobre permissões inesperadas

### ❌ Evitar

- ❌ Executar com `--auto-fix --create-users` em produção sem revisar
- ❌ Dar permissões `admin` para aplicações
- ❌ Reutilizar mesma senha para múltiplos usuários
- ❌ Ignorar erros no relatório
- ❌ Executar como `postgres` superuser (usar admin dedicado)

---

## Anexos

### A. Tabela de Permissões por Tipo

| Permissão | Admin | User | Readonly |
|-----------|:-----:|:----:|:--------:|
| **Tabelas** |
| SELECT | ✅ + GRANT | ✅ | ✅ |
| INSERT | ✅ + GRANT | ✅ | ❌ |
| UPDATE | ✅ + GRANT | ✅ | ❌ |
| DELETE | ✅ + GRANT | ✅ | ❌ |
| TRUNCATE | ✅ + GRANT | ❌ | ❌ |
| REFERENCES | ✅ + GRANT | ❌ | ❌ |
| TRIGGER | ✅ + GRANT | ❌ | ❌ |
| **Sequences** |
| USAGE | ✅ + GRANT | ✅ | ❌ |
| SELECT | ✅ + GRANT | ❌ | ❌ |
| UPDATE | ✅ + GRANT | ❌ | ❌ |
| **Functions** |
| EXECUTE | ✅ + GRANT | ✅ | ❌ |
| **Schema** |
| USAGE | ✅ | ✅ | ✅ |
| CREATE | ✅ | ❌ | ❌ |
| **Database** |
| CONNECT | ✅ | ✅ | ✅ |
| CREATE | ✅ | ❌ | ❌ |
| TEMP | ✅ | ❌ | ❌ |

### B. Códigos de Erro Comuns

| Código | Mensagem | Causa | Solução |
|--------|----------|-------|---------|
| 42P01 | relation does not exist | Tabela não existe | Verificar nome da tabela |
| 42501 | permission denied | Falta permissão | Grant necessário |
| 3D000 | database does not exist | Banco não existe | Criar banco |
| 42710 | duplicate object | Usuário já existe | Usar IF NOT EXISTS |
| 28P01 | password authentication failed | Credencial errada | Verificar secrets/ |

### C. Referências

- [PostgreSQL 18 Documentation - GRANT](https://www.postgresql.org/docs/18/sql-grant.html)
- [PostgreSQL 18 Documentation - ALTER DEFAULT PRIVILEGES](https://www.postgresql.org/docs/18/sql-alterdefaultprivileges.html)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Privilege System](https://www.postgresql.org/docs/18/ddl-priv.html)

---

## Changelog

### v2.0.0 - 2026-01-16

✨ **Novidades:**
- Suporte a configuração via JSON
- Detecção automática de tipo de usuário (admin/user/readonly)
- Três níveis de permissão bem definidos
- Exportação de relatórios em JSON

🐛 **Correções:**
- Resolvido erro "cross-database references"
- Corrigido total de tabelas = 0
- Detecção de admin agora respeita JSON `permission_type`

### v1.0.0 - 2025-12-11

- Versão inicial
- Modo interativo
- Correção automática de permissões

---

**Última atualização**: 16 de janeiro de 2026
**Autor**: Sistema de Migração VYA
**Contato**: DevOps Team
