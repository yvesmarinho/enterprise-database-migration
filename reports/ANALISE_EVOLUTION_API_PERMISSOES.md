# Análise: Evolution API e Verificação de Permissões

**Data:** 2 de novembro de 2025
**Contexto:** Problema de acesso ao Evolution API e validação de permissões PostgreSQL
**Repositório:** https://github.com/EvolutionAPI/evolution-api

---

## 📋 Sumário Executivo

A Evolution API é um sistema de integração WhatsApp/Messaging baseado em:
- **Backend:** Node.js 20+ + TypeScript 5+
- **Database:** Prisma ORM (PostgreSQL/MySQL)
- **Autenticação:** API Key global + Instance Tokens
- **Arquitetura:** RouterBroker com Guards de segurança

### Problema Identificado
O erro de permissões em bancos `evolution*` afeta:
- Criação de usuários (39/59 usuários criados)
- Aplicação de privilégios (0/59 privilégios aplicados - **CRÍTICO**)
- Operações DDL bloqueadas no tablespace `ts_enterprise_data`

---

## 🔍 Estrutura da Evolution API

### 1. Autenticação e Autorização

#### Padrão de Autenticação (src/api/guards/auth.guard.ts)

```typescript
// Dois níveis de autenticação:

// 1. API Key Global (AUTHENTICATION.API_KEY)
if (env.KEY === key) {
  return next();  // Acesso total ao sistema
}

// 2. Instance Token (por instância)
const instance = await prismaRepository.instance.findUnique({
  where: { name: param.instanceName },
});
if (instance.token === key) {
  return next();  // Acesso à instância específica
}
```

#### Guard de Autorização

```typescript
// src/api/guards/instance.guard.ts
export async function instanceExistsGuard(req, res, next) {
  // Verifica se instância existe
  // Carrega de cache ou banco de dados
}

export async function instanceLoggedGuard(req, res, next) {
  // Verifica se instância está conectada
  // Valida token de sessão
}
```

### 2. Estrutura de Rotas com Guards

```typescript
// Padrão RouterBroker
export class ChatRouter extends RouterBroker {
  constructor(...guards: RequestHandler[]) {
    super();
    this.router
      .post(
        this.routerPath('findMessages'),
        ...guards,  // ← instanceExistsGuard, instanceLoggedGuard, authGuard
        async (req, res) => {
          // Validação via JSONSchema7
          const response = await this.dataValidate<Query<Message>>({
            request: req,
            schema: messageValidateSchema,
            ClassRef: Query<Message>,
            execute: (instance, data) =>
              chatController.fetchMessages(instance, data),
          });

          return res.status(HttpStatus.OK).json(response);
        }
      );
  }
}
```

### 3. Esquemas de Validação (JSONSchema7)

```typescript
// src/validate/chat.schema.ts - Exemplo
export const messageValidateSchema: JSONSchema7 = {
  $id: v4(),
  type: 'object',
  properties: {
    where: {
      type: 'object',
      properties: {
        _id: { type: 'string', minLength: 1 },
        remoteJid: { type: 'string', minLength: 1 },
      },
    },
    limit: { type: 'integer' },
  },
};
```

---

## 🚀 Exemplos de Query API

### 1. **Criar Instância WhatsApp**

#### Request
```bash
curl -X POST http://localhost:8080/instance/create \
  -H "Content-Type: application/json" \
  -H "apikey: sua-chave-api-global" \
  -d '{
    "instanceName": "minha-instancia-wa",
    "integration": "BAILEYS"
  }'
```

#### Response (201 Created)
```json
{
  "instance": {
    "id": "uuid-instance-id",
    "name": "minha-instancia-wa",
    "number": null,
    "status": "disconnected",
    "token": "instance-token-unico",
    "integration": "BAILEYS",
    "clientName": "postgresql"
  }
}
```

#### Permissões Necessárias
- API Key Global válida
- Acesso à tabela `Instance` (CREATE)
- Permissão em schema `public` (CREATE)

---

### 2. **Buscar Instâncias (Autenticado)**

#### Request
```bash
curl -X GET http://localhost:8080/instance/fetchInstances \
  -H "apikey: sua-chave-api-global"
```

#### Query SQL Equivalente (Prisma)
```typescript
const instances = await prismaRepository.instance.findMany({
  where: {
    clientName: configService.get<Database>('DATABASE')
      .CONNECTION.CLIENT_NAME
  },
});
```

#### SQL Gerado (PostgreSQL via Prisma)
```sql
SELECT "id", "name", "number", "status", "token", "integration",
       "clientName", "createdAt", "updatedAt"
FROM "Instance"
WHERE "clientName" = 'postgresql';
```

---

### 3. **Enviar Mensagem (Instance-Specific)**

#### Request
```bash
curl -X POST http://localhost:8080/message/sendText/minha-instancia-wa \
  -H "Content-Type: application/json" \
  -H "apikey: instance-token-unico" \
  -d '{
    "number": "5511999999999",
    "text": "Olá, teste de mensagem"
  }'
```

#### Validação (JSONSchema7)
```typescript
const sendTextSchema = {
  type: 'object',
  properties: {
    number: { type: 'string', minLength: 1 },
    text: { type: 'string', minLength: 1 },
  },
  required: ['number', 'text'],
};
```

#### Query SQL Equivalente
```sql
-- Inserir mensagem
INSERT INTO "Message" (
  "key", "messageTimestamp", "status", "pushName", "data"
)
VALUES (...)
RETURNING *;

-- Atualizar chat
UPDATE "Chat"
SET "updatedAt" = CURRENT_TIMESTAMP
WHERE "remoteJid" = '5511999999999@s.whatsapp.net';
```

---

### 4. **Integração ChatwootAPI (PostgreSQL Query Direta)**

#### Request
```bash
curl -X POST http://localhost:8080/chatwoot/set \
  -H "Content-Type: application/json" \
  -H "apikey: instance-token" \
  -d '{
    "enabled": true,
    "accountId": 1,
    "token": "chatwoot-api-token",
    "url": "https://chatwoot.example.com",
    "signMsg": true
  }'
```

#### Query SQL Chatwoot (Importação de Contatos)

```typescript
// src/api/integrations/chatbot/chatwoot/utils/chatwoot-import-helper.ts
class ChatwootImport {
  public async importHistoryContacts(instance: InstanceDto, provider: ChatwootDto) {
    const pgClient = postgresClient.getChatwootConnection();

    // Query 1: Buscar label
    const labelSql = `
      SELECT id FROM labels
      WHERE title = '${provider.nameInbox}'
        AND account_id = ${provider.accountId}
      LIMIT 1
    `;
    const labelId = (await pgClient.query(labelSql))?.rows[0]?.id;

    // Query 2: Buscar ou criar contatos
    const fksQuery = `
      WITH new_contact AS (
        INSERT INTO contacts (account_id, phone_number, name)
        VALUES ($1, $2, $3)
        ON CONFLICT (account_id, phone_number) DO UPDATE SET
          name = EXCLUDED.name
        RETURNING id
      ),
      new_contact_inbox AS (
        INSERT INTO contact_inboxes (contact_id, inbox_id, source_id)
        SELECT nc.id, $4, $5
        FROM new_contact nc
        ON CONFLICT (contact_id, inbox_id) DO NOTHING
        RETURNING contact_id, inbox_id
      )
      SELECT contact_id FROM new_contact_inbox
      UNION
      SELECT c.id contact_id
      FROM contacts c
      JOIN contact_inboxes ci ON ci.contact_id = c.id
      WHERE c.phone_number = $2 AND c.account_id = $1;
    `;

    return pgClient.query(fksQuery, [
      provider.accountId,
      phoneNumber,
      contactName,
      inboxId,
      sourceId
    ]);
  }
}
```

---

### 5. **Operações OpenAI (Com Validação)**

#### Request: Listar Modelos Disponíveis
```bash
curl -X GET "http://localhost:8080/openai/getModels/minha-instancia" \
  -H "apikey: instance-token"
```

#### Código TypeScript (Validação + Query)
```typescript
// src/api/integrations/chatbot/openai/controllers/openai.controller.ts
export class OpenaiController {
  public async getModels(
    instance: InstanceDto,
    openaiCredsId?: string
  ) {
    // 1. Validar instance existe
    const instanceId = await this.prismaRepository.instance
      .findFirst({
        where: { name: instance.instanceName }
      })
      .then((inst) => inst.id);

    if (!instanceId) throw new Error('Instance not found');

    // 2. Buscar credenciais OpenAI
    let apiKey: string;

    if (openaiCredsId) {
      const creds = await this.credsRepository.findFirst({
        where: {
          id: openaiCredsId,
          instanceId: instanceId  // ← Validação de propriedade
        }
      });
      if (!creds) throw new Error('Credentials not found');
      apiKey = creds.apiKey;
    } else {
      // Query padrão
      const defaultSettings = await this.settingsRepository.findFirst({
        where: { instanceId: instanceId },
        include: { OpenaiCreds: true }
      });
      if (!defaultSettings?.OpenaiCreds) {
        throw new Error('No credentials found');
      }
      apiKey = defaultSettings.OpenaiCreds.apiKey;
    }

    // 3. Chamar API OpenAI
    const client = new OpenAI({ apiKey });
    const models = await client.models.list();
    return models?.body?.data;
  }
}
```

#### SQL Equivalente (Prisma)
```sql
-- Query 1: Verificar acesso à instância
SELECT id FROM "Instance"
WHERE name = $1
LIMIT 1;

-- Query 2: Buscar credenciais OpenAI com validação
SELECT * FROM "OpenaiCreds"
WHERE id = $1 AND "instanceId" = $2;

-- Query 3: Buscar settings com relacionamento
SELECT s.*, oc."apiKey"
FROM "OpenaiSetting" s
LEFT JOIN "OpenaiCreds" oc ON oc.id = s."openaiCredsId"
WHERE s."instanceId" = $1;
```

---

## 🔐 Problemas de Permissão Identificados

### Problema 1: Aplicação de Privilégios Falha

**Sintoma:** `fix_evolution_permissions.py` reporta 0/59 privilégios aplicados

**Causa Raiz:**
```python
# core/fix_evolution_permissions.py (linhas ~300-350)
def apply_database_privileges(self, database_name: str):
    """❌ PROBLEMA: Verifica usuários após criar banco"""

    # Erro 1: Usuario pode nao estar em lista de "existing_users"
    existing_users = self.get_existing_users()

    # Erro 2: Fase 3 faz query APÓS criacao de usuario
    #         mas nao atualiza cache de existing_users

    for privilege in privileges:
        # Tenta aplicar privilege a usuario que "nao existe" segundo cache
        # Mas usuario JA FOI CRIADO na fase 2

        if privilege['user'] not in existing_users:  # ← AQUI: Falha!
            self.logger.error(f"Usuario {privilege['user']} nao existe")
            continue  # ← Pula o GRANT
```

**Solução:**
```python
def apply_database_privileges_fixed(self, database_name: str):
    """✅ CORRIGIDO: Atualizar existing_users ANTES de validar"""

    # IMPORTANTE: Re-buscar usuarios do banco
    existing_users = self.get_existing_users()  # ← Re-busca ATUAL

    for privilege in privileges:
        # Agora a lista está atualizada
        if privilege['user'] not in existing_users:
            # Debug: Por que nao existe?
            self.logger.debug(
                f"Usuario {privilege['user']} realmente nao existe"
            )
            # Criar user antes de aplicar privilege
            self.create_user(privilege['user'])

        # Agora aplicar privilégio
        self.apply_grant(
            database=database_name,
            user=privilege['user'],
            privilege=privilege['type']
        )
```

---

### Problema 2: Tablespace Configurado mas Dados não Migram

**Sintoma:** `ALTER DATABASE SET TABLESPACE` sucede, mas dados permanecem em `pg_default`

**Causa:** PostgreSQL não move dados existentes automaticamente

```sql
-- ❌ ERRADO: Dados não se movem
ALTER DATABASE evolution_db SET TABLESPACE ts_enterprise_data;

-- ✅ CORRETO: Precisa recriar dados
ALTER DATABASE evolution_db SET TABLESPACE ts_enterprise_data;

-- Validar dados FISICAMENTE movidos
SELECT datname, spcname FROM pg_database
JOIN pg_tablespace ON pg_database.dattablespace = pg_tablespace.oid
WHERE datname = 'evolution_db';

-- Se mostrar pg_default, dados nao foram movidos
-- Solucao: REINDEX + VACUUM + Reorganizar dados

-- Ver pasta fisica do tablespace
ls -la /var/lib/postgresql/16/tablespaces/
```

---

## 📊 Matriz de Permissões vs Operações

| Operação | Permissão Necessária | Autenticação | Guard | Query SQL |
|----------|---------------------|--------------|-------|-----------|
| Create Instance | `INSTANCE:CREATE` | Global API Key | `authGuard` | `INSERT INTO "Instance"...` |
| Read Instance | `INSTANCE:READ` | Global API Key ou Instance Token | `authGuard + instanceExistsGuard` | `SELECT * FROM "Instance"...` |
| Update Settings | `SETTINGS:UPDATE` | Instance Token | `authGuard + instanceLoggedGuard` | `UPDATE "Settings"...` |
| Send Message | `MESSAGE:SEND` | Instance Token | `authGuard + instanceLoggedGuard + validateMessage` | `INSERT INTO "Message"...` |
| Create OpenAI Creds | `OPENAI:CREDS:CREATE` | Instance Token | `authGuard + validateOpenaiCreds` | `INSERT INTO "OpenaiCreds"...` |
| Fetch Chatwoot Labels | `CHATWOOT:READ` | External DB Access | PostgreSQL direct query | `SELECT * FROM labels WHERE...` (Chatwoot DB) |

---

## 🔧 Recomendações para Correção

### Curto Prazo (Imediato)
1. ✅ Atualizar cache de `existing_users` APÓS criar usuarios
2. ✅ Validar aplicação de privilégios com query direto no banco
3. ✅ Adicionar retry logic para operações DDL

### Médio Prazo (1-2 semanas)
1. Implementar transações distribuídas (fases 1-3 como unit)
2. Criar tabela de auditoria para rastrear privilégios aplicados
3. Adicionar verificação de integridade pós-migração

### Longo Prazo
1. Migrar para ORM (SQLAlchemy) para gerenciar permissões
2. Implementar RBAC (Role-Based Access Control) nativo
3. Documentar matriz de permissões por tipo de usuário

---

## 📁 Arquivos Gerados

```
enterprise-database-migration/
├── test_evolution_api_permissions.py (este script)
├── core/fix_evolution_permissions.py  (com correções propostas)
└── ANALISE_EVOLUTION_API_PERMISSOES.md (este documento)
```

---

## 🎯 Próximos Passos

1. **Executar teste de permissões:**
   ```bash
   python3 test_evolution_api_permissions.py \
     --url http://localhost:8080 \
     --apikey sua-chave-api \
     --simulate-all \
     --report test-results.json
   ```

2. **Aplicar correção de privilégios:**
   ```bash
   python3 run_fix_evolution_permissions.py \
     --server wfdb02 \
     --dry-run \
     --verbose
   ```

3. **Validar resultado:**
   ```bash
   python3 core/validator.py --validate-all
   ```

---

## 📚 Referências

- [Evolution API Repository](https://github.com/EvolutionAPI/evolution-api)
- [Evolution API Documentation](https://doc.evolution-api.com/)
- [Prisma ORM Documentation](https://www.prisma.io/docs/)
- [PostgreSQL Security Guide](https://www.postgresql.org/docs/current/sql-grant.html)

---

**Análise Completa:** 2 de novembro de 2025
**Última Atualização:** 2025-11-02T14:30:00Z
