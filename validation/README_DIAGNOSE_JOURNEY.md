# 🔍 Diagnóstico de Permissões - journey_system PostgreSQL 18

## Objetivo

Diagnóstico completo de permissões no PostgreSQL 18 (wfdb02) para o usuário `journey_system` que não consegue ler tabelas apesar de ter grants de banco de dados.

## Configuração de Credenciais

### ⚠️ IMPORTANTE: Credenciais NÃO devem estar no código!

O script carrega credenciais de arquivos seguros no diretório `secrets/`:

#### 1. Arquivo: `secrets/wfdb02_user_journey.txt`

Crie este arquivo com as credenciais do journey_system:

```
user=journey_system
password=bra-Lhudri5ubikeDrin
```

**Formato**: Uma credencial por linha, no formato `chave=valor`

**Segurança**:
- Este arquivo está no `.gitignore` (não será commitado)
- Nunca compartilhe ou versione este arquivo
- Use permissões restritas: `chmod 600 secrets/wfdb02_user_journey.txt`

#### 2. Arquivo: `secrets/destination_config.txt`

Deve existir com configurações do servidor destino (JSON):

```json
{
  "host": "82.197.64.145",
  "port": 5432,
  "database": "postgres",
  "ssl_mode": "prefer",
  "possible_users": [
    {
      "username": "migration_user",
      "password": "..."
    }
  ],
  "cleanup_protection": {
    "protected_databases": [...],
    "protected_users": [...]
  }
}
```

## Problema Identificado

- **Sintoma**: journey_system não consegue ler tabelas do banco
- **Grants DB**: O usuário TEM permissões nos grants do banco de dados
- **Causa Provável**:
  - Falta de permissão USAGE no schema (geralmente `public`)
  - Problema com grants do tablespace
  - Falta de permissão SELECT nas tabelas específicas

## Como Usar

### 1. Preparar Credenciais

```bash
# Criar arquivo de credenciais (NÃO fazer commit!)
cat > secrets/wfdb02_user_journey.txt << EOF
user=journey_system
password=bra-Lhudri5ubikeDrin
EOF

# Proteger arquivo
chmod 600 secrets/wfdb02_user_journey.txt
```

### 2. Verificar Configuração

```bash
# Verificar que destination_config.txt existe
ls -la secrets/destination_config.txt

# Verificar que wfdb02_user_journey.txt existe
ls -la secrets/wfdb02_user_journey.txt
```

### 3. Instalação de Dependências

```bash
# Python 3.12+ com SQLAlchemy
pip install sqlalchemy>=2.0

# Ou instalar no projeto
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration
pip install -r requirements.txt
```

### 4. Executar Diagnóstico

```bash
# Executar o diagnóstico
python3 validation/diagnose_journey_permissions.py

# O script irá:
# ✅ Carregar credenciais de secrets/wfdb02_user_journey.txt
# ✅ Carregar config de secrets/destination_config.txt
# ✅ Exportar resultados em JSON
```

### 3. Saída Esperada

O script exibe:

```
================================================================================
DIAGNÓSTICO DE PERMISSÕES - PostgreSQL 18 wfdb02
================================================================================

Usuário alvo: journey_system
Host: wfdb02.vya.digital

➜ 1. Conectando ao PostgreSQL
────────────────────────────────────────────────────────────────
String de conexão: postgresql://...@wfdb02.vya.digital:5432/postgres
[✓] Conectado com sucesso como 'journey_system'

➜ 2. Verificando Role do Usuário
────────────────────────────────────────────────────────────────
Username: journey_system
Superuser: False
Can Create DB: False
Can Create Role: False
Inherits Permissions: True
Role OID: 16384

➜ 3. Permissões em Schemas
────────────────────────────────────────────────────────────────
✗ public → NENHUMA
✓ information_schema → (permissions)

[...continua com análise completa...]

➜ 7. Comandos SQL Recomendados
────────────────────────────────────────────────────────────────
Execute os seguintes comandos como superuser (postgres):

-- Conceder USAGE no schema
GRANT USAGE ON SCHEMA public TO journey_system;
-- Conceder SELECT em tabelas
GRANT SELECT ON ALL TABLES IN SCHEMA public TO journey_system;
-- Para futuras tabelas
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO journey_system;

Nota: Execute em um terminal conectado como postgres
```

## Resultados

O script cria um arquivo JSON em `reports/diagnosis_journey_system_YYYYMMDD_HHMMSS.json` com:

- Status de conexão
- Informações da role
- Permissões em schemas
- Permissões em tabelas
- Informações de tablespaces
- Lista detalhada de problemas encontrados

## Estrutura do Código

### Dataclasses

- `PermissionIssue`: Representa um problema encontrado
- `DiagnosisResult`: Resultado completo do diagnóstico

### Funções Principais

#### Leitura de Permissões

- `get_role_info()` - Obtém informações da role
- `get_role_memberships()` - Memberships da role
- `get_schema_permissions()` - Permissões em schemas
- `get_table_permissions()` - Permissões em tabelas
- `get_tablespace_info()` - Informações de tablespaces

#### Análise

- `analyze_issues()` - Identifica e classifica problemas
- `run_diagnostic()` - Executa diagnóstico completo

#### Exportação

- `export_results()` - Exporta relatório em JSON
- `print_sql_recommendations()` - Imprime comandos SQL para corrigir

## Possíveis Problemas e Soluções

### Problema 1: Sem USAGE no Schema

**Sintoma**: `[✗] public → NENHUMA`

**Solução**:
```sql
GRANT USAGE ON SCHEMA public TO journey_system;
```

### Problema 2: Sem SELECT nas Tabelas

**Sintoma**: `Tabelas SEM SELECT: (lista de tabelas)`

**Solução**:
```sql
GRANT SELECT ON ALL TABLES IN SCHEMA public TO journey_system;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO journey_system;
```

### Problema 3: Problema com Tablespace

**Sintoma**: `Tablespace 'XXX' pode ter ACLs restritivas`

**Solução**: Verificar ACLs do tablespace:
```sql
SELECT spcname, pg_get_userbyid(spcowner), spcacl FROM pg_tablespace;
```

### Problema 4: Usuário não existe

**Sintoma**: `Usuário journey_system não encontrado!`

**Solução**: Criar o usuário:
```sql
CREATE USER journey_system WITH PASSWORD '...';
```

## Credenciais

O script carrega credenciais de forma segura:

### Arquivo: secrets/wfdb02_user_journey.txt
```
user=journey_system
password=bra-Lhudri5ubikeDrin
```

### Arquivo: secrets/destination_config.txt
Arquivo JSON com configuração do servidor

**Nota**: Estes arquivos estão no `.gitignore` e NÃO devem ser commitados no Git.

## Segurança de Credenciais

1. **Nunca hardcode credenciais no código**
   - ❌ `password="abc123"` no código
   - ✅ Carregar de arquivo: `secrets/wfdb02_user_journey.txt`

2. **Proteger arquivo de credenciais**
   ```bash
   chmod 600 secrets/wfdb02_user_journey.txt
   ```

3. **Verificar .gitignore**
   ```bash
   # Deve conter:
   secrets/*.txt
   secrets/*.json
   !secrets/.example
   ```

4. **Nunca compartilhar credenciais**
   - Não envie por email
   - Não coloque em logs
   - Não coloque em commits do Git

## Cores na Saída

- 🟢 **Verde**: OK, sucesso
- 🔴 **Vermelho**: Erro, crítico
- 🟡 **Amarelo**: Aviso, precisa atenção
- 🔵 **Cyan**: Informação

## Tratamento de Erros

O script trata:
- Erros de conexão (OperationalError)
- Erros de permissão (ProgrammingError)
- Erros gerais (Exception)

## Limitações

1. Conecta com credenciais de usuário específico (não admin)
2. Algumas queries podem ser bloqueadas por falta de permissão
3. Não modifica permissões automaticamente (apenas recomenda)

## Próximos Passos Após Diagnóstico

1. Revisar o relatório JSON gerado
2. Executar comandos SQL recomendados como superuser (`postgres`)
3. Re-executar o diagnóstico para confirmar fixes
4. Testar conexão do journey_system ao banco

## Referências

- [PostgreSQL Permissions](https://www.postgresql.org/docs/18/ddl-priv.html)
- [Schema Permissions](https://www.postgresql.org/docs/18/ddl-schemas.html)
- [Tablespace Management](https://www.postgresql.org/docs/18/manage-ag-tablespaces.html)
