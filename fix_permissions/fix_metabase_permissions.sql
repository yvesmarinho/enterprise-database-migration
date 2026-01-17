-- ============================================================================
-- FIX METABASE PERMISSIONS
-- ============================================================================

\echo '==============================================================='
\echo 'Corrigindo permissões do metabase_user no banco metabase_db'
\echo '==============================================================='

-- 1. Tornar metabase_user o OWNER do banco
\echo ''
\echo '1. Transferindo ownership do banco para metabase_user...'
ALTER DATABASE "metabase_db" OWNER TO "metabase_user";

-- 2. Conceder TODOS os privilégios no banco
\echo '2. Concedendo privilégios no database...'
GRANT ALL PRIVILEGES ON DATABASE "metabase_db" TO "metabase_user";

-- Conectar ao banco para configurar permissões internas
\c metabase_db

-- 3. Privilégios no schema public
\echo '3. Concedendo privilégios no schema public...'
GRANT ALL ON SCHEMA public TO "metabase_user";

-- 4. Transferir ownership de TODAS as tabelas
\echo '4. Transferindo ownership de todas as tabelas...'
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER TABLE public.%I OWNER TO metabase_user', r.tablename);
        RAISE NOTICE 'Ownership de % transferido', r.tablename;
    END LOOP;
END $$;

-- 5. Transferir ownership de sequences
\echo '5. Transferindo ownership de sequences...'
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT sequencename
        FROM pg_sequences
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('ALTER SEQUENCE public.%I OWNER TO metabase_user', r.sequencename);
        RAISE NOTICE 'Ownership de sequence % transferido', r.sequencename;
    END LOOP;
END $$;

-- 6. Privilégios em objetos existentes
\echo '6. Concedendo privilégios em objetos existentes...'
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "metabase_user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "metabase_user";
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "metabase_user";

-- 7. DEFAULT PRIVILEGES para objetos futuros
\echo '7. Configurando DEFAULT PRIVILEGES para objetos futuros...'
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO "metabase_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO "metabase_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO "metabase_user";

-- 8. Verificações
\echo ''
\echo '==============================================================='
\echo 'VERIFICAÇÕES:'
\echo '==============================================================='

\echo ''
\echo 'Owner do banco:'
SELECT datname, pg_catalog.pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'metabase_db';

\echo ''
\echo 'Owner da tabela auth_identity:'
SELECT tableowner
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'auth_identity';

\echo ''
\echo 'Permissões de CREATE INDEX:'
SELECT has_table_privilege('metabase_user', 'auth_identity', 'REFERENCES');

\echo ''
\echo '==============================================================='
\echo 'Correção concluída!'
\echo 'Reinicie o Metabase: docker-compose restart dashboard'
\echo '==============================================================='
