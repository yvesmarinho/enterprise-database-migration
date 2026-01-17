-- ==============================================================================
-- Marca a migração v58.2025-11-12T00:00:02 como executada no Liquibase
-- ==============================================================================
-- Motivo: A FK fk_auth_identity_core_user_id já foi criada manualmente via
--         fix_auth_identity_final.sql para resolver o problema de tipo UUID/INTEGER
--
-- Objetivo: Evitar erro "constraint already exists" na próxima execução do Metabase
-- ==============================================================================

\set ON_ERROR_STOP on
\timing on

BEGIN;

-- Inserir registro no changelog do Liquibase apenas se não existir
INSERT INTO databasechangelog (
    id,
    author,
    filename,
    dateexecuted,
    orderexecuted,
    exectype,
    md5sum,
    description,
    comments,
    tag,
    liquibase,
    contexts,
    labels,
    deployment_id
)
SELECT
    'v58.2025-11-12T00:00:02',
    'edpaget',
    'migrations/058_update_migrations.yaml',
    NOW(),
    (SELECT COALESCE(MAX(orderexecuted), 0) + 1 FROM databasechangelog),
    'EXECUTED',
    '9:manual_fix_fk_already_exists',
    'addForeignKeyConstraint constraintName=fk_auth_identity_core_user_id, baseColumnNames=user_id, baseTableName=auth_identity, referencedColumnNames=id, referencedTableName=core_user',
    'FK manually created via fix_auth_identity_final.sql - bypassing duplicate constraint error',
    NULL,
    '4.27.0',
    NULL,
    NULL,
    CAST(FLOOR(EXTRACT(EPOCH FROM NOW())) AS TEXT)
WHERE NOT EXISTS (
    SELECT 1
    FROM databasechangelog
    WHERE id = 'v58.2025-11-12T00:00:02'
      AND author = 'edpaget'
      AND filename = 'migrations/058_update_migrations.yaml'
);

-- Verificar se a inserção foi bem-sucedida
DO $$
BEGIN
    IF FOUND THEN
        RAISE NOTICE '✅ Migração marcada como executada no changelog';
    ELSE
        RAISE NOTICE '⚠️  Migração já estava marcada como executada';
    END IF;
END $$;

-- Mostrar o registro inserido
SELECT
    id,
    author,
    filename,
    dateexecuted,
    orderexecuted,
    exectype,
    description
FROM databasechangelog
WHERE id = 'v58.2025-11-12T00:00:02'
  AND author = 'edpaget'
  AND filename = 'migrations/058_update_migrations.yaml';

COMMIT;

\echo '✅ Script executado com sucesso!'
