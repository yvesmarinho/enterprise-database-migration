# 🧹 PostgreSQL Database Cleanup Module

## 📋 **Índice de Arquivos**

### **🎯 Scripts Principais:**
- `cleanup_database.py` - Script principal de limpeza de bancos PostgreSQL
- `exemplo_cleanup.py` - Exemplos interativos de uso do cleanup

### **📚 Documentação:**
- `CLEANUP_README.md` - Documentação completa do sistema de cleanup

### **🧪 Scripts de Teste:**
- `test_double_confirmation.py` - Testa lógica de confirmação dupla
- `test_protection_config.py` - Valida configurações de proteção
- `test_sql_fix.py` - Testa correções das queries SQL
- `test_user_dependencies.py` - Testa verificação de dependências

## 🚀 **Como Usar**

### **Execução Principal:**
```bash
# Modo seguro (simulação)
python3 cleanup_database.py --server destino --dry-run

# Execução real
python3 cleanup_database.py --server destino
```

### **Exemplos Interativos:**
```bash
python3 exemplo_cleanup.py
```

### **Testes:**
```bash
python3 test_protection_config.py
python3 test_double_confirmation.py
python3 test_sql_fix.py
python3 test_user_dependencies.py
```

## 🛡️ **Funcionalidades**

- ✅ **Confirmação dupla** com informação de host
- ✅ **Verificação de dependências** para evitar erros
- ✅ **Proteção de usuários/bancos** críticos
- ✅ **Modo dry-run** para simulação segura
- ✅ **Logs detalhados** de todas as operações
- ✅ **Configuração via JSON** flexível

## 📊 **Configurações**

As configurações são carregadas de:
- `../config/source_config.json` (servidor origem)
- `../config/destination_config.json` (servidor destino)

Seção `cleanup_protection` define bancos e usuários protegidos.

---
**⚡ Módulo de limpeza totalmente funcional e seguro!**
