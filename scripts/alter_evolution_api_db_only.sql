-- ================================================================
-- Arquivo: alter_evolution_api_db_only.sql
-- Propósito: Alterar configurações e privilégios apenas no database
--            "evolution_api_db" de forma idempotente e segura.
-- Execução:
--  - Conectar como superuser (ex: psql -U postgres -d postgres)
--  - Executar este arquivo
-- ================================================================

/*
.. function:: alter_evolution_api_db() -> boolean

   Altera configurações e privilégios do database "evolution_api_db".

   Retorna True em sucesso e False em erro.

   - Verifica existência do database.
   - Ajusta OWNER para 'postgres' se necessário.
   - Ajusta TABLESPACE para 'ts_enterprise_data' se diferente.
   - Ajusta CONNECTION LIMIT para -1.
   - Revoga ALL do PUBLIC sobre o database.
   - Concede CONNECT ao role 'analytics' (se existir), 'evolution_api_user', 'evoluton_api_user'.
   - Concede ALL PRIVILEGES ao superuser 'postgres'.

   :returns: boolean

   Example:
   >>> -- conectar como superuser e executar:
   >>> SELECT alter_evolution_api_db();
   -- retorna true em sucesso

*/
CREATE OR REPLACE FUNCTION alter_evolution_api_db() RETURNS boolean AS $$
DECLARE
  v_exists boolean;
  v_owner text;
  v_tablespace text;
  v_current_connlimit integer;
  v_target_tablespace constant text := 'ts_enterprise_data';
  v_db constant text := 'evolution_api_db';
  v_roles text[] := ARRAY['analytics', 'evolution_api_user', 'evoluton_api_user'];
  v_role text;
BEGIN
  -- Validação: checar se database existe
  SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = v_db) INTO v_exists;
  IF NOT v_exists THEN
    RAISE NOTICE 'Database "%" não existe.', v_db;
    RETURN FALSE;
  END IF;

  -- 1) Ajustar OWNER para postgres se necessário
  SELECT pg_roles.rolname
    INTO v_owner
    FROM pg_database d
    JOIN pg_roles ON pg_roles.oid = d.datdba
    WHERE d.datname = v_db;

  IF COALESCE(v_owner, '') <> 'postgres' THEN
    RAISE NOTICE 'Alterando owner do DB "%" de "%" para "postgres".', v_db, COALESCE(v_owner, '<unknown>');
    EXECUTE format('ALTER DATABASE %I OWNER TO %I;', v_db, 'postgres');
  ELSE
    RAISE NOTICE 'Owner do DB "%" já é "postgres"; pulando.', v_db;
  END IF;

  -- 2) Ajustar TABLESPACE se necessário
  SELECT ts.spcname
    INTO v_tablespace
    FROM pg_database d
    LEFT JOIN pg_tablespace ts ON ts.oid = d.dattablespace
    WHERE d.datname = v_db;

  IF COALESCE(v_tablespace, '') <> v_target_tablespace THEN
    RAISE NOTICE 'Alterando tablespace do DB "%" de "%" para "%".', v_db, COALESCE(v_tablespace, '<default>'), v_target_tablespace;
    -- Pode falhar se houver restrições; tratamos no EXCEPTION
    EXECUTE format('ALTER DATABASE %I SET TABLESPACE %I;', v_db, v_target_tablespace);
  ELSE
    RAISE NOTICE 'Tablespace do DB "%" já é "%"; pulando.', v_db, v_target_tablespace;
  END IF;

  -- 3) Ajustar CONNECTION LIMIT para -1 (ilimitado) se necessário
  SELECT datconnlimit INTO v_current_connlimit FROM pg_database WHERE datname = v_db;
  IF v_current_connlimit IS NULL OR v_current_connlimit <> -1 THEN
    RAISE NOTICE 'Ajustando connection limit do DB "%" para -1.', v_db;
    EXECUTE format('ALTER DATABASE %I CONNECTION LIMIT -1;', v_db);
  ELSE
    RAISE NOTICE 'Connection limit do DB "%" já é -1; pulando.', v_db;
  END IF;

  -- 4) Segurança: remover privilégios amplos do PUBLIC no nível de database
  --    Evitar conceder ALL a PUBLIC em produção.
  BEGIN
    EXECUTE format('REVOKE ALL ON DATABASE %I FROM PUBLIC;', v_db);
    RAISE NOTICE 'Revogado ALL ON DATABASE % para PUBLIC (se havia).', v_db;
  EXCEPTION WHEN others THEN
    RAISE WARNING 'Falha ao revogar ALL ON DATABASE % FROM PUBLIC: %', v_db, SQLERRM;
    -- continuar; não retornamos FALSE imediatamente pois pode não ser crítico
  END;

  -- 5) Conceder CONNECT no database para roles/usuários necessários; se role não existir, apenas logamos
  FOREACH v_role IN ARRAY v_roles LOOP
    BEGIN
      IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname = v_role) THEN
        EXECUTE format('GRANT CONNECT ON DATABASE %I TO %I;', v_db, v_role);
        RAISE NOTICE 'Concedido CONNECT ON DATABASE % a %', v_db, v_role;
      ELSE
        RAISE NOTICE 'Role/usuário "%" não existe; pulando GRANT CONNECT para ele.', v_role;
      END IF;
    EXCEPTION WHEN others THEN
      RAISE WARNING 'Falha ao conceder CONNECT ON DATABASE % a %: %', v_db, v_role, SQLERRM;
      -- continuar loop
    END;
  END LOOP;

  -- 6) Conceder ALL PRIVILEGES no database ao superuser 'postgres' (normalmente redundante)
  BEGIN
    IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname = 'postgres') THEN
      EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I;', v_db, 'postgres');
      RAISE NOTICE 'Concedido ALL PRIVILEGES ON DATABASE % a postgres.', v_db;
    ELSE
      RAISE WARNING 'Role postgres não existe no cluster; pulando GRANT ALL a postgres.';
    END IF;
  EXCEPTION WHEN others THEN
    RAISE WARNING 'Falha ao conceder ALL PRIVILEGES ON DATABASE % a postgres: %', v_db, SQLERRM;
    -- não falha de vez
  END;

  -- Tudo ok
  RETURN TRUE;

EXCEPTION WHEN others THEN
  RAISE WARNING 'Erro em alter_evolution_api_db(): %', SQLERRM;
  RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Executar a função (exemplo); ela irá retornar true em sucesso, false em erro.
-- (Execute esta linha conectado como superuser: psql -U postgres -d postgres -c "SELECT alter_evolution_api_db();")
SELECT alter_evolution_api_db();

-- --------------------------------------------------------
-- Comandos diretos (alternativa/para revisão manual)
-- --------------------------------------------------------
-- Note: estes são comandos equivalentes executáveis manualmente por um superuser.
-- ALTER DATABASE evolution_api_db OWNER TO postgres;
-- ALTER DATABASE evolution_api_db SET TABLESPACE ts_enterprise_data;
-- ALTER DATABASE evolution_api_db CONNECTION LIMIT -1;
-- REVOKE ALL ON DATABASE evolution_api_db FROM PUBLIC;
-- GRANT CONNECT ON DATABASE evolution_api_db TO analytics;
-- GRANT CONNECT ON DATABASE evolution_api_db TO evolution_api_user;
-- GRANT CONNECT ON DATABASE evolution_api_db TO evoluton_api_user;
-- GRANT ALL PRIVILEGES ON DATABASE evolution_api_db TO postgres;

-- Fim do arquivo