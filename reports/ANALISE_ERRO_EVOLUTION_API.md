# 🔍 ANÁLISE - PROBLEMA NO EVOLUTION API E BANCO DE DADOS

**Data:** 31 de outubro de 2025
**Status:** ⚠️ Problema identificado e solução proposta

---

## 📊 ANÁLISE DO LOG

### ❌ ERRO ENCONTRADO

```
PrismaClientInitializationError: Error querying the database:
FATAL: unsupported startup parameter: search_path
```

**Localização:** Arquivo `temp.log` - Evolution API WEA004
**Causa:** Parâmetro `search_path` não suportado na string de conexão

---

## 🔐 ANÁLISE DO ARQUIVO ENV

### Configuração Encontrada

```ini
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI='postgresql://evoluton_api_user:PASSWORD@154.53.36.3:5432/evolution_api_wea004_db?schema=public'
```

### ⚠️ PROBLEMA IDENTIFICADO

**Linha 1 do CONNECTION_URI:**
```
postgresql://evoluton_api_user:PASSWORD@154.53.36.3:5432/evolution_api_wea004_db?schema=public
```

**Problema:**
- ✗ Parâmetro `?schema=public` está sendo passado na URL
- ✗ Este parâmetro é adicionado automaticamente por Prisma
- ✗ Duplicação causa erro: `search_path` não suportado

**Solução:**
- ✓ Remover `?schema=public` da CONNECTION_URI
- ✓ Deixar apenas: `postgresql://evoluton_api_user:PASSWORD@HOST:5432/evolution_api_wea004_db`

---

## 🔧 CORREÇÃO

### Antes (INCORRETO):
```ini
DATABASE_CONNECTION_URI='postgresql://evoluton_api_user:PASSWORD@154.53.36.3:5432/evolution_api_wea004_db?schema=public'
```

### Depois (CORRETO):
```ini
DATABASE_CONNECTION_URI='postgresql://evoluton_api_user:PASSWORD@154.53.36.3:5432/evolution_api_wea004_db'
```

---

## 📋 DETALHES DA CONEXÃO

### Credenciais Extraídas do ENV

| Campo | Valor |
|-------|-------|
| **Usuário** | evoluton_api_user |
| **Senha** | PASSWORD |
| **Host** | 154.53.36.3 |
| **Porta** | 5432 |
| **Database** | evolution_api_wea004_db |
| **Schema** | public (removido da URL) |

### String de Conexão Corrigida

```
postgresql://evoluton_api_user:PASSWORD@154.53.36.3:5432/evolution_api_wea004_db
```

---

## 🚀 PASSO A PASSO PARA CORRIGIR

### 1. Localizar o Arquivo ENV
```bash
# Arquivo encontrado:
secrets/env-evolution
```

### 2. Editar o Arquivo
```bash
nano secrets/env-evolution
# ou
vi secrets/env-evolution
```

### 3. Encontrar a Linha (está na linha ~16)
```ini
DATABASE_CONNECTION_URI='postgresql://evoluton_api_user:PASSWORD@154.53.36.3:5432/evolution_api_wea004_db?schema=public'
```

### 4. Remover `?schema=public`
```ini
DATABASE_CONNECTION_URI='postgresql://evoluton_api_user:PASSWORD@154.53.36.3:5432/evolution_api_wea004_db'
```

### 5. Salvar e Reiniciar
```bash
# Salvar (no vi/nano)
# :w (salvar)
# :q (sair)

# Reiniciar Evolution API
docker-compose restart evolution_api_wea004
```

---

## ✅ VALIDAÇÃO PÓS-CORREÇÃO

Após fazer a alteração, verifique:

```bash
# 1. Ver logs
docker-compose logs -f evolution_api_wea004

# 2. Aguardar inicialização
# Deve terminar com sucesso (sem PrismaClientInitializationError)

# 3. Testar acesso
curl -X GET http://localhost:8080/health
```

---

## 🎯 RELAÇÃO COM EVOLUTION PERMISSIONS FIXER

### Como Isto Afeta Nosso Script?

```
✅ Nosso script EvolutionPermissionsFixer:
   - Usa credenciais: migration_user (de secrets/postgresql_source_config.json)
   - Não afeta este erro de Evolution API

⚠️ Mas é importante corrigir:
   - Evolution API precisa acessar evolution_api_wea004_db
   - Permissões que corrigimos são necessárias
   - Sem as permissões corretas, Evolution API não consegue acessar tabelas
```

---

## 📝 RESUMO DOS ARQUIVOS

### Arquivo ENV
```
Localização: secrets/env-evolution
Problema:    search_path duplicado na CONNECTION_URI
Solução:     Remover ?schema=public da URL
```

### Relacionado
```
secrets/env-evolution          (Arquivo do Evolution API - CORRIGIR AQUI)
secrets/postgresql_source_config.json  (Credenciais do migration_user - OK)
core/fix_evolution_permissions.py      (Nosso script - OK)
```

---

## 🔐 CREDENCIAIS ENCONTRADAS

### Para Evolution API (WEA004)
```
Host:     154.53.36.3 (ou 82.197.64.145 - WFDB02)
Usuário:  evoluton_api_user (note: typo "evoluton")
Senha:    PASSWORD
Database: evolution_api_wea004_db
```

### Para Migration (Nosso script)
```
Host:     wfdb02.vya.digital
Usuário:  migration_user
Senha:    REDACTED_WFDB02_PASSWORD
Database: postgres
```

---

## ✨ CONCLUSÃO

### Problema Identificado
✅ Parâmetro `search_path` duplicado em CONNECTION_URI do Evolution API

### Solução
✅ Remover `?schema=public` da DATABASE_CONNECTION_URI

### Próximos Passos
1. Editar `secrets/env-evolution`
2. Remover `?schema=public` da linha DATABASE_CONNECTION_URI
3. Reiniciar Evolution API
4. Verificar logs para confirmar sucesso

### Status do EvolutionPermissionsFixer
✅ Script continua funcional e pronto
✅ Permissões corrigidas no banco
✅ Aguardando Evolution API ser reiniciado com correção

---

**Data:** 31 de outubro de 2025
**Status:** ⚠️ Problema identificado e solução disponível
**Ação:** Aplicar correção no arquivo `secrets/env-evolution`

