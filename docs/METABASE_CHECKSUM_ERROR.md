# Documentação: Erro de Checksum no Metabase v0.58.1

## 📋 Resumo do Erro

**Erro:** `ValidationFailedException: Validation Failed: 1 changesets check sum`
**Migração:** `migrations/058_update_migrations.yaml::v58.2025-11-12T00:00:02::edpaget`
**Data:** 2026-01-16 21:31:00

## 🔍 Análise do Problema

### Causa Raiz
A migração foi marcada manualmente como executada no `databasechangelog` com um MD5 checksum personalizado (`9:manual_fix_fk_already_exists`), mas o Liquibase esperava o checksum original do arquivo de migração (`9:c195d03033b54181e3bf4d8071950414`).

### Sequência de Eventos

1. **Problema Original:** Tabela `auth_identity` criada com `user_id UUID` ao invés de `INTEGER`
2. **Primeira Correção:** Script `fix_auth_identity_final.sql` recriou a tabela com tipo correto
3. **Segunda Correção:** FK `fk_auth_identity_core_user_id` já existia (criada pelo script)
4. **Terceira Correção:** Marcamos migração como executada, mas com checksum incorreto
5. **Erro Atual:** Liquibase rejeitou o checksum personalizado

### Log do Erro

```
liquibase.exception.ValidationFailedException: Validation Failed:
     1 changesets check sum
          migrations/058_update_migrations.yaml::v58.2025-11-12T00:00:02::edpaget
          was: 9:manual
          but is now: 9:c195d03033b54181e3bf4d8071950414
```

## ✅ Solução Implementada

### Script de Correção
**Arquivo:** `scripts/fix_migration_checksum.sql`

```sql
UPDATE databasechangelog
SET
    md5sum = '9:c195d03033b54181e3bf4d8071950414',
    comments = 'FK manually created via fix_auth_identity_final.sql - checksum corrected'
WHERE
    id = 'v58.2025-11-12T00:00:02'
    AND author = 'edpaget'
    AND filename = 'migrations/058_update_migrations.yaml';
```

### Execução
```bash
psql -h wfdb02.vya.digital -U yves_marinho -d metabase_db \
  -f scripts/fix_migration_checksum.sql
```

## 📊 Estado do Banco

### Constraint Verificada
```sql
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conname = 'fk_auth_identity_core_user_id';
```

**Resultado:**
```
constraint_name: fk_auth_identity_core_user_id
definition: FOREIGN KEY (user_id) REFERENCES core_user(id) ON DELETE CASCADE
```

### Propriedade da Tabela
```sql
SELECT tablename, tableowner FROM pg_tables WHERE tablename = 'auth_identity';
```

**Resultado:**
```
tablename: auth_identity
tableowner: metabase_user
```

### Tipo da Coluna
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'auth_identity' AND column_name = 'user_id';
```

**Resultado:**
```
column_name: user_id
data_type: integer
```

## 🔄 Próximos Passos

1. **Executar correção de checksum:**
   ```bash
   psql -h wfdb02.vya.digital -U yves_marinho -d metabase_db \
     -f scripts/fix_migration_checksum.sql
   ```

2. **Reiniciar Metabase:**
   ```bash
   docker-compose restart dashboard
   ```

3. **Monitorar logs:**
   ```bash
   docker-compose logs -f dashboard | grep -E "(Migration|ERROR|SUCCESS)"
   ```

4. **Verificar migrações pendentes:**
   - Total esperado: 37 migrações restantes (38 - 1 já executada)
   - Status esperado: Todas devem completar sem erros

## 📝 Histórico de Correções

### 1. fix_auth_identity_final.sql
- Recriou tabela com `user_id INTEGER`
- Adicionou FK `fk_auth_identity_core_user_id`
- Criou 3 índices
- ✅ Sucesso

### 2. ALTER TABLE ... OWNER TO metabase_user
- Transferiu propriedade para usuário correto
- ✅ Sucesso

### 3. mark_fk_migration_as_executed.sql
- Inseriu registro no `databasechangelog`
- ❌ Checksum incorreto: `9:manual_fix_fk_already_exists`

### 4. fix_migration_checksum.sql (atual)
- Atualiza checksum para: `9:c195d03033b54181e3bf4d8071950414`
- ⏳ Pendente execução

## ⚠️ Lições Aprendidas

1. **Checksums são obrigatórios:** Liquibase valida integridade via MD5
2. **Use valores reais:** Copiar checksum do arquivo original, não inventar
3. **Alternativa:** Usar `validCheckSum` ou desabilitar validação (não recomendado)
4. **Documentação:** Registrar motivo em `comments` para auditoria futura

## 🔗 Referências

- **Migração original:** `metabase-core/migrations/058_update_migrations.yaml`
- **Changeset ID:** `v58.2025-11-12T00:00:02`
- **Autor:** `edpaget`
- **Descrição:** `addForeignKeyConstraint` para `auth_identity.user_id`
