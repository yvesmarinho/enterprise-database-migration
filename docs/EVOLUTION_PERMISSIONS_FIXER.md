# EvolutionPermissionsFixer - Corretor de Permissões Evolution API

## Descrição

Módulo Python robusto que corrige automaticamente permissões em bancos de dados `evolution*` após criação de tablespaces. Implementa a lógica equivalente ao arquivo SQL `alter_evolution_api_db_only.sql` com controles robustos de transação e tratamento de erros.

## Problema Resolvido

Após criação de um novo tablespace (`ts_enterprise_data`), usuários podem perder permissão de acesso ao schema `public` e suas tabelas nos bancos evolution*. Este módulo:

- ✓ Localiza automaticamente todos os bancos que começam com `evolution`
- ✓ Corrige owner do banco (para `postgres`)
- ✓ Ajusta tablespace para `ts_enterprise_data`
- ✓ Define connection limit como ilimitado (-1)
- ✓ Revoga privilégios amplos do PUBLIC
- ✓ Concede permissões apropriadas aos roles necessários
- ✓ Corrige permissões no schema public e suas tabelas
- ✓ Suporta modo de simulação (dry-run)
- ✓ Transações atômicas com rollback automático

## Estrutura do Código

### Classe Principal: `EvolutionPermissionsFixer`

```python
fixer = EvolutionPermissionsFixer(
    connection_string="postgresql://user:pass@host:port/db",
    dry_run=False,           # Simula operações sem executar
    stop_on_error=False,     # Continua mesmo com erros
    timeout_seconds=30       # Timeout para operações
)

results = fixer.process_evolution_databases()
fixer.print_results()
```

### Métodos Principais

#### `find_evolution_databases(session)`
Localiza todos os bancos que correspondem ao padrão `evolution*`.

```python
databases = fixer.find_evolution_databases(session)
# Retorna: ['evolution_api_db', 'evolution_db_backup']
```

#### `get_database_info(session, database_name)`
Obtém informações do banco de dados.

```python
info = fixer.get_database_info(session, "evolution_api_db")
# Retorna: DatabaseInfo(name=..., owner=..., tablespace=..., connlimit=...)
```

#### `fix_database_owner(session, db_name, current_owner)`
Corrige o owner do banco para `postgres`.

```python
success = fixer.fix_database_owner(session, "evolution_api_db", "app_user")
```

#### `fix_database_tablespace(session, db_name, current_tablespace)`
Ajusta tablespace para `ts_enterprise_data`.

```python
success = fixer.fix_database_tablespace(session, "evolution_api_db", "pg_default")
```

#### `fix_connection_limit(session, db_name, current_limit)`
Define connection limit como -1 (ilimitado).

```python
success = fixer.fix_connection_limit(session, "evolution_api_db", 100)
```

#### `revoke_public_privileges(session, db_name)`
Revoga privilégios amplos do PUBLIC.

```python
success = fixer.revoke_public_privileges(session, "evolution_api_db")
```

#### `grant_database_connect(session, db_name, role_name)`
Concede CONNECT no database para um role.

```python
success = fixer.grant_database_connect(session, "evolution_api_db", "evolution_api_user")
```

#### `fix_schema_public_permissions(db_name, roles=None)`
Corrige permissões do schema public e suas tabelas.

```python
success = fixer.fix_schema_public_permissions(
    "evolution_api_db",
    roles=["evolution_api_user", "analytics"]
)
```

#### `process_evolution_databases()`
Processa todos os bancos evolution* encontrados.

```python
results = fixer.process_evolution_databases()
# Retorna dicionário com resultados detalhados
```

## Uso

### Instalação de Dependências

```bash
pip install -r requirements.txt
```

### Modo Básico (Simulação)

```python
from core.fix_evolution_permissions import fix_evolution_database_permissions

# Simular operações (seguro para testar)
results = fix_evolution_database_permissions(
    connection_string="postgresql://postgres:pass@localhost:5432/postgres",
    dry_run=True  # Apenas simula
)

# Imprimir resultados
print(results)
```

### Modo Avançado (Com Controle Fino)

```python
from core.fix_evolution_permissions import EvolutionPermissionsFixer

fixer = EvolutionPermissionsFixer(
    connection_string="postgresql://postgres:pass@localhost:5432/postgres",
    dry_run=False,           # Executa de verdade
    stop_on_error=False,     # Continua com erros
    timeout_seconds=60
)

results = fixer.process_evolution_databases()
fixer.print_results()

# Analisar erros
if results['errors']:
    for error in results['errors']:
        print(f"Erro em {error['database']}: {error['error']}")
```

### Com Variáveis de Ambiente

```bash
# Arquivo .env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=seu_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
```

```python
import os
from dotenv import load_dotenv
from core.fix_evolution_permissions import fix_evolution_database_permissions

load_dotenv()

connection_string = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

results = fix_evolution_database_permissions(connection_string)
```

## Exemplo Completo

```python
#!/usr/bin/env python3
import logging
from core.fix_evolution_permissions import EvolutionPermissionsFixer

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Conexão
connection_string = "postgresql://postgres:pass@localhost:5432/postgres"

# Criar instância
fixer = EvolutionPermissionsFixer(
    connection_string=connection_string,
    dry_run=False,
    stop_on_error=False
)

# Executar
results = fixer.process_evolution_databases()

# Análise de resultados
fixer.print_results()

if results['databases_failed']:
    print(f"\n⚠ {len(results['databases_failed'])} banco(s) falharam!")
    exit(1)
else:
    print("\n✓ Sucesso! Todos os bancos foram corrigidos.")
    exit(0)
```

## Recursos de Segurança

### 1. Transações Atômicas
- ✓ Rollback automático em caso de erro
- ✓ Todas as operações são executadas em uma transação

### 2. Controle de Erros
- ✓ Captura de exceções específicas
- ✓ Opção `stop_on_error` para interromper no primeiro erro crítico
- ✓ Logging detalhado de todas as operações

### 3. Modo de Simulação
- ✓ Flag `dry_run` permite testar sem fazer alterações
- ✓ Mostra exatamente o que seria executado

### 4. Desconexão Automática
- ✓ Desconecta outras conexões antes de alterações estruturais
- ✓ Permite ajustes de tablespace sem bloqueios

### 5. Validação de Roles
- ✓ Verifica se o role existe antes de conceder permissões
- ✓ Evita erros de permissão

## Estrutura de Resultados

```python
{
    "databases_processed": ["evolution_api_db"],
    "databases_skipped": [],
    "databases_failed": [],
    "permissions_fixed": 1,
    "errors": []
}
```

## Logging

O módulo produz logs detalhados em diversos níveis:

```
INFO:    Operações bem-sucedidas (✓)
DEBUG:   Detalhes de execução
WARNING: Situações não críticas (⚠)
ERROR:   Erros críticos (✗)
```

### Exemplo de Saída

```
2025-10-31 10:30:45 - INFO - ✓ Encontrados 1 banco(s) evolution*: ['evolution_api_db']

======================================================================
Processando banco: evolution_api_db
======================================================================

INFO - ✓ Conexão com banco de dados estabelecida com sucesso
INFO - Info atual: DatabaseInfo(name=evolution_api_db, owner=app_user, ...)
INFO - ✓ Owner já é 'postgres'; pulando
INFO - ✓ Alterando tablespace de 'evolution_api_db' para 'ts_enterprise_data'
INFO - ✓ Ajustando connection limit de 'evolution_api_db' para -1
INFO - ✓ Revogando ALL do PUBLIC em 'evolution_api_db'
INFO - ✓ Concedendo CONNECT em 'evolution_api_db' a 'evolution_api_user'
INFO - ✓ Permissões do schema public corrigidas em 'evolution_api_db'

======================================================================
RELATÓRIO FINAL
======================================================================
Bancos processados: 1
  ✓ evolution_api_db
Permissões ajustadas: 1
```

## Tratamento de Erros Comuns

### Erro: "Não foi possível resolver a importação"
**Solução**: Instale as dependências
```bash
pip install sqlalchemy psycopg2-binary python-dotenv
```

### Erro: "Connection refused"
**Solução**: Verifique credenciais e se o servidor PostgreSQL está rodando

### Erro: "role does not exist"
**Solução**: O módulo ignora roles que não existem (comportamento esperado)

## Notas de Produção

1. **Backup**: Sempre faça backup antes de executar
2. **Teste**: Use `dry_run=True` para testar primeiro
3. **Horário**: Execute fora de horas de pico
4. **Monitoramento**: Monitore logs durante execução
5. **Verificação**: Execute `--dry-run` depois de produção para validar

## Comparação com SQL Puro

| Aspecto | SQL Puro | Python + SQLAlchemy |
|---------|----------|-------------------|
| Transações | Manual | Automático |
| Erro handling | Manual | Automático |
| Logging | Console | Estruturado |
| Dry-run | Não | Sim |
| Descoberta automática | Não | Sim |
| Validação | Manual | Automático |

## Licença

MIT

## Autor

Database Migration System
Data: 2025-10-31
