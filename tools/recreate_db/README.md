# Database Recreator - Recriador de Bancos de Dados

Ferramenta Python para recriar bancos de dados MySQL e PostgreSQL de forma segura, coletando metadados antes da exclusão.

## 🎯 Funcionalidades

- ✅ Suporte para MySQL e PostgreSQL
- ✅ Detecção automática do tipo de banco
- ✅ Coleta de metadados antes da exclusão
- ✅ Recriação com mesmos parâmetros (charset, collation, encoding)
- ✅ Geração de relatórios JSON
- ✅ Confirmação de segurança
- ✅ Logs detalhados
- ✅ Suporte a diferentes estruturas de JSON de configuração

## 📋 Requisitos

```bash
pip install pymysql psycopg2-binary
```

Ou use o arquivo requirements.txt:
```bash
pip install -r requirements.txt
```

## 🚀 Uso

### Uso Básico

```bash
# MySQL
python recreate_database.py \
  --config ../../secrets/mysql_config.json \
  --database perfexcrm_db

# PostgreSQL
python recreate_database.py \
  --config ../../secrets/postgresql_source_config.json \
  --database app_workforce
```

### Opções Avançadas

```bash
# Forçar exclusão (termina conexões ativas no PostgreSQL)
python recreate_database.py -c config.json -d mydb --force

# Modo verboso (DEBUG)
python recreate_database.py -c config.json -d mydb --verbose

# Sem gerar relatório
python recreate_database.py -c config.json -d mydb --no-report
```

### Uso como Módulo Python

```python
from recreate_database import DatabaseRecreator

# Instancia o recreator
recreator = DatabaseRecreator(
    config_path='../../secrets/mysql_config.json',
    database_name='perfexcrm_db'
)

# Executa recriação completa
result = recreator.execute_full_recreation(
    force=False,      # Terminar conexões ativas?
    save_report=True  # Salvar relatório?
)

print(f"Sucesso: {result['success']}")
print(f"Metadados: {result['metadata']}")
print(f"Relatório: {result.get('report_file')}")
```

## 📁 Estrutura dos Arquivos JSON

O módulo aceita diferentes estruturas de configuração JSON:

### MySQL (Estrutura Source/Destination)

```json
{
  "source": {
    "host": "hostname",
    "port": 3306,
    "user": "username",
    "password": "password",
    "charset": "utf8mb4"
  }
}
```

### PostgreSQL (Estrutura Server/Authentication)

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

## 📊 Metadados Coletados

### MySQL
- Nome do banco
- Character set (charset)
- Collation
- Número de tabelas
- Timestamp da operação

### PostgreSQL
- Nome do banco
- Encoding
- Collate e Ctype
- Tamanho do banco
- Número de tabelas
- Timestamp da operação

## 📝 Relatórios

Os relatórios são salvos em `reports/recreate_{database}_{timestamp}.json`:

```json
{
  "operation": "database_recreation",
  "database": "perfexcrm_db",
  "type": "mysql",
  "metadata_before": {
    "database_name": "perfexcrm_db",
    "exists": true,
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "table_count": 42
  },
  "config_file": "secrets/mysql_config.json",
  "timestamp": "20260305_143022"
}
```

## ⚠️ Segurança

1. **Confirmação Obrigatória**: O script solicita digitação de 'SIM' antes de executar
2. **Logs Detalhados**: Todas as operações são registradas
3. **Backup de Metadados**: Informações são salvas antes da exclusão
4. **Validações**: Verifica existência do banco antes de tentar apagar

## 🛠️ Argumentos da CLI

| Argumento | Curto | Obrigatório | Descrição |
|-----------|-------|-------------|-----------|
| `--config` | `-c` | Sim | Caminho para o JSON de configuração |
| `--database` | `-d` | Sim | Nome do banco a recriar |
| `--force` | - | Não | Termina conexões ativas (PostgreSQL) |
| `--no-report` | - | Não | Não gera relatório |
| `--verbose` | `-v` | Não | Ativa modo DEBUG |

## 📖 Exemplos Práticos

### Exemplo 1: Recriar banco MySQL do PerfexCRM

```bash
python recreate_database.py \
  --config ../../secrets/mysql_config.json \
  --database perfexcrm_db \
  --verbose
```

### Exemplo 2: Recriar PostgreSQL forçando desconexão

```bash
python recreate_database.py \
  -c ../../secrets/postgresql_source_config.json \
  -d app_workforce \
  --force
```

### Exemplo 3: Uso programático

```python
from recreate_database import DatabaseRecreator
import json

# Configuração inline
config_data = {
    "source": {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "password",
        "charset": "utf8mb4"
    }
}

# Salva config temporária
with open('temp_config.json', 'w') as f:
    json.dump(config_data, f)

# Executa recriação
try:
    recreator = DatabaseRecreator('temp_config.json', 'test_db')
    recreator.connect()
    recreator.collect_metadata()

    if recreator.metadata['exists']:
        print(f"Banco tem {recreator.metadata['table_count']} tabelas")
        recreator.drop_database()

    recreator.create_database()
    print("✓ Banco recriado com sucesso!")

finally:
    recreator.close()
```

## 🔍 Troubleshooting

### Erro: "Estrutura de configuração não reconhecida"
- Verifique se o JSON tem 'source', 'server' ou 'destination'
- Confirme a porta (3306 para MySQL, 5432 para PostgreSQL)

### Erro: "Cannot drop database because it is currently in use"
- Use `--force` para terminar conexões ativas no PostgreSQL
- Feche todos os clientes conectados ao banco

### Erro de importação: "No module named 'pymysql'"
- Instale as dependências: `pip install -r requirements.txt`

## 📄 Licença

Este código faz parte do projeto Enterprise Database Migration.

## 👥 Autor

Vya Digital - Database Migration Team
