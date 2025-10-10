-- Database: botpress_db

-- DROP DATABASE IF EXISTS botpress_db;

CREATE DATABASE botpress_db
    WITH
    OWNER = root
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

GRANT TEMPORARY, CONNECT ON DATABASE botpress_db TO PUBLIC;

GRANT ALL ON DATABASE botpress_db TO botpress_user;

GRANT ALL ON DATABASE botpress_db TO root;
