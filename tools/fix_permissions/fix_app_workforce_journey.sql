-- Script de Correção de Permissões - app_workforce (WF008)
-- Base de dados: app_workforce
-- Usuário principal: journey_system
-- Data: 2026-02-17

-- =====================================================================
-- PARTE 1: Concessão de privilégios no banco de dados
-- =====================================================================

GRANT CONNECT ON DATABASE app_workforce TO journey_system;
GRANT CREATE ON DATABASE app_workforce TO journey_system;
GRANT TEMPORARY ON DATABASE app_workforce TO journey_system;

-- =====================================================================
-- PARTE 2: Concessão de privilégios no schema
-- =====================================================================

GRANT USAGE ON SCHEMA public TO journey_system;
GRANT CREATE ON SCHEMA public TO journey_system;

-- =====================================================================
-- PARTE 3: Concessão de privilégios em todas as tabelas existentes
-- =====================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO journey_system;

-- =====================================================================
-- PARTE 4: Concessão de privilégios em todas as sequências
-- =====================================================================

GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO journey_system;

-- =====================================================================
-- PARTE 5: Configuração de privilégios padrão para objetos futuros
-- =====================================================================

-- Privilégios padrão para tabelas criadas no futuro
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO journey_system;

-- Privilégios padrão para sequências criadas no futuro
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO journey_system;

-- =====================================================================
-- PARTE 6: Verificação de permissões concedidas
-- =====================================================================

print '\n=== Verificando Privilégios do Usuário journey_system ===\n';

-- Verificar privilégios no schema
SELECT
    schemaname,
    has_schema_privilege('journey_system', schemaname, 'USAGE') as "USAGE",
    has_schema_privilege('journey_system', schemaname, 'CREATE') as "CREATE"
FROM pg_namespace
WHERE schemaname = 'public';

-- Verificar privilégios em tabelas
SELECT
    count(*) as total_tables,
    sum(CASE WHEN has_table_privilege('journey_system', schemaname||'.'||tablename, 'SELECT') THEN 1 ELSE 0 END) as can_select,
    sum(CASE WHEN has_table_privilege('journey_system', schemaname||'.'||tablename, 'INSERT') THEN 1 ELSE 0 END) as can_insert,
    sum(CASE WHEN has_table_privilege('journey_system', schemaname||'.'||tablename, 'UPDATE') THEN 1 ELSE 0 END) as can_update,
    sum(CASE WHEN has_table_privilege('journey_system', schemaname||'.'||tablename, 'DELETE') THEN 1 ELSE 0 END) as can_delete
FROM pg_tables
WHERE schemaname = 'public';

-- Verificação de privilégios em sequências
SELECT
    count(*) as total_sequences,
    sum(CASE WHEN has_sequence_privilege('journey_system', schemaname||'.'||sequencename, 'USAGE') THEN 1 ELSE 0 END) as can_usage,
    sum(CASE WHEN has_sequence_privilege('journey_system', schemaname||'.'||sequencename, 'SELECT') THEN 1 ELSE 0 END) as can_select,
    sum(CASE WHEN has_sequence_privilege('journey_system', schemaname||'.'||sequencename, 'UPDATE') THEN 1 ELSE 0 END) as can_update
FROM pg_sequences
WHERE schemaname = 'public';
