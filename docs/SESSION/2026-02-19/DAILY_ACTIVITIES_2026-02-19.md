# 📋 Atividades do Dia — 2026-02-19

## Contexto

Sessão de trabalho focada na criação de utilitários operacionais PostgreSQL e na
organização do repositório. Trabalho executado em um ambiente com:

- **Origem**: wfdb02 (82.197.64.145 — PostgreSQL 14)
- **Destino**: home016 (127.0.0.1 — PostgreSQL 16)
- **Python**: 3.13.3 (.venv)
- **Driver**: psycopg2-binary

---

## Linha do Tempo

### 09:00 – Análise do problema

- Usuário solicitou script para copiar usuários e banco `app_workforce` do wfdb02 para home016
- Arquivos de config fornecidos: `wfdb02_source_config.json` e `home016_destiny_config.json`
- Identificados dois formatos de JSON diferentes (source vs destiny)

### 10:00 – Criação do `migrate_targeted_users_and_db.py`

- Pesquisado código existente em `app/core/migrate_users.py`, `app/core/sqlalchemy_migration.py`
- Criado `scripts/migrate_targeted_users_and_db.py` com:
  - Filtro de usuários: `migration_user`, `backup`, `journey*`, `yves_marinho`, `vanderson_andrade`
  - Criação do banco `app_workforce` com `pt_BR.UTF-8`
  - Cópia de grants via `aclexplode()`
  - Seção de verificação final no destino

### 11:00 – Adição de argv e modo interativo

- Adicionados `--source`, `--destiny`, `--dry-run`, `--verbose`, `--list-configs`
- Helper `_resolve_config_path()` para busca em `secrets/`
- Modo interativo quando args omitidos

### 12:30 – Execução em produção (SUCESSO)

Resultado da execução real com `SOURCE=wfdb02_source_config.json DESTINY=home016_destiny_config.json`:

| Item | Status |
|------|--------|
| backup | ✅ Criado |
| journey_system | ✅ Criado |
| journey_typebot | ✅ Criado |
| journeydb_user | ✅ Criado |
| journeytypebot | ✅ Criado |
| migration_user | ✅ Criado |
| vanderson_andrade | ✅ Criado |
| yves_marinho | ✅ Criado |
| app_workforce DB | ✅ Criado |
| Grants aplicados | ✅ 6/8 (2 ignorados — PUBLIC/"-") |

### 13:30 – Bug: grantee `-`

- Detectado: `aclexplode()` representa PUBLIC (OID 0) como literal `-`
- Corrigido: adicionado `"-"` a `SKIP_GRANTEES = {"-", "PUBLIC", "postgres"}`

### 14:00 – Seção de verificação final

- Adicionada ao final do script: exibe usuários, metadados do banco e grants no destino

### 15:00 – Estrutura `tools/`

Criada a estrutura:
```
tools/
├── README.md
├── Makefile
├── migrate_users/
│   └── migrate_targeted_users_and_db.py
└── fix_permissions/
    ├── fix_permissions.py         (refatorado)
    ├── fix_permissions.json
    ├── fix_permissions_wf008.json
    ├── fix_app_workforce_journey.py
    ├── fix_app_workforce_journey.sql
    ├── verify_metabase_permissions.py
    ├── fix_metabase_permissions.sql
    └── fix_metabase_ownership_restored.sql
```

### 16:30 – Refatoração do `fix_permissions.py`

- Anterior: 506 linhas, classe `PermissionsFixer`, conexão via `config['connection']['config_file']`
- Novo: 428 linhas, estilo funcional, `--server` + `--config` (igual ao migrate_users)
- `build_dsn()` suporta ambos os formatos de JSON (source e destiny)
- Default seguro: `--dry-run` quando `--execute` é omitido
- Verificação pós-operação integrada

### 17:00 – Documentação

- `tools/README.md`: tabelas de argumentos, exemplos, formato dos JSONs
- `tools/Makefile`: targets para ambas as ferramentas com variáveis `SOURCE`, `DESTINY`, `SERVER`, `DB`, `CONFIG`

---

## Resumo de Arquivos Criados/Modificados

| Arquivo | Ação |
|---------|------|
| `scripts/migrate_targeted_users_and_db.py` | Criado |
| `tools/migrate_users/migrate_targeted_users_and_db.py` | Criado (cópia em tools/) |
| `tools/fix_permissions/fix_permissions.py` | Refatorado |
| `tools/fix_permissions/fix_permissions.json` | Copiado |
| `tools/fix_permissions/fix_permissions_wf008.json` | Copiado |
| `tools/fix_permissions/fix_app_workforce_journey.py` | Copiado |
| `tools/fix_permissions/fix_app_workforce_journey.sql` | Copiado |
| `tools/fix_permissions/verify_metabase_permissions.py` | Copiado |
| `tools/fix_permissions/fix_metabase_permissions.sql` | Copiado |
| `tools/fix_permissions/fix_metabase_ownership_restored.sql` | Copiado |
| `tools/README.md` | Criado |
| `tools/Makefile` | Criado |
