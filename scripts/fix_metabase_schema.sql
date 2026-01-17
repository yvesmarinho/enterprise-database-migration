-- Script para corrigir nomenclatura das colunas auth_identity
-- Tenta salvar dados existentes convertendo camelCase -> snake_case
-- Execução: psql -h wfdb02.vya.digital -p 5432 -U migration_user -d metabase_db -f fix_metabase_schema.sql

\echo 'Verificando estrutura atual...'

-- 1. Ver estrutura atual
\d auth_identity

-- 2. Renomear colunas se existirem (camelCase -> snake_case)
DO $$
BEGIN
    -- userId -> user_id
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'auth_identity' AND column_name = 'userId') THEN
        ALTER TABLE auth_identity RENAME COLUMN "userId" TO user_id;
        RAISE NOTICE 'Renomeado: userId -> user_id';
    END IF;

    -- providerId -> provider_id
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'auth_identity' AND column_name = 'providerId') THEN
        ALTER TABLE auth_identity RENAME COLUMN "providerId" TO provider_id;
        RAISE NOTICE 'Renomeado: providerId -> provider_id';
    END IF;

    -- providerType -> provider_type
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'auth_identity' AND column_name = 'providerType') THEN
        ALTER TABLE auth_identity RENAME COLUMN "providerType" TO provider_type;
        RAISE NOTICE 'Renomeado: providerType -> provider_type';
    END IF;

    -- createdAt -> created_at
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'auth_identity' AND column_name = 'createdAt') THEN
        ALTER TABLE auth_identity RENAME COLUMN "createdAt" TO created_at;
        RAISE NOTICE 'Renomeado: createdAt -> created_at';
    END IF;

    -- updatedAt -> updated_at
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'auth_identity' AND column_name = 'updatedAt') THEN
        ALTER TABLE auth_identity RENAME COLUMN "updatedAt" TO updated_at;
        RAISE NOTICE 'Renomeado: updatedAt -> updated_at';
    END IF;

    RAISE NOTICE 'Renomeação concluída!';
END $$;

-- 3. Verificar nova estrutura
\echo 'Nova estrutura:'
\d auth_identity

-- 4. Verificar constraint (deve ser provider_id, provider_type agora)
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'auth_identity'::regclass;

\echo 'Schema corrigido! Reinicie o Metabase agora.'
