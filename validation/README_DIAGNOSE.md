# Como Executar o Diagnóstico de Permissões

## Scripts Disponíveis

### 1. `diagnose_journey_permissions.py` - Diagnóstico Genérico
Analisa permissões de **múltiplos usuários** em bancos de dados PostgreSQL.

### 2. `fix_database_permissions.py` - Correção Automática
Analisa e **corrige automaticamente** permissões de usuários em um banco específico.

---

## 1. Diagnóstico de Múltiplos Usuários

### Execução Básica

```bash
python3 validation/diagnose_journey_permissions.py
```

### Fluxo Interativo

O script vai solicitar:

#### **Passo 1: Nome do Banco**
```
Digite o nome do banco de dados:
> metabase_db
```

#### **Passo 2: Sugestões Automáticas**
O script sugere usuários baseado no nome do banco:
```
Usuários sugeridos para o banco metabase_db:
  - metabase_user
  - metabase_readonly
```

#### **Passo 3: Ver Todos os Usuários (Opcional)**
```
Deseja ver todos os usuários do servidor? (s/n):
> s

Usuários disponíveis no servidor:
   1. journey_user
   2. journey_readonly
   3. metabase_user
   4. metabase_readonly
   5. chatwoot_user
   6. analytics_user
```

#### **Passo 4: Selecionar Usuários**
```
Digite o(s) nome(s) do(s) usuário(s) a analisar:
(Separados por vírgula para múltiplos usuários)
(Enter para usar os usuários sugeridos)
> metabase_user, metabase_readonly
```

Ou simplesmente pressione **Enter** para usar os usuários sugeridos.

#### **Passo 5: Bancos Adicionais (Opcional)**
```
Deseja testar acesso a bancos específicos? (s/n):
> s

Digite os nomes dos bancos separados por vírgula:
> metabase_db, analytics_db
```

### Exemplo Completo

```bash
$ python3 validation/diagnose_journey_permissions.py

================================================================================
DIAGNÓSTICO DE PERMISSÕES - PostgreSQL
================================================================================

Digite o nome do banco de dados:
> journey

Usuários sugeridos para o banco journey:
  - journey_user
  - journey_readonly

Deseja ver todos os usuários do servidor? (s/n):
> n

Digite o(s) nome(s) do(s) usuário(s) a analisar:
(Separados por vírgula para múltiplos usuários)
(Enter para usar os usuários sugeridos)
>

Usando usuários sugeridos

Usuários a analisar: 2
  - journey_user
  - journey_readonly

Deseja testar acesso a bancos específicos? (s/n):
> s

Digite os nomes dos bancos separados por vírgula:
> journey_db, analytics_db

================================================================================
ANALISANDO USUÁRIO 1/2: journey_user
================================================================================

➜ 1. Conectando ao PostgreSQL (usuário admin)
------------------------------------------------------------

Conectando como: migration_user
[✓] Conectado como migration_user

➜ 2. Verificando Role do Usuário (journey_user)
------------------------------------------------------------

...
```

### Saída

O script gera:

1. **Análise detalhada** de cada usuário no terminal
2. **Relatórios JSON** individuais em `reports/diagnosis_<usuario>_<timestamp>.json`
3. **Sumário consolidado** ao final com status de todos os usuários
4. **Recomendações SQL** para correção de problemas

---

## 2. Correção Automática de Permissões

### Execução

```bash
python3 validation/fix_database_permissions.py
```

### Fluxo Interativo

#### **Passo 1: Nome do Banco**
```
Digite o nome do banco de dados:
> metabase_db
```

#### **Passo 2: Aplicar Correções?**
```
Aplicar correções automaticamente? (s/n):
> s
```

#### **Passo 3: Criar Usuários?**
```
Criar usuários se não existirem? (s/n):
> s
```

### O que o script faz automaticamente:

✅ Verifica usuários `<database>_user` e `<database>_readonly`
✅ Cria usuários que não existem (se autorizado)
✅ Concede permissão `CONNECT` no banco
✅ Concede permissão `USAGE` no schema public
✅ Concede permissões nas tabelas:
   - **_user**: SELECT, INSERT, UPDATE, DELETE
   - **_readonly**: apenas SELECT
✅ Configura privilégios padrão para futuras tabelas
✅ Gera relatório JSON em `reports/`

---

## Exemplos Práticos

### Exemplo 1: Diagnosticar um único usuário

```bash
python3 validation/diagnose_journey_permissions.py
```
```
Digite o nome do banco de dados:
> chatwoot_db

Digite o(s) nome(s) do(s) usuário(s) a analisar:
> chatwoot_user
```

### Exemplo 2: Diagnosticar usuário principal + readonly

```bash
python3 validation/diagnose_journey_permissions.py
```
```
Digite o nome do banco de dados:
> metabase_db

Digite o(s) nome(s) do(s) usuário(s) a analisar:
> [Enter para usar sugeridos]
```

### Exemplo 3: Diagnosticar todos os usuários de um serviço

```bash
python3 validation/diagnose_journey_permissions.py
```
```
Digite o nome do banco de dados:
> journey_db

Digite o(s) nome(s) do(s) usuário(s) a analisar:
> journey_user, journey_readonly, journey_admin, analytics_user
```

### Exemplo 4: Corrigir permissões automaticamente

```bash
python3 validation/fix_database_permissions.py
```
```
Digite o nome do banco de dados:
> metabase_db

Aplicar correções automaticamente? (s/n):
> s

Criar usuários se não existirem? (s/n):
> s
```

---

## Padrões de Nomenclatura

O sistema segue o padrão:

```
<nome_do_banco>_user      → Permissões completas (SELECT, INSERT, UPDATE, DELETE)
<nome_do_banco>_readonly  → Apenas leitura (SELECT)
```

**Exemplos:**
- `journey_db` → `journey_user`, `journey_readonly`
- `metabase_db` → `metabase_user`, `metabase_readonly`
- `chatwoot_db` → `chatwoot_user`, `chatwoot_readonly`

---

## Relatórios Gerados

### Localização
```
reports/diagnosis_<usuario>_<timestamp>.json
reports/fix_permissions_<database>_<timestamp>.json
```

### Conteúdo do Relatório
```json
{
  "timestamp": "2026-01-16T15:30:00",
  "user": "metabase_user",
  "database": "metabase_db",
  "server": "wfdb02.vya.digital",
  "connected": true,
  "role_info": { ... },
  "schema_permissions": { ... },
  "table_permissions": { ... },
  "issues": [ ... ],
  "summary": "Diagnóstico completo com 3 problema(s) identificado(s)"
}
```

---

## Requisitos

### Arquivo de Credenciais
O script precisa do arquivo:
```
secrets/postgresql_destination_config.json
```

**Formato:**
```json
{
  "authentication": {
    "user": "migration_user",
    "password": "sua_senha_admin"
  },
  "server": {
    "host": "wfdb02.vya.digital",
    "port": 5432
  }
}
```

### Dependências Python
```bash
pip install sqlalchemy psycopg2-binary
```

---

## Troubleshooting

### Erro: "Arquivo de configuração não encontrado"
➡️ Certifique-se que existe: `secrets/postgresql_destination_config.json`

### Erro: "ERRO ao carregar credenciais do admin"
➡️ Verifique o formato JSON do arquivo de configuração

### Erro: "Falha ao conectar"
➡️ Verifique:
- Host e porta estão corretos
- Senha do usuário admin está correta
- Firewall permite conexão ao PostgreSQL

### Nenhum problema encontrado, mas ainda há erros de acesso
➡️ Execute `fix_database_permissions.py` para correção automática

---

## Modo Não-Interativo (Futuro)

Para uso em scripts, você pode passar argumentos:

```bash
# A implementar
python3 validation/diagnose_journey_permissions.py \
  --database metabase_db \
  --users "metabase_user,metabase_readonly" \
  --test-databases "metabase_db,analytics_db"
```

---

## Contato

Para dúvidas ou problemas, consulte a documentação completa do projeto.
