-- Script para corrigir incompatibilidade de tipo: user_id (UUID) -> INTEGER
-- Metabase v58 espera user_id como INTEGER referenciando core_user.id
-- Execução: psql -h wfdb02.vya.digital -p 5432 -U migration_user -d metabase_db -f fix_user_id_type_mismatch.sql

\echo '=== 1. Verificando tipos atuais ==='
SELECT
    'auth_identity' as tabela,
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_name = 'auth_identity'
AND column_name = 'user_id';

SELECT
    'core_user' as tabela,
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_name = 'core_user'
AND column_name = 'id';

\echo ''
\echo '=== 2. Dados de exemplo antes da conversão ==='
SELECT user_id, provider_id, provider_type, created_at
FROM auth_identity
LIMIT 5;

\echo ''
\echo '=== 3. CONVERTENDO user_id de UUID para INTEGER ==='

-- Fazer backup dos dados
CREATE TEMP TABLE auth_identity_backup AS
SELECT * FROM auth_identity;

\echo 'Backup criado em tabela temporária'

-- Remover constraints existentes que referenciam user_id
DO $$
DECLARE
    constraint_rec RECORD;
BEGIN
    FOR constraint_rec IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'auth_identity'::regclass
        AND conname LIKE '%user%'
    LOOP
        EXECUTE 'ALTER TABLE auth_identity DROP CONSTRAINT IF EXISTS ' || quote_ident(constraint_rec.conname);
        RAISE NOTICE 'Constraint removida: %', constraint_rec.conname;
    END LOOP;
END $$;

-- Dropar coluna user_id (UUID)
ALTER TABLE auth_identity DROP COLUMN IF EXISTS user_id CASCADE;
\echo 'Coluna user_id (UUID) removida'

-- Adicionar coluna user_id (INTEGER)
ALTER TABLE auth_identity ADD COLUMN user_id INTEGER;
\echo 'Coluna user_id (INTEGER) adicionada'

-- Restaurar dados convertendo UUID para INTEGER através do core_user
UPDATE auth_identity
SET user_id = (
    SELECT id::INTEGER
    FROM core_user
    WHERE core_user.id::TEXT = auth_identity_backup.user_id::TEXT
    LIMIT 1
)
FROM auth_identity_backup
WHERE auth_identity.provider_id = auth_identity_backup.provider_id
AND auth_identity.provider_type = auth_identity_backup.provider_type;

\echo 'Dados restaurados com conversão UUID->INTEGER'

\echo ''
\echo '=== 4. Verificando resultado ==='
SELECT user_id, provider_id, provider_type, created_at
FROM auth_identity
LIMIT 5;

\echo ''
\echo '=== 5. Verificando tipos finais ==='
SELECT
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_name = 'auth_identity'
AND column_name = 'user_id';

\echo ''
\echo '✅ Conversão concluída! Reinicie o Metabase para continuar as migrações.'
