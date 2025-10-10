# Otimização de Dependências

## ✅ O que foi feito

Análise completa dos códigos Python do projeto identificou que **muitas bibliotecas** estavam listadas no `requirements.txt` mas **não eram utilizadas** no código.

## 📊 Resultado da análise

### Bibliotecas REALMENTE utilizadas:
- `psycopg2-binary` - Conector PostgreSQL (usado extensivamente)
- `SQLAlchemy` - ORM para operações de banco (usado em cleanup e migrations)
- `colorama` - Cores no terminal (usado no orchestrator_pure_python)
- `mysql-connector-python` - Conector MySQL (usado em testes de validação)
- `jsonschema` - Validação de JSON (usado indiretamente)

### Bibliotecas REMOVIDAS (não utilizadas):
- `asyncpg` - Não há código assíncrono
- `click`, `rich`, `typer` - Não há CLI avançada implementada
- `pandas`, `numpy` - Não há processamento de dados científicos
- `pytest*` - Frameworks de teste (movidos para requirements-dev.txt)
- `black`, `isort`, `flake8`, `pylint`, `mypy` - Ferramentas de qualidade (movidos para dev)
- `httpx`, `aiohttp` - Clientes HTTP não utilizados
- `fastapi`, `uvicorn`, `jinja2` - Web framework não implementado
- `redis`, `aioredis` - Cache não implementado
- `bcrypt`, `cryptography` - Criptografia não utilizada
- `prometheus-client` - Métricas não implementadas
- E muitas outras...

## 📁 Estrutura resultante

```
requirements.txt                 # Dependências essenciais (5 bibliotecas)
requirements-dev.txt            # Dependências de desenvolvimento (opcional)
pyproject.toml                  # Configuração moderna com dependências organizadas
PYPROJECT_OPTIMIZATION.md      # Documentação da otimização do pyproject.toml
core/requirements.migration.txt # Mantido para referência
```

## 🚀 Benefícios

1. **Instalação mais rápida** - Apenas 6 bibliotecas vs ~30+ anteriores
2. **Menor tamanho** - Redução significativa do tamanho da instalação
3. **Menos conflitos** - Menor chance de conflitos de dependências
4. **Manutenção mais fácil** - Menos dependências para gerenciar
5. **Deploy mais eficiente** - Especialmente importante em containers

## 📝 Como usar

### Instalação básica (recomendada)
```bash
pip install -r requirements.txt
```

### Instalação com ferramentas de desenvolvimento
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Instalação com uv (mais rápida)
```bash
uv pip install -r requirements.txt
```

## 🆕 Opção Moderna: pyproject.toml

Agora o projeto também possui um `pyproject.toml` otimizado que oferece:

### Instalação moderna (recomendada)
```bash
pip install -e .                    # Dependências básicas
pip install -e ".[dev]"             # Com ferramentas de desenvolvimento
pip install -e ".[dev,advanced]"    # Com funcionalidades futuras
```

### Scripts CLI integrados
```bash
migrate-db          # Script principal de migração
db-orchestrator     # Orquestrador direto
```

Ver `PYPROJECT_OPTIMIZATION.md` para detalhes completos.
