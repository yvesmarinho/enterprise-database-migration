-- Script para recriar Metabase Database limpo
-- Execução: psql -h wfdb02.vya.digital -p 5432 -U migration_user -d postgres -f recreate_metabase_clean.sql

-- Terminar conexões ativas
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'metabase_db'
  AND pid <> pg_backend_pid();

-- Drop e recriar database
DROP DATABASE IF EXISTS metabase_db;
CREATE DATABASE metabase_db
  WITH OWNER = metabase_user
       ENCODING = 'UTF8'
       TABLESPACE = ts_enterprise_data
       LC_COLLATE = 'en_US.UTF-8'
       LC_CTYPE = 'en_US.UTF-8'
       CONNECTION LIMIT = -1;

-- Conectar ao novo banco e configurar permissões
\c metabase_db

-- Garantir permissões completas
GRANT ALL PRIVILEGES ON DATABASE metabase_db TO metabase_user WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON SCHEMA public TO metabase_user WITH GRANT OPTION;

-- Permissões padrão para objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON TABLES TO metabase_user WITH GRANT OPTION;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON SEQUENCES TO metabase_user WITH GRANT OPTION;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT ALL ON FUNCTIONS TO metabase_user WITH GRANT OPTION;

-- Verificação
SELECT
  current_database() as database,
  current_user as current_user,
  pg_database.datdba::regrole as owner,
  pg_size_pretty(pg_database_size(current_database())) as size
FROM pg_database
WHERE datname = current_database();

\echo 'Metabase database recriado com sucesso!'
