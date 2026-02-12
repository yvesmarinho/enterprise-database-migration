#!/bin/bash
# Exemplos de uso do setup_database_user_permissions.py

























































































































































































































































































































































🔐 **Segurança em primeiro lugar - Sem exceções, sem concessões**---**Status:** ✅ Ativo**Versão:** 3.0.0  **Data de Implementação:** 28 de janeiro de 2026  ---| **Validação** | ✅ Verifica se database existe || **Modo Interativo** | ✅ Atualizado (solicita database) || **Retrocompatibilidade** | ⚠️ Scripts antigos precisam atualização || **Segurança** | ✅ Máxima (princípio do menor privilégio) || **--database** | 🔒 Obrigatório para TODOS os tipos || **Acesso Global** | 🚫 Completamente removido ||------|--------|| Item | Status |## ✨ Resumo---6. ✅ **SECURITY_UPDATE_V3.md** - Este documento5. ✅ [setup_database_permissons_run.sh](setup_database_permissons_run.sh) - Script de exemplo4. ✅ [examples_setup_database_permissions.sh](examples_setup_database_permissions.sh) - Exemplos3. ✅ [SECURITY_RULES.md](SECURITY_RULES.md) - Regras de segurança2. ✅ [README_ADMIN_PASSWORD_JSON.md](README_ADMIN_PASSWORD_JSON.md) - Guia de autenticação1. ✅ [setup_database_user_permissions.py](setup_database_user_permissions.py) - Código principalTodos os seguintes documentos foram atualizados para refletir esta mudança:## 📚 Documentos Atualizados---   ```   python scripts/setup_database_user_permissions.py   ```bash3. Use o modo interativo para testes:   ```   bash scripts/examples_setup_database_permissions.sh   ```bash2. Execute os exemplos:   - [SECURITY_RULES.md](SECURITY_RULES.md)   - [README_ADMIN_PASSWORD_JSON.md](README_ADMIN_PASSWORD_JSON.md)1. Verifique a documentação atualizada:Para dúvidas ou problemas relacionados a esta mudança:## 📞 Suporte---- Digite `n` e verifique o nome correto da database- Digite `S` se a database será criada depois**Solução:** ```Deseja criar permissões para 'xyz' mesmo assim? (S/n):   ...   • botpress_db   • app_workforce   • ai_process_dbDatabases disponíveis (47):⚠️  AVISO: Database 'xyz' não encontrada```### Erro 2: Database não encontrada---**Solução:** Adicione `--database nome_da_database` ao comando```🚨 ERRO DE SEGURANÇA: Parâmetro --database é OBRIGATÓRIO```### Erro 1: Database obrigatória## 🚨 Mensagens de Erro Comuns---```SHOW GRANTS FOR 'backup_user'@'%';-- Verificar grants de um usuárioORDER BY User, Host;WHERE User NOT IN ('root', 'mysql.sys', 'mysql.session')FROM mysql.user    Delete_priv    Update_priv,    Insert_priv,    Select_priv,    Host,    User, SELECT -- Listar todos os usuários e seus hosts```sql### MySQL```ORDER BY datname;WHERE datistemplate = falseFROM pg_database    has_database_privilege('backup_user', datname, 'CONNECT') AS can_connect    datname AS database,SELECT -- Verificar permissões de um usuário específico em cada databaseORDER BY r.rolname;GROUP BY r.rolname, r.rolsuper  AND d.datistemplate = falseWHERE r.rolcanlogin = trueLEFT JOIN pg_database d ON trueLEFT JOIN pg_auth_members m ON r.oid = m.memberFROM pg_roles r    array_agg(DISTINCT d.datname) AS databases    END AS type,        ELSE 'REGULAR'        WHEN r.rolsuper THEN 'SUPERUSER'    CASE     r.rolname AS username,SELECT -- Listar todos os usuários e suas permissões```sql### PostgreSQL## 🔍 Como Verificar Usuários Existentes---- [ ] Comunicar mudança à equipe- [ ] Atualizar documentação interna  - [ ] Planejar restrição de permissões (se necessário)  - [ ] Verificar se algum tem acesso global desnecessário- [ ] Revisar usuários existentes no banco  - [ ] Validar permissões concedidas  - [ ] Testar em ambiente de desenvolvimento  - [ ] Adicionar `--database nome_da_database`  - [ ] Determinar a database apropriada- [ ] Para cada script identificado:- [ ] Verificar quais NÃO especificam `--database`- [ ] Identificar todos os scripts que usam `setup_database_user_permissions.py`Se você usa este script em produção, siga este checklist:## 📝 Checklist de Migração---   - Permite rastreamento detalhado   - Facilita auditorias de segurança   - Cada permissão é explícita e documentada5. **Auditoria e Rastreabilidade**   - Sem exceções = sem erros de configuração   - Impossível criar usuários com privilégios excessivos por engano4. **Prevenção de Erros Humanos**   - SOX e outras normas exigem auditoria detalhada   - LGPD/GDPR requerem controle granular   - PCI-DSS exige segregação de acesso3. **Conformidade Regulatória**   - Uma brecha em um usuário não compromete tudo   - Quanto menos acesso, menor o risco2. **Redução de Superfície de Ataque**   - Acesso global viola este princípio fundamentalmente   - Usuários devem ter APENAS as permissões necessárias1. **Princípio do Menor Privilégio**### Por que remover completamente acesso global?## 🛡️ Justificativa de Segurança---```    --database app_workforce  # ADICIONADO    --type read \    --password monitor123 \    --username monitoring \    --admin-user migration_user \    --db-type postgresql \python scripts/setup_database_user_permissions.py \# Criar usuário read-only para database específica# ✅ SCRIPT CORRIGIDO#!/bin/bash```bash**Como corrigir:**```# RESULTADO: ERRO - database obrigatória    --type read    --password monitor123 \    --username monitoring \    --admin-user migration_user \    --db-type postgresql \python scripts/setup_database_user_permissions.py \# Criar usuário read-only global# ❌ ESTE SCRIPT NÃO FUNCIONA MAIS#!/bin/bash```bash**Exemplo de script antigo que não funciona mais:**Se você tinha scripts que criavam usuários SEM `--database`, eles **FALHARÃO** agora.### Scripts Existentes Afetados## 📊 Impacto da Mudança---| **Acesso Global** | 🟡 Possível (alguns tipos) | 🚫 **REMOVIDO** || **Com --database** | ✅ Permitido | ✅ Permitido || **Migration sem --database** | ⚠️ Confirmação 'SIM' | ❌ Bloqueado || **Write sem --database** | ⚠️ Confirmação 'SIM' | ❌ Bloqueado || **Read sem --database** | ⚠️ Confirmação 'SIM' | ❌ Bloqueado || **Backup sem --database** | ❌ Bloqueado | ❌ Bloqueado ||----------------|----------------------|-------------------|| Funcionalidade | Versão 2.0 (Anterior) | Versão 3.0 (Atual) |## 🔄 Comparação: Antes vs Agora---```    --database evolution_api_1    --type migration \    --password dba_pass \    --username dba_evolution \    --admin-user migration_user \    --db-type postgresql \python scripts/setup_database_user_permissions.py \# ✅ Migration (DBA)    --database botpress_db    --type write \    --password write_pass \    --username write_botpress \    --admin-user migration_user \    --db-type postgresql \python scripts/setup_database_user_permissions.py \# ✅ Write    --database kutt    --type read \    --password read_pass \    --username readonly_kutt \    --admin-user migration_user \    --db-type postgresql \python scripts/setup_database_user_permissions.py \# ✅ Read-only    --database app_workforce    --type backup \    --password backup_pass \    --username backup_workforce \    --admin-user migration_user \    --db-type postgresql \python scripts/setup_database_user_permissions.py \# ✅ Backup```bash### Todos os tipos DEVEM especificar --database## ✅ COMO USAR AGORA---```❌ Operação cancelada por motivos de segurança.  --database kutt --type read  --database app_workforce --type backupExemplos:Use o parâmetro --database para especificar a database.a databases específicas. Acesso global NÃO é permitido.Por motivos de segurança, TODOS os usuários devem ser restritos======================================================================🚨 ERRO DE SEGURANÇA: Parâmetro --database é OBRIGATÓRIO======================================================================```**TODOS os comandos acima resultarão em:**```    --password senha    --username admin_user \    --type migration \python scripts/setup_database_user_permissions.py \# ❌ ERRO: Tipo migration sem database    --password senha    --username write_user \    --type write \python scripts/setup_database_user_permissions.py \# ❌ ERRO: Tipo write sem database    --password senha    --username readonly_user \    --type read \python scripts/setup_database_user_permissions.py \# ❌ ERRO: Tipo read sem database    --password senha    --username backup_user \    --type backup \python scripts/setup_database_user_permissions.py \# ❌ ERRO: Tipo backup sem database```bash### ❌ BLOQUEADO: Qualquer usuário sem --database## 🚫 O que NÃO É MAIS PERMITIDO---Por questões de segurança máxima, o parâmetro `--database` agora é **OBRIGATÓRIO** para **TODOS** os tipos de usuário, sem exceções.**ACESSO GLOBAL FOI COMPLETAMENTE REMOVIDO DO SISTEMA**## 📋 Mudança Crítica---## Versão: 3.0.0 - ACESSO GLOBAL COMPLETAMENTE REMOVIDO## Data: 28 de janeiro de 2026# Com autenticação automática via JSON

echo "================================================"
echo "Exemplos: setup_database_user_permissions.py"
echo "================================================"
echo ""

# Exemplo 1: PostgreSQL - Busca senha automaticamente do JSON
echo "1️⃣ Criar usuário backup (PostgreSQL) - Database específica OBRIGATÓRIA"
echo "   Senha do admin_user será buscada automaticamente do JSON"
echo "   🚨 Parâmetro --database é OBRIGATÓRIO (sem exceções)"
echo ""
echo "python scripts/setup_database_user_permissions.py \\"
echo "    --db-type postgresql \\"
echo "    --host wfdb02.vya.digital \\"
echo "    --admin-user migration_user \\"
echo "    --username backup_user \\"
echo "    --password backup_pass_123 \\"
echo "    --type backup \\"
echo "    --database app_workforce"
echo ""
echo "---"
echo ""

# Exemplo 2: PostgreSQL - Usuário read-only em database específica
echo "2️⃣ Criar usuário read-only em database específica (PostgreSQL)"
echo "   🚨 --database é OBRIGATÓRIO para TODOS os tipos"
echo ""
echo "python scripts/setup_database_user_permissions.py \\"
echo "    --db-type postgresql \\"
echo "    --admin-user migration_user \\"
echo "    --username readonly_user \\"
echo "    --password readonly_pass_123 \\"
echo "    --type read \\"
echo "    --database app_workforce"
echo ""
echo "---"
echo ""

# Exemplo 3: PostgreSQL - Usuário write para database específica
echo "3️⃣ Criar usuário write em database específica"
echo "   🚨 --database é OBRIGATÓRIO (acesso global não é permitido)"
echo ""
echo "python scripts/setup_database_user_permissions.py \\"
echo "    --db-type postgresql \\"
echo "    --admin-user migration_user \\"
echo "    --username app_user \\"
echo "    --password app_pass_123 \\"
echo "    --type write \\"
echo "    --database app_workforce"
echo ""
echo "---"
echo ""

# Exemplo 5: Modo interativo (sem parâmetros)
echo "5️⃣ Modo interativo"
echo "   O script solicitará todas as informações necessárias"
echo ""
echo "python scripts/setup_database_user_permissions.py"
echo ""
echo "---"
echo ""

# Exemplo 5: Usando arquivo de configuração específico
echo "5️⃣ Usar arquivo de configuração específico"
echo ""
echo "python scripts/setup_database_user_permissions.py \\"
echo "    --db-type postgresql \\"
echo "    --config secrets/postgresql_source_config.json \\"
echo "    --admin-user postgres \\"
echo "    --username migration_user \\"
echo "    --password mig_pass_123 \\"
echo "    --type migration"
echo ""
echo "---"
echo ""

# Exemplo 6: Listar databases disponíveis
echo "6️⃣ Listar databases antes de criar usuário"
echo ""
echo "python scripts/setup_database_user_permissions.py \\"
echo "    --db-type postgresql \\"
echo "    --admin-user migration_user \\"
echo "    --list-databases"
echo ""
echo "---"
echo ""

# Exemplo 7: Mostrar grants após criação
echo "7️⃣ Criar usuário e mostrar privilégios concedidos"
echo ""
echo "python scripts/setup_database_user_permissions.py \\"
echo "    --db-type postgresql \\"
echo "    --admin-user migration_user \\"
echo "    --username test_user \\"
echo "    --password test_pass_123 \\"
echo "    --type read \\"
echo "    --show-grants"
echo ""
echo "---"
echo ""

# Erro esperado 1: Usuário não existe no JSON
echo "⚠️ ERRO ESPERADO 1: Usuário não encontrado no JSON"
echo ""
echo "python scripts/setup_database_user_permissions.py \\"
echo "    --db-type postgresql \\"
echo "    --admin-user usuario_invalido \\"
echo "    --username test_user \\"
echo "    --password test_pass \\"
echo "    --type read"
echo ""
echo "Resultado esperado:"
echo "❌ ERRO: Usuário 'usuario_invalido' não encontrado no arquivo de configuração"
echo "   Usuário disponível no JSON: 'migration_user'"
echo ""
echo "---"
echo ""

# Erro esperado 2: Qualquer tipo sem database
echo "🚨 ERRO ESPERADO 2: Qualquer tipo sem database (BLOQUEADO)"
echo "   🚨 NOVO: TODOS os tipos exigem --database"
echo ""
echo "python scripts/setup_database_user_permissions.py \\"
echo "    --db-type postgresql \\"
echo "    --admin-user migration_user \\"
echo "    --username any_user \\"
echo "    --password any_pass \\"
echo "    --type read"
echo ""
echo "Resultado esperado:"
echo "🚨 ERRO DE SEGURANÇA: Parâmetro --database é OBRIGATÓRIO"
echo "Por motivos de segurança, TODOS os usuários devem ser restritos"
echo "a databases específicas. Acesso global NÃO é permitido."
echo ""
echo "================================================"
