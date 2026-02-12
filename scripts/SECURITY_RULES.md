# 🔐 Regras de Segurança - setup_database_user_permissions.py

## 📋 Visão Geral

O script `setup_database_user_permissions.py` implementa regras rígidas de segurança para prevenir a criação acidental de usuários com permissões excessivas.

---

## 🚨 Regra 1: Tipo 'backup' Não Pode Ser Global

### Problema
Usuários do tipo `backup` com acesso global a todas as databases representam um risco de segurança significativo.

### Solução Implementada
**Tipo 'backup' SEMPRE requer database específica.**

### ❌ Bloqueado

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username backup_user \
    --password backup_pass \
    --type backup
# SEM --database = BLOQUEADO
```

**Mensagem de erro:**
```
======================================================================
🚨 ERRO DE SEGURANÇA: Tipo 'backup' não pode ter acesso global
======================================================================

Usuários do tipo 'backup' devem ser restritos a databases específicas.
Use o parâmetro --database para especificar a database.

Exemplo:
  --database app_workforce --type backup

❌ Operação cancelada por motivos de segurança.
```

### ✅ Correto

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username backup_user \
    --password backup_pass \
    --type backup \
    --database app_workforce  # ✅ Database específica
```

---

## ⚠️ Regra 2: Acesso Global Requer Confirmação Explícita

### Problema
Criar usuários com acesso a TODAS as databases pode ser perigoso se feito acidentalmente.

### Solução Implementada
**Sistema solicita confirmação explícita digitando 'SIM'**

### Comportamento

Quando você **NÃO** especifica `--database`, o sistema:

1. Lista quantas databases serão afetadas
2. Mostra exemplos das databases
3. Exibe o tipo de permissão que será concedido
4. Solicita que você digite **exatamente** `SIM` para confirmar

### Exemplo de Uso

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username readonly_global \
    --password readonly_pass \
    --type read
# SEM --database = Solicitará confirmação
```

**O sistema exibirá:**

```
======================================================================
⚠️  ATENÇÃO: ACESSO GLOBAL A TODAS AS DATABASES
======================================================================

🔓 O usuário 'readonly_global' terá permissões em 47 databases:
   • ai_process_db
   • app_workforce
   • botpress_db
   • evolution_api_1
   • evolution_api_2
   ... e mais 42 databases

⚠️  Tipo de permissão: 'read'

======================================================================

Deseja continuar? (digite 'SIM' para confirmar): _
```

### Opções de Resposta

| Digitação | Resultado |
|-----------|-----------|
| `SIM` | ✅ Continua e cria o usuário com acesso global |
| Qualquer outra coisa | ❌ Cancela a operação |
| `sim` (minúsculo) | ❌ Cancela (precisa ser MAIÚSCULO) |
| `S` | ❌ Cancela (precisa ser exatamente 'SIM') |

---

## 📊 Matriz de Permissões

| Tipo de Usuário | Database Específica | Acesso Global | Requer Confirmação |
|----------------|-------------------|---------------|-------------------|
| `read` | ✅ Permitido | ✅ Permitido | ✅ Sim |
| `write` | ✅ Permitido | ✅ Permitido | ✅ Sim |
| `migration` | ✅ Permitido | ✅ Permitido | ✅ Sim |
| `backup` | ✅ Permitido | ❌ **BLOQUEADO** | N/A |

---

## 🎯 Casos de Uso Comuns

### Caso 1: Backup de Database Específica (Recomendado)

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username backup_workforce \
    --password backup_pass_123 \
    --type backup \
    --database app_workforce
```

**Status:** ✅ Permitido (sem confirmação)

---

### Caso 2: Read-Only Global (Auditoria)

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username audit_reader \
    --password audit_pass_123 \
    --type read
```

**Status:** ⚠️ Permitido (requer digitação de 'SIM')

---

### Caso 3: Write em Database Específica (Aplicação)

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username app_workforce_rw \
    --password app_pass_123 \
    --type write \
    --database app_workforce
```

**Status:** ✅ Permitido (sem confirmação)

---

### Caso 4: Migration Global (DBA)

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username dba_full \
    --password dba_pass_123 \
    --type migration
```

**Status:** ⚠️ Permitido (requer digitação de 'SIM')

---

## 🔧 Implementação Técnica

### PostgreSQL

```python
def grant_privileges(self, username, user_type, database=None, host_pattern='%'):
    # Validação 1: Bloqueia backup global
    if user_type == 'backup' and database is None:
        print("🚨 ERRO DE SEGURANÇA: Tipo 'backup' não pode ter acesso global")
        return False

    databases = [database] if database else self.get_all_databases()

    # Validação 2: Confirmação para acesso global
    if database is None:
        print(f"⚠️  ATENÇÃO: ACESSO GLOBAL A {len(databases)} DATABASES")
        response = input("Deseja continuar? (digite 'SIM' para confirmar): ")
        if response != 'SIM':
            print("❌ Operação cancelada pelo usuário.")
            return False

    # Continua com a concessão de permissões...
```

### MySQL

A mesma lógica é aplicada para MySQL/MariaDB.

---

## 📝 Parâmetros do Script

### Obrigatórios

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `--db-type` | Tipo de banco | `postgresql`, `mysql` |
| `--username` | Nome do novo usuário | `backup_user` |
| `--password` | Senha do novo usuário | `backup_pass_123` |
| `--type` | Tipo de permissão | `read`, `write`, `backup`, `migration` |

### Opcionais

| Parâmetro | Descrição | Padrão | Impacto de Segurança |
|-----------|-----------|--------|---------------------|
| `--database` | Database específica | `None` (global) | ⚠️ Se omitido, requer confirmação |
| `--admin-user` | Usuário admin | Do JSON | Validado no JSON |
| `--host` | Host do servidor | Do JSON | - |
| `--config` | Arquivo de config | Padrão do tipo | - |

---

## 🚀 Exemplos Práticos

### Exemplo 1: Backup Seguro (✅ Recomendado)

```bash
# Criar usuário backup para database específica
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username backup_kutt \
    --password KuttBackup2026! \
    --type backup \
    --database kutt
```

**Resultado:** Criado sem perguntas (seguro por padrão)

---

### Exemplo 2: Read-Only Global (⚠️ Requer Cuidado)

```bash
# Criar usuário read-only para todas as databases
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username monitoring_reader \
    --password Monitor2026! \
    --type read
```

**Resultado:** Sistema perguntará "Deseja continuar? (digite 'SIM' para confirmar):"

Você deve digitar: `SIM` ⏎

---

### Exemplo 3: Tentativa de Backup Global (❌ Bloqueado)

```bash
# ERRO: Tentar criar backup global
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username backup_all \
    --password BackupAll2026! \
    --type backup
```

**Resultado:**
```
🚨 ERRO DE SEGURANÇA: Tipo 'backup' não pode ter acesso global
❌ Operação cancelada por motivos de segurança.
```

---

## 🛡️ Justificativa de Segurança

### Por que bloquear backup global?

1. **Princípio do Menor Privilégio**: Usuários devem ter apenas as permissões necessárias
2. **Redução de Superfície de Ataque**: Limitar acesso reduz riscos
3. **Conformidade**: Muitas normas exigem segregação de acesso
4. **Auditoria**: Mais fácil auditar acessos específicos
5. **Prevenção de Erros**: Evita erros acidentais de configuração

### Por que exigir confirmação para acesso global?

1. **Conscientização**: Força o administrador a pensar antes de agir
2. **Prevenção de Acidentes**: Evita criação acidental de super-usuários
3. **Registro de Intenção**: Fica claro que foi uma decisão consciente
4. **Transparência**: Mostra exatamente o que será afetado

---

## 📚 Documentação Relacionada

- [README_ADMIN_PASSWORD_JSON.md](README_ADMIN_PASSWORD_JSON.md) - Autenticação via JSON
- [setup_database_user_permissions.py](setup_database_user_permissions.py) - Script principal
- [examples_setup_database_permissions.sh](examples_setup_database_permissions.sh) - Exemplos de uso

---

## 🔍 Troubleshooting

### Problema: "Operação cancelada pelo usuário"

**Causa:** Você não digitou exatamente `SIM` (maiúsculo)

**Solução:** Execute novamente e digite `SIM` quando solicitado

---

### Problema: "Tipo 'backup' não pode ter acesso global"

**Causa:** Você tentou criar usuário backup sem especificar `--database`

**Solução:** Adicione `--database nome_da_database` ao comando

---

### Problema: Quero criar backup global mesmo assim

**Resposta:** 🚫 Isso é bloqueado propositalmente por segurança.

**Alternativas:**
1. Use tipo `read` (somente leitura) com confirmação
2. Crie múltiplos usuários backup, um para cada database
3. Use tipo `migration` (administrador) com confirmação

---

## 📊 Estatísticas de Uso

### Comandos Bloqueados (Esperado)
```bash
# Estes comandos DEVEM falhar por design
--type backup                          # ❌ Sem database
--type backup --database ""            # ❌ Database vazia
```

### Comandos que Requerem Confirmação
```bash
--type read                            # ⚠️ Confirmar com 'SIM'
--type write                           # ⚠️ Confirmar com 'SIM'
--type migration                       # ⚠️ Confirmar com 'SIM'
```

### Comandos Seguros (Sem Confirmação)
```bash
--type backup --database X             # ✅ Executado diretamente
--type read --database X               # ✅ Executado diretamente
--type write --database X              # ✅ Executado diretamente
--type migration --database X          # ✅ Executado diretamente
```

---

**Última atualização:** 28 de janeiro de 2026
**Versão do script:** 2.0.0 (com validações de segurança)
