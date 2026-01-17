# 📁 Estrutura do Projeto - Enterprise Database Migration v4.0.0

**Data de Atualização:** 2 de novembro de 2025
**Status:** ✅ Reorganização Completa

---

## 🏗️ Visão Geral da Arquitetura

```
enterprise-database-migration/
├── 📄 main.py                           # Ponto de entrada principal
├── 📄 README.md                         # Documentação principal
├── 📄 requirements.txt                  # Dependências Python
├── 📄 pyproject.toml                    # Configuração do projeto
├── 📄 Makefile                          # Automação de tarefas
├── 📄 docker-compose.yml                # Orquestração de containers
├── 📄 Dockerfile                        # Imagem Docker
├── 📄 config.ini                        # Configuração geral
│
├── 🗂️ app/                              # ⭐ CÓDIGO PRINCIPAL DA APLICAÇÃO
│   ├── __init__.py                      # Package marker
│   │
│   ├── 🗂️ core/                         # Lógica de migração
│   │   ├── __init__.py
│   │   ├── migration_orchestrator.py    # Orquestrador principal
│   │   ├── migration_structure.py       # Estruturas de dados
│   │   ├── complete_migration.py        # Migração completa
│   │   ├── phase1_extract_wf004.py      # Fase 1: Extração
│   │   ├── phase2_generate_scripts.py   # Fase 2: Geração de scripts
│   │   ├── phase3_controlled_executor.py # Fase 3: Execução
│   │   ├── migrate_users.py             # Migração de usuários
│   │   ├── fix_evolution_permissions.py # Correção de permissões
│   │   ├── validator.py                 # Validação de integridade
│   │   ├── sqlalchemy_migration.py      # Migração com SQLAlchemy
│   │   │
│   │   ├── 🗂️ modules/
│   │   │   ├── data_extractor.py        # Extração de dados
│   │   │   ├── migration_executor.py    # Executor de migração
│   │   │   └── __init__.py
│   │   │
│   │   └── 🗂️ reports/                  # Relatórios de migração
│   │       └── (arquivos de relatório gerados)
│   │
│   ├── 🗂️ cleanup/                      # Limpeza de banco de dados
│   │   ├── __init__.py
│   │   ├── cleanup_database.py          # Script principal
│   │   ├── test_*.py                    # Testes de proteção
│   │   └── README.md
│   │
│   ├── 🗂️ validation/                   # Validação de dados
│   │   ├── __init__.py
│   │   ├── validate_grants_*.py         # Validação de privilégios
│   │   ├── check_wfdb02_status.py       # Status do servidor
│   │   ├── check_scram_auth.py          # Verificação SCRAM
│   │   └── README.md
│   │
│   └── 🗂️ orchestrators/                # Orquestradores alternativos
│       ├── __init__.py
│       ├── orchestrator_pure_python.py  # Orquestrador em Python puro
│       ├── migration_orchestrator.py    # Com SQLAlchemy
│       └── README.md
│
├── 🗂️ scripts/                          # ⭐ SCRIPTS EXECUTÁVEIS
│   ├── run_fix_evolution_permissions.py # Corretor de permissões
│   ├── simulate_evolution_api.py        # Simulador da Evolution API
│   ├── test_evolution_api_permissions.py # Testes de permissões
│   ├── organize_*.py                    # Scripts auxiliares
│   └── README.md
│
├── 🗂️ reports/                          # ⭐ DOCUMENTAÇÃO E RELATÓRIOS
│   ├── ANALISE_*.md                     # Análises técnicas
│   ├── RESUMO_*.md                      # Sumários executivos
│   ├── RESULTADO_*.md                   # Resultados de execução
│   ├── COMO_USAR_*.md                   # Guias de uso
│   ├── *.json                           # Relatórios estruturados
│   ├── *.log                            # Logs de execução
│   └── README.md
│
├── 🗂️ test/                             # 🧪 TESTES
│   ├── test_*.py                        # Testes unitários
│   ├── debug_*.py                       # Scripts de debug
│   ├── conftest.py                      # Configuração pytest
│   └── README.md
│
├── 🗂️ config/                           # ⚙️ CONFIGURAÇÃO
│   ├── migration_config.json            # Config de migração
│   ├── migration_rules.json             # Regras de migração
│   └── templates/                       # Templates SQL
│
├── 🗂️ secrets/                          # 🔐 CREDENCIAIS (gitignore)
│   ├── postgresql_source_config.json    # Config WF004
│   ├── postgresql_destination_config.json # Config WFDB02
│   └── README.md
│
├── 🗂️ examples/                         # 📚 EXEMPLOS
│   ├── example_*.py                     # Exemplos de uso
│   └── README.md
│
├── 🗂️ docs/                             # 📖 DOCUMENTAÇÃO TÉCNICA
│   ├── *.sql                            # Schemas e queries
│   ├── ANÁLISE_*.md                     # Análises técnicas
│   ├── optimization_*.md                # Guias de otimização
│   └── README.md
│
├── 🗂️ utils/                            # 🔧 UTILITÁRIOS
│   ├── discover_users.py                # Descobrir usuários
│   ├── database_helpers.py              # Helpers de banco
│   └── README.md
│
├── 🗂️ backup/                           # 💾 BACKUPS
│   └── (backups automáticos)
│
├── 🗂️ extracted_data/                   # 📊 DADOS EXTRAÍDOS
│   └── (dados intermediários)
│
├── 🗂️ generated_scripts/                # 📝 SCRIPTS GERADOS
│   └── (scripts SQL autogenerados)
│
├── 🗂️ logs/                             # 📋 LOGS
│   └── (logs de execução)
│
├── 🗂️ legacy/                           # 🏚️ CÓDIGO LEGADO
│   └── (código antigo/backup)
│
└── 🗂️ __pycache__/                      # (cache Python, ignorar)
```

---

## 📦 Estrutura de Módulos

### **Camada de Aplicação (`/app/`)**

```python
# Imports corretos para novos arquivos:

# Do core
from app.core.migration_orchestrator import MigrationOrchestrator
from app.core.migration_structure import MigrationConfig
from app.core.validator import Validator

# Do cleanup
from app.cleanup.cleanup_database import CleanupDatabase

# Da validation
from app.validation.validate_grants_simple import GrantValidator

# Dos orchestrators
from app.orchestrators.orchestrator_pure_python import Orchestrator
```

### **Camada de Scripts (`/scripts/`)**

```bash
# Execução de scripts:
python3 scripts/run_fix_evolution_permissions.py --help
python3 scripts/simulate_evolution_api.py --server wfdb02
python3 scripts/test_evolution_api_permissions.py --url http://localhost:8080
```

### **Camada de Testes (`/test/`)**

```python
# Imports corretos em testes:
from app.core.migration_orchestrator import MigrationOrchestrator
from app.cleanup.cleanup_database import CleanupDatabase

# Execução:
pytest test/
pytest test/test_cleanup_config.py -v
```

---

## 🔄 Padrão de Importação

### ❌ ANTES (Antigo - NÃO USAR)
```python
from core.migration_orchestrator import MigrationOrchestrator
from cleanup.cleanup_database import CleanupDatabase
from validation.validate_grants import GrantValidator
```

### ✅ DEPOIS (Novo - USAR AGORA)
```python
from app.core.migration_orchestrator import MigrationOrchestrator
from app.cleanup.cleanup_database import CleanupDatabase
from app.validation.validate_grants import GrantValidator
```

---

## 📍 Onde Criar Novos Arquivos?

| Tipo de Arquivo | Local | Exemplo |
|---|---|---|
| **Lógica de migração** | `/app/core/` | `app/core/novo_modulo.py` |
| **Limpeza de dados** | `/app/cleanup/` | `app/cleanup/novo_cleanup.py` |
| **Validação de dados** | `/app/validation/` | `app/validation/novo_validador.py` |
| **Orquestração** | `/app/orchestrators/` | `app/orchestrators/novo_orquestrador.py` |
| **Script executável** | `/scripts/` | `scripts/novo_script.py` |
| **Teste unitário** | `/test/` | `test/test_novo_modulo.py` |
| **Documentação técnica** | `/docs/` | `docs/ANALISE_novo_feature.md` |
| **Relatório/análise** | `/reports/` | `reports/RESULTADO_execucao.md` |
| **Exemplo de uso** | `/examples/` | `examples/exemplo_novo_uso.py` |
| **Configuração** | `/config/` | `config/nova_config.json` |
| **Credenciais** | `/secrets/` | `secrets/novo_config.json` |

---

## 🚀 Scripts Principais

### 1. **Correção de Permissões Evolution**
```bash
python3 scripts/run_fix_evolution_permissions.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --dry-run \
  --verbose
```

### 2. **Simulador Evolution API**
```bash
python3 scripts/simulate_evolution_api.py \
  --server wfdb02 \
  --database evolution_api_wea001_db \
  --validate-all \
  --report report.json
```

### 3. **Testes de Permissões**
```bash
python3 scripts/test_evolution_api_permissions.py \
  --url http://localhost:8080 \
  --apikey sua-chave-api \
  --simulate-all
```

---

## 🔐 Segurança e .gitignore

### Não fazer commit:
```
secrets/              # Credenciais
backup/              # Backups sensíveis
extracted_data/      # Dados intermediários
logs/                # Logs com dados sensíveis
.env                 # Variáveis de ambiente
```

### Fazer commit:
```
app/                 # Código principal
scripts/             # Scripts
config/              # Configuração genérica
docs/                # Documentação
test/                # Testes
reports/             # Relatórios públicos
requirements.txt     # Dependências
```

---

## 📊 Hierarquia de Dependências

```
main.py (Raiz)
  ↓
/scripts/ (Executáveis)
  ↓
/app/ (Lógica Principal)
  ├── /app/core/ (Núcleo)
  ├── /app/cleanup/ (Limpeza)
  ├── /app/validation/ (Validação)
  └── /app/orchestrators/ (Orquestração)
  ↓
/config/ (Configuração)
/secrets/ (Credenciais)
/test/ (Testes)
/examples/ (Exemplos)
/docs/ (Documentação)
```

---

## ✅ Checklist para Novos Arquivos

- [ ] Arquivo criado no diretório correto
- [ ] Imports atualizados com prefixo `app.`
- [ ] `__init__.py` existe no diretório
- [ ] Funciona: `python3 scripts/seu_script.py --help`
- [ ] Testes adicionados em `/test/`
- [ ] Documentação em `/reports/` ou `/docs/`
- [ ] Não contém credenciais ou dados sensíveis

---

## 🔧 Manutenção

### Adicionar novo módulo em `/app/core/`:
```bash
# 1. Criar arquivo
touch app/core/novo_modulo.py

# 2. Implementar classe/funções
# from app.core.outro_modulo import OutroModulo

# 3. Testar import
python3 -c "from app.core.novo_modulo import NovaClasse; print('✅')"

# 4. Criar teste
touch test/test_novo_modulo.py

# 5. Documentar
touch reports/RESULTADO_novo_modulo.md
```

### Adicionar novo script em `/scripts/`:
```bash
# 1. Criar arquivo
touch scripts/novo_script.py

# 2. Adicionar imports corretos
# from app.core.modulo import Classe

# 3. Testar help
python3 scripts/novo_script.py --help

# 4. Criar README
echo "# Novo Script\n\n..." >> scripts/README.md
```

---

## 📚 Referências Rápidas

- **Ponto de Entrada:** `main.py`
- **Código Principal:** `/app/`
- **Scripts CLI:** `/scripts/`
- **Testes:** `/test/` (execute com `pytest`)
- **Documentação:** `/docs/` e `/reports/`
- **Configuração:** `/config/` (genérica) e `/secrets/` (sensível)
- **Exemplos:** `/examples/`

---

**Versão:** 4.0.0
**Última Atualização:** 2025-11-02
**Responsável:** Yves Marinho
