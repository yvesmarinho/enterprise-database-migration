# Otimização do pyproject.toml

## ✅ Modernização Completa

Transformei o `pyproject.toml` básico em uma configuração moderna e profissional seguindo as melhores práticas do Python packaging.

## 🔄 O que mudou

### **ANTES:**
```toml
[project]
name = "enterprise-database-migration"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = []
```

### **DEPOIS:** Configuração completa e otimizada

## 🚀 Principais melhorias

### 1. **Metadados Completos**
- Descrição detalhada do projeto
- Informações do autor
- Keywords para descoberta
- Classificadores PyPI adequados
- URLs do projeto (GitHub, Issues, Docs)

### 2. **Dependências Organizadas**
```toml
# Dependências essenciais (apenas as realmente usadas)
dependencies = [
    "psycopg2-binary>=2.9.7",
    "SQLAlchemy>=2.0.23",
    "colorama>=0.4.6",
    "mysql-connector-python>=8.1.0",
    "jsonschema>=4.20.0",
]

# Dependências opcionais organizadas por categoria
[project.optional-dependencies]
dev = [...]        # Ferramentas de desenvolvimento
advanced = [...]   # Funcionalidades futuras
monitoring = [...] # Métricas e profiling
```

### 3. **Scripts CLI Definidos**
```toml
[project.scripts]
migrate-db = "run_migration:main"
db-orchestrator = "orchestrator_pure_python:main"
```

### 4. **Configuração de Ferramentas**
- **Black** - Formatação de código
- **isort** - Organização de imports
- **pytest** - Configuração de testes
- **mypy** - Type checking
- **coverage** - Cobertura de testes

### 5. **Compatibilidade Python**
- Mudou de `>=3.13` para `>=3.9` (compatível com dependências modernas)
- Suporte explícito para Python 3.9-3.13
- Resolve conflitos com `pre-commit` que requer Python>=3.9

## 📦 Como usar

### Instalação básica
```bash
pip install -e .
```

### Com dependências de desenvolvimento
```bash
pip install -e ".[dev]"
```

### Com todas as funcionalidades
```bash
pip install -e ".[dev,advanced,monitoring]"
```

### Usando uv (mais rápido)
```bash
uv pip install -e ".[dev]"
```

## 🛠️ Comandos disponíveis

Após instalação, você pode usar:
```bash
migrate-db          # Script principal de migração
db-orchestrator     # Orquestrador direto
```

## 📊 Benefícios

1. **Padrão moderno** - Segue PEP 621 e melhores práticas
2. **Instalação flexível** - Dependências opcionais organizadas
3. **Configuração centralizada** - Todas as ferramentas em um lugar
4. **Publicação PyPI ready** - Pronto para ser publicado
5. **Desenvolvimento mais fácil** - Scripts e configurações integradas
