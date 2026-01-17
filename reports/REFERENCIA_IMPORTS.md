# 🔗 Padrão de Importação - Referência Rápida

**Data:** 2 de novembro de 2025
**Status:** ✅ Estrutura Finalizada

---

## 📋 Tabela de Imports

### **Core Module** (`/app/core/`)

| Classe/Função | Import | Exemplo |
|---|---|---|
| MigrationOrchestrator | `from app.core.migration_orchestrator import MigrationOrchestrator` | `orchestrator = MigrationOrchestrator(config)` |
| MigrationConfig | `from app.core.migration_structure import MigrationConfig` | `config = MigrationConfig(...)` |
| Validator | `from app.core.validator import Validator` | `validator = Validator()` |
| DataExtractor | `from app.core.modules.data_extractor import DataExtractor` | `extractor = DataExtractor(db)` |
| MigrationExecutor | `from app.core.modules.migration_executor import MigrationExecutor` | `executor = MigrationExecutor()` |

### **Cleanup Module** (`/app/cleanup/`)

| Classe/Função | Import | Exemplo |
|---|---|---|
| CleanupDatabase | `from app.cleanup.cleanup_database import CleanupDatabase` | `cleanup = CleanupDatabase(db)` |

### **Validation Module** (`/app/validation/`)

| Classe/Função | Import | Exemplo |
|---|---|---|
| GrantValidator | `from app.validation.validate_grants_simple import GrantValidator` | `validator = GrantValidator(db)` |
| WFDBStatusChecker | `from app.validation.check_wfdb02_status import WFDBStatusChecker` | `checker = WFDBStatusChecker()` |
| ScramAuthChecker | `from app.validation.check_scram_auth import ScramAuthChecker` | `checker = ScramAuthChecker()` |

### **Orchestrators Module** (`/app/orchestrators/`)

| Classe/Função | Import | Exemplo |
|---|---|---|
| OrchestratorPurePython | `from app.orchestrators.orchestrator_pure_python import Orchestrator` | `orch = Orchestrator()` |

---

## 📁 Localização de Importação por Tipo

### ✅ Em Arquivos `/app/**/*.py`

```python
# Não precisa de prefixo, está dentro do app
from app.core.migration_orchestrator import MigrationOrchestrator
from app.cleanup.cleanup_database import CleanupDatabase

# Ou (menos comum):
from .migration_orchestrator import MigrationOrchestrator  # import relativo
```

### ✅ Em Arquivos `/scripts/*.py`

```python
# Sempre use prefixo app.
from app.core.migration_orchestrator import MigrationOrchestrator
from app.cleanup.cleanup_database import CleanupDatabase
from app.validation.validate_grants_simple import GrantValidator
```

### ✅ Em Arquivos `/test/test_*.py`

```python
# Use prefixo app.
from app.core.migration_orchestrator import MigrationOrchestrator
from app.cleanup.cleanup_database import CleanupDatabase
import pytest
```

### ✅ Em `/main.py`

```python
# Use prefixo app.
from app.core.migration_orchestrator import MigrationOrchestrator
from app.orchestrators.orchestrator_pure_python import Orchestrator
```

### ✅ Em `/examples/*.py`

```python
# Use prefixo app.
from app.core.migration_orchestrator import MigrationOrchestrator
from app.core.migration_structure import MigrationConfig
```

---

## ❌ Padrão ANTIGO (Não usar mais)

```python
# ❌ ERRADO
from core.migration_orchestrator import MigrationOrchestrator
from cleanup.cleanup_database import CleanupDatabase
from validation.validate_grants import GrantValidator
from orchestrators.orchestrator_pure_python import Orchestrator

# ✅ CORRETO
from app.core.migration_orchestrator import MigrationOrchestrator
from app.cleanup.cleanup_database import CleanupDatabase
from app.validation.validate_grants import GrantValidator
from app.orchestrators.orchestrator_pure_python import Orchestrator
```

---

## 🔍 Como Atualizar Imports Existentes

### Opção 1: Manualmente
```bash
# Abra o arquivo e substitua:
# core. → app.core.
# cleanup. → app.cleanup.
# validation. → app.validation.
# orchestrators. → app.orchestrators.
```

### Opção 2: Usando sed (Linux/Mac)
```bash
# Em um diretório específico:
find . -name "*.py" -exec sed -i 's/from core\./from app.core./g' {} \;
find . -name "*.py" -exec sed -i 's/from cleanup\./from app.cleanup./g' {} \;
find . -name "*.py" -exec sed -i 's/from validation\./from app.validation./g' {} \;
find . -name "*.py" -exec sed -i 's/from orchestrators\./from app.orchestrators./g' {} \;
```

### Opção 3: Usando VS Code
1. Pressione `Ctrl+H` (Find and Replace)
2. Ative "Use Regular Expression" (.*abc)
3. Busque: `from (core|cleanup|validation|orchestrators)\.`
4. Substitua: `from app.$1.`

---

## 📚 Exemplo Completo

### Arquivo: `/scripts/novo_script.py`

```python
#!/usr/bin/env python3
"""Novo script para operação XYZ"""

import argparse
import sys
from pathlib import Path

# ✅ Imports corretos do app
from app.core.migration_orchestrator import MigrationOrchestrator
from app.core.migration_structure import MigrationConfig
from app.cleanup.cleanup_database import CleanupDatabase
from app.validation.validate_grants_simple import GrantValidator

def main():
    parser = argparse.ArgumentParser(description="Novo script")
    parser.add_argument('--server', required=True)
    parser.add_argument('--database', default='evolution_api_wea001_db')
    args = parser.parse_args()

    # ✅ Usando as classes importadas
    config = MigrationConfig(server=args.server)
    orchestrator = MigrationOrchestrator(config)

    # Continuar com lógica...
    print("✅ Script funcionando!")

if __name__ == '__main__':
    main()
```

---

## 🧪 Teste de Importação

Para verificar se todos os imports estão funcionando:

```bash
# Teste individual
python3 -c "from app.core.migration_orchestrator import MigrationOrchestrator; print('✅ OK')"

# Teste em batch
python3 << 'EOF'
from app.core.migration_orchestrator import MigrationOrchestrator
from app.cleanup.cleanup_database import CleanupDatabase
from app.validation.validate_grants_simple import GrantValidator
from app.orchestrators.orchestrator_pure_python import Orchestrator
print("✅ Todos os imports funcionam!")
EOF
```

---

## 🐛 Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'app'`

**Solução:** Certifique-se de que:
1. O arquivo `/app/__init__.py` existe
2. Você está no diretório raiz do projeto
3. Não está tentando fazer import antes de `sys.path.insert(0, str(Path(__file__).parent))`

```python
# Adicione no início do script se necessário:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### Erro: `ImportError: cannot import name 'ClasseX' from 'app.core.modulo'`

**Solução:**
1. Verifique se a classe existe no arquivo
2. Verifique se o `__init__.py` existe no diretório
3. Verifique a grafia correta da classe

---

## ✅ Checklist Final

- [ ] Todos os arquivos em `/app/` têm `__init__.py`
- [ ] Todos os imports usam prefixo `app.`
- [ ] Não há imports circulares
- [ ] Scripts em `/scripts/` funcionam com `python3 script_name.py --help`
- [ ] Testes rodam com `pytest test/`
- [ ] Documentação atualizada em `/reports/`

---

**Versão:** 1.0
**Data:** 2025-11-02
**Próxima Revisão:** 2025-12-02
