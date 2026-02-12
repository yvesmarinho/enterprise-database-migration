# 🔧 Guia de Uso - extra_params

## 📋 O que é extra_params?

O campo `extra_params` no arquivo JSON permite passar parâmetros adicionais para a conexão PostgreSQL via psycopg2.

## ✅ Parâmetros Suportados (Seguros)

O código agora valida automaticamente os `extra_params` e **remove parâmetros não suportados**, emitindo avisos no log.

### Lista de Parâmetros Válidos:

```json
{
  "extra_params": {
    "channel_binding": "prefer",
    "keepalives": 1,
    "keepalives_idle": 60,
    "keepalives_interval": 10,
    "keepalives_count": 5,
    "tcp_user_timeout": 0,
    "client_encoding": "UTF8",
    "sslcert": "/path/to/client.crt",
    "sslkey": "/path/to/client.key",
    "sslrootcert": "/path/to/ca.crt"
  }
}
```

## ❌ Parâmetros NÃO Suportados

### ⚠️ options com -c (PROBLEMA COMUM)

**NÃO FUNCIONA:**
```json
{
  "extra_params": {
    "options": "-c statement_timeout=0"  // ❌ ERRO!
  }
}
```

**Erro gerado:**
```
FATAL: unsupported startup parameter in options: statement_timeout
```

**Por que não funciona?**
O PostgreSQL não aceita parâmetros de configuração (`-c`) como parâmetros de startup da conexão. Eles devem ser executados APÓS a conexão ser estabelecida.

## ✅ Solução - Como Definir statement_timeout

### Opção 1: Remover extra_params (Mais Simples)

```json
{
  "host": "localhost",
  "port": 5432,
  "db_source": "meu_banco",
  "db_destiny": "meu_banco_clone"
  // Sem extra_params
}
```

O sistema funcionará normalmente sem nenhum `extra_params`.

### Opção 2: Executar SET Após Conexão

Se você REALMENTE precisa de `statement_timeout=0`, modifique o código para executar após conectar:

```python
# Após a conexão ser estabelecida
with engine.connect() as conn:
    conn.execute(text("SET statement_timeout = 0"))
    # Resto do código...
```

### Opção 3: Usar Parâmetros Válidos

Use apenas parâmetros que são suportados na conexão inicial:

```json
{
  "extra_params": {
    "channel_binding": "prefer",
    "keepalives": 1
  }
}
```

## 🔍 O que o Código Faz Agora?

### Validação Automática

O método `_filter_safe_extra_params()` no arquivo `pg_json_config_Version2.py`:

1. **Verifica** se cada parâmetro em `extra_params` é suportado
2. **Remove** parâmetros não suportados
3. **Emite avisos** no log sobre parâmetros removidos
4. **Validação especial** para `options` com `-c`

### Exemplo de Log:

```
2026-02-10 11:06:12 - root - WARNING - Parâmetro 'options' com '-c' não é suportado no startup. Use SET após conectar. Valor ignorado: -c statement_timeout=0
2026-02-10 11:06:12 - root - INFO - Parâmetros não suportados removidos: options=-c statement_timeout=0
```

## 📚 Exemplos de Configuração

### Exemplo 1: Sem extra_params (Recomendado)

```json
{
  "host": "localhost",
  "port": 5432,
  "ssl_mode": "false",
  "possible_users": [
    {
      "username": "postgres",
      "password": "senha",
      "priority": 0
    }
  ],
  "db_source": "origem_db",
  "db_destiny": "destino_db"
}
```

### Exemplo 2: Com SSL

```json
{
  "host": "db.exemplo.com",
  "port": 5432,
  "ssl_mode": "require",
  "extra_params": {
    "sslcert": "/etc/ssl/certs/client.crt",
    "sslkey": "/etc/ssl/private/client.key",
    "sslrootcert": "/etc/ssl/certs/ca.crt"
  },
  "possible_users": [{"username": "user", "password": "pass", "priority": 0}],
  "db_source": "origin",
  "db_destiny": "dest"
}
```

### Exemplo 3: Com Keepalives

```json
{
  "host": "remote-db.com",
  "port": 5432,
  "ssl_mode": "false",
  "extra_params": {
    "keepalives": 1,
    "keepalives_idle": 60,
    "keepalives_interval": 10,
    "keepalives_count": 5
  },
  "possible_users": [{"username": "user", "password": "pass", "priority": 0}],
  "db_source": "app_db",
  "db_destiny": "app_db_backup"
}
```

## 🧪 Como Testar sua Configuração

### Teste 1: Validar JSON

```bash
python3 -m json.tool seu_config.json
```

### Teste 2: Testar Conexão Manualmente

```bash
# Sem extra_params problemáticos
psql -h localhost -U seu_usuario -d postgres -c "SELECT version();"
```

### Teste 3: Executar com Verbose

```bash
python3 clone_database_Version2.py seu_config.json --verbose
```

Verifique os logs para avisos sobre parâmetros removidos.

## 🚨 Problemas Comuns

### Problema 1: Erro "unsupported startup parameter"

**Causa:** `extra_params` contém `options` com `-c`
**Solução:** Remova o campo `extra_params` ou use apenas parâmetros válidos

### Problema 2: Parâmetros ignorados silenciosamente

**Causa:** Parâmetros não suportados no `extra_params`
**Solução:** Execute com `--verbose` para ver avisos

### Problema 3: Preciso de statement_timeout=0

**Causa:** Queries muito longas que precisam de timeout infinito
**Solução:** Modifique o código para executar `SET` após conectar, ou use configuração no servidor PostgreSQL

## 📖 Referências

### Parâmetros Psycopg2:
- [Documentação Psycopg2 - Connection](https://www.psycopg.org/docs/module.html#psycopg2.connect)

### Parâmetros PostgreSQL:
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS)

### Lista Completa de Parâmetros Suportados:

Consulte o código em `pg_json_config_Version2.py`, método `_filter_safe_extra_params()`:

```python
supported_params = {
    'connect_timeout', 'client_encoding', 'options',
    'application_name', 'fallback_application_name',
    'keepalives', 'keepalives_idle', 'keepalives_interval',
    'keepalives_count', 'tcp_user_timeout', 'replication',
    'gssencmode', 'sslmode', 'sslcompression', 'sslcert',
    'sslkey', 'sslrootcert', 'sslcrl', 'requirepeer',
    'ssl_min_protocol_version', 'ssl_max_protocol_version',
    'krbsrvname', 'gsslib', 'service', 'target_session_attrs',
    'channel_binding'
}
```

## ✅ Checklist de Configuração

Antes de executar a clonagem:

- [ ] Removi `"options": "-c ..."` do `extra_params`
- [ ] Verifiquei que todos os parâmetros em `extra_params` são válidos
- [ ] Testei a conexão manualmente com psql
- [ ] Executei com `--verbose` para verificar avisos
- [ ] Li os logs para confirmar que nenhum parâmetro foi removido

## 🎯 Recomendação Final

**Para a maioria dos casos, não use `extra_params`!**

O sistema já configura:
- ✅ `connect_timeout`
- ✅ `application_name`
- ✅ `sslmode`
- ✅ Todos os parâmetros essenciais

Só adicione `extra_params` se você REALMENTE precisa de configurações especiais como SSL com certificados ou keepalives personalizados.

---

**Última Atualização:** 10/02/2026
**Versão do Sistema:** 2.0.0
**Status:** ✅ Validação automática implementada
