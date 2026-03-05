# Revisão do JSON wfdb02_postgres.json

## Status: ✅ JSON Revisado e Compatível

O arquivo `secrets/wfdb02_postgres.json` foi revisado para atender às especificações do código `recreate_database.py`.

## 📋 Mudanças Realizadas

### ❌ Estrutura ANTIGA (Incompatível):
```json
{
  "host": "wfdb02.vya.digital",
  "port": 5432,
  "ssl_mode": "false",
  "possible_users": [
    {
      "username": "migration_user",
      "password": "-5FRifRucho3wudu&re2opafa+tuFr8#",
      "priority": 0
    }
  ],
  "db_source": "chatwoot_db",
  "db_destiny": "chatwoot_dev_db",
  ...
}
```

**Problemas:**
- ❌ Não tinha chaves `source`, `server` ou `destination`
- ❌ Detecção do tipo de banco não funcionava
- ❌ Extração de parâmetros de conexão falhava
- ❌ Usuários em array `possible_users` não era reconhecido

---

### ✅ Estrutura NOVA (Compatível):
```json
{
  "server": {
    "name": "wfdb02-postgresql",
    "description": "Servidor PostgreSQL WFDB02",
    "host": "wfdb02.vya.digital",
    "port": 5432,
    "database_version": "PostgreSQL 14+",
    "ssl_mode": "disable"
  },
  "authentication": {
    "user": "migration_user",
    "password": "-5FRifRucho3wudu&re2opafa+tuFr8#",
    "auth_method": "password"
  },
  "connection_settings": {
    "connection_timeout": 10,
    "query_timeout": 300,
    "max_connections": 10,
    "pool_size": 5,
    "max_overflow": 10,
    "application_name": "pg_clone_system"
  },
  "databases": {
    "chatwoot_db": {
      "description": "Banco principal Chatwoot - Produção",
      "source": true
    },
    "chatwoot_dev_db": {
      "description": "Banco Chatwoot - Desenvolvimento",
      "destination": true
    }
  },
  ...
}
```

**Melhorias:**
- ✅ Estrutura `server` + `authentication` reconhecida
- ✅ Detecção automática do tipo (PostgreSQL via porta 5432)
- ✅ Parâmetros de conexão extraídos corretamente
- ✅ Documentação de bancos disponíveis
- ✅ Configurações de segurança (protected_databases)
- ✅ Settings de logging e retry

---

## 🔧 Compatibilidade com recreate_database.py

### Estruturas Reconhecidas pelo Código:

O código `recreate_database.py` aceita 3 formatos:

#### 1️⃣ Formato `source` (MySQL/PostgreSQL):
```json
{
  "source": {
    "host": "hostname",
    "port": 3306,
    "user": "username",
    "password": "password"
  }
}
```

#### 2️⃣ Formato `server` + `authentication` (PostgreSQL) ← **USADO**:
```json
{
  "server": {
    "host": "hostname",
    "port": 5432
  },
  "authentication": {
    "user": "username",
    "password": "password"
  }
}
```

#### 3️⃣ Formato `destination`:
```json
{
  "destination": {
    "host": "hostname",
    "port": 3306,
    "user": "username",
    "password": "password"
  }
}
```

---

## 🎯 Como Usar o Novo JSON

### Exemplo 1: Recriar chatwoot_dev_db
```bash
cd tools/recreate_db

python3 recreate_database.py \
  --config ../../secrets/wfdb02_postgres.json \
  --database chatwoot_dev_db \
  --force \
  --verbose
```

### Exemplo 2: Usando o script helper
```bash
cd tools/recreate_db
./recreate.sh wfdb02_postgres.json chatwoot_dev_db --force
```

### Exemplo 3: Usando Makefile
```bash
cd tools/recreate_db
make postgres DB=chatwoot_dev_db CONFIG=wfdb02_postgres.json
```

### Exemplo 4: Modo programático
```python
from recreate_database import DatabaseRecreator

recreator = DatabaseRecreator(
    config_path='../../secrets/wfdb02_postgres.json',
    database_name='chatwoot_dev_db'
)

result = recreator.execute_full_recreation(
    force=True,      # Termina conexões ativas
    save_report=True # Salva relatório
)

print(f"Sucesso: {result['success']}")
```

---

## 📊 Bancos Disponíveis no Config

| Banco | Tipo | Descrição |
|-------|------|-----------|
| `chatwoot_db` | Source | Banco principal - Produção |
| `chatwoot_dev_db` | Destination | Banco de Desenvolvimento |

---

## 🔐 Segurança

### Bancos Protegidos (não podem ser apagados):
- `postgres`
- `template0`
- `template1`

Para recriar qualquer outro banco, o código irá:
1. ✅ Validar que não está na lista protegida
2. ✅ Coletar metadados antes de apagar
3. ✅ Salvar relatório em `reports/`
4. ✅ Apagar banco
5. ✅ Recriar vazio com mesmos parâmetros

---

## 📝 Informações Preservadas

Ao recriar um banco, os seguintes parâmetros são mantidos:

**PostgreSQL:**
- Encoding (UTF8)
- Collate (pt_BR.UTF-8)
- Ctype (pt_BR.UTF-8)

**MySQL:**
- Charset (utf8mb4)
- Collation (utf8mb4_unicode_ci)

---

## ✅ Validação

Para testar se o JSON está funcionando:

```bash
cd tools/recreate_db
python3 test_json.py
```

**Saída esperada:**
```
✅ Tipo detectado: postgresql
✅ Host: wfdb02.vya.digital
✅ Port: 5432
✅ User: migration_user

✅ JSON COMPATÍVEL COM O CÓDIGO!
```

---

## 📚 Referências

- [recreate_database.py](../recreate_db/recreate_database.py) - Código principal
- [README.md](../recreate_db/README.md) - Documentação completa
- [INDEX.md](../recreate_db/INDEX.md) - Índice de arquivos

---

**Status Final:** ✅ JSON revisado e 100% compatível com o código!
