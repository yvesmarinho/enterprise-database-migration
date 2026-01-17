# Quick Start Guide - EvolutionPermissionsFixer

## 🚀 5 Minutos para Começar

### Passo 1: Instalar Dependências
```bash
pip install -r requirements.txt
```

### Passo 2: Configurar Variáveis de Ambiente (Opcional)
```bash
# Arquivo .env (na raiz do projeto)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha
POSTGRES_HOST=wf004.vya.digital
POSTGRES_PORT=5432
POSTGRES_DB=postgres
```

### Passo 3: Testar em Modo Seguro (Dry-Run)
```bash
# Simulará as operações sem fazer alterações
python3 run_fix_evolution_permissions.py --dry-run
```

### Passo 4: Executar (Se tudo parecer OK)
```bash
# Executará as alterações de verdade
python3 run_fix_evolution_permissions.py --execute
```

---

## 📋 Casos de Uso Comuns

### ✓ Caso 1: Usar Variáveis de Ambiente
```bash
# Assumindo que .env está configurado
python3 run_fix_evolution_permissions.py --dry-run
python3 run_fix_evolution_permissions.py --execute
```

### ✓ Caso 2: Credenciais Específicas
```bash
python3 run_fix_evolution_permissions.py --execute \
  --host wf004.vya.digital \
  --user postgres \
  --password sua_senha \
  --port 5432
```

### ✓ Caso 3: Debug Detalhado
```bash
python3 run_fix_evolution_permissions.py --execute --verbose
```

### ✓ Caso 4: Parar no Primeiro Erro
```bash
python3 run_fix_evolution_permissions.py --execute --stop-on-error
```

### ✓ Caso 5: Usar Diretamente em Python
```python
from core.fix_evolution_permissions import fix_evolution_database_permissions

results = fix_evolution_database_permissions(
    connection_string="postgresql://postgres:pass@localhost/postgres",
    dry_run=False
)

print(results)
```

---

## 🧪 Testes

### Executar Testes
```bash
# Todos os testes
python3 -m pytest test/test_fix_evolution_permissions.py -v

# Ou direto
python3 test/test_fix_evolution_permissions.py
```

### Exemplo de Saída
```
test_connection_string_stored ... ok
test_database_info_dataclass ... ok
test_default_roles ... ok
test_expected_owner ... ok
test_results_initialization ... ok
...

Ran 20 tests in 0.5s
OK
```

---

## 📊 Entender os Resultados

### Saída do Dry-Run
```
======================================================================
EvolutionPermissionsFixer - Corretor de Permissões
======================================================================
Conectando a: wf004.vya.digital:5432/postgres
Usuário: postgres
⊘ MODO DRY-RUN: Nenhuma alteração será feita

======================================================================
Processando banco: evolution_api_db
======================================================================
ℹ Info atual: DatabaseInfo(name=evolution_api_db, owner=app_user, ...)
✓ Alterando owner de 'evolution_api_db' para 'postgres'
✓ Alterando tablespace de 'evolution_api_db' para 'ts_enterprise_data'
✓ Ajustando connection limit de 'evolution_api_db' para -1
✓ Revogando ALL do PUBLIC em 'evolution_api_db'
✓ Concedendo CONNECT em 'evolution_api_db' a 'evolution_api_user'
✓ Permissões do schema public corrigidas em 'evolution_api_db'

======================================================================
RELATÓRIO FINAL
======================================================================
Bancos processados: 1
  ✓ evolution_api_db
Permissões ajustadas: 1
```

### Significado dos Símbolos
- `✓` = Sucesso
- `⚠` = Aviso
- `✗` = Erro
- `ℹ` = Informação
- `⊘` = Pulado/Simulado

---

## 🔍 Troubleshooting

### Problema: "Unable to import 'dotenv'"
**Solução:**
```bash
pip install python-dotenv
```

### Problema: "Connection refused"
**Solução:**
- Verificar se PostgreSQL está rodando
- Verificar host, porta, usuário e senha
- Testar com: `psql -h host -U user -d postgres`

### Problema: "Permission denied"
**Solução:**
- Usar superuser (postgres)
- Ou usuário com privilégios CREATEDB e ALTER ROLE

### Problema: "Role does not exist"
**Solução:**
- Esperado! O módulo pula roles que não existem
- Verifique logs de AVISO

### Problema: "statement timeout"
**Solução:**
```bash
python3 run_fix_evolution_permissions.py --execute --timeout 60
```

---

## 📚 Documentação

Para mais informações, consulte:

- **Documentação Completa**: `docs/EVOLUTION_PERMISSIONS_FIXER.md`
- **Resumo de Implementação**: `docs/IMPLEMENTATION_SUMMARY_FIX_EVOLUTION_PERMISSIONS.md`
- **Exemplos Detalhados**: `examples/example_fix_evolution_permissions.py`
- **Testes**: `test/test_fix_evolution_permissions.py`

---

## ⚡ Resumo Rápido

```bash
# 1. Testar (SEMPRE FAZER ISSO PRIMEIRO)
python3 run_fix_evolution_permissions.py --dry-run

# 2. Se tudo OK, executar
python3 run_fix_evolution_permissions.py --execute

# 3. Validar no banco
psql -U postgres -d evolution_api_db -c "\d public"
```

---

## 🆘 Suporte

Mensagens de erro incluem:
- ✓ Descrição clara do problema
- ✓ Banco afetado
- ✓ SQL exato executado
- ✓ Sugestões de correção

Verifique o logging em `-v` (verbose) para mais detalhes.

---

## ✅ Checklist Pré-Produção

- [ ] Backup do banco feito
- [ ] Testou com `--dry-run`
- [ ] Reviewou saída de dry-run
- [ ] Nenhum erro ou aviso crítico
- [ ] Janela de manutenção agendada
- [ ] Time informado sobre manutenção
- [ ] Rodou testes: `python3 test/test_fix_evolution_permissions.py`
- [ ] Conexão testada com: `psql -U postgres -d postgres`
- [ ] Variáveis de ambiente corretas (ou credenciais via CLI)
- [ ] Prontos para `--execute`

---

## 🎯 O que o Script Faz

Para cada banco `evolution*`:

1. ✓ Localiza o banco
2. ✓ Obtém informações
3. ✓ Ajusta owner para `postgres`
4. ✓ Ajusta tablespace para `ts_enterprise_data`
5. ✓ Define connection limit como -1
6. ✓ Revoga privilégios do PUBLIC
7. ✓ Concede CONNECT aos roles especificados
8. ✓ Corrige permissões do schema public
9. ✓ Faz commit ou rollback (automático)
10. ✓ Relata resultados

---

## 📞 Contato para Dúvidas

Verifique a seção "Troubleshooting" acima ou consulte:
- Documentação: `docs/EVOLUTION_PERMISSIONS_FIXER.md`
- Exemplos: `examples/example_fix_evolution_permissions.py`

---

**Pronto? Vamos começar! 🚀**

```bash
python3 run_fix_evolution_permissions.py --dry-run
```
