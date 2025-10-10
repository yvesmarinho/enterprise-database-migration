# 🧹 Guia de Limpeza de Arquivos - Sistema v4.0.0

Este documento identifica arquivos que podem ser **arquivados** ou **removidos** após a consolidação do sistema v4.0.0.

---

## 📂 **Arquivos para Arquivar**

### **🔬 Scripts de Debug (Desenvolvimento)**
*Podem ser movidos para `legacy/debug/`*

```
debug_apply_privileges.py      # Debug de aplicação de privilégios
debug_get_privileges.py        # Debug de obtenção de privilégios
debug_grants_destino.py        # Debug de grants no destino
debug_privileges.py            # Debug geral de privilégios
debug_privileges_issue.py      # Debug de problema específico
debug_quick.py                 # Debug rápido
```

### **🧪 Scripts de Teste (Desenvolvimento)**
*Podem ser movidos para `legacy/tests/`*

```
test_cleanup_config.py         # Teste de configuração de limpeza
test_commit_fix.py            # Teste de correção de commit
test_grant_application.py     # Teste de aplicação de grants
test_grants_stackoverflow.py  # Teste baseado em StackOverflow
test_privilege_collection.py  # Teste de coleta de privilégios
test_privileges.py            # Teste geral de privilégios
test_protections.py           # Teste de proteções
test_user_creation.py         # Teste de criação de usuários
```

### **📋 Scripts de Validação (Desenvolvimento)**
*Podem ser movidos para `legacy/validation/`*

```
validate_grants.py            # Validação de grants (v1)
validate_grants_corrected.py  # Validação corrigida (v2)
validate_grants_final.py      # Validação final (v3)
validate_grants_simple.py     # Validação simples (v4)
```

### **⚙️ Scripts de Execução (Versões Antigas)**
*Podem ser movidos para `legacy/executors/`*

```
execute_real_migration.py     # Executor real (v1)
execute_real_migration_fixed.py  # Executor corrigido (v2)
```

### **🔍 Scripts de Análise (Desenvolvimento)**
*Podem ser movidos para `legacy/analysis/`*

```
analise_resultados_grants.py  # Análise de resultados de grants
investigate_contradiction.py  # Investigação de contradições
verify_after_debug.py        # Verificação pós-debug
```

### **📊 Scripts de Fase (Protótipos)**
*Podem ser movidos para `legacy/phases/`*

```
phase1_extract_wf004.py       # Protótipo Fase 1 - Extração
phase2_generate_scripts.py    # Protótipo Fase 2 - Geração
phase3_controlled_executor.py # Protótipo Fase 3 - Execução
```

---

## ✅ **Arquivos Ativos (Manter)**

### **🏗️ Sistema Principal**
```
migration_orchestrator.py     # ✅ Orquestrador principal v4.0.0
README.md                     # ✅ Documentação principal
setup.sh                      # ✅ Script de instalação
exemplo_uso.py               # ✅ Exemplos de uso
```

### **📁 Módulos Core**
```
core/modules/data_extractor.py     # ✅ Extrator de dados v4.0.0
core/modules/script_generator.py   # ✅ Gerador de scripts v4.0.0
core/modules/migration_executor.py # ✅ Executor v4.0.0
```

### **⚙️ Configuração**
```
config/migration_config.json  # ✅ Configuração unificada
secrets/*.json                # ✅ Credenciais de conexão
```

### **📚 Documentação**
```
docs/PROGRESS_DOCUMENTATION.md # ✅ Documentação de progresso
docs/*.md                     # ✅ Documentação técnica
```

---

## 🚀 **Comandos de Organização**

### **Criar Estrutura Legacy:**
```bash
mkdir -p legacy/{debug,tests,validation,executors,analysis,phases}
```

### **Mover Arquivos de Debug:**
```bash
mv debug_*.py legacy/debug/
```

### **Mover Arquivos de Teste:**
```bash
mv test_*.py legacy/tests/
```

### **Mover Scripts de Validação:**
```bash
mv validate_*.py legacy/validation/
```

### **Mover Executores Antigos:**
```bash
mv execute_real_migration*.py legacy/executors/
```

### **Mover Scripts de Análise:**
```bash
mv analise_*.py investigate_*.py verify_*.py legacy/analysis/
```

### **Mover Protótipos de Fase:**
```bash
mv phase*.py legacy/phases/
```

---

## 📊 **Impacto da Limpeza**

### **Antes da Limpeza:**
- 📁 **~50 arquivos** na raiz do projeto
- 🔍 **Difícil navegação** entre arquivos importantes e temporários
- ⚠️ **Confusão** entre versões ativas e arquivadas

### **Após a Limpeza:**
- 📁 **~15 arquivos** na raiz (apenas essenciais)
- ✅ **Navegação limpa** e profissional
- 🎯 **Foco claro** no sistema v4.0.0 produção

---

## ⚠️ **Considerações Importantes**

1. **🔒 Backup**: Fazer backup completo antes da limpeza
2. **🔗 Dependencies**: Verificar se algum arquivo ativo referencia os arquivos a mover
3. **📝 Documentation**: Manter registro dos arquivos movidos
4. **🔄 Reversibility**: Estrutura permite restauração fácil se necessário

---

## 📅 **Cronograma Sugerido**

1. **Fase 1** - Criar estrutura `legacy/`
2. **Fase 2** - Mover arquivos de debug e teste
3. **Fase 3** - Mover scripts de validação
4. **Fase 4** - Mover executores e protótipos antigos
5. **Fase 5** - Verificar funcionamento do sistema limpo

---

*Documento gerado em: 6 de outubro de 2025*
*Para sistema: PostgreSQL Enterprise Migration System v4.0.0*
