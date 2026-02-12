# Autenticação Automática via JSON - setup_database_user_permissions.py

## 📋 Resumo das Mudanças

O script `setup_database_user_permissions.py` foi atualizado para **buscar automaticamente a senha do admin_user** do arquivo de configuração JSON, eliminando a necessidade de passar `--admin-password` na linha de comando quando um arquivo de configuração está disponível.

## 🔐 Como Funciona

### Cenário 1: Com Arquivo de Configuração (Recomendado)

Quando você especifica `--admin-user` e existe um arquivo de configuração JSON:

1. O script carrega o JSON (padrão ou especificado via `--config`)
2. Valida se o usuário informado em `--admin-user` existe no JSON
3. **Busca automaticamente a senha** do usuário no JSON
4. Se o usuário não existir no JSON → **ERRO e encerra**

#### Exemplo:
```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --host wfdb02.vya.digital \
    --admin-user migration_user \
    --username backup_user \
    --password senha_backup \
    --type backup
```

**Nota**: Neste caso, a senha de `migration_user` será buscada automaticamente de:
- `secrets/postgresql_destination_config.json` (padrão para PostgreSQL)

### Cenário 2: Sem Arquivo de Configuração

Quando não há arquivo de configuração disponível:

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --host localhost \
    --admin-user postgres \
    --admin-password sua_senha_aqui \
    --username backup_user \
    --password senha_backup \
    --type backup
```

**Nota**: Neste caso, `--admin-password` é **obrigatório**.

### Cenário 3: Validação de Usuário

Se você tentar usar um usuário que não existe no JSON:

```bash
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --host wfdb02.vya.digital \
    --admin-user usuario_invalido \
    --username backup_user \
    --password senha_backup \
    --type backup
```

**Resultado**:
```
❌ ERRO: Usuário 'usuario_invalido' não encontrado no arquivo de configuração
   Usuário disponível no JSON: 'migration_user'
   Use --admin-user migration_user ou atualize o arquivo de configuração

❌ OPERAÇÃO CANCELADA: Não foi possível autenticar o usuário
```

## 🚨 Regras de Segurança Implementadas

### 1. Parâmetro --database É OBRIGATÓRIO Para TODOS os Tipos

**NOVA POLÍTICA:** Por motivos de segurança, **TODOS** os usuários devem ser restritos a databases específicas. Acesso global **NÃO** é mais permitido em nenhuma hipótese.

**❌ Bloqueado (Todos os tipos sem --database):**
```bash
# ERRO: Falta --database
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username backup_user \
    --type backup

# ERRO: Falta --database
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username readonly_user \
    --type read

# ERRO: Falta --database
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username write_user \
    --type write
```

**Mensagem de erro:**
```
======================================================================
🚨 ERRO DE SEGURANÇA: Parâmetro --database é OBRIGATÓRIO
======================================================================

Por motivos de segurança, TODOS os usuários devem ser restritos
a databases específicas. Acesso global NÃO é permitido.

Use o parâmetro --database para especificar a database.

Exemplos:
  --database app_workforce --type backup
  --database kutt --type read

❌ Operação cancelada por motivos de segurança.
```

**✅ Correto (Todos os tipos COM --database):**
```bash
# ✅ Backup em database específica
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username backup_user \
    --password backup_pass \
    --type backup \
    --database app_workforce

# ✅ Read-only em database específica
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username readonly_user \
    --password read_pass \
    --type read \
    --database kutt

# ✅ Write em database específica
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username write_user \
    --password write_pass \
    --type write \
    --database botpress_db
```

### 2. Sem Exceções - Princípio do Menor Privilégio

- **Não há opção de acesso global** - completamente removido
- **Todos os usuários são restritos** a databases específicas
- **Operação será bloqueada** sem --database
- **Aplica-se a TODOS os tipos**: read, write, backup, migration

## 🎯 Benefícios

1. **Segurança Máxima**: Implementação rigorosa do princípio do menor privilégio
2. **Sem Exceções**: Nenhum usuário pode ter acesso global
3. **Prevenção Total**: Impossível criar usuários com permissões excessivas
4. **Validação Automática**: Sistema verifica e bloqueia operações inseguras
5. **Conformidade**: Alinhado com melhores práticas de segurança de banco de dados
6. **Auditoria Facilitada**: Todas as permissões são explícitas e rastreáveis

## 📁 Arquivos de Configuração Padrão

O script busca automaticamente os seguintes arquivos:

- **PostgreSQL**: `secrets/postgresql_destination_config.json`
- **MySQL**: `secrets/mysql_config.json`

### Estrutura do JSON (PostgreSQL)

```json
{
  "server": {
    "host": "wfdb02.vya.digital",
    "port": 5432
  },
  "authentication": {
    "user": "migration_user",
    "password": "senha_secreta_aqui"
  }
}
```

## 🔧 Exemplos de Uso

### PostgreSQL - Modo Recomendado

```bash
# ✅ Cria usuário de backup em database específica (--database OBRIGATÓRIO)
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username backup_user \
    --password backup_pass_123 \
    --type backup \
    --database app_workforce

# ✅ Cria usuário read-only em database específica (--database OBRIGATÓRIO)
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username readonly_user \
    --password readonly_123 \
    --type read \
    --database app_workforce

# ✅ Cria usuário write em database específica (--database OBRIGATÓRIO)
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username write_user \
    --password write_123 \
    --type write \
    --database botpress_db

# ❌ ERRO: Qualquer tipo sem --database será bloqueado
python scripts/setup_database_user_permissions.py \
    --db-type postgresql \
    --admin-user migration_user \
    --username any_user \
    --password any_pass \
    --type read
# Resultado: 🚨 ERRO DE SEGURANÇA: Parâmetro --database é OBRIGATÓRIO
```

### MySQL - Modo Recomendado

```bash
python scripts/setup_database_user_permissions.py \
    --db-type mysql \
    --admin-user root \
    --username backup_mysql \
    --password backup_pass_123 \
    --type backup
```

## 🚨 Mensagens de Erro

### Usuário não encontrado no JSON
```
❌ ERRO: Usuário 'root' não encontrado no arquivo de configuração
   Usuário disponível no JSON: 'migration_user'
   Use --admin-user migration_user ou atualize o arquivo de configuração
```

### Senha não encontrada no JSON
```
❌ ERRO: Senha não encontrada no JSON para o usuário 'migration_user'
```

### Arquivo de configuração não encontrado
```
❌ Arquivo não encontrado: secrets/postgresql_destination_config.json
```

## 📝 Parâmetros Necessários

### Obrigatórios (sempre):
- `--db-type`: Tipo de banco (postgresql, mysql, etc)
- `--username`: Nome do novo usuário a criar
- `--password`: Senha do novo usuário
- `--type`: Tipo de permissão (read, write, backup, migration)

### Condicionais:
- `--admin-user`: Nome do usuário admin
  - Com JSON: Busca senha automaticamente
  - Sem JSON: Requer `--admin-password`

- `--host`: Host do servidor
  - Opcional se usar `--config` ou arquivo padrão
  - Obrigatório se não houver JSON

## 🔍 Troubleshooting

### Problema: Script não encontra o arquivo JSON
**Solução**: Especifique o caminho completo com `--config`
```bash
python scripts/setup_database_user_permissions.py \
    --config /caminho/completo/para/config.json \
    ...
```

### Problema: Usuário do JSON diferente do solicitado
**Solução**: Use o usuário que está no JSON ou atualize o JSON

### Problema: Quer usar senha diferente da que está no JSON
**Solução**: Não especifique `--admin-user`, o script usará as credenciais do JSON automaticamente

## 📚 Documentação Adicional

Execute o script com `--help` para ver todas as opções:
```bash
python scripts/setup_database_user_permissions.py --help
```
