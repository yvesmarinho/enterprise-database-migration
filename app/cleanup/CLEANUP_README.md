# 🧹 PostgreSQL Database Cleanup Utility

## 🎯 **Visão Geral**

Script Python independente para apagar **todos os bancos de dados e usuários** de servidores PostgreSQL usando SQLAlchemy.

> ⚠️ **ATENÇÃO**: Este é um script **DESTRUTIVO**! Use apenas em ambientes de desenvolvimento/teste.

## 📁 **Arquivos**

- `cleanup_database.py` - Script principal de limpeza
- `exemplo_cleanup.py` - Exemplos interativos de uso
- `CLEANUP_README.md` - Esta documentação

## 🚀 **Uso Rápido**

### 🔍 **Modo Seguro (Simulação)**
```bash
# Ver o que seria apagado (sem executar)
python3 cleanup_database.py --server origem --dry-run

# Simular limpeza completa em ambos servidores
python3 cleanup_database.py --server ambos --dry-run
```

### 🗑️ **Execução Real (CUIDADO!)**
```bash
# Apagar bancos e usuários do servidor origem
python3 cleanup_database.py --server origem

# Limpeza forçada (sem confirmação)
python3 cleanup_database.py --server origem --force

# Apagar apenas bancos de dados
python3 cleanup_database.py --server origem --databases-only

# Apagar apenas usuários
python3 cleanup_database.py --server origem --users-only
```

### 📖 **Exemplos Interativos**
```bash
# Menu com exemplos prontos
python3 exemplo_cleanup.py
```

## ⚙️ **Configuração**

O script usa as configurações existentes:
- `src/migration/config/source_config.json` (servidor origem)
- `src/migration/config/destination_config.json` (servidor destino)

## 🛡️ **Proteções Integradas**

### **🚨 Confirmação DUPLA OBRIGATÓRIA**
**TODOS os servidores** agora exigem **DUAS confirmações** obrigatórias:

**Para servidor ORIGEM apenas:**
1. **[1/2]** Digite `CONFIRMO`
2. **[2/2]** Digite `ORIGEM-CONFIRMO`

**Para servidor DESTINO apenas:**
1. **[1/2]** Digite `CONFIRMO`
2. **[2/2]** Digite `FINAL-CONFIRMO`

**Para AMBOS servidores:**
1. **[1/2]** Digite `CONFIRMO`
2. **[2/2]** Digite `AMBOS-CONFIRMO`

🖥️ **Informação de HOST**: Todas as confirmações agora mostram o endereço IP e porta dos servidores que serão afetados!

> 💡 **Por quê?** Operações destrutivas são irreversíveis e precisam de máxima segurança!

### **Bancos Protegidos** (nunca são apagados):
- `postgres` - Banco padrão do sistema
- `template0` - Template padrão
- `template1` - Template padrão
- *Outros definidos no arquivo de configuração*

### **Usuários Protegidos** (nunca são apagados):
- `postgres` - Superusuário padrão
- `rds_superuser` - AWS RDS
- `cloudsqlsuperuser` - Google Cloud SQL
- `azure_superuser` - Azure
- *Outros definidos no arquivo de configuração*

### **🔍 Verificação Inteligente de Dependências**
Antes de tentar excluir um usuário, o script **automaticamente verifica** se ele:
- É proprietário de algum banco de dados
- É proprietário de schemas
- É proprietário de tabelas ou outros objetos

**Usuários com dependências são PULADOS** automaticamente, evitando erros como:
```
ERROR: role "prometheus" cannot be dropped because some objects depend on it
```

## 📊 **Opções de Linha de Comando**

```bash
python3 cleanup_database.py [OPÇÕES]

Opções:
  --server {origem,destino,ambos}    Servidor(es) para limpar
  --dry-run                          Simular sem executar (modo seguro)
  --databases-only                   Apagar apenas bancos de dados
  --users-only                       Apagar apenas usuários
  --force                           Pular confirmação (cuidado!)
  -h, --help                        Mostrar ajuda
```

## 🔍 **Exemplos de Uso**

### **1. Verificação Segura**
```bash
# Ver o que seria apagado
python3 cleanup_database.py --server origem --dry-run
```

**Saída esperada:**
```
📋 Bancos encontrados: 5
   🛡️ postgres
   🛡️ template0
   🛡️ template1
   🗑️ empresa_desenvolvimento
   🗑️ teste_migracao

👥 Usuários encontrados: 4
   🛡️ postgres
   🗑️ enterprise_user
   🗑️ migration_user
   🗑️ teste_user

🔍 [DRY-RUN] Apagaria banco: empresa_desenvolvimento
🔍 [DRY-RUN] Apagaria banco: teste_migracao
🔍 [DRY-RUN] Apagaria usuário: enterprise_user
🔍 [DRY-RUN] Usuário 'prometheus' seria PULADO (possui dependências)
🔍 [DRY-RUN] Apagaria usuário: migration_user
🔍 [DRY-RUN] Apagaria usuário: teste_user
```

### **2. Limpeza Real com Confirmação**
```bash
python3 cleanup_database.py --server origem
```

**Processo interativo (CONFIRMAÇÃO DUPLA OBRIGATÓRIA COM HOST):**
```
⚠️  ATENÇÃO: OPERAÇÃO DESTRUTIVA!
======================================================================
🎯 Servidor(es) alvo:
   • ORIGEM: 82.197.64.145:5432

🗑️ Esta operação irá APAGAR:
   • Todos os bancos de dados (exceto protegidos)
   • Todos os usuários (exceto protegidos)

❓ [1/2] Tem CERTEZA que deseja continuar? Digite 'CONFIRMO': CONFIRMO

🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴
🚨 CONFIRMAÇÃO FINAL OBRIGATÓRIA!
🚨 Esta operação é IRREVERSÍVEL!
🚨 Dados serão PERMANENTEMENTE perdidos!

🎯 HOSTS QUE SERÃO AFETADOS:
   🔴 82.197.64.145:5432 (origem)
🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴

🔴 [2/2] CONFIRMAÇÃO FINAL - Digite 'ORIGEM-CONFIRMO': ORIGEM-CONFIRMO
✅ Confirmação DUPLA realizada com sucesso. Prosseguindo...

🗑️ Banco apagado: empresa_desenvolvimento
🗑️ Banco apagado: teste_migracao
🗑️ Usuário apagado: enterprise_user
🗑️ Usuário apagado: migration_user
🗑️ Usuário apagado: teste_user

🎉 Limpeza concluída com sucesso!
```

### **3. Limpeza do Servidor DESTINO**
```bash
python3 cleanup_database.py --server destino
```

**Processo com confirmação dupla (MOSTRA HOST):**
```
⚠️  ATENÇÃO: OPERAÇÃO DESTRUTIVA!
======================================================================
🎯 Servidor(es) alvo:
   • DESTINO: 82.197.64.145:6432

❓ [1/2] Tem CERTEZA que deseja continuar? Digite 'CONFIRMO': CONFIRMO

🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴
🚨 CONFIRMAÇÃO FINAL OBRIGATÓRIA!
🚨 Esta operação é IRREVERSÍVEL!
🚨 Dados serão PERMANENTEMENTE perdidos!

🎯 HOSTS QUE SERÃO AFETADOS:
   🔴 82.197.64.145:6432 (destino)
🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴

🔴 [2/2] CONFIRMAÇÃO FINAL - Digite 'FINAL-CONFIRMO': FINAL-CONFIRMO
✅ Confirmação DUPLA realizada com sucesso. Prosseguindo...
```

### **4. Limpeza de AMBOS os Servidores**
```bash
python3 cleanup_database.py --server ambos
```

**Processo com múltiplos hosts:**
```
⚠️  ATENÇÃO: OPERAÇÃO DESTRUTIVA!
======================================================================
🎯 Servidor(es) alvo:
   • ORIGEM: 82.197.64.145:5432
   • DESTINO: 82.197.64.145:6432

❓ [1/2] Tem CERTEZA que deseja continuar? Digite 'CONFIRMO': CONFIRMO

🎯 HOSTS QUE SERÃO AFETADOS:
   🔴 82.197.64.145:5432 (origem)
   🔴 82.197.64.145:6432 (destino)

🔴 [2/2] CONFIRMAÇÃO FINAL - Digite 'AMBOS-CONFIRMO': AMBOS-CONFIRMO
✅ Confirmação DUPLA realizada com sucesso. Prosseguindo...
```

### **5. Limpeza Específica**
```bash
# Apenas bancos de dados
python3 cleanup_database.py --server origem --databases-only

# Apenas usuários
python3 cleanup_database.py --server origem --users-only
```

### **4. Exemplo de Usuários com Dependências**
```bash
python3 cleanup_database.py --server origem --users-only
```

**Saída mostrando verificação de dependências:**
```
🗑️ Iniciando limpeza de usuários...
⚠️ Processando 3 usuário(s): ['prometheus', 'enterprise_user', 'test_user']

⚠️ Usuário 'prometheus' PULADO - possui dependências
   📁 Bancos proprietários: ['monitoring_db']
   📂 Schemas proprietários: ['prometheus_schema']
   📋 Tabelas proprietárias: ['public.metrics', 'public.alerts', 'public.targets']

🗑️ Usuário apagado: enterprise_user
🗑️ Usuário apagado: test_user

📊 Usuários - Apagados: 2, Pulados: 1, Falharam: 0
```

## 🔧 **Funcionamento Interno**

### **Processo de Limpeza de Bancos:**
1. Lista todos os bancos de dados
2. Filtra bancos protegidos
3. Termina conexões ativas para cada banco
4. Executa `DROP DATABASE` para cada banco

### **Processo de Limpeza de Usuários:**
1. Lista todos os usuários
2. Filtra usuários protegidos
3. **🔍 Verifica dependências de cada usuário:**
   - Bancos de dados de propriedade do usuário
   - Schemas de propriedade do usuário
   - Tabelas de propriedade do usuário
4. **⚠️ PULA usuários com dependências** (evita erros)
5. Termina sessões ativas do usuário
6. Executa `DROP USER` para usuários sem dependências

### **SQLAlchemy Engine:**
- Usa `isolation_level="AUTOCOMMIT"` para `DROP DATABASE`
- Connection pooling automático
- Tratamento de erros por operação

## ⚡ **Casos de Uso Práticos**

### **🧪 Reset de Ambiente de Desenvolvimento**
```bash
# Limpar tudo e começar do zero
python3 cleanup_database.py --server origem --force
```

### **🔄 Preparar para Nova Migração**
```bash
# Limpar destino antes de migrar
python3 cleanup_database.py --server destino --databases-only
```

### **🧹 Manutenção Periódica**
```bash
# Verificar o que existe
python3 cleanup_database.py --server ambos --dry-run

# Limpar usuários de teste
python3 cleanup_database.py --server origem --users-only
```

## 🛠️ **Troubleshooting**

### **Erro: "Arquivo de configuração não encontrado"**
```bash
# Verificar se existe
ls -la src/migration/config/source_config.json
ls -la src/migration/config/destination_config.json
```

### **Erro: "Falha na conexão"**
- Verificar credenciais em `source_config.json`
- Testar conectividade de rede
- Confirmar que PostgreSQL está rodando

### **Erro: "Permission denied"**
- Usuário precisa de privilégios `CREATEDB` e `CREATEROLE`
- Para bancos de outros usuários, precisa ser owner ou superuser

### **Banco não pode ser apagado**
```
❌ Erro ao apagar banco 'meu_banco': database "meu_banco" is being accessed by other users
```
**Solução**: O script já tenta terminar conexões automaticamente, mas em alguns casos pode precisar de intervenção manual.

## 🔒 **Segurança**

### **Medidas de Proteção:**
1. **Confirmação interativa** obrigatória (exceto com `--force`)
2. **Lista de proteção** para bancos/usuários críticos
3. **Modo dry-run** para teste seguro
4. **Logs detalhados** de todas as operações

### **Recomendações:**
- **NUNCA use em produção**
- Sempre teste com `--dry-run` primeiro
- Mantenha backups antes de usar
- Use `--force` apenas em scripts automatizados seguros

## 📝 **Log de Exemplo**

```
2025-10-03 10:30:15 | INFO     | 🔌 Conectando ao origem (82.197.64.145:5432)...
2025-10-03 10:30:15 | INFO     | ✅ Conectado: PostgreSQL 16.0
2025-10-03 10:30:15 | INFO     | 📋 Bancos encontrados: 5
2025-10-03 10:30:15 | INFO     |    🛡️ postgres
2025-10-03 10:30:15 | INFO     |    🛡️ template0
2025-10-03 10:30:15 | INFO     |    🛡️ template1
2025-10-03 10:30:15 | INFO     |    🗑️ empresa_desenvolvimento
2025-10-03 10:30:15 | INFO     |    🗑️ teste_migracao
2025-10-03 10:30:15 | WARNING  | ⚠️ Será apagado 2 banco(s): ['empresa_desenvolvimento', 'teste_migracao']
2025-10-03 10:30:15 | INFO     | 🔌 Conexões terminadas para banco 'empresa_desenvolvimento'
2025-10-03 10:30:15 | INFO     | ✅ Banco apagado: empresa_desenvolvimento
2025-10-03 10:30:15 | INFO     | 🔌 Conexões terminadas para banco 'teste_migracao'
2025-10-03 10:30:15 | INFO     | ✅ Banco apagado: teste_migracao
2025-10-03 10:30:15 | INFO     | 📊 Bancos apagados: 2/2
```

## 🔧 **Correções Recentes**

### **v1.2.0 - Correção Completa das Queries SQL** (03/10/2025)
- ✅ **1º Bug corrigido**: Erro `column "schemaname" does not exist`
- ✅ **2º Bug corrigido**: Erro `column "tableowner" does not exist`
- ✅ **Solução definitiva**: Migração para catálogo PostgreSQL direto
  - `information_schema.schemata` → `pg_namespace` (catálogo nativo)
  - `information_schema.tables` → `pg_class + pg_namespace` (catálogo nativo)
- ✅ **Queries robustas**: Sem dependência de views do information_schema
- ✅ **Resultado**: Verificação de dependências 100% funcional
- ✅ **Impacto**: Usuários sem dependências serão corretamente identificados para exclusão

### **Evolução das correções:**
```
❌ v1.0: information_schema com nomes incorretos → ERRO
🔄 v1.1: information_schema com nomes corretos → ERRO PARCIAL
✅ v1.2: Catálogo PostgreSQL nativo → FUNCIONAL
```

### **Queries finais (v1.2.0):**
```sql
-- Schemas: pg_namespace (nativo)
SELECT nspname FROM pg_namespace n JOIN pg_authid a ON n.nspowner = a.oid

-- Tabelas: pg_class + pg_namespace (nativo)
SELECT n.nspname, c.relname FROM pg_class c JOIN pg_namespace n ON c.relnamespace = n.oid
```---

**⚠️ Lembre-se**: Este script é uma ferramenta poderosa. Use com responsabilidade!
