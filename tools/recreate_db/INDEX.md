# Database Recreator - Índice de Arquivos

Módulo para recriação segura de bancos de dados MySQL/PostgreSQL.

## 📁 Estrutura de Arquivos

```
tools/recreate_db/
├── __init__.py                 # Módulo Python (permite imports)
├── recreate_database.py        # ⭐ Script principal (executável)
├── example_usage.py            # 📚 Exemplos de uso (executável)
├── test_recreator.py           # 🧪 Testes automatizados (executável)
├── recreate.sh                 # 🔧 Script bash helper (executável)
├── requirements.txt            # 📦 Dependências Python
├── README.md                   # 📖 Documentação completa
├── INDEX.md                    # 📋 Este arquivo
└── .gitignore                  # 🚫 Arquivos ignorados pelo git
```

## 📄 Descrição dos Arquivos

### recreate_database.py
**Arquivo principal do módulo**

Classe `DatabaseRecreator` que implementa:
- Conexão automática MySQL/PostgreSQL
- Coleta de metadados do banco
- Exclusão segura do banco
- Recriação com mesmos parâmetros
- Geração de relatórios JSON

**Uso CLI:**
```bash
python3 recreate_database.py --config ../../secrets/mysql_config.json --database nome_db
```

**Uso como módulo:**
```python
from recreate_database import DatabaseRecreator

recreator = DatabaseRecreator('config.json', 'database_name')
result = recreator.execute_full_recreation()
```

### example_usage.py
**Exemplos práticos de uso**

6 exemplos diferentes:
1. Recriação simples MySQL
2. PostgreSQL com force (termina conexões)
3. Execução passo a passo
4. Apenas coletar metadados (sem modificar)
5. Recriar múltiplos bancos
6. Recriação com validação

**Uso:**
```bash
python3 example_usage.py
# Escolha um exemplo no menu interativo
```

### test_recreator.py
**Suite de testes automatizados**

Testa:
- Carregamento de configs MySQL/PostgreSQL
- Detecção automática do tipo de banco
- Extração de parâmetros de conexão
- Estrutura de metadados
- Métodos da classe

**Uso:**
```bash
python3 test_recreator.py
```

### recreate.sh
**Helper bash para facilitar execução**

Modos:
- **Lista configs:** `./recreate.sh list`
- **Modo direto:** `./recreate.sh mysql_config.json perfexcrm_db`
- **Interativo:** `./recreate.sh` (sem argumentos)
- **Com force:** `./recreate.sh config.json database --force`

**Uso:**
```bash
# Listar configs disponíveis
./recreate.sh list

# Executar diretamente
./recreate.sh mysql_config.json perfexcrm_db

# Modo interativo
./recreate.sh
```

### requirements.txt
**Dependências Python**

```
pymysql>=1.0.2          # MySQL
psycopg2-binary>=2.9.3  # PostgreSQL
```

**Instalação:**
```bash
pip install -r requirements.txt
```

### README.md
**Documentação completa**

Contém:
- Descrição das funcionalidades
- Requisitos e instalação
- Guia de uso (CLI e módulo)
- Estrutura dos arquivos JSON
- Metadados coletados
- Exemplos práticos
- Troubleshooting

### __init__.py
**Inicializador do módulo Python**

Permite importar a classe diretamente:
```python
from recreate_db import DatabaseRecreator
```

### .gitignore
**Arquivos ignorados pelo git**

Ignora:
- `__pycache__/`
- Arquivos temporários
- Configs de teste
- Logs

## 🚀 Quick Start

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Executar Testes
```bash
python3 test_recreator.py
```

### 3. Usar o Módulo

**Opção A: CLI**
```bash
python3 recreate_database.py \
  --config ../../secrets/mysql_config.json \
  --database perfexcrm_db \
  --verbose
```

**Opção B: Script Helper**
```bash
./recreate.sh list                              # Lista configs
./recreate.sh mysql_config.json perfexcrm_db    # Executa
```

**Opção C: Código Python**
```python
from recreate_database import DatabaseRecreator

recreator = DatabaseRecreator('config.json', 'db_name')
result = recreator.execute_full_recreation()
```

## 🔍 Fluxo de Execução

```
1. Lê arquivo JSON de configuração
2. Detecta tipo do banco (MySQL/PostgreSQL)
3. Conecta ao servidor
4. Coleta metadados do banco
   - Charset, collation, encoding
   - Número de tabelas
   - Tamanho
5. Salva relatório JSON
6. Apaga banco de dados
7. Recria banco vazio (com mesmos parâmetros)
8. Fecha conexão
```

## 📊 Relatórios Gerados

Salvos em: `../../reports/recreate_{database}_{timestamp}.json`

Exemplo:
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
    "table_count": 42,
    "timestamp": "2026-03-05T10:09:49"
  },
  "config_file": "secrets/mysql_config.json",
  "timestamp": "20260305_100949"
}
```

## 🔧 Arquivos de Configuração

O módulo busca configs em: `../../secrets/`

Estruturas suportadas:

### MySQL
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

### PostgreSQL
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

## 📚 Recursos Adicionais

- [README.md](README.md) - Documentação completa
- [example_usage.py](example_usage.py) - 6 exemplos práticos
- [test_recreator.py](test_recreator.py) - Suite de testes

## ⚙️ Configurações Avançadas

### Flags da CLI

| Flag | Descrição |
|------|-----------|
| `-c, --config` | Caminho do JSON de configuração (obrigatório) |
| `-d, --database` | Nome do banco (obrigatório) |
| `--force` | Termina conexões ativas (PostgreSQL) |
| `--no-report` | Não gera relatório JSON |
| `-v, --verbose` | Modo DEBUG |

### Métodos da Classe

| Método | Descrição |
|--------|-----------|
| `connect()` | Conecta ao servidor |
| `collect_metadata()` | Coleta metadados |
| `drop_database()` | Apaga banco |
| `create_database()` | Cria banco vazio |
| `save_metadata_report()` | Salva relatório |
| `execute_full_recreation()` | Processo completo |
| `close()` | Fecha conexão |

## 🎯 Casos de Uso

1. **Limpar banco para testes:** Recria banco vazio mantendo estrutura
2. **Reset de ambiente:** Apaga dados mas mantém configurações
3. **Preparar migração:** Backup de metadados antes de mudanças
4. **Desenvolvimento:** Recria banco rapidamente
5. **CI/CD:** Automatiza preparação de ambientes

## ⚠️ Avisos de Segurança

1. ⚠️ **APAGA TODOS OS DADOS!** Use com cuidado
2. ✅ Confirmação obrigatória: digite 'SIM'
3. 💾 Relatório salvo antes da exclusão
4. 📋 Logs detalhados de todas operações
5. 🔒 Nunca commite senhas nos configs

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte [README.md](README.md)
2. Execute `python3 recreate_database.py --help`
3. Rode testes: `python3 test_recreator.py`
4. Veja exemplos: `python3 example_usage.py`

---

**Vya Digital - Database Migration Team**
*Enterprise Database Migration Project*
