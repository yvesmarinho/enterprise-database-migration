# Fix Permissions - Sistema de Correção de Permissões PostgreSQL

## Descrição

Sistema automatizado para correção e verificação de permissões em bancos de dados PostgreSQL, desenvolvido durante a migração e troubleshooting do Metabase v0.56.19.1.

## Arquivos

- **fix_permissions.json**: Configuração declarativa das operações
- **fix_permissions.py**: Script Python de execução
- **README.md**: Esta documentação

## Configuração (fix_permissions.json)

### Estrutura

```json
{
  "description": "Descrição do sistema",
  "version": "1.0.0",
  "databases": [
    {
      "name": "nome_do_banco",
      "type": "postgres",
      "owner": "usuario_dono",
      "description": "Descrição do banco",
      "operations": [...]
    }
  ],
  "connection": {...},
  "verification": {...}
}
```

### Tipos de Operações

#### 1. Transfer Ownership
```json
{
  "type": "transfer_ownership",
  "target": "tables|sequences|views",
  "from_user": "usuario_origem",
  "to_user": "usuario_destino"
}
```

#### 2. Grant Privileges
```json
{
  "type": "grant_privileges",
  "target": "schema|all_tables|all_sequences",
  "schema": "public",
  "user": "usuario",
  "privileges": ["SELECT", "INSERT", "UPDATE", "DELETE"]
}
```

#### 3. Set Default Privileges
```json
{
  "type": "set_default_privileges",
  "target": "tables|sequences",
  "schema": "public",
  "user": "usuario",
  "privileges": ["ALL"]
}
```

## Uso

### Modo Dry-Run (Simulação)

```bash
# Verificar um banco específico sem executar
python3 fix_permissions/fix_permissions.py --database metabase_db --dry-run

# Simular todos os bancos
python3 fix_permissions/fix_permissions.py --all --dry-run --verbose
```

### Modo Execução

```bash
# Executar correções em um banco
python3 fix_permissions/fix_permissions.py --database metabase_db --execute

# Executar em todos os bancos
python3 fix_permissions/fix_permissions.py --all --execute --verbose
```

### Modo Verificação

```bash
# Apenas verificar estado atual
python3 fix_permissions/fix_permissions.py --database metabase_db --verify

# Verificar com detalhes
python3 fix_permissions/fix_permissions.py --database n8n_db --verify --verbose
```

## Parâmetros

| Parâmetro | Descrição |
|-----------|-----------|
| `--database <nome>` | Banco específico a processar |
| `--all` | Processar todos os bancos do config |
| `--dry-run` | Simular sem executar (padrão) |
| `--execute` | Executar as operações de fato |
| `--verify` | Apenas verificar estado atual |
| `--verbose` | Modo detalhado |
| `--config <path>` | Caminho alternativo para config JSON |

## Bancos Configurados

### 1. metabase_db
- **Owner**: `metabase_user`
- **Operações**: Transfer ownership completo + grants
- **Descrição**: Banco de dados do Metabase BI

### 2. n8n_db
- **Owner**: `n8n_user`
- **Operações**: Grants de privilégios
- **Descrição**: Banco de dados do N8N Automações

### 3. evolution_api
- **Owner**: `evolution_user`
- **Operações**: Grants completos
- **Descrição**: Banco de dados da Evolution API WhatsApp

## Verificações Automáticas

Quando habilitadas em `verification.enabled`:

1. **user_exists**: Verifica se o usuário owner existe
2. **ownership**: Verifica ownership das tabelas
3. **privileges**: Verifica privilégios concedidos
4. **default_privileges**: Verifica privilégios padrão

## Exemplos de Saída

### Dry-Run
```
================================================================================
PROCESSANDO: metabase_db (Banco de dados do Metabase - BI e Analytics)
Owner esperado: metabase_user
Modo: DRY-RUN
================================================================================

[2026-01-16 20:15:30] ✓ Usuário 'metabase_user' encontrado

[1/8] Operação: transfer_ownership
[2026-01-16 20:15:31] → DRY-RUN: ALTER TABLE public.core_user OWNER TO metabase_user;
[2026-01-16 20:15:31] → DRY-RUN: ALTER TABLE public.report_card OWNER TO metabase_user;
...
[2026-01-16 20:15:32] ✓ Ownership transferido para 141 tabelas

================================================================================
RESULTADO: 8/8 operações concluídas
================================================================================
```

### Execução Real
```
================================================================================
PROCESSANDO: metabase_db (Banco de dados do Metabase - BI e Analytics)
Owner esperado: metabase_user
Modo: EXECUÇÃO
================================================================================

[2026-01-16 20:20:15] ✓ Usuário 'metabase_user' encontrado
[2026-01-16 20:20:16] ✓ Executado: ALTER TABLE public.core_user OWNER TO metabase_user;
[2026-01-16 20:20:16] ✓ Ownership transferido para 141 tabelas

────────────────────────────────────────────────────────────────────────────────
VERIFICAÇÕES FINAIS:
────────────────────────────────────────────────────────────────────────────────

[2026-01-16 20:20:30] → Ownership verificado: {'metabase_user': 141}
[2026-01-16 20:20:30] ✓ Owner 'metabase_user' possui 141 tabelas
[2026-01-16 20:20:31] ✓ Usuário 'metabase_user' tem privilégios em 154 objetos

================================================================================
RESULTADO: 8/8 operações concluídas
================================================================================

✓ Processo concluído com sucesso!
```

## Conexão

Utiliza as credenciais de `secrets/postgresql_destination_config.json`:

```json
{
  "server": {
    "host": "wfdb02.vya.digital",
    "port": 5432
  },
  "authentication": {
    "user": "migration_user",
    "password": "..."
  }
}
```

## Casos de Uso

### 1. Restauração de Backup
Após restaurar backup do Metabase:
```bash
python3 fix_permissions/fix_permissions.py --database metabase_db --execute
```

### 2. Nova Instalação
Configurar permissões em banco novo:
```bash
python3 fix_permissions/fix_permissions.py --database evolution_api --execute
```

### 3. Auditoria
Verificar estado atual sem modificar:
```bash
python3 fix_permissions/fix_permissions.py --all --verify --verbose
```

### 4. Desenvolvimento
Testar mudanças antes de aplicar:
```bash
python3 fix_permissions/fix_permissions.py --database n8n_db --dry-run --verbose
```

## Troubleshooting

### Usuário não existe
```
✗ Usuário 'metabase_user' NÃO EXISTE
```
**Solução**: Criar usuário antes:
```sql
CREATE USER metabase_user WITH PASSWORD 'senha';
```

### Permissão negada
```
✗ Erro ao executar SQL: permission denied for table xxx
```
**Solução**: Executar com usuário com privilégios suficientes (migration_user tem SUPERUSER)

### Banco não encontrado no config
```
✗ Banco de dados 'meu_banco' não encontrado no config
```
**Solução**: Adicionar configuração em `fix_permissions.json`

## Logs

O script gera logs detalhados com timestamps:
- `→` Informação
- `✓` Sucesso
- `✗` Erro
- `⚠` Aviso

## Segurança

- **Dry-run por padrão**: Requer `--execute` explícito
- **Verificações antes de aplicar**: Valida usuários e conexões
- **Rollback manual**: Não há rollback automático, documentar estado antes
- **Credenciais**: Nunca commitar `secrets/` no git

## Histórico

- **v1.0.0** (2026-01-16): Versão inicial
  - Suporte a transfer ownership
  - Grants de privilégios
  - Default privileges
  - Verificações automáticas
  - Modos dry-run, execute e verify

## Manutenção

Para adicionar novo banco:
1. Adicionar entry em `fix_permissions.json`
2. Testar com `--dry-run`
3. Executar com `--execute`
4. Verificar com `--verify`

## Referências

- [PostgreSQL: GRANT](https://www.postgresql.org/docs/current/sql-grant.html)
- [PostgreSQL: ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)
- [PostgreSQL: ALTER DEFAULT PRIVILEGES](https://www.postgresql.org/docs/current/sql-alterdefaultprivileges.html)
