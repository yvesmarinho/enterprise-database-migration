-- Script para adicionar coluna 'provider' que falta no auth_identity
-- Metabase v58 espera: provider, provider_id, user_id (tudo snake_case)
-- Execução: psql -h wfdb02.vya.digital -p 5432 -U migration_user -d metabase_db -f fix_metabase_provider_column.sql

\echo '=== Verificando estrutura atual auth_identity ==='
\d auth_identity

\echo ''
\echo '=== Adicionando coluna provider se não existir ==='

DO $$
BEGIN
    -- Verificar se coluna 'provider' existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'auth_identity'
                   AND column_name = 'provider') THEN

        -- Adicionar coluna provider (VARCHAR 255)
        ALTER TABLE auth_identity ADD COLUMN provider VARCHAR(255);
        RAISE NOTICE 'Coluna provider adicionada';

        -- Se provider_type existe, copiar valores para provider
        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'auth_identity'
                   AND column_name = 'provider_type') THEN
            UPDATE auth_identity SET provider = provider_type;
            RAISE NOTICE 'Valores copiados de provider_type para provider';
        END IF;

    ELSE
        RAISE NOTICE 'Coluna provider já existe';
    END IF;

    -- Remover constraint antiga com provider_id + provider_type se existir
    IF EXISTS (SELECT 1 FROM pg_constraint
               WHERE conname = 'auth_identity_pkey'
               AND conrelid = 'auth_identity'::regclass) THEN

        -- Ver constraint atual
        DECLARE
            constraint_def TEXT;
        BEGIN
            SELECT pg_get_constraintdef(oid) INTO constraint_def
            FROM pg_constraint
            WHERE conname = 'auth_identity_pkey';

            RAISE NOTICE 'Constraint atual: %', constraint_def;

            -- Se constraint usa provider_type, recriar com provider
            IF constraint_def LIKE '%provider_type%' THEN
                ALTER TABLE auth_identity DROP CONSTRAINT auth_identity_pkey;
                RAISE NOTICE 'Constraint antiga removida';
            END IF;
        END;
    END IF;

    -- Criar nova PRIMARY KEY: (provider_id, provider)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'auth_identity_pkey') THEN
        ALTER TABLE auth_identity
        ADD CONSTRAINT auth_identity_pkey
        PRIMARY KEY (provider_id, provider);
        RAISE NOTICE 'Nova PRIMARY KEY criada: (provider_id, provider)';
    END IF;

END $$;

\echo ''
\echo '=== Estrutura final auth_identity ==='
\d auth_identity

\echo ''
\echo '=== Constraints finais ==='
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'auth_identity'::regclass;

\echo ''
\echo '=== Dados de exemplo (primeiras 5 linhas) ==='
SELECT provider_id, provider, provider_type, user_id
FROM auth_identity
LIMIT 5;

\echo ''
\echo 'Schema corrigido! Reinicie o Metabase agora.'
