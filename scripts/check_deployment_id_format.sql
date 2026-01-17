-- ==============================================================================
-- Verifica o formato correto da coluna deployment_id na tabela databasechangelog
-- ==============================================================================

\set ON_ERROR_STOP on
\timing on

-- Ver estrutura da coluna deployment_id
SELECT
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'databasechangelog'
  AND column_name = 'deployment_id';

\echo ''
\echo '=== Exemplos de deployment_id existentes ==='

-- Ver exemplos de deployment_id reais no banco
SELECT DISTINCT
    deployment_id,
    LENGTH(deployment_id) as len,
    orderexecuted,
    dateexecuted
FROM databasechangelog
WHERE deployment_id IS NOT NULL
ORDER BY orderexecuted DESC
LIMIT 10;
