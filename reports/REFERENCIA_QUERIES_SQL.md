# 📖 Referência: Queries SQL do Simulador Evolution API

**Documento:** Queries SQL que o simulador executa
**Data:** 2 de novembro de 2025
**Banco:** PostgreSQL (Evolution API)

---

## 📋 Índice de Queries

1. [Validação de Conexão](#validação-de-conexão)
2. [Banco de Dados](#banco-de-dados)
3. [Tabelas](#tabelas)
4. [Permissões](#permissões)
5. [Instâncias](#instâncias)
6. [Usuários](#usuários)
7. [Mensagens](#mensagens)
8. [Estatísticas](#estatísticas)

---

## Validação de Conexão

### Query 1: Teste de Conexão (Simples)

```sql
-- Simples: SELECT 1 (testa conectividade)
SELECT 1 as connection_test;
```

**Resultado Esperado:**
```
 connection_test
-----------------
               1
(1 row)
```

---

## Banco de Dados

### Query 2: Verificar Banco Existe

```sql
-- Listar bancos de dados
SELECT datname, spcname, datacl
FROM pg_database
LEFT JOIN pg_tablespace ON pg_database.dattablespace = pg_tablespace.oid
WHERE datname = 'evolution_db';
```

**Resultado Esperado:**
```
   datname    |        spcname        |          datacl
---------------+-----------------------+---------------------------
 evolution_db  | ts_enterprise_data    | {postgres=CTc/postgres,...}
(1 row)
```

---

### Query 3: Tamanho do Banco

```sql
-- Ver tamanho do banco de dados
SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datname = 'evolution_db';
```

**Resultado Esperado:**
```
   datname    |  size
---------------+--------
 evolution_db  | 125 MB
(1 row)
```

---

## Tabelas

### Query 4: Listar Tabelas Evolution

```sql
-- Listar tabelas do schema public
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Resultado Esperado:**
```
 table_schema |   table_name    | table_type
--------------+-----------------+----------
 public       | Chat            | BASE TABLE
 public       | Contact         | BASE TABLE
 public       | Instance        | BASE TABLE
 public       | Message         | BASE TABLE
 public       | Settings        | BASE TABLE
 ...
(7 rows)
```

---

### Query 5: Estrutura da Tabela Instance

```sql
-- Ver colunas da tabela "Instance"
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'Instance'
ORDER BY ordinal_position;
```

**Resultado Esperado:**
```
      column_name      |       data_type        | is_nullable | column_default
-----------------------+------------------------+-------------+-------------------
 id                    | uuid                   | NO          | gen_random_uuid()
 name                  | character varying      | NO          |
 number                | character varying      | YES         |
 status                | character varying      | NO          | 'disconnected'
 token                 | character varying      | NO          |
 integration           | character varying      | NO          | 'BAILEYS'
 clientName            | character varying      | NO          | 'postgresql'
 createdAt             | timestamp with tz      | NO          | CURRENT_TIMESTAMP
 updatedAt             | timestamp with tz      | NO          | CURRENT_TIMESTAMP
(9 rows)
```

---

### Query 6: Verificar Índices

```sql
-- Listar índices das tabelas
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public' AND tablename = 'Instance';
```

**Resultado Esperado:**
```
 tablename |      indexname      |            indexdef
-----------+---------------------+---------------------------
 Instance  | Instance_pkey       | CREATE UNIQUE INDEX ...
 Instance  | Instance_name_idx   | CREATE INDEX Instance_name_idx ON public."Instance" (name)
(2 rows)
```

---

## Permissões

### Query 7: Verificar Permissões do Usuário

```sql
-- Listar permissões do usuário atual
SELECT grantee, privilege_type, is_grantable
FROM information_schema.table_privileges
WHERE table_schema = 'public' AND grantee = 'migration_user'
ORDER BY table_name, privilege_type;
```

**Resultado Esperado:**
```
     grantee      | privilege_type | is_grantable
------------------+----------------+--------------
 migration_user   | SELECT         | NO
 migration_user   | INSERT         | NO
 migration_user   | UPDATE         | NO
 migration_user   | DELETE         | NO
 migration_user   | TRUNCATE       | NO
 migration_user   | REFERENCES     | NO
 migration_user   | TRIGGER        | NO
(7 rows)
```

---

### Query 8: Permissões em Schema

```sql
-- Listar permissões no schema
SELECT grantee, privilege_type
FROM information_schema.schemata
WHERE schema_name = 'public';
```

---

### Query 9: Permissões de Banco de Dados

```sql
-- Listar permissões no banco
SELECT * FROM aclinfo
WHERE oid = (SELECT oid FROM pg_database WHERE datname = 'evolution_db');
```

---

### Query 10: Verificar Quem Pode Conectar

```sql
-- Ver roles e suas permissões de conexão
SELECT rolname, rolsuper, rolcreatedb, rolcanlogin
FROM pg_roles
WHERE rolname = 'migration_user';
```

**Resultado Esperado:**
```
     rolname      | rolsuper | rolcreatedb | rolcanlogin
------------------+----------+-------------+-------------
 migration_user   | f        | f           | t
(1 row)
```

---

## Instâncias

### Query 11: Buscar Instâncias WhatsApp (Simula Evolution API)

```sql
-- Simula: GET /instance/fetchInstances
SELECT
    id,
    name,
    number,
    status,
    token,
    integration,
    "clientName" as client_name,
    "createdAt" as created_at,
    "updatedAt" as updated_at
FROM "Instance"
WHERE "clientName" = 'postgresql'
ORDER BY "createdAt" DESC;
```

**Resultado Esperado:**
```
                   id                   |   name    |      number      |   status    |
-----------+-----------+
 123e4567-e89b-12d3-a456-426614174000   | wa-bot-1  | 5511999999999    | connected   |
 223e4567-e89b-12d3-a456-426614174000   | wa-bot-2  | NULL             | disconnected|
(2 rows)
```

---

### Query 12: Buscar Instância por Nome

```sql
-- Simula: GET /instance/minha-instancia
SELECT * FROM "Instance"
WHERE name = 'wa-bot-1'
LIMIT 1;
```

---

### Query 13: Contar Instâncias

```sql
-- Total de instâncias criadas
SELECT COUNT(*) as total_instances
FROM "Instance";
```

**Resultado Esperado:**
```
 total_instances
-----------------
               2
(1 row)
```

---

## Usuários

### Query 14: Listar Usuários PostgreSQL

```sql
-- Listar todos os usuários
SELECT usename, usesuper, usecreatedb, usecreaterole, usecanlogin
FROM pg_user
ORDER BY usename;
```

**Resultado Esperado:**
```
      usename      | usesuper | usecreatedb | usecreaterole | usecanlogin
--------------------+----------+-------------+---------------+-------------
 migration_user     | f        | f           | f             | t
 postgres           | t        | t           | t             | t
 replication_user   | f        | f           | f             | t
(3 rows)
```

---

### Query 15: Verificar Último Login

```sql
-- Ver último acesso de um usuário
SELECT usename, (SELECT max(query_start)
                 FROM pg_stat_statements
                 WHERE userid = pg_user.usesysid)
FROM pg_user
WHERE usename = 'migration_user';
```

---

## Mensagens

### Query 16: Contar Mensagens

```sql
-- Total de mensagens registradas
SELECT COUNT(*) as total_messages
FROM "Message";
```

**Resultado Esperado:**
```
 total_messages
----------------
             42
(1 row)
```

---

### Query 17: Mensagens por Instância

```sql
-- Mensagens agrupadas por instância
SELECT i.name as instance_name, COUNT(m.id) as message_count
FROM "Instance" i
LEFT JOIN "Message" m ON m."instanceId" = i.id
GROUP BY i.id, i.name
ORDER BY message_count DESC;
```

**Resultado Esperado:**
```
 instance_name | message_count
---------------+---------------
 wa-bot-1      |            42
 wa-bot-2      |             0
(2 rows)
```

---

### Query 18: Mensagens Recentes

```sql
-- Últimas 10 mensagens
SELECT id, "remoteJid", "messageTimestamp", "status"
FROM "Message"
ORDER BY "messageTimestamp" DESC
LIMIT 10;
```

---

## Estatísticas

### Query 19: Estatísticas Gerais

```sql
-- Estatísticas do banco
SELECT
    (SELECT COUNT(*) FROM "Instance") as instances,
    (SELECT COUNT(*) FROM "Message") as messages,
    (SELECT COUNT(*) FROM "Chat") as chats,
    (SELECT COUNT(*) FROM "Contact") as contacts,
    (SELECT COUNT(*) FROM "Settings") as settings;
```

**Resultado Esperado:**
```
 instances | messages | chats | contacts | settings
-----------+----------+-------+----------+----------
         2 |       42 |     8 |       15 |        2
(1 row)
```

---

### Query 20: Tamanho das Tabelas

```sql
-- Tamanho de cada tabela
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Resultado Esperado:**
```
  tablename  |  size
--------------+--------
 Message      | 8.5 MB
 Chat         | 2.1 MB
 Instance     | 64 kB
 Contact      | 96 kB
 Settings     | 32 kB
(5 rows)
```

---

### Query 21: Tabelas com Mais Dados

```sql
-- Ver quais tabelas têm mais registros
SELECT
    schemaname,
    tablename,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

---

## Validação de Integridade

### Query 22: Verificar Foreign Keys

```sql
-- Listar foreign keys
SELECT
    constraint_name,
    table_name,
    column_name,
    foreign_table_name,
    foreign_column_name
FROM information_schema.referential_constraints
JOIN information_schema.key_column_usage
    ON referential_constraints.constraint_name = key_column_usage.constraint_name
WHERE table_schema = 'public';
```

---

### Query 23: Verificar Constraints

```sql
-- Listar todas as constraints
SELECT
    constraint_name,
    constraint_type,
    table_name
FROM information_schema.table_constraints
WHERE table_schema = 'public'
ORDER BY table_name, constraint_type;
```

---

## Queries Combinadas (Validação Completa)

### Query 24: Status Completo de Validação

```sql
-- Validação completa em uma query
WITH stats AS (
    SELECT
        'Instance' as table_name,
        COUNT(*) as row_count
    FROM "Instance"
    UNION ALL
    SELECT 'Message', COUNT(*) FROM "Message"
    UNION ALL
    SELECT 'Chat', COUNT(*) FROM "Chat"
    UNION ALL
    SELECT 'Contact', COUNT(*) FROM "Contact"
    UNION ALL
    SELECT 'Settings', COUNT(*) FROM "Settings"
),
permissions AS (
    SELECT COUNT(*) as permission_count
    FROM information_schema.table_privileges
    WHERE table_schema = 'public' AND grantee = 'migration_user'
)
SELECT
    (SELECT COUNT(*) FROM stats WHERE row_count > 0)::text || '/' ||
    (SELECT COUNT(*) FROM stats)::text as tables_with_data,
    (SELECT SUM(row_count) FROM stats)::text as total_rows,
    (SELECT permission_count::text FROM permissions) as user_permissions,
    CURRENT_TIMESTAMP as check_time;
```

---

## 🔍 Como Usar Essas Queries

### Executar uma Query

```bash
# Via psql
psql -U migration_user -d evolution_db -h localhost -c "SELECT * FROM \"Instance\";"

# Via SSH tunnel
ssh -L 5432:localhost:5432 user@wfdb02.vya.digital
psql -U migration_user -d evolution_db -c "SELECT COUNT(*) FROM \"Message\";"
```

---

### Salvar Resultado em Arquivo

```bash
# Export para CSV
psql -U migration_user -d evolution_db \
  -c "COPY (SELECT * FROM \"Instance\") TO STDOUT CSV HEADER;" \
  > instances.csv

# Export para JSON
psql -U migration_user -d evolution_db \
  -c "SELECT row_to_json(t) FROM \"Instance\" t;" \
  > instances.json
```

---

### Executar Script SQL

```bash
# Criar arquivo queries.sql
cat > queries.sql << 'EOF'
-- Query 1
SELECT COUNT(*) FROM "Instance";

-- Query 2
SELECT * FROM "Instance" ORDER BY "createdAt" DESC;
EOF

# Executar
psql -U migration_user -d evolution_db -f queries.sql
```

---

## 📊 Equivalência com REST API

### Query ↔ API Endpoint

| Query SQL | API Evolution |
|-----------|---|
| `SELECT * FROM "Instance"` | `GET /instance/fetchInstances` |
| `SELECT * FROM "Instance" WHERE name = ?` | `GET /instance/{instanceName}` |
| `INSERT INTO "Instance"` | `POST /instance/create` |
| `SELECT * FROM "Message"` | `GET /message/findMessages` |
| `INSERT INTO "Message"` | `POST /message/sendText` |

---

## ✅ Checklist de Validação

Execute essas queries para validar:

- [ ] Query 2: Banco existe?
- [ ] Query 4: Tabelas existem?
- [ ] Query 7: Permissões aplicadas?
- [ ] Query 11: Instâncias criadas?
- [ ] Query 16: Mensagens registradas?
- [ ] Query 19: Estatísticas OK?
- [ ] Query 23: Constraints intactas?
- [ ] Query 24: Validação completa OK?

---

## 📞 Referências

- [PostgreSQL Information Schema](https://www.postgresql.org/docs/current/information-schema.html)
- [PostgreSQL System Catalogs](https://www.postgresql.org/docs/current/catalogs.html)
- [Evolution API Documentation](https://doc.evolution-api.com/)
- [Prisma ORM Database](https://www.prisma.io/docs/concepts/database)

---

**Versão:** 1.0
**Data:** 2 de novembro de 2025
**Status:** Referência Completa
