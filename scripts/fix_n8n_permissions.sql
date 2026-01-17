-- ================================================================
-- Arquivo: fix_n8n_permissions.sql
-- Propósito: Corrigir permissões do usuário n8n_admin no banco n8n_db
-- Problema: Docker do n8n reportando que n8n_admin não tem permissão
--           para fazer alterações no banco n8n_db
--
-- Execução:
--   # Com senhas padrão
--   psql -U postgres -d postgres -f scripts/fix_n8n_permissions.sql
--
--   # Com senhas customizadas
--   psql -U postgres -d postgres \
--     -v n8n_admin_password='sua_senha_admin_aqui' \
--     -v n8n_user_password='sua_senha_user_aqui' \
--     -f scripts/fix_n8n_permissions.sql
-- ================================================================

-- Configurar valores padrão para senhas (se não fornecidas via -v)
\set n8n_admin_password :n8n_admin_password
\set n8n_user_password :n8n_user_password

-- Se as variáveis não foram definidas, usar valores padrão
SELECT COALESCE(:'n8n_admin_password', 'changeme_admin_n8n') AS tmp_admin_pwd \gset
SELECT COALESCE(:'n8n_user_password', 'changeme_user_n8n') AS tmp_user_pwd \gset

\echo '=========================================='
\echo 'Corrigindo permissões do n8n_admin'
\echo '=========================================='
\echo ''
\echo 'NOTA: Usando senhas das variáveis (ou padrões se não fornecidas)'
\echo ''

-- 1. Garantir que o usuário n8n_admin existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'n8n_admin') THEN
        RAISE NOTICE 'Criando usuário n8n_admin...';
        EXECUTE format('CREATE ROLE "n8n_admin" WITH LOGIN INHERIT PASSWORD %L', :'tmp_admin_pwd');
    ELSE
        RAISE NOTICE 'Usuário n8n_admin já existe';
        -- Atualizar senha caso usuário já exista
        EXECUTE format('ALTER ROLE "n8n_admin" WITH PASSWORD %L', :'tmp_admin_pwd');
        RAISE NOTICE 'Senha do n8n_admin atualizada';
    END IF;
END
$$;

-- 2. Adicionar privilégios necessários ao usuário n8n_admin
-- Concedendo CREATEDB para que ele possa criar objetos no banco
\echo ''
\echo 'Garantindo privilégios CREATEDB ao n8n_admin...'
ALTER ROLE "n8n_admin" WITH CREATEDB;

-- 3. Garantir que o banco n8n_db existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'n8n_db') THEN
        RAISE NOTICE 'Banco n8n_db não existe. Por favor, crie o banco primeiro!';
        RAISE EXCEPTION 'Banco n8n_db não encontrado';
    ELSE
        RAISE NOTICE 'Banco n8n_db encontrado';
    END IF;
END
$$;

-- 4. Alterar o OWNER do banco para n8n_admin
-- Isso dá controle total ao n8n_admin sobre o banco
\echo ''
\echo 'Alterando OWNER do banco n8n_db para n8n_admin...'
ALTER DATABASE "n8n_db" OWNER TO "n8n_admin";

-- 5. Garantir privilégios explícitos no nível de database
\echo ''
\echo 'Concedendo privilégios explícitos no banco n8n_db...'
GRANT ALL PRIVILEGES ON DATABASE "n8n_db" TO "n8n_admin";

-- 6. Conectar ao banco n8n_db e ajustar permissões no schema public
\echo ''
\echo 'Conectando ao banco n8n_db para ajustar permissões de schema...'
\c n8n_db

-- 7. Garantir que n8n_admin tem privilégios completos no schema public
\echo 'Concedendo ALL no schema public...'
GRANT ALL ON SCHEMA public TO "n8n_admin";

-- 8. Garantir privilégios em todas as tabelas existentes
\echo 'Concedendo ALL em todas as tabelas existentes...'
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "n8n_admin";

-- 9. Garantir privilégios em todas as sequences existentes
\echo 'Concedendo ALL em todas as sequences existentes...'
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "n8n_admin";

-- 10. Garantir privilégios em todas as funções existentes
\echo 'Concedendo EXECUTE em todas as funções existentes...'
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "n8n_admin";

-- 11. Configurar privilégios padrão para objetos futuros
\echo 'Configurando privilégios padrão para objetos futuros...'
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO "n8n_admin";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO "n8n_admin";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO "n8n_admin";

-- 12. Configurar n8n_user como usuário SOMENTE LEITURA (caso ele seja usado)
\echo ''
\echo 'Verificando e ajustando permissões do n8n_user (SOMENTE LEITURA)...'
DO $$
BEGIN
    -- Criar usuário n8n_user se não existir
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'n8n_user') THEN
        RAISE NOTICE 'Criando usuário n8n_user...';
        EXECUTE format('CREATE ROLE "n8n_user" WITH LOGIN INHERIT PASSWORD %L', :'tmp_user_pwd');
    ELSE
        RAISE NOTICE 'Usuário n8n_user já existe';
        -- Atualizar senha caso usuário já exista
        EXECUTE format('ALTER ROLE "n8n_user" WITH PASSWORD %L', :'tmp_user_pwd');
        RAISE NOTICE 'Senha do n8n_user atualizada';
    END IF;

    -- Conceder privilégios SOMENTE LEITURA
    RAISE NOTICE 'Concedendo privilégios SOMENTE LEITURA ao n8n_user...';
    -- Conceder USAGE no schema (necessário para acessar objetos)
    EXECUTE 'GRANT USAGE ON SCHEMA public TO "n8n_user"';
    -- Conceder SELECT em todas as tabelas (somente leitura)
    EXECUTE 'GRANT SELECT ON ALL TABLES IN SCHEMA public TO "n8n_user"';
    -- Conceder SELECT em todas as sequences (necessário para leitura de sequences)
    EXECUTE 'GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO "n8n_user"';
    -- Conceder EXECUTE em funções (somente se forem funções de leitura)
    EXECUTE 'GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "n8n_user"';

    -- Configurar default privileges para objetos futuros (SOMENTE LEITURA)
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "n8n_user"';
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO "n8n_user"';
    EXECUTE 'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO "n8n_user"';
END
$$;

-- 13. Voltar ao banco postgres
\c postgres

-- 14. Verificar as permissões aplicadas
\echo ''
\echo '=========================================='
\echo 'Verificação de Permissões'
\echo '=========================================='
\echo ''

\echo 'Privilégios do role n8n_admin:'
SELECT
    r.rolname,
    r.rolsuper AS superuser,
    r.rolinherit AS inherit,
    r.rolcreaterole AS createrole,
    r.rolcreatedb AS createdb,
    r.rolcanlogin AS canlogin,
    r.rolreplication AS replication,
    r.rolconnlimit AS connlimit
FROM pg_roles r
WHERE r.rolname = 'n8n_admin';

\echo ''
\echo 'Owner do banco n8n_db:'
SELECT
    d.datname AS database,
    pg_catalog.pg_get_userbyid(d.datdba) AS owner
FROM pg_database d
WHERE d.datname = 'n8n_db';

\echo ''
\echo 'Privilégios no banco n8n_db:'
SELECT
    grantee::regrole::text AS user,
    string_agg(privilege_type, ', ') AS privileges
FROM pg_database d,
     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
WHERE d.datname = 'n8n_db'
  AND grantee::regrole::text IN ('n8n_admin', 'n8n_user')
GROUP BY grantee
ORDER BY grantee;

\echo ''
\echo '=========================================='
\echo 'Correção Concluída!'
\echo '=========================================='
\echo ''
\echo 'USUÁRIOS CONFIGURADOS:'
\echo '  - n8n_admin: Administrador (leitura + escrita)'
\echo '  - n8n_user: Somente leitura (readonly)'
\echo ''
\echo '⚠️  IMPORTANTE - SENHAS:'
\echo '  Se você usou as senhas padrão, ALTERE-AS em produção!'
\echo '  Use: ALTER ROLE "n8n_admin" WITH PASSWORD ''nova_senha'';'
\echo ''
\echo 'PRÓXIMOS PASSOS:'
\echo '1. Reinicie o container do n8n Docker'
\echo '2. Verifique os logs do n8n para confirmar que não há mais erros de permissão'
\echo '3. Atualize a string de conexão do n8n para usar n8n_admin'
\echo '4. ALTERE as senhas padrão se foram usadas!'
\echo ''
