-- ================================================================
-- Arquivo: create_n8n_read_user.sql
-- Propósito: Criar usuário n8n_read_user com permissões SOMENTE LEITURA
--           no banco n8n_db
--
-- Uso: Este usuário é ideal para:
--   - Aplicações que precisam apenas consultar dados do n8n
--   - Dashboards e relatórios
--   - Ferramentas de monitoramento
--   - Backups e auditorias
--
-- Execução:
--   # Com senha padrão
--   psql -U postgres -d postgres -f scripts/create_n8n_read_user.sql
--
--   # Com senha customizada
--   psql -U postgres -d postgres \
--     -v n8n_read_password='sua_senha_segura_aqui' \
--     -f scripts/create_n8n_read_user.sql
-- ================================================================

-- Configurar valores padrão para senha (se não fornecida via -v)
\set n8n_read_password :n8n_read_password

-- Se a variável não foi definida, usar valor padrão
SELECT COALESCE(:'n8n_read_password', 'changeme_read_n8n') AS tmp_read_pwd \gset

\echo '=========================================='
\echo 'Criando usuário n8n_read_user (SOMENTE LEITURA)'
\echo '=========================================='
\echo ''
\echo 'NOTA: Usando senha da variável (ou padrão se não fornecida)'
\echo ''

-- 1. Garantir que o banco n8n_db existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'n8n_db') THEN
        RAISE EXCEPTION 'Banco n8n_db não encontrado. Crie o banco primeiro!';
    ELSE
        RAISE NOTICE 'Banco n8n_db encontrado';
    END IF;
END
$$;

-- 2. Criar ou atualizar o usuário n8n_read_user usando SQL dinâmico
\echo ''
\echo 'Criando/atualizando usuário n8n_read_user...'

-- Verificar se o usuário existe e criar o comando apropriado
SELECT CASE
    WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'n8n_read_user')
    THEN format('ALTER ROLE "n8n_read_user" WITH PASSWORD %L; -- Usuário já existe, atualizando senha', :'tmp_read_pwd')
    ELSE format('CREATE ROLE "n8n_read_user" WITH LOGIN PASSWORD %L; -- Criando novo usuário', :'tmp_read_pwd')
END AS create_user_sql \gset

-- Executar o comando SQL gerado
\echo :create_user_sql
:create_user_sql

-- 3. Garantir que o usuário NÃO tem privilégios elevados
\echo ''
\echo 'Removendo privilégios elevados (se houver)...'
ALTER ROLE "n8n_read_user" WITH
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    NOINHERIT;

-- 4. Conceder privilégio de conexão no banco n8n_db
\echo ''
\echo 'Concedendo privilégio de conexão ao banco n8n_db...'
GRANT CONNECT ON DATABASE "n8n_db" TO "n8n_read_user";

-- 5. Conectar ao banco n8n_db para aplicar permissões de schema
\echo ''
\echo 'Conectando ao banco n8n_db...'
\c n8n_db

-- 6. Conceder USAGE no schema public (necessário para acessar objetos)
\echo 'Concedendo USAGE no schema public...'
GRANT USAGE ON SCHEMA public TO "n8n_read_user";

-- 7. Conceder SELECT em todas as tabelas existentes (somente leitura)
\echo 'Concedendo SELECT em todas as tabelas existentes...'
GRANT SELECT ON ALL TABLES IN SCHEMA public TO "n8n_read_user";

-- 8. Conceder SELECT em todas as sequences existentes
\echo 'Concedendo SELECT em todas as sequences existentes...'
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO "n8n_read_user";

-- 9. Conceder EXECUTE apenas em funções de leitura (se necessário)
\echo 'Concedendo EXECUTE em funções públicas...'
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "n8n_read_user";

-- 10. Configurar privilégios padrão para objetos futuros (SOMENTE LEITURA)
\echo ''
\echo 'Configurando privilégios padrão para objetos futuros...'
\echo 'Isto garante que novas tabelas também terão permissão de leitura...'

-- Para objetos criados pelo owner do banco
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO "n8n_read_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON SEQUENCES TO "n8n_read_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO "n8n_read_user";

-- Para objetos criados por n8n_admin (se existir)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'n8n_admin') THEN
        RAISE NOTICE 'Configurando default privileges para objetos criados por n8n_admin...';
        EXECUTE 'ALTER DEFAULT PRIVILEGES FOR ROLE "n8n_admin" IN SCHEMA public GRANT SELECT ON TABLES TO "n8n_read_user"';
        EXECUTE 'ALTER DEFAULT PRIVILEGES FOR ROLE "n8n_admin" IN SCHEMA public GRANT SELECT ON SEQUENCES TO "n8n_read_user"';
        EXECUTE 'ALTER DEFAULT PRIVILEGES FOR ROLE "n8n_admin" IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO "n8n_read_user"';
    END IF;
END
$$;

-- 11. Voltar ao banco postgres
\c postgres

-- 12. Verificar as permissões aplicadas
\echo ''
\echo '=========================================='
\echo 'Verificação de Permissões'
\echo '=========================================='
\echo ''

\echo 'Privilégios do role n8n_read_user:'
SELECT
    r.rolname AS "Usuário",
    r.rolsuper AS "Superuser",
    r.rolinherit AS "Inherit",
    r.rolcreaterole AS "Create Role",
    r.rolcreatedb AS "Create DB",
    r.rolcanlogin AS "Can Login",
    r.rolreplication AS "Replication",
    r.rolconnlimit AS "Conn Limit"
FROM pg_roles r
WHERE r.rolname = 'n8n_read_user';

\echo ''
\echo 'Privilégios de conexão no banco n8n_db:'
SELECT
    datname AS "Banco",
    has_database_privilege('n8n_read_user', datname, 'CONNECT') AS "Pode Conectar"
FROM pg_database
WHERE datname = 'n8n_db';

-- Conectar ao n8n_db para verificar privilégios de schema e tabelas
\c n8n_db

\echo ''
\echo 'Privilégios no schema public:'
SELECT
    'n8n_read_user' AS "Usuário",
    has_schema_privilege('n8n_read_user', 'public', 'USAGE') AS "USAGE no Schema"
;

\echo ''
\echo 'Exemplo de privilégios em tabelas (primeiras 5 tabelas):'
SELECT
    schemaname AS "Schema",
    tablename AS "Tabela",
    has_table_privilege('n8n_read_user', schemaname||'.'||tablename, 'SELECT') AS "SELECT",
    has_table_privilege('n8n_read_user', schemaname||'.'||tablename, 'INSERT') AS "INSERT",
    has_table_privilege('n8n_read_user', schemaname||'.'||tablename, 'UPDATE') AS "UPDATE",
    has_table_privilege('n8n_read_user', schemaname||'.'||tablename, 'DELETE') AS "DELETE"
FROM pg_tables
WHERE schemaname = 'public'
LIMIT 5;

\c postgres

\echo ''
\echo '=========================================='
\echo 'Criação Concluída com Sucesso!'
\echo '=========================================='
\echo ''
\echo 'USUÁRIO CONFIGURADO:'
\echo '  - n8n_read_user: SOMENTE LEITURA (read-only)'
\echo ''
\echo 'PERMISSÕES CONCEDIDAS:'
\echo '  ✓ CONNECT no banco n8n_db'
\echo '  ✓ USAGE no schema public'
\echo '  ✓ SELECT em todas as tabelas'
\echo '  ✓ SELECT em todas as sequences'
\echo '  ✓ EXECUTE em todas as funções'
\echo '  ✓ Privilégios automáticos para objetos futuros'
\echo ''
\echo 'PERMISSÕES NEGADAS:'
\echo '  ✗ INSERT, UPDATE, DELETE em tabelas'
\echo '  ✗ CREATE, DROP de objetos'
\echo '  ✗ Alteração de estruturas'
\echo '  ✗ Privilégios de administração'
\echo ''
\echo '⚠️  IMPORTANTE - SEGURANÇA:'
\echo '  1. Se você usou a senha padrão, ALTERE-A imediatamente!'
\echo '     ALTER ROLE "n8n_read_user" WITH PASSWORD ''sua_senha_forte'';'
\echo ''
\echo '  2. Use uma senha forte com pelo menos:'
\echo '     - 12+ caracteres'
\echo '     - Letras maiúsculas e minúsculas'
\echo '     - Números e símbolos'
\echo ''
\echo 'STRING DE CONEXÃO:'
\echo '  postgresql://n8n_read_user:sua_senha@host:5432/n8n_db'
\echo ''
\echo 'TESTE DE CONEXÃO:'
\echo '  psql -U n8n_read_user -d n8n_db -h localhost'
\echo ''
\echo 'PARA TESTAR PERMISSÕES:'
\echo '  psql -U n8n_read_user -d n8n_db -c "SELECT count(*) FROM pg_tables WHERE schemaname='"'"'public'"'"';"'
\echo ''
