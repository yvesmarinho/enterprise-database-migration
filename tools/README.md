# tools/ — Utilitários PostgreSQL

Ferramentas operacionais de uso frequente para manutenção, migração e correção de permissões nos servidores PostgreSQL da infraestrutura Vya.

Os configs de conexão ficam em `../secrets/` e são referenciados por nome nos comandos abaixo.

---

## Estrutura

```
tools/
├── README.md                  ← este arquivo
├── Makefile                   ← atalhos de uso rápido
│
├── migrate_users/
│   └── migrate_targeted_users_and_db.py
│       Copia usuários selecionados e o banco app_workforce
│       de um servidor PostgreSQL de origem para um de destino.
│
└── fix_permissions/
    ├── fix_permissions.py          Script principal (guiado por JSON)
    ├── fix_permissions.json        Config padrão (metabase + wfdb02)
    ├── fix_permissions_wf008.json  Config alternativa (wf008)
    ├── fix_app_workforce_journey.py  Correções específicas app_workforce
    ├── fix_app_workforce_journey.sql SQL complementar
    ├── verify_metabase_permissions.py  Verificação pós-correção
    ├── fix_metabase_permissions.sql    SQL correção metabase
    └── fix_metabase_ownership_restored.sql  Restauração de ownership
```

---

## migrate_users

Migra um conjunto filtrado de usuários (`migration_user`, `backup`, `journey*`, `yves_marinho`, `vanderson_andrade`) e o banco `app_workforce` com seus grants entre dois servidores.

### Uso rápido (via Makefile)

```bash
# Listar configs disponíveis em secrets/
make migrate-list

# Simulação (sem alterações)
make migrate-dry SOURCE=wfdb02_source_config.json DESTINY=home016_destiny_config.json

# Execução real
make migrate SOURCE=wfdb02_source_config.json DESTINY=home016_destiny_config.json

# Execução real com log detalhado
make migrate-verbose SOURCE=wfdb02_source_config.json DESTINY=home016_destiny_config.json
```

### Uso direto

```bash
# A partir da raiz do projeto
python3 tools/migrate_users/migrate_targeted_users_and_db.py \
    --source  wfdb02_source_config.json \
    --destiny home016_destiny_config.json \
    --dry-run

# Modo interativo: pede os arquivos ao executar
python3 tools/migrate_users/migrate_targeted_users_and_db.py

# Ver configs disponíveis
python3 tools/migrate_users/migrate_targeted_users_and_db.py --list-configs
```

### Argumentos

| Argumento        | Descrição                                                             |
|------------------|-----------------------------------------------------------------------|
| `--source`       | JSON de origem (nome em `secrets/` ou caminho completo)               |
| `--destiny`      | JSON de destino (nome em `secrets/` ou caminho completo)              |
| `--dry-run`      | Simula sem aplicar alterações                                         |
| `--verbose`      | Exibe usuários que foram ignorados pelo filtro                        |
| `--list-configs` | Lista os `.json` disponíveis em `secrets/` e encerra                  |

### Formato do JSON de origem (`wfdb02_source_config.json`)

```json
{
  "host": "82.197.64.145",
  "port": 5432,
  "database": "postgres",
  "ssl_mode": "prefer",
  "possible_users": [
    { "username": "migration_user", "password": "..." }
  ]
}
```

### Formato do JSON de destino (`home016_destiny_config.json`)

```json
{
  "server":         { "host": "home016", "host_ip": "127.0.0.1", "port": 5432, "ssl_mode": "disable" },
  "authentication": { "user": "postgres", "password": "..." },
  "connection_settings": { "connection_timeout": 30 }
}
```

---

## fix_permissions

Corrige permissões, ownership e grants em bancos PostgreSQL de forma declarativa.
A conexão com o servidor é separada das operações — use qualquer JSON de `secrets/` como `--server`.

### Uso rápido (via Makefile)

```bash
# Listar servidores e configs de operações disponíveis
make fix-list

# Simulação para um banco específico
make fix-dry SERVER=postgresql_destination_config.json DB=metabase_db

# Execução real para um banco específico
make fix SERVER=postgresql_destination_config.json DB=metabase_db

# Executar para todos os bancos do config
make fix-all SERVER=postgresql_destination_config.json

# Com config de operações alternativa (ex: wf008)
make fix SERVER=wf008-postgresql_source_config.json DB=app_workforce CONFIG=fix_permissions_wf008.json

# Modo interativo (pede servidor, config e banco ao executar)
make fix-interactive

# Verificar permissões do metabase após correção
make fix-verify
```

### Uso direto

```bash
# A partir da raiz do projeto
python3 tools/fix_permissions/fix_permissions.py \
    --server  postgresql_destination_config.json \
    --config  fix_permissions.json \
    --database metabase_db \
    --dry-run

python3 tools/fix_permissions/fix_permissions.py \
    --server  postgresql_destination_config.json \
    --config  fix_permissions.json \
    --all --execute --verbose

# Modo interativo (pede servidor, config e banco)
python3 tools/fix_permissions/fix_permissions.py --execute

# Ver configs disponíveis
python3 tools/fix_permissions/fix_permissions.py --list-configs
```

### Argumentos

| Argumento        | Descrição                                                               |
|------------------|-------------------------------------------------------------------------|
| `--server`       | JSON de credenciais do servidor (nome em `secrets/` ou caminho)         |
| `--config`       | JSON de operações (nome em `tools/fix_permissions/` ou caminho)         |
| `--database`     | Nome do banco a processar                                               |
| `--all`          | Processa todos os bancos do config                                      |
| `--dry-run`      | Simula sem aplicar alterações (padrão quando `--execute` é omitido)     |
| `--execute`      | Aplica as alterações                                                    |
| `--verbose`      | Log detalhado de cada operação                                          |
| `--list-configs` | Lista JSONs disponíveis em `secrets/` e `tools/fix_permissions/`        |

### Configs de operações disponíveis

| Arquivo                        | Uso                                      |
|--------------------------------|------------------------------------------|
| `fix_permissions.json`         | metabase_db, n8n_db, evolution_api       |
| `fix_permissions_wf008.json`   | app_workforce no servidor wf008          |

---

## Pré-requisitos

```bash
# Instalar dependência (já inclusa no requirements.txt do projeto)
pip install psycopg2-binary

# Ou via uv
uv pip install psycopg2-binary
```

---

## Configs disponíveis em secrets/

```bash
make list-secrets
```
