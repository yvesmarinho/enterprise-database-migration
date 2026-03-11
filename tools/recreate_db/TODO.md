# Alterações necessárias

## ✅ CORRIGIDO - 2026-03-11

- ✅ o código python não está coletando os grants da base de dados na coleta.

### Correções Implementadas:

#### PostgreSQL (`_collect_postgresql_grants`)
Agora coleta:
- ✅ Grants a nível de DATABASE (datacl)
- ✅ Grants a nível de SCHEMA (nspacl)
- ✅ Grants a nível de TABELA/VIEW (information_schema.table_privileges)
- ✅ Owner de cada objeto
- ✅ Contador total de grants coletados

O método agora conecta temporariamente ao banco específico para coletar permissões detalhadas de schemas, tabelas e views (limitado a 100 objetos).

#### MySQL (`_collect_mysql_grants`)
Agora coleta:
- ✅ Grants a nível de SCHEMA/DATABASE (information_schema.SCHEMA_PRIVILEGES)
- ✅ Grants a nível de TABELA (information_schema.TABLE_PRIVILEGES) - limitado a 100 tabelas
- ✅ Grants a nível de COLUNA (information_schema.COLUMN_PRIVILEGES) - limitado a 50 colunas
- ✅ Agrupamento de grants por tabela
- ✅ Contador total de grants coletados

### Estrutura de retorno atualizada:

**PostgreSQL:**
```json
{
  "database": "nome_db",
  "owner": "usuario_owner",
  "database_acl": [],
  "schema_privileges": [...],
  "table_privileges": [...],
  "total_grants": 42
}
```

**MySQL:**
```json
{
  "database": "nome_db",
  "schema_privileges": [...],
  "table_privileges": [...],
  "column_privileges": [...],
  "total_grants": 123
}
```
