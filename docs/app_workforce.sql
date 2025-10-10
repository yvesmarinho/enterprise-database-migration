-- Database: app_workforce

-- DROP DATABASE IF EXISTS app_workforce;

CREATE DATABASE app_workforce
    WITH
    OWNER = root
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

GRANT TEMPORARY, CONNECT ON DATABASE app_workforce TO PUBLIC;

GRANT ALL ON DATABASE app_workforce TO app_workforce_user;

GRANT ALL ON DATABASE app_workforce TO root;

GRANT ALL ON DATABASE app_workforce TO testemigracao;
