# ✅ Status Final — 2026-02-19

> Estado completo do projeto ao final da sessão de 19 de fevereiro de 2026.

---

## 1. Ferramentas Operacionais (`tools/`)

### `tools/migrate_users/migrate_targeted_users_and_db.py`

| Atributo | Valor |
|----------|-------|
| Status | ✅ PRODUÇÃO — testado e executado com sucesso |
| Linhas | ~440 |
| Dependência | psycopg2-binary |
| CLI | `--source`, `--destiny`, `--dry-run`, `--verbose`, `--list-configs` |
| Interativo | Sim (quando args omitidos) |
| Formatos JSON | Source (`possible_users[]`) e Destiny (`server{}/authentication{}`) |

### `tools/fix_permissions/fix_permissions.py`

| Atributo | Valor |
|----------|-------|
| Status | ✅ Refatorado — sintaxe validada; pendente teste em produção |
| Linhas | 428 |
| Dependência | psycopg2-binary |
| CLI | `--server`, `--config`, `--database`, `--all`, `--dry-run`, `--execute`, `--verbose`, `--list-configs` |
| Interativo | Sim |
| Formatos JSON | Source + Destiny (mesmo suporte do migrate_users) |
| Default | `--dry-run` quando `--execute` não passado |

---

## 2. Estado dos Servidores PostgreSQL

### wfdb02 (82.197.64.145 — ORIGEM) — **Não modificado**

Servidor de origem. Apenas leitura durante a sessão.

### home016 (127.0.0.1 — DESTINO) — **Modificado**

Usuários criados nesta sessão:
```
backup              [NOLOGIN]
journey_system      [LOGIN]
journey_typebot     [LOGIN]
journeydb_user      [LOGIN]
journeytypebot      [LOGIN]
migration_user      [LOGIN, SUPERUSER]
vanderson_andrade   [LOGIN]
yves_marinho        [LOGIN, SUPERUSER, CREATEDB, CREATEROLE]
```

Banco criado:
```
app_workforce   —   UTF8 / pt_BR.UTF-8   —   ~8 kB (vazio)
```

Grants ativos no banco `app_workforce`:
```
CONNECT, CREATE, TEMPORARY  →  journeydb_user
CONNECT, CREATE, TEMPORARY  →  journey_system
```

---

## 3. Estrutura `tools/`

```
tools/
├── README.md                          ← documentação completa com exemplos
├── Makefile                           ← atalhos de uso rápido
│
├── migrate_users/
│   └── migrate_targeted_users_and_db.py    ← ✅ produção
│
└── fix_permissions/
    ├── fix_permissions.py                  ← ✅ refatorado (pendente teste)
    ├── fix_permissions.json               ← metabase_db, n8n_db, evolution_api
    ├── fix_permissions_wf008.json         ← app_workforce no wf008
    ├── fix_app_workforce_journey.py       ← script específico wf008
    ├── fix_app_workforce_journey.sql      ← SQL complementar
    ├── verify_metabase_permissions.py     ← verificador (read-only)
    ├── fix_metabase_permissions.sql       ← correção metabase
    └── fix_metabase_ownership_restored.sql ← restauração de ownership
```

---

## 4. Configurações em `secrets/` (não versionadas)

| Arquivo | Servidor | Formato |
|---------|----------|---------|
| `wfdb02_source_config.json` | 82.197.64.145 (wfdb02) | source (`possible_users[]`) |
| `home016_destiny_config.json` | 127.0.0.1 (home016) | destiny (`server{}/authentication{}`) |
| outros `*_config.json` | vários | variado |

---

## 5. Regras de Uso

### Executar migração de usuários
```bash
cd tools
make migrate SOURCE=wfdb02_source_config.json DESTINY=home016_destiny_config.json
# ou dry-run:
make migrate-dry SOURCE=wfdb02_source_config.json DESTINY=home016_destiny_config.json
```

### Corrigir permissões
```bash
cd tools
make fix-dry SERVER=postgresql_destination_config.json DB=metabase_db
make fix     SERVER=postgresql_destination_config.json DB=metabase_db
```

---

## 6. Pendências para Próxima Sessão

- [ ] Testar `fix_permissions.py --execute` em produção
- [ ] Confirmar que os usuários migrados conseguem conectar no home016
- [ ] Decidir sobre `app_workforce` — popular via dump ou nova configuração
- [ ] `verify_metabase_permissions.py` — migrar de SQLAlchemy para psycopg2 direto (consistência)
