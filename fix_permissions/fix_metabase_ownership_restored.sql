-- ================================================================
-- Script para corrigir ownership e permissões do Metabase
-- Após restauração do backup
-- Data: 2026-01-16
-- ================================================================

\c metabase_db;

-- 1. Transferir ownership de todas as tabelas
DO $$
DECLARE
    tbl RECORD;
BEGIN
    FOR tbl IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE public.%I OWNER TO metabase_user;', tbl.tablename);
        RAISE NOTICE 'Tabela % transferida para metabase_user', tbl.tablename;
    END LOOP;
END $$;

-- 2. Transferir ownership de sequências
DO $$
DECLARE
    seq RECORD;
BEGIN
    FOR seq IN
        SELECT sequencename
        FROM pg_sequences
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER SEQUENCE public.%I OWNER TO metabase_user;', seq.sequencename);
        RAISE NOTICE 'Sequência % transferida para metabase_user', seq.sequencename;
    END LOOP;
END $$;

-- 3. Transferir ownership de views (se existirem)
DO $$
DECLARE
    v RECORD;
BEGIN
    FOR v IN
        SELECT viewname
        FROM pg_views
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER VIEW public.%I OWNER TO metabase_user;', v.viewname);
        RAISE NOTICE 'View % transferida para metabase_user', v.viewname;
    END LOOP;
END $$;

-- 4. Garantir privilégios completos no schema public
GRANT ALL ON SCHEMA public TO metabase_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO metabase_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO metabase_user;

-- 5. Configurar privilégios default para objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES TO metabase_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO metabase_user;

-- 6. Verificar resultado
\echo ''
\echo '=== VERIFICAÇÃO DE OWNERSHIP ==='
SELECT
    tableowner,
    COUNT(*) as quantidade
FROM pg_tables
WHERE schemaname = 'public'
GROUP BY tableowner
ORDER BY tableowner;

\echo ''
\echo '=== VERIFICAÇÃO DE PRIVILÉGIOS ==='
SELECT
    grantee,
    COUNT(DISTINCT table_name) as tabelas_com_acesso
FROM information_schema.table_privileges
WHERE table_schema = 'public'
AND grantee = 'metabase_user'
GROUP BY grantee;

\echo ''
\echo '✓ Ownership e privilégios corrigidos!'
\echo 'Todas as tabelas agora pertencem a metabase_user'
