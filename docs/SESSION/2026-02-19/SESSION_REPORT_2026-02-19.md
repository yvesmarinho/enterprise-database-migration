# 📊 Session Report — 2026-02-19

> **Projeto**: Enterprise Database Migration  
> **Data**: 19 de fevereiro de 2026  
> **Duração estimada**: ~8 horas  
> **Resultado geral**: ✅ SUCESSO — ferramentas criadas e migração executada em produção

---

## 1. Objetivos da Sessão

| # | Objetivo | Status |
|---|----------|--------|
| 1 | Criar script de migração de usuários selecionados + banco `app_workforce` | ✅ Concluído |
| 2 | Suporte a múltiplos servidores via argv (sem hardcode) | ✅ Concluído |
| 3 | Executar migração real em produção (wfdb02 → home016) | ✅ Executado |
| 4 | Organizar em `tools/` com README e Makefile | ✅ Concluído |
| 5 | Refatorar `fix_permissions.py` no mesmo padrão | ✅ Concluído |

---

## 2. Entregáveis Técnicos

### 2.1 `tools/migrate_users/migrate_targeted_users_and_db.py`

**Função**: Migra usuários filtrados + banco `app_workforce` entre servidores PostgreSQL.

**Filtro de usuários**:
- Exatos: `migration_user`, `backup`, `yves_marinho`, `vanderson_andrade`
- Prefixo: `journey*`

**Características**:
- Lê `pg_authid` para obter todos os atributos do role (login, super, replication, etc.)
- Cria `CREATE ROLE` com senha hash preservada
- Cria `app_workforce` com `UTF8 / pt_BR.UTF-8` via `ISOLATION_LEVEL_AUTOCOMMIT`
- Copia grants via `aclexplode(COALESCE(datacl, acldefault(...)))` — inclui defaults
- Pula grantees: `{"-", "PUBLIC", "postgres"}` ("`-`" = PUBLIC OID 0 no aclexplode)
- Verificação final do estado no destino

**CLI**: `--source`, `--destiny`, `--dry-run`, `--verbose`, `--list-configs`  
**Modo interativo** quando args omitidos

### 2.2 `tools/fix_permissions/fix_permissions.py` (refatorado)

**Função**: Corrige ownership, grants e default privileges declarativamente.

**Mudanças**:
- De: classe `PermissionsFixer`, conexão via `config['connection']['config_file']`
- Para: estilo funcional, `--server` + `--config` (mesmo padrão do migrate_users)
- `build_dsn()` aceita ambos os formatos de JSON (source: `possible_users[]`, destiny: `server{}/authentication{}`)
- Default seguro: dry-run quando `--execute` não é passado

**CLI**: `--server`, `--config`, `--database`, `--all`, `--dry-run`, `--execute`, `--verbose`, `--list-configs`

### 2.3 `tools/README.md` e `tools/Makefile`

- `README.md`: tabelas de argumentos, exemplos de uso, formato dos JSONs para ambos os formatos
- `Makefile`: atalhos completos com `SOURCE`, `DESTINY`, `SERVER`, `DB`, `CONFIG`

---

## 3. Migração Executada em Produção

### Ambiente

| Componente | Detalhes |
|------------|----------|
| Origem | wfdb02, 82.197.64.145:5432, PostgreSQL 14 |
| Destino | home016, 127.0.0.1:5432, PostgreSQL 16 |
| Usuário origem | `migration_user` |
| Usuário destino | `postgres` |
| Data execução | 2026-02-19 |

### Resultado

8 usuários migrados:
```
backup, journey_system, journey_typebot, journeydb_user,
journeytypebot, migration_user, vanderson_andrade, yves_marinho
```

Banco criado:
```
app_workforce  —  UTF8 / pt_BR.UTF-8
```

Grants aplicados (6/8):
```
CONNECT  → journeydb_user    ✅
CONNECT  → journey_system    ✅
CREATE   → journeydb_user    ✅
CREATE   → journey_system    ✅
TEMPORARY → journeydb_user   ✅
TEMPORARY → journey_system   ✅
(PUBLIC e "-" — ignorados corretamente)
```

---

## 4. Descobertas Técnicas

### PostgreSQL: aclexplode e PUBLIC

`aclexplode()` representa o role PUBLIC (OID 0) como o literal `-` ao converter com `::regrole::text`. Isso causa erro se passado num GRANT. **Solução**: incluir `"-"` no `SKIP_GRANTEES`.

### Dois formatos de JSON de config

O projeto tem dois formatos:
1. **Source** (`possible_users[]`): usado por `wfdb02_source_config.json`
2. **Destiny** (`server{}/authentication{}`): usado por `home016_destiny_config.json`

Ambos suportados via detecção da chave `possible_users`.

### CREATE DATABASE fora de transação

`CREATE DATABASE` não pode ser executado dentro de uma transação. **Solução**: `conn.set_isolation_level(0)` (AUTOCOMMIT) antes do comando, restaurado depois.

---

## 5. Issues e Resoluções

| Issue | Resolução |
|-------|-----------|
| Erro grantee `-` | Adicionado `"-"` a SKIP_GRANTEES |
| CREATE DATABASE falha em transação | set_isolation_level(0) + restore |
| JSON de origem vs destino tem formato diferente | build_dsn() detecta chave `possible_users` |

---

## 6. Débito Técnico Identificado

- `fix_permissions.py` refatorado mas **não testado em produção** — precisa de run real
- `verify_metabase_permissions.py` usa SQLAlchemy (não psycopg2 direto) — inconsistência
- `tools/fix_permissions/fix_app_workforce_journey.py` ainda tem hardcode de `secrets/wf008-postgresql_source_config.json`

---

## 7. Próximas Sessões Sugeridas

1. Testar `fix_permissions.py` em produção (metabase_db)
2. Verificar usuários migrados conseguem conectar no home016
3. Considerar unificar `verify_metabase_permissions.py` para usar psycopg2 direto
4. Futuramente: `tools/clone_database/` (clone completo de banco, não só usuários)
