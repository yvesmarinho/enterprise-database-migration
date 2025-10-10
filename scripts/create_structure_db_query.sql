
create user <nome do usuário> with encrypted password '<senha do usuário';


CREATE DATABASE <database_name> WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False
	TEMPLATE=template0;

GRANT TEMPORARY, CONNECT ON DATABASE <database_name> TO PUBLIC;
GRANT ALL PRIVILEGES ON DATABASE <database_name> TO <nome do usuário>;
