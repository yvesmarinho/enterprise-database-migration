-- ==============================================================================
-- Corrige o checksum da migração v58.2025-11-12T00:00:02 no changelog Liquibase
-- ==============================================================================
-- Problema: MD5 manual não corresponde ao MD5 real do arquivo de migração
-- Causa: Registro inserido manualmente com checksum '9:manual_fix_fk_already_exists'
-- Correto: '9:c195d03033b54181e3bf4d8071950414' (do arquivo original)
-- ==============================================================================

\set ON_ERROR_STOP on
\timing on

BEGIN;

-- Atualizar o checksum para corresponder ao arquivo de migração original
UPDATE databasechangelog
SET
    md5sum = '9:c195d03033b54181e3bf4d8071950414',
    comments = 'FK manually created via fix_auth_identity_final.sql - checksum corrected'
WHERE
    id = 'v58.2025-11-12T00:00:02'
    AND author = 'edpaget'
    AND filename = 'migrations/058_update_migrations.yaml';

-- Verificar a atualização
SELECT
    id,
    author,
    filename,
    md5sum,
    exectype,
    comments
FROM databasechangelog
WHERE id = 'v58.2025-11-12T00:00:02'
  AND author = 'edpaget';

COMMIT;

\echo ''
\echo '✅ Checksum corrigido com sucesso!'
\echo 'Reinicie o Metabase: docker-compose restart dashboard'
