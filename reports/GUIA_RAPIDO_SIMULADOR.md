# 🚀 Guia Rápido: Simulador Evolution API

**⏱️ Tempo de leitura:** 5 minutos
**🎯 Objetivo:** Validar configurações de acesso ao Evolution API

---

## 📋 O que Você Precisa Saber

### Problema
O banco PostgreSQL `evolution_db` estava inacessível devido a permissões incorretas.

### Solução
Criamos um **simulador que testa o acesso** e **valida que as permissões estão corretas**.

---

## 🚀 Como Usar

### 1️⃣ Verificar que o script existe

```bash
ls -lh simulate_evolution_api.py
# Output: -rwxr-xr-x simulate_evolution_api.py
```

### 2️⃣ Ver opções disponíveis

```bash
python3 simulate_evolution_api.py --help
```

**Saída esperada:**
```
usage: simulate_evolution_api.py [-h] --server {wf004,source,wfdb02,destination}
                                 [--validate-all] [--list-users]
                                 [--check-permissions] [--verbose]
                                 [--report REPORT]

Simulador: Evolution API - Buscar Instâncias

options:
  --server {wf004,source,wfdb02,destination}  Servidor PostgreSQL
  --validate-all                               Executar todas as validações
  --list-users                                 Listar usuários do banco
  --check-permissions                          Verificar permissões
  --verbose                                    Modo debug
  --report REPORT                              Salvar relatório em JSON
```

### 3️⃣ Configurar Acesso ao PostgreSQL

**Opção A: SSH Tunnel (Recomendado)**

```bash
# Terminal 1: Criar tunnel
ssh -L 5432:localhost:5432 user@wfdb02.vya.digital

# Deixe essa janela aberta...
```

**Opção B: Acesso Direto (Se VPN ativa)**

```bash
# Modificar arquivo de config
nano secrets/postgresql_destination_config.json

# Mudar "host" de "localhost" para o IP direto:
# "host": "82.197.64.145"
```

### 4️⃣ Executar o Simulador

```bash
# Teste simples (sem validações completas)
python3 simulate_evolution_api.py --server wfdb02 --verbose

# Com validações completas
python3 simulate_evolution_api.py --server wfdb02 --validate-all --verbose

# Com relatório
python3 simulate_evolution_api.py --server wfdb02 --validate-all --report resultado.json

# Listar usuários
python3 simulate_evolution_api.py --server wfdb02 --list-users

# Verificar permissões
python3 simulate_evolution_api.py --server wfdb02 --check-permissions
```

### 5️⃣ Revisar Resultado

```bash
# Ver relatório JSON
cat resultado.json | python3 -m json.tool

# Ou com pretty print
python3 -c "import json; print(json.dumps(json.load(open('resultado.json')), indent=2))"
```

---

## 📊 O Que o Simulador Valida

| # | Validação | Esperado | Comando |
|---|-----------|----------|---------|
| 1 | Conexão ao PostgreSQL | ✅ Conecta | `--validate-all` |
| 2 | Banco `evolution_db` existe | ✅ Existe | `--validate-all` |
| 3 | Tabelas existem | ✅ 5+ tabelas | `--validate-all` |
| 4 | Permissões do usuário | ✅ SELECT, INSERT, UPDATE, DELETE | `--check-permissions` |
| 5 | Instâncias criadas | ✅ 1+ instâncias | `--validate-all` |
| 6 | Mensagens registradas | ✅ 0+ mensagens | `--validate-all` |
| 7 | Integridade dos dados | ✅ Sem erros | `--validate-all` |

---

## ⚡ Casos de Uso Rápidos

### Caso 1: Só Verificar Conexão

```bash
python3 simulate_evolution_api.py --server wfdb02
```

**Se funcionar:**
```
✅ Conectado com sucesso!
```

**Se falhar:**
```
❌ Erro ao conectar: Connection refused
   (Configure SSH tunnel primeiro)
```

---

### Caso 2: Validar Permissões Aplicadas

```bash
python3 simulate_evolution_api.py --server wfdb02 --check-permissions --verbose
```

**Resultado esperado:**
```
✅ Usuário migration_user tem permissões:
   - SELECT em Instance
   - INSERT em Instance
   - UPDATE em Instance
   - DELETE em Instance
   - SELECT em Message
   - SELECT em Settings
```

---

### Caso 3: Listar Instâncias WhatsApp

```bash
python3 simulate_evolution_api.py --server wfdb02 --validate-all
```

**Resultado esperado:**
```
✅ Instâncias encontradas:
   1. nome: "wa-bot-1"
      status: "connected"
      numero: "5511999999999"
      integração: "BAILEYS"

   2. nome: "wa-bot-2"
      status: "disconnected"
      numero: null
      integração: "META"
```

---

### Caso 4: Gerar Relatório para Documentação

```bash
python3 simulate_evolution_api.py \
  --server wfdb02 \
  --validate-all \
  --verbose \
  --report relatorio-validacao.json

# Depois compartilhar
cat relatorio-validacao.json
```

---

## 🔧 Troubleshooting

### Erro: Connection refused

```
❌ Erro ao conectar: connection to server at "localhost" (127.0.0.1),
   port 5432 failed: Connection refused
```

**Solução:**

```bash
# 1. Verificar se SSH tunnel está ativo
ssh -L 5432:localhost:5432 user@wfdb02.vya.digital &

# 2. Ou usar IP direto
nano secrets/postgresql_destination_config.json
# Mudar host para: 82.197.64.145
```

---

### Erro: Permission denied (publickey)

```
❌ Permission denied (publickey)
```

**Solução:**

```bash
# 1. Verificar chave SSH
ssh-keygen -t rsa

# 2. Adicionar chave ao servidor
ssh-copy-id -i ~/.ssh/id_rsa.pub user@wfdb02.vya.digital

# 3. Tentar novamente
ssh -L 5432:localhost:5432 user@wfdb02.vya.digital
```

---

### Erro: Database does not exist

```
❌ banco 'evolution_db' não existe
```

**Solução:**

```bash
# Criar banco primeiro
python3 run_fix_evolution_permissions.py --server wfdb02 --execute

# Depois validar
python3 simulate_evolution_api.py --server wfdb02 --validate-all
```

---

## 📈 Interpretar Resultados

### Teste Passou (✅)

```
✅ PASSOU: Conexão ao Servidor PostgreSQL
   ✅ Conectado em localhost:5432
   Duração: 125ms
```

Significa: O teste funcionou e a validação passou.

---

### Teste Falhou (❌)

```
❌ FALHOU: Permissões de Usuário
   ❌ Usuário não tem permissão de INSERT
   Detalhes: permission denied for schema public
```

Significa: A permissão não foi aplicada. Execute:

```bash
# Aplicar permissões
python3 run_fix_evolution_permissions.py --server wfdb02 --execute --verbose

# Depois validar novamente
python3 simulate_evolution_api.py --server wfdb02 --check-permissions
```

---

### Teste Aguardando (⏳)

```
⏳ AGUARDANDO: Instâncias Evolution
   ⚠️ Servidor não acessível
```

Significa: PostgreSQL não está acessível. Configure SSH tunnel.

---

## 📊 Interpretação do Relatório JSON

### Arquivo gerado

```bash
python3 simulate_evolution_api.py --server wfdb02 --validate-all --report resultado.json
```

### Visualizar

```json
{
  "timestamp": "2025-11-02T11:00:00Z",
  "server": "wfdb02",
  "total_tests": 7,
  "passed": 7,
  "failed": 0,
  "success_rate": 100.0,
  "tests": [
    {
      "name": "Conexão ao Servidor PostgreSQL",
      "passed": true,
      "message": "Conectado em localhost:5432",
      "duration_ms": 125.5,
      "details": {
        "host": "localhost",
        "port": 5432
      }
    },
    ...
  ]
}
```

### Interpretar

| Campo | Significado |
|-------|-----------|
| `success_rate` | 100% = Tudo OK, <100% = Alguns testes falharam |
| `passed` | Quantidade de testes que passaram |
| `failed` | Quantidade de testes que falharam |
| `duration_ms` | Tempo gasto em cada teste |

---

## ✅ Checklist de Validação

- [ ] SSH tunnel configurado ou VPN ativa
- [ ] Pode fazer ping em `wfdb02.vya.digital`
- [ ] Script `simulate_evolution_api.py` existe
- [ ] Executou com `--help` com sucesso
- [ ] Executou validação com `--validate-all`
- [ ] Todos os 7 testes passaram
- [ ] Gerou relatório JSON
- [ ] Permissões estão funcionando

---

## 📞 Próximas Etapas

### Se Tudo Passou ✅

```
1. Salvar relatório para documentação
2. Validar que Evolution API está funcionando
3. Testar criar/enviar mensagens WhatsApp
4. Documentar resultado
```

### Se Algo Falhou ❌

```
1. Executar com --verbose para mais detalhes
python3 simulate_evolution_api.py --server wfdb02 --validate-all --verbose

2. Executar correção de permissões novamente
python3 run_fix_evolution_permissions.py --server wfdb02 --execute --verbose

3. Revalidar
python3 simulate_evolution_api.py --server wfdb02 --check-permissions
```

---

## 📚 Mais Informações

| Arquivo | Conteúdo |
|---------|----------|
| `SUMARIO_SIMULADOR_EVOLUÇÃO.md` | Visão geral completa |
| `ANALISE_EVOLUÇÃO_API_PERMISSÕES.md` | Análise técnica detalhada |
| `ANALISE_EXECUCAO_SIMULADOR.md` | Relatório de execução |
| `simulate_evolution_api.py` | Código-fonte do simulador |

---

## 🎯 Objetivo Alcançado

✅ Simulador criado
✅ Validações implementadas
✅ Documentação completa
✅ Pronto para usar

**Próximo passo:** Conectar e validar!

---

**Versão:** 1.0
**Data:** 2 de novembro de 2025
**Status:** Pronto para Produção
