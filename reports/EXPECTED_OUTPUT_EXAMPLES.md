# 🖼️ EXEMPLOS DE SAÍDA ESPERADA

## Execução em Modo Dry-Run

### Comando
```bash
python3 run_fix_evolution_permissions.py --dry-run --verbose
```

### Saída Esperada
```
2025-10-31 14:30:45 - __main__ - INFO - ======================================================================
2025-10-31 14:30:45 - __main__ - INFO - EvolutionPermissionsFixer - Corretor de Permissões
2025-10-31 14:30:45 - __main__ - INFO - ======================================================================
2025-10-31 14:30:45 - __main__ - INFO - Conectando a: localhost:5432/postgres
2025-10-31 14:30:45 - __main__ - INFO - Usuário: postgres
2025-10-31 14:30:45 - __main__ - WARNING - ⊘ MODO DRY-RUN: Nenhuma alteração será feita
2025-10-31 14:30:45 - __main__ - INFO -

2025-10-31 14:30:46 - core.fix_evolution_permissions - INFO - ✓ Conexão com banco de dados estabelecida com sucesso
2025-10-31 14:30:46 - core.fix_evolution_permissions - INFO - ✓ Encontrados 1 banco(s) evolution*: ['evolution_api_db']

======================================================================
Processando banco: evolution_api_db
======================================================================

2025-10-31 14:30:47 - core.fix_evolution_permissions - INFO - Info atual: DatabaseInfo(name=evolution_api_db, owner=app_user, tablespace=pg_default, connlimit=100)
2025-10-31 14:30:47 - core.fix_evolution_permissions - INFO -   Alterando owner de 'evolution_api_db' para 'postgres'
2025-10-31 14:30:47 - core.fix_evolution_permissions - INFO -   ⊘ [DRY-RUN] Alterando tablespace de 'evolution_api_db' para 'ts_enterprise_data'
2025-10-31 14:30:47 - core.fix_evolution_permissions - INFO -   ⊘ [DRY-RUN] Ajustando connection limit de 'evolution_api_db' para -1
2025-10-31 14:30:47 - core.fix_evolution_permissions - INFO -   ⊘ [DRY-RUN] Revogando ALL do PUBLIC em 'evolution_api_db'
2025-10-31 14:30:48 - core.fix_evolution_permissions - INFO -   ⊘ [DRY-RUN] Concedendo CONNECT em 'evolution_api_db' a 'analytics'
2025-10-31 14:30:48 - core.fix_evolution_permissions - INFO -   ⊘ [DRY-RUN] Concedendo CONNECT em 'evolution_api_db' a 'evolution_api_user'
2025-10-31 14:30:48 - core.fix_evolution_permissions - INFO -   ⊘ [DRY-RUN] Concedendo CONNECT em 'evolution_api_db' a 'evoluton_api_user'
2025-10-31 14:30:49 - core.fix_evolution_permissions - INFO -   Corrigindo permissões do schema public em 'evolution_api_db'
2025-10-31 14:30:49 - core.fix_evolution_permissions - INFO -   ✓ Permissões do schema public corrigidas em 'evolution_api_db'

======================================================================
RELATÓRIO FINAL
======================================================================
Bancos processados: 1
  ✓ evolution_api_db

Bancos pulados: 0

Bancos com falha: 0

Permissões ajustadas: 1
======================================================================

2025-10-31 14:30:49 - __main__ - INFO - ✓ Sucesso! Todos os bancos foram processados com sucesso!
```

**Status de Saída:** `0` (sucesso)

---

## Execução em Modo Real

### Comando
```bash
python3 run_fix_evolution_permissions.py --execute
```

### Saída Esperada
```
2025-10-31 14:35:00 - __main__ - INFO - ======================================================================
2025-10-31 14:35:00 - __main__ - INFO - EvolutionPermissionsFixer - Corretor de Permissões
2025-10-31 14:35:00 - __main__ - INFO - ======================================================================
2025-10-31 14:35:00 - __main__ - INFO - Conectando a: wf004.vya.digital:5432/postgres
2025-10-31 14:35:00 - __main__ - INFO - Usuário: postgres
2025-10-31 14:35:00 - __main__ - WARNING - ⚠ MODO EXECUÇÃO: Alterações serão feitas no banco!
2025-10-31 14:35:00 - __main__ - INFO -

2025-10-31 14:35:01 - core.fix_evolution_permissions - INFO - ✓ Conexão com banco de dados estabelecida com sucesso
2025-10-31 14:35:01 - core.fix_evolution_permissions - INFO - ✓ Encontrados 3 banco(s) evolution*: ['evolution_api_db', 'evolution_api_db_backup', 'evolution_db']

======================================================================
Processando banco: evolution_api_db
======================================================================

2025-10-31 14:35:02 - core.fix_evolution_permissions - INFO - Info atual: DatabaseInfo(name=evolution_api_db, owner=app_user, tablespace=pg_default, connlimit=100)
2025-10-31 14:35:02 - core.fix_evolution_permissions - INFO -   ✓ Alterando owner de 'evolution_api_db' para 'postgres'
2025-10-31 14:35:03 - core.fix_evolution_permissions - INFO -   ✓ Desconectadas 2 conexão(ões) de 'evolution_api_db'
2025-10-31 14:35:04 - core.fix_evolution_permissions - INFO -   ✓ Alterando tablespace de 'evolution_api_db' para 'ts_enterprise_data'
2025-10-31 14:35:04 - core.fix_evolution_permissions - INFO -   ✓ Ajustando connection limit de 'evolution_api_db' para -1
2025-10-31 14:35:05 - core.fix_evolution_permissions - INFO -   ✓ Revogando ALL do PUBLIC em 'evolution_api_db'
2025-10-31 14:35:05 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_api_db' a 'analytics'
2025-10-31 14:35:05 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_api_db' a 'evolution_api_user'
2025-10-31 14:35:06 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_api_db' a 'evoluton_api_user'
2025-10-31 14:35:06 - core.fix_evolution_permissions - INFO - ✓ Permissões do schema public corrigidas em 'evolution_api_db'

======================================================================
Processando banco: evolution_api_db_backup
======================================================================

2025-10-31 14:35:07 - core.fix_evolution_permissions - INFO - Info atual: DatabaseInfo(name=evolution_api_db_backup, owner=app_user, tablespace=pg_default, connlimit=100)
2025-10-31 14:35:07 - core.fix_evolution_permissions - INFO -   ✓ Alterando owner de 'evolution_api_db_backup' para 'postgres'
2025-10-31 14:35:08 - core.fix_evolution_permissions - INFO -   ✓ Alterando tablespace de 'evolution_api_db_backup' para 'ts_enterprise_data'
2025-10-31 14:35:09 - core.fix_evolution_permissions - INFO -   ✓ Ajustando connection limit de 'evolution_api_db_backup' para -1
2025-10-31 14:35:09 - core.fix_evolution_permissions - INFO -   ✓ Revogando ALL do PUBLIC em 'evolution_api_db_backup'
2025-10-31 14:35:09 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_api_db_backup' a 'analytics'
2025-10-31 14:35:10 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_api_db_backup' a 'evolution_api_user'
2025-10-31 14:35:10 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_api_db_backup' a 'evoluton_api_user'
2025-10-31 14:35:10 - core.fix_evolution_permissions - INFO - ✓ Permissões do schema public corrigidas em 'evolution_api_db_backup'

======================================================================
Processando banco: evolution_db
======================================================================

2025-10-31 14:35:11 - core.fix_evolution_permissions - INFO - Info atual: DatabaseInfo(name=evolution_db, owner=app_user, tablespace=pg_default, connlimit=100)
2025-10-31 14:35:11 - core.fix_evolution_permissions - INFO -   ✓ Alterando owner de 'evolution_db' para 'postgres'
2025-10-31 14:35:12 - core.fix_evolution_permissions - INFO -   ✓ Alterando tablespace de 'evolution_db' para 'ts_enterprise_data'
2025-10-31 14:35:13 - core.fix_evolution_permissions - INFO -   ✓ Ajustando connection limit de 'evolution_db' para -1
2025-10-31 14:35:13 - core.fix_evolution_permissions - INFO -   ✓ Revogando ALL do PUBLIC em 'evolution_db'
2025-10-31 14:35:13 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_db' a 'analytics'
2025-10-31 14:35:14 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_db' a 'evolution_api_user'
2025-10-31 14:35:14 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_db' a 'evoluton_api_user'
2025-10-31 14:35:14 - core.fix_evolution_permissions - INFO - ✓ Permissões do schema public corrigidas em 'evolution_db'

======================================================================
RELATÓRIO FINAL
======================================================================
Bancos processados: 3
  ✓ evolution_api_db
  ✓ evolution_api_db_backup
  ✓ evolution_db

Bancos pulados: 0

Bancos com falha: 0

Permissões ajustadas: 3
======================================================================

2025-10-31 14:35:15 - __main__ - INFO - ✓ Sucesso! Todos os bancos foram processados com sucesso!
```

**Status de Saída:** `0` (sucesso)
**Tempo Total:** ~15 segundos

---

## Execução com Erro (Role Não Existe)

### Comando
```bash
python3 run_fix_evolution_permissions.py --execute
```

### Saída Esperada
```
...
2025-10-31 14:40:05 - core.fix_evolution_permissions - INFO - ⊘ Role 'analytics' não existe; pulando
2025-10-31 14:40:05 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_api_db' a 'evolution_api_user'
2025-10-31 14:40:05 - core.fix_evolution_permissions - INFO -   ✓ Concedendo CONNECT em 'evolution_api_db' a 'evoluton_api_user'
...
```

✓ **Comportamento:** Continua normalmente (role inexistente é ignorado)

---

## Execução com Erro Crítico

### Comando
```bash
python3 run_fix_evolution_permissions.py --execute \
  --host db_invalido.com \
  --user postgres \
  --password senha
```

### Saída Esperada
```
2025-10-31 14:45:00 - __main__ - INFO - ======================================================================
2025-10-31 14:45:00 - __main__ - INFO - EvolutionPermissionsFixer - Corretor de Permissões
2025-10-31 14:45:00 - __main__ - INFO - ======================================================================
2025-10-31 14:45:00 - __main__ - INFO - Conectando a: db_invalido.com:5432/postgres
2025-10-31 14:45:00 - __main__ - INFO - Usuário: postgres
2025-10-31 14:45:00 - __main__ - WARNING - ⚠ MODO EXECUÇÃO: Alterações serão feitas no banco!
2025-10-31 14:45:00 - __main__ - INFO -

2025-10-31 14:45:05 - __main__ - ERROR -

✗ Erro crítico: (psycopg2.OperationalError) could not translate host name "db_invalido.com" to address: Name or service not known

2025-10-31 14:45:05 - __main__ - INFO -
```

**Status de Saída:** `1` (erro)

---

## Execução Verbose (Debug)

### Comando
```bash
python3 run_fix_evolution_permissions.py --dry-run --verbose
```

### Saída Esperada (Trecho)
```
2025-10-31 14:50:00 - core.fix_evolution_permissions - DEBUG -   Executando: Alterando owner de 'evolution_api_db' para 'postgres'
2025-10-31 14:50:00 - core.fix_evolution_permissions - DEBUG -      SQL: ALTER DATABASE "evolution_api_db" OWNER TO postgres;
2025-10-31 14:50:00 - core.fix_evolution_permissions - DEBUG -   Executando: Revogando ALL do PUBLIC em 'evolution_api_db'
2025-10-31 14:50:00 - core.fix_evolution_permissions - DEBUG -      SQL: REVOKE ALL ON DATABASE "evolution_api_db" FROM PUBLIC;
2025-10-31 14:50:01 - core.fix_evolution_permissions - DEBUG - ✓ Transação confirmada
```

---

## Exemplos em Python

### Uso Básico
```python
from core.fix_evolution_permissions import fix_evolution_database_permissions

results = fix_evolution_database_permissions(
    connection_string="postgresql://postgres:pass@localhost:5432/postgres",
    dry_run=True
)

print(results)
# Output:
# {
#   'databases_processed': ['evolution_api_db'],
#   'databases_skipped': [],
#   'databases_failed': [],
#   'permissions_fixed': 1,
#   'errors': []
# }
```

### Uso Avançado
```python
from core.fix_evolution_permissions import EvolutionPermissionsFixer

fixer = EvolutionPermissionsFixer(
    connection_string="postgresql://postgres:pass@localhost:5432/postgres",
    dry_run=False,
    stop_on_error=False
)

results = fixer.process_evolution_databases()
fixer.print_results()

if results['databases_failed']:
    print(f"❌ {len(results['databases_failed'])} banco(s) falharam")
    for error in results['errors']:
        print(f"  • {error['database']}: {error['error']}")
else:
    print("✅ Sucesso!")
```

### Teste Unitário
```python
import unittest
from unittest.mock import patch
from core.fix_evolution_permissions import EvolutionPermissionsFixer

class TestFixer(unittest.TestCase):
    def test_initialization(self):
        fixer = EvolutionPermissionsFixer(
            connection_string="postgresql://user:pass@localhost/db",
            dry_run=True
        )
        self.assertTrue(fixer.dry_run)
        self.assertEqual(fixer.timeout_seconds, 30)

if __name__ == '__main__':
    unittest.main()
```

---

## Variações de Saída

### Sem Bancos Encontrados
```
2025-10-31 14:55:00 - core.fix_evolution_permissions - WARNING - Nenhum banco evolution* encontrado

======================================================================
RELATÓRIO FINAL
======================================================================
Bancos processados: 0
Permissões ajustadas: 0
======================================================================
```

### Com Roles Customizadas
```
Concedendo CONNECT em 'evolution_api_db' a 'app_user'
Concedendo CONNECT em 'evolution_api_db' a 'readonly_user'
Concedendo CONNECT em 'evolution_api_db' a 'analytics_user'
```

### Com Timeout Elevado
```bash
python3 run_fix_evolution_permissions.py --execute --timeout 120
# Cada operação terá 120 segundos de timeout
```

---

## Checklist de Validação

Após execução em produção, verificar:

```bash
# 1. Conectar ao banco
psql -h localhost -U postgres -d evolution_api_db

# 2. Verificar owner
SELECT datname, rolname
FROM pg_database d
LEFT JOIN pg_roles ON d.datdba = pg_roles.oid
WHERE datname = 'evolution_api_db';

# 3. Verificar tablespace
SELECT datname, spcname
FROM pg_database d
LEFT JOIN pg_tablespace ts ON d.dattablespace = ts.oid
WHERE datname = 'evolution_api_db';

# 4. Verificar connection limit
SELECT datname, datconnlimit
FROM pg_database
WHERE datname = 'evolution_api_db';

# 5. Verificar permissões do schema public
SELECT * FROM information_schema.role_table_grants
WHERE table_schema = 'public' LIMIT 10;
```

---

**Exemplos criados em:** 31 de outubro de 2025
**Versão:** 1.0.0
