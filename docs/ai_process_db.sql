-- Database: ai_process_db

-- DROP DATABASE IF EXISTS ai_process_db;

CREATE DATABASE ai_process_db
    WITH
    OWNER = root
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

COMMENT ON DATABASE ai_process_db
    IS 'Utilizado no Flowise';
