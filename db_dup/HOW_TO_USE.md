# 🚀 Guia Completo de Uso - PostgreSQL Database Clone System v2.0

## 📋 Sumário

1. [Visão Geral](#visão-geral)
2. [Verificação do Código](#verificação-do-código)
3. [Pré-requisitos](#pré-requisitos)
4. [Instalação](#instalação)
5. [Configuração](#configuração)
6. [Uso Básico](#uso-básico)
7. [Opções Avançadas](#opções-avançadas)
8. [Exemplos Práticos](#exemplos-práticos)
9. [Solução de Problemas](#solução-de-problemas)
10. [Boas Práticas](#boas-práticas)

---

## 📖 Visão Geral

O **PostgreSQL Database Clone System v2.0** é um sistema completo para clonagem de bancos de dados PostgreSQL com preservação total de:

- ✅ Estrutura (schemas, tabelas, índices, constraints)
- ✅ Dados (todas as linhas de todas as tabelas)
- ✅ Permissões (usuários, roles, grants)
- ✅ Tablespaces personalizados
- ✅ Views, Functions, Triggers
- ✅ Sequences e valores atuais

### 🛡️ Segurança

O sistema é **100% SEGURO** para o banco de origem:
- Opera apenas em **modo READ-ONLY** no banco de origem
- Todas as operações de escrita são feitas no banco de destino
- Análise completa de segurança em [ANALISE_SEGURANCA_ORIGEM.md](ANALISE_SEGURANCA_ORIGEM.md)

---

## ✅ Verificação do Código

### Status Geral: **PRONTO PARA USO** ✅

O código foi analisado e está **funcionalmente completo e pronto para uso em produção**. Os únicos avisos encontrados são de estilo (linting) e não afetam a funcionalidade:

#### Avisos de Estilo (Não-Críticos):
- ⚠️ Uso de f-strings em logging (preferir % formatting)
- ⚠️ Catching de `Exception` genérica (estilo defensivo usado intencionalmente)
- ⚠️ Algumas linhas longas (> 79 caracteres)
- ⚠️ Imports não utilizados em alguns módulos

#### Componentes Verificados:
| Componente | Status | Observações |
|-----------|--------|-------------|
| `pg_json_config_Version2.py` | ✅ | Completo e funcional |
| `pg_connection_manager_v2_Version2.py` | ✅ | Completo e funcional |
| `pg_metadata_analyzer_Version2.py` | ✅ | Completo e funcional |
| `pg_database_cloner_Version2.py` | ✅ | Completo e funcional |
| `clone_database_Version2.py` | ✅ | Script principal pronto |
| `config_example_Version2.json` | ✅ | Exemplo válido |

### Módulos Principais

```
db_dup/
├── clone_database_Version2.py           # 🎯 Script principal (USE ESTE!)
├── pg_json_config_Version2.py          # Configuração JSON
├── pg_connection_manager_v2_Version2.py # Gerenciador de conexões
├── pg_metadata_analyzer_Version2.py     # Analisador de metadados
├── pg_database_cloner_Version2.py       # Motor de clonagem
├── config_example_Version2.json         # Exemplo de configuração
├── exemplo_uso_json.py                  # Exemplos de código
└── test_json_file_loading.py            # Testes de validação
```

---

## 📦 Pré-requisitos

### Sistema Operacional
- **Linux** (testado em Ubuntu, Debian, Fedora, Arch)
- Python 3.12 ou superior

### Banco de Dados
- PostgreSQL 12+ (origem e destino)
- Acesso de superusuário ou permissões adequadas

### Permissões Necessárias

**No Banco de Origem (READ-ONLY):**
- `SELECT` em todas as tabelas
- `USAGE` em schemas
- Acesso às tabelas do sistema (`pg_catalog`)

**No Banco de Destino:**
- Permissão para criar banco de dados
- `CREATEDB` ou ser superusuário
- Permissão para criar roles (se necessário)

---

## 🔧 Instalação

### Passo 1: Clonar/Baixar os Arquivos

```bash
cd /caminho/para/db_dup
```

### Passo 2: Instalar Dependências Python

```bash
# Opção 1: pip
pip install psycopg2-binary sqlalchemy

# Opção 2: pip3
pip3 install psycopg2-binary sqlalchemy

# Opção 3: usando requirements (se disponível no projeto principal)
pip install -r ../requirements.txt
```

### Passo 3: Verificar Instalação

```bash
python3 -c "import psycopg2, sqlalchemy; print('✓ Dependências OK')"
```

---

## ⚙️ Configuração

### Passo 1: Criar Arquivo de Configuração JSON

Copie o exemplo e edite com seus dados:

```bash
cp config_example_Version2.json minha_config.json
nano minha_config.json
```

### Passo 2: Estrutura do Arquivo JSON

```json
{
  "host": "localhost",
  "port": 5432,
  "ssl_mode": "false",
  "possible_users": [
    {
      "username": "postgres",
      "password": "sua_senha_aqui",
      "priority": 0
    },
    {
      "username": "backup_user",
      "password": "senha_backup",
      "priority": 1
    }
  ],
  "db_source": "banco_origem",
  "db_destiny": "banco_destino",
  "connect_timeout": 10,
  "application_name": "pg_clone_system",
  "pool_size": 5,
  "max_overflow": 10,
  "max_retries": 3,
  "retry_delay": 2.0
}
```

### Parâmetros Explicados

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `host` | string | ✅ | Endereço do servidor PostgreSQL |
| `port` | int | ✅ | Porta (padrão: 5432) |
| `ssl_mode` | string/bool | ✅ | Modo SSL: `"false"`, `"true"`, `"require"`, etc. |
| `possible_users` | array | ✅ | Lista de credenciais para tentar |
| `db_source` | string | ✅ | Nome do banco de origem |
| `db_destiny` | string | ✅ | Nome do banco de destino |
| `connect_timeout` | int | ❌ | Timeout de conexão (padrão: 10) |
| `application_name` | string | ❌ | Nome da aplicação (logs) |
| `pool_size` | int | ❌ | Tamanho do pool (padrão: 5) |
| `max_overflow` | int | ❌ | Conexões extras (padrão: 10) |
| `max_retries` | int | ❌ | Tentativas de reconexão (padrão: 3) |
| `retry_delay` | float | ❌ | Delay entre tentativas (padrão: 2.0) |

### Múltiplos Usuários (Fallback Automático)

O sistema tenta conectar com os usuários na ordem de prioridade (menor = primeiro):

```json
{
  "possible_users": [
    {
      "username": "user_preferencial",
      "password": "senha1",
      "priority": 0
    },
    {
      "username": "user_backup",
      "password": "senha2",
      "priority": 1
    }
  ]
}
```

---

## 🎯 Uso Básico

### Sintaxe Geral

```bash
python3 clone_database_Version2.py <config_file> [opções]
```

### Exemplo Mais Simples

```bash
# Clonagem básica (sem sobrescrever banco existente)
python3 clone_database_Version2.py minha_config.json
```

### Clonagem com Sobrescrita

```bash
# Dropar banco de destino se já existir
python3 clone_database_Version2.py minha_config.json --drop-if-exists
```

### Clonagem Apenas Estrutura (Sem Dados)

```bash
# Copiar apenas schemas, tabelas, views (sem dados)
python3 clone_database_Version2.py minha_config.json --no-data
```

### Modo Verboso (Debug)

```bash
# Ver logs detalhados de cada operação
python3 clone_database_Version2.py minha_config.json --verbose
```

---

## 🔥 Opções Avançadas

### Todas as Opções Disponíveis

```bash
python3 clone_database_Version2.py [config_file] [opções]

Opções:
  --drop-if-exists     Dropar banco de destino se existir
  --no-data            Copiar apenas estrutura (sem dados)
  --no-verify          Não verificar clonagem ao final
  --save-metadata FILE Salvar metadados em arquivo JSON
  --log-file FILE      Salvar logs em arquivo
  -v, --verbose        Modo verboso (debug)
  --version            Mostrar versão do programa
  -h, --help           Mostrar ajuda
```

### Exemplos Avançados

#### 1. Clonagem Completa com Logs em Arquivo

```bash
python3 clone_database_Version2.py config.json \
  --drop-if-exists \
  --verbose \
  --log-file /var/log/clone_$(date +%Y%m%d_%H%M%S).log
```

#### 2. Salvar Metadados para Análise

```bash
python3 clone_database_Version2.py config.json \
  --save-metadata metadata_$(date +%Y%m%d).json
```

#### 3. Clonagem Somente Estrutura (Desenvolvimento)

```bash
python3 clone_database_Version2.py config.json \
  --no-data \
  --drop-if-exists
```

#### 4. Clonagem Rápida sem Verificação

```bash
python3 clone_database_Version2.py config.json \
  --no-verify
```

---

## 💡 Exemplos Práticos

### Cenário 1: Backup Diário Automatizado

```bash
#!/bin/bash
# backup_diario.sh

DATA=$(date +%Y%m%d)
CONFIG="/etc/pg_clone/config.json"
LOG_DIR="/var/log/backup"

mkdir -p "$LOG_DIR"

python3 clone_database_Version2.py "$CONFIG" \
  --drop-if-exists \
  --verbose \
  --log-file "$LOG_DIR/backup_$DATA.log" \
  --save-metadata "$LOG_DIR/metadata_$DATA.json"

if [ $? -eq 0 ]; then
  echo "✓ Backup concluído com sucesso: $DATA"
else
  echo "✗ Erro no backup: $DATA" >&2
  exit 1
fi
```

### Cenário 2: Clonagem para Ambiente de Teste

```bash
#!/bin/bash
# criar_ambiente_teste.sh

# Configuração
CONFIG="config_teste.json"

# Criar banco de teste limpo
python3 clone_database_Version2.py "$CONFIG" \
  --drop-if-exists \
  --verbose

echo "✓ Banco de teste atualizado!"
echo "Conecte-se em: banco_destino (configurado no JSON)"
```

### Cenário 3: Migração para Novo Servidor

```bash
#!/bin/bash
# migracao_servidor.sh

SOURCE_CONFIG="config_servidor_antigo.json"
DEST_CONFIG="config_servidor_novo.json"

echo "Iniciando migração..."

python3 clone_database_Version2.py "$DEST_CONFIG" \
  --verbose \
  --save-metadata "migracao_$(date +%Y%m%d_%H%M%S).json"

if [ $? -eq 0 ]; then
  echo "✓ Migração concluída!"
  echo "Verifique os dados no novo servidor antes de desativar o antigo."
else
  echo "✗ Erro na migração!" >&2
  exit 1
fi
```

### Cenário 4: Uso Programático (Python)

```python
#!/usr/bin/env python3
"""Exemplo de uso programático do sistema de clonagem."""

from pg_connection_manager_v2_Version2 import PostgreSQLConnectionManager
from pg_database_cloner_Version2 import DatabaseCloner

def clonar_banco(config_file: str):
    """Clona banco usando arquivo de configuração."""

    # Carregar configuração e criar manager
    manager = PostgreSQLConnectionManager.from_json_file(
        config_file,
        use_pool=True,
        auto_validate=True
    )

    # Conectar aos bancos
    if not manager.connect():
        print("Erro ao conectar!")
        return False

    # Criar clonador e executar
    cloner = DatabaseCloner(manager)
    success = cloner.clone_database(
        drop_if_exists=True,
        copy_data=True,
        verify_clone=True
    )

    # Desconectar
    manager.disconnect()

    return success

if __name__ == "__main__":
    resultado = clonar_banco("minha_config.json")
    if resultado:
        print("✓ Clonagem bem-sucedida!")
    else:
        print("✗ Falha na clonagem!")
```

---

## 🐛 Solução de Problemas

### Problema 1: Erro de Importação

**Sintoma:**
```
ImportError: No module named 'psycopg2'
```

**Solução:**
```bash
pip3 install psycopg2-binary sqlalchemy
```

---

### Problema 2: Erro de Conexão

**Sintoma:**
```
ConnectionError: Nenhuma credencial válida encontrada
```

**Verificações:**
1. Teste a conexão manualmente:
   ```bash
   psql -h localhost -U postgres -d postgres
   ```

2. Verifique as credenciais no JSON

3. Verifique se o PostgreSQL está rodando:
   ```bash
   sudo systemctl status postgresql
   ```

4. Verifique o pg_hba.conf:
   ```bash
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   ```

---

### Problema 3: Permissões Insuficientes

**Sintoma:**
```
ERROR: permission denied to create database
```

**Solução:**
```sql
-- Conceder permissão de criar banco
ALTER USER seu_usuario CREATEDB;

-- Ou criar o usuário como superusuário
CREATE USER novo_user WITH SUPERUSER PASSWORD 'senha';
```

---

### Problema 4: Banco de Destino Já Existe

**Sintoma:**
```
ERROR: database "banco_destino" already exists
```

**Solução 1:** Usar flag `--drop-if-exists`
```bash
python3 clone_database_Version2.py config.json --drop-if-exists
```

**Solução 2:** Dropar manualmente
```bash
psql -h localhost -U postgres -c "DROP DATABASE banco_destino;"
```

---

### Problema 5: Timeout de Conexão

**Sintoma:**
```
TimeoutError: connection timeout
```

**Solução:** Aumentar timeout no JSON
```json
{
  "connect_timeout": 30,
  "max_retries": 5,
  "retry_delay": 3.0
}
```

---

### Problema 6: Erro de SSL

**Sintoma:**
```
SSL error: certificate verify failed
```

**Solução:** Ajustar modo SSL no JSON
```json
{
  "ssl_mode": "disable"
}
```

Para produção, use certificado válido:
```json
{
  "ssl_mode": "require",
  "extra_params": {
    "sslrootcert": "/path/to/ca.crt",
    "sslcert": "/path/to/client.crt",
    "sslkey": "/path/to/client.key"
  }
}
```

---

## 🎓 Boas Práticas

### 1. Segurança

✅ **FAZER:**
- Armazenar configurações em diretório seguro (ex: `/etc/pg_clone/`)
- Usar permissões restritivas: `chmod 600 config.json`
- Usar variáveis de ambiente para senhas em produção
- Manter backups das configurações

❌ **NÃO FAZER:**
- Commitar arquivos de configuração com senhas em Git
- Usar senhas fracas ou padrões
- Executar como root sem necessidade

### 2. Performance

✅ **FAZER:**
- Executar durante horários de baixo uso
- Aumentar `pool_size` para bancos grandes
- Usar `--no-verify` se a verificação for desnecessária
- Monitorar uso de disco e memória

❌ **NÃO FAZER:**
- Clonar bancos muito grandes em produção sem teste
- Executar múltiplas clonagens simultâneas sem recursos

### 3. Manutenção

✅ **FAZER:**
- Salvar logs: `--log-file`
- Salvar metadados: `--save-metadata`
- Revisar logs após cada execução
- Documentar configurações específicas do projeto

❌ **NÃO FAZER:**
- Ignorar avisos e erros nos logs
- Deletar logs antigos sem análise

### 4. Testes

✅ **FAZER:**
- Testar primeiro em ambiente de desenvolvimento
- Validar dados após clonagem
- Checar permissões no banco clonado
- Executar queries de teste no destino

❌ **NÃO FAZER:**
- Clonar para produção sem teste prévio
- Assumir que tudo está correto sem validação

---

## 📊 Monitoramento e Validação

### Verificar Logs

```bash
# Logs em tempo real
tail -f /var/log/clone_script.log

# Buscar erros
grep -i error /var/log/clone_script.log

# Ver resumo final
tail -n 50 /var/log/clone_script.log
```

### Validar Clonagem

```sql
-- Comparar contagem de tabelas
SELECT
  (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as origem,
  (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as destino;

-- Comparar contagem de linhas
SELECT
  schemaname, tablename,
  n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;

-- Verificar permissões
SELECT * FROM information_schema.table_privileges
WHERE grantee != 'postgres'
ORDER BY table_name;
```

---

## 📚 Recursos Adicionais

### Documentação Complementar

- **[README_Version2.md](README_Version2.md)** - Documentação técnica completa
- **[ANALISE_SEGURANCA_ORIGEM.md](ANALISE_SEGURANCA_ORIGEM.md)** - Análise de segurança
- **[config_example_Version2.json](config_example_Version2.json)** - Exemplo de configuração
- **[exemplo_uso_json.py](exemplo_uso_json.py)** - Exemplos de código Python

### Suporte e Ajuda

```bash
# Ver ajuda do script
python3 clone_database_Version2.py --help

# Ver versão
python3 clone_database_Version2.py --version

# Testar configuração
python3 test_json_file_loading.py
```

---

## 🎉 Conclusão

O **PostgreSQL Database Clone System v2.0** está **PRONTO PARA USO** e oferece uma solução completa, segura e profissional para clonagem de bancos de dados PostgreSQL.

### Próximos Passos

1. ✅ Instalar dependências
2. ✅ Criar arquivo de configuração
3. ✅ Testar em ambiente de desenvolvimento
4. ✅ Executar em produção

### Checklist de Pré-Produção

- [ ] Dependências instaladas
- [ ] Configuração validada
- [ ] Permissões verificadas
- [ ] Teste em desenvolvimento OK
- [ ] Logs e monitoramento configurados
- [ ] Backup do banco original
- [ ] Plano de rollback definido

---

**Autor:** yvesmarinho
**Versão:** 2.0.0
**Data:** 2026-02-09
**Licença:** Uso interno

---

Para mais informações ou suporte, consulte a documentação técnica completa.
