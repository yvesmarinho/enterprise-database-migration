-- ================================================================
-- Arquivo: 03b_apply_grants_n8n_readonly.sql
-- Propósito: Complemento ao script de grants - ajusta n8n_user como readonly
-- IMPORTANTE: Executar APÓS 03_apply_grants.sql
-- ================================================================

\echo '=========================================='
\echo 'Ajustando grants do n8n_user para READONLY'
\echo '=========================================='
\echo ''

-- 1. Revogar permissões de escrita do n8n_user (caso tenham sido concedidas)
\echo 'Revogando permissões de escrita do n8n_user...'
REVOKE CREATE, TEMPORARY ON DATABASE "n8n_db" FROM "n8n_user";

-- 2. Garantir que n8n_user tenha apenas CONNECT
\echo 'Garantindo apenas CONNECT para n8n_user...'
GRANT CONNECT ON DATABASE "n8n_db" TO "n8n_user";

-- 3. Conectar ao banco n8n_db para ajustar permissões de schema
\echo ''
\echo 'Conectando ao banco n8n_db...'
\c n8n_db

-- 4. Conceder USAGE no schema public (necessário para leitura)
\echo 'Concedendo USAGE no schema public...'
GRANT USAGE ON SCHEMA public TO "n8n_user";

-- 5. Conceder SELECT em todas as tabelas (somente leitura)
\echo 'Concedendo SELECT em todas as tabelas...'
GRANT SELECT ON ALL TABLES IN SCHEMA public TO "n8n_user";

-- 6. Conceder SELECT em todas as sequences
\echo 'Concedendo SELECT em todas as sequences...'
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO "n8n_user";

-- 7. Conceder EXECUTE em funções (se necessário para leitura)
\echo 'Concedendo EXECUTE em funções...'
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO "n8n_user";

-- 8. Configurar default privileges para objetos futuros (SOMENTE LEITURA)
\echo ''
\echo 'Configurando default privileges (READONLY)...'
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO "n8n_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON SEQUENCES TO "n8n_user";

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO "n8n_user";

-- 9. Voltar ao banco postgres
\c postgres

-- 10. Verificar permissões aplicadas
\echo ''
\echo '=========================================='
\echo 'Verificação de Permissões'
\echo '=========================================='
\echo ''

\echo 'Permissões do n8n_user no banco n8n_db:'
SELECT
    grantee::regrole::text AS user,
    string_agg(privilege_type, ', ') AS privileges
FROM pg_database d,
     aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
WHERE d.datname = 'n8n_db'
  AND grantee::regrole::text = 'n8n_user'
GROUP BY grantee;

\echo ''
\echo '=========================================='
\echo 'Ajuste Concluído!'
\echo '=========================================='
\echo ''
\echo 'O usuário n8n_user agora tem:'
\echo '  ✅ CONNECT no database'
\echo '  ✅ USAGE no schema public'
\echo '  ✅ SELECT em todas as tabelas (somente leitura)'
\echo '  ✅ SELECT em sequences'
\echo '  ✅ EXECUTE em funções'
\echo '  ❌ Sem permissões de escrita (CREATE, INSERT, UPDATE, DELETE)'
\echo ''
