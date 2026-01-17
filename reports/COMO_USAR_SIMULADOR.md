# 🚀 Como Usar o Simulador da Evolution API

**Arquivo:** `simulate_evolution_api.py`
**Propósito:** Simular acesso à Evolution API e validar configurações PostgreSQL
**Data:** 2 de novembro de 2025

---

## 📋 Comandos Básicos

### 1️⃣ Verificar Ajuda
```bash
python3 simulate_evolution_api.py --help
```

**Saída:**
```
usage: simulate_evolution_api.py [-h] --server {wf004,source,wfdb02,destination}
                                  [--database DATABASE] [--validate-all]
                                  [--list-users] [--check-permissions]
                                  [--verbose] [--report REPORT]

Simulador: Evolution API - Buscar Instâncias
```

---

## 🔍 Exemplos de Uso

### 2️⃣ Conectar ao banco Evolution API (RECOMENDADO)

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --verbose
```

**O que faz:**
- ✅ Conecta em `wfdb02.vya.digital:5432`
- ✅ Usa banco de dados `evolution_api_wea001_db`
- ✅ Mostra logs detalhados de conexão

**Esperado:**
```
2025-11-02 11:04:45 - __main__ - INFO - Conectando em wfdb02.vya.digital:5432/evolution_api_wea001_db...
2025-11-02 11:04:45 - __main__ - INFO - ✅ Conectado com sucesso!
```

---

### 3️⃣ Executar Todas as Validações

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --validate-all \
  --verbose
```

**Testes Executados:**
1. ✅ Conexão ao banco
2. ✅ Permissão SELECT na tabela `Instance`
3. ✅ Acesso a dados sensíveis (token)
4. ✅ Contagem de instâncias
5. ✅ Inserção de teste (transação)
6. ✅ Atualização de teste (transação)
7. ✅ Permissões de usuário
8. ✅ Verificação de schema

---

### 4️⃣ Listar Usuários do Banco

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --list-users \
  --verbose
```

**Saída Esperada:**
```
📊 Usuários do Banco:
- migration_user (role)
- postgres (superuser)
- backup (role)
- dynamic_user (role)
...
```

---

### 5️⃣ Verificar Permissões do Usuário Atual

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --check-permissions \
  --verbose
```

**Testes:**
- ✅ Pode fazer SELECT?
- ✅ Pode fazer INSERT?
- ✅ Pode fazer UPDATE?
- ✅ Pode ler dados sensíveis?

---

### 6️⃣ Gerar Relatório JSON

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --validate-all \
  --report test-results.json
```

**Arquivo Gerado:** `test-results.json`

```json
{
  "timestamp": "2025-11-02T11:05:30.123456Z",
  "server": "wfdb02",
  "database": "evolution_api_wea001_db",
  "total_tests": 8,
  "passed": 8,
  "failed": 0,
  "success_rate": 100.0,
  "tests": [
    {
      "name": "Conexão",
      "passed": true,
      "duration_ms": 120.5
    },
    ...
  ]
}
```

---

## 🎯 Comandos Recomendados por Cenário

### Cenário 1: Validação Inicial da Configuração

```bash
# 1. Teste simples de conexão
python3 simulate_evolution_api.py --server wfdb02 --database evolution_api_wea001_db

# 2. Com logs detalhados
python3 simulate_evolution_api.py --server wfdb02 --database evolution_api_wea001_db --verbose

# 3. Com relatório
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --validate-all \
  --report initial-validation.json
```

---

### Cenário 2: Verificar Permissões após Migração

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --check-permissions \
  --verbose
```

---

### Cenário 3: Auditar Usuários

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --list-users \
  --verbose
```

---

### Cenário 4: Teste Completo com Documentação

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --validate-all \
  --verbose \
  --report full-validation-$(date +%Y%m%d-%H%M%S).json
```

---

## 📊 Parâmetros Explicados

| Parâmetro | Obrigatório | Valores | Descrição |
|-----------|------------|---------|-----------|
| `--server` | ✅ Sim | `wf004`, `source`, `wfdb02`, `destination` | Qual servidor usar |
| `--database` | ❌ Não | string | Nome do banco (padrão: `postgres`) |
| `--validate-all` | ❌ Não | - | Executar todos os testes |
| `--list-users` | ❌ Não | - | Listar usuários do banco |
| `--check-permissions` | ❌ Não | - | Verificar permissões |
| `--verbose` | ❌ Não | - | Modo debug (mais logs) |
| `--report` | ❌ Não | filepath | Salvar resultado em JSON |

---

## 🔐 Configuração de Acesso

### Servidor: `wfdb02` (Banco Evolution)

**Arquivo de Config:** `secrets/postgresql_destination_config.json`

```json
{
  "server": {
    "host": "wfdb02.vya.digital",
    "port": 5432
  },
  "authentication": {
    "user": "migration_user",
    "password": "***[PROTEGIDO]***"
  }
}
```

**Como conectar:**
```bash
# Opção 1: Acesso direto (requer conectividade de rede)
python3 simulate_evolution_api.py --server wfdb02 --database evolution_api_wea001_db

# Opção 2: Via SSH Tunnel
ssh -L 5432:localhost:5432 archaris@82.197.64.145 -p 5010
# (em outro terminal)
python3 simulate_evolution_api.py --server wfdb02 --database evolution_api_wea001_db
```

---

## ✅ Verificação de Sucesso

### Conexão OK
```
✅ Conectado com sucesso!
```

### Todos os Testes Passaram
```
Taxa de sucesso: 100.0%
```

### Permissões Validadas
```
✅ Permissão SELECT confirmada
✅ Acesso a dados sensíveis confirmado
```

---

## ❌ Troubleshooting

### Erro: "Connection refused"
```
❌ Erro ao conectar: connection to server... failed: Connection refused
```

**Solução:**
- Verificar se servidor está online
- Usar SSH tunnel se estiver fora da rede
- Checar firewall

### Erro: "invalid dsn: invalid connection option"
```
❌ Erro inesperado: invalid dsn: invalid connection option
```

**Solução:**
- ✅ CORRIGIDO: Script agora usa `dbname=` em vez de `database=`
- Atualizar script para última versão

### Erro: "password authentication failed"
```
❌ Erro ao conectar: FATAL: password authentication failed
```

**Solução:**
- Verificar credenciais em `secrets/postgresql_destination_config.json`
- Validar usuário `migration_user` existe no banco
- Verificar se usuário tem permissão de conexão

### Erro: "database does not exist"
```
❌ Erro ao conectar: FATAL: database "evolution_api_wea001_db" does not exist
```

**Solução:**
- Criar banco: `CREATE DATABASE evolution_api_wea001_db;`
- Ou usar banco existente: `--database nome_correto`

---

## 📝 Exemplo Completo: Do Início ao Fim

```bash
# 1. Teste simples
python3 simulate_evolution_api.py --server wfdb02 --database evolution_api_wea001_db

# 2. Se conectou, validar tudo
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --validate-all \
  --verbose

# 3. Se passou, listar usuários
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --list-users

# 4. Salvar relatório final
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --validate-all \
  --report final-validation.json

# 5. Visualizar relatório
cat final-validation.json | python3 -m json.tool
```

---

## 🎓 Entendendo os Testes

### O que o Simulador Valida?

1. **Conexão SSH + PostgreSQL**
   - Acesso ao servidor remoto
   - Autenticação do usuário
   - Conectividade de rede

2. **Permissões de Banco**
   - `SELECT` na tabela `Instance`
   - `INSERT` para testes
   - `UPDATE` para testes
   - Acesso a dados sensíveis

3. **Integridade de Dados**
   - Tabelas existem
   - Colunas acessíveis
   - Índices funcionam

4. **Performance**
   - Tempo de resposta
   - Transações funcionam
   - Sem deadlocks

---

## 📞 Suporte

Para problemas:
1. Verificar logs com `--verbose`
2. Consultar relatório JSON com `--report`
3. Verificar arquivo de configuração em `secrets/postgresql_destination_config.json`
4. Testar conectividade: `nc -zv wfdb02.vya.digital 5432`

---

**Última Atualização:** 2 de novembro de 2025
**Versão:** 1.2 (com suporte a `--database`)
