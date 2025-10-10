# Solução de Problemas: uv sync

## 🚨 Problema Identificado

```
× No solution found when resolving dependencies for split (markers: python_full_version >= '3.8.1' and python_full_version < '3.9'):
╰─▶ Because pre-commit>=3.6.0 depends on Python>=3.9, we can conclude that pre-commit>=3.6.0 cannot be used.
```

## 🔍 Análise dos Logs

### Evidências encontradas:
- **Log de migração**: Sistema rodando com `Python 3.12.3`
- **Arquivo `.python-version`**: Definido para `3.13`
- **Conflito**: `pyproject.toml` estava com `requires-python = ">=3.8"` mas `pre-commit>=3.6.0` requer Python>=3.9

## ✅ Solução Implementada

### 1. **Ajuste de Compatibilidade Python**
```toml
# ANTES
requires-python = ">=3.8"

# DEPOIS
requires-python = ">=3.9"
```

### 2. **Atualização de Dependência Conflitante**
```toml
# ANTES
"pre-commit>=3.6.0"

# DEPOIS
"pre-commit>=3.7.0"  # Compatível com Python 3.9+
```

### 3. **Classificadores Atualizados**
Removido `"Programming Language :: Python :: 3.8"` dos classificadores para manter consistência.

## 🧪 Teste da Solução

Execute novamente:
```bash
uv sync
```

O comando agora deve funcionar corretamente pois:
- ✅ Python 3.9+ é suportado por todas as dependências
- ✅ `pre-commit>=3.7.0` é compatível com Python 3.9+
- ✅ Sistema atual (Python 3.13) está dentro do range suportado

## 📊 Compatibilidade Resultante

| Dependência | Versão Mínima Python | Status |
|-------------|---------------------|---------|
| psycopg2-binary | 3.7+ | ✅ |
| SQLAlchemy | 3.7+ | ✅ |
| colorama | 3.7+ | ✅ |
| mysql-connector | 3.8+ | ✅ |
| jsonschema | 3.8+ | ✅ |
| pre-commit | **3.9+** | ✅ (corrigido) |
| pytest | 3.7+ | ✅ |
| black | 3.8+ | ✅ |

## 🚨 Segundo Problema: Build do Pacote

Após resolver o conflito de dependências, apareceu um novo erro:
```
ValueError: Unable to determine which files to ship inside the wheel using the following heuristics
The most likely cause of this is that there is no directory that matches the name of your project (enterprise_database_migration).
```

### 🔍 Análise
- O Hatchling não encontrou um diretório `enterprise_database_migration/`
- O projeto tem estrutura não-padrão com múltiplos diretórios na raiz
- Precisamos especificar explicitamente quais arquivos incluir

### ✅ Solução: Configuração Hatchling
```toml
[tool.hatch.build.targets.wheel]
packages = [
    "core", "utils", "cleanup", "validation",
    "components", "orchestrators", "cli"
]
include = [
    "*.py",
    "config/*.json",
    "secrets/*.json"
]
```

## 🎯 Resultado Final

- **Versão Python mínima**: 3.9 (equilibrio entre compatibilidade e modernidade)
- **Versões suportadas**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Dependências resolvidas**: Todas compatíveis
- **Build configurado**: Hatchling sabe quais arquivos incluir
- **uv sync**: Deve executar sem erros
