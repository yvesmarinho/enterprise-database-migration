# 🚀 PostgreSQL Migration System - VS Code Workspace

Este arquivo workspace configura o VS Code para desenvolvimento otimizado do sistema de migração PostgreSQL.

## 📋 Como Usar o Workspace

### 1. **Abrir o Workspace**
```bash
# Método 1: Via linha de comando
cd src/migration
code postgresql-migration-system.code-workspace

# Método 2: Via VS Code
# File > Open Workspace from File... > selecionar postgresql-migration-system.code-workspace
```

### 2. **Instalação de Extensões**
O workspace recomenda extensões essenciais. Quando abrir, o VS Code perguntará se deseja instalar:

**Extensões Python:**
- `ms-python.python` - Suporte Python
- `ms-python.black-formatter` - Formatação automática
- `ms-python.pylint` - Linting
- `ms-python.flake8` - Verificação de código

**Extensões de Configuração:**
- `redhat.vscode-yaml` - Suporte YAML
- `ms-vscode.makefile-tools` - Suporte Makefile
- `ms-azuretools.vscode-docker` - Suporte Docker

**Extensões GitHub:**
- `github.copilot` - GitHub Copilot
- `github.copilot-chat` - Copilot Chat

## 🎯 Funcionalidades Configuradas

### 📁 **Pastas Organizadas**
O workspace organiza o projeto em pastas lógicas:
- **PostgreSQL Migration System** - Pasta principal
- **Core Components** - Componentes centrais
- **Configuration** - Arquivos de configuração
- **Secrets** - Configurações sensíveis
- **Documentation** - Documentação
- **Scripts** - Scripts auxiliares
- **Tests** - Testes automatizados

### ⌨️ **Tarefas Pré-configuradas**
Pressione `Ctrl+Shift+P` e digite "Tasks" para acessar:

**Setup e Configuração:**
- `Migration: Setup Project` - Setup completo
- `Migration: Activate MCP` - Ativar contexto MCP

**Execução de Migração:**
- `Migration: Run Interactive` - Migração interativa
- `Migration: Run Auto` - Migração automática
- `Migration: Validate` - Validar dados

**Desenvolvimento:**
- `Migration: Test All` - Executar testes
- `Migration: Format Code` - Formatar código
- `Migration: Lint Code` - Verificar qualidade

**Monitoramento:**
- `Migration: Check Status` - Status da migração
- `Migration: Monitor` - Monitor tempo real
- `Migration: View Logs` - Ver logs

**Docker:**
- `Migration: Docker Up` - Iniciar ambiente
- `Migration: Docker Down` - Parar ambiente

### 🐛 **Debug Configurado**
Pressione `F5` ou vá em `Run and Debug`:

**Configurações Disponíveis:**
- `Migration: Debug Interactive` - Debug migração interativa
- `Migration: Debug Auto` - Debug migração automática
- `Migration: Debug Orchestrator` - Debug orquestrador
- `Migration: Debug Validator` - Debug validador
- `Migration: Debug Cleanup` - Debug limpeza
- `Migration: Test Current File` - Debug teste atual

### 🎨 **Tema Personalizado**
- **Barra de título**: Verde (tema migração PostgreSQL)
- **Barra de status**: Verde matching
- **Tema**: Dark+ otimizado

### 📂 **File Nesting**
Arquivos relacionados são agrupados automaticamente:
- `requirements.txt` agrupa `requirements*.txt`
- `docker-compose.yml` agrupa `Dockerfile*`
- `README.md` agrupa outros `*.md`
- `.env.example` agrupa `.env*`

## ⚙️ **Configurações Automáticas**

### 🐍 **Python**
- Formatação automática ao salvar
- Organização de imports automática
- Ambiente virtual detectado automaticamente
- Pytest configurado para testes

### 📝 **Editor**
- Rulers em 80 e 120 caracteres
- Remoção automática de espaços em branco
- Inserção automática de linha final
- Tab size otimizado por tipo de arquivo

### 🔍 **Busca e Exclusões**
- Pastas desnecessárias excluídas da busca
- Arquivos temporários ocultados
- Secrets protegidos da busca acidental

### 🌐 **Variáveis de Ambiente**
- `PYTHONPATH` configurado automaticamente
- `MIGRATION_LOG_LEVEL=DEBUG` para desenvolvimento
- Suporte multi-plataforma (Linux, macOS, Windows)

## 🚀 **Quick Start**

### 1. **Primeira Execução**
```bash
# Abrir workspace
code postgresql-migration-system.code-workspace

# Instalar extensões recomendadas (quando solicitado)
# Executar setup
Ctrl+Shift+P > Tasks: Run Task > Migration: Setup Project
```

### 2. **Desenvolvimento Diário**
```bash
# Ativar MCP
Ctrl+Shift+P > Tasks: Run Task > Migration: Activate MCP

# Executar testes
Ctrl+Shift+P > Tasks: Run Task > Migration: Test All

# Debug migração
F5 > Migration: Debug Interactive
```

### 3. **Execução de Migração**
```bash
# Modo interativo
Ctrl+Shift+P > Tasks: Run Task > Migration: Run Interactive

# Modo automático
Ctrl+Shift+P > Tasks: Run Task > Migration: Run Auto

# Validar resultados
Ctrl+Shift+P > Tasks: Run Task > Migration: Validate
```

## 🔧 **Comandos de Terminal Integrado**

O workspace configura o terminal com:
- `PYTHONPATH` automático
- `MIGRATION_LOG_LEVEL=DEBUG`
- Ativação automática do ambiente Python

### Comandos Essenciais:
```bash
# Via terminal integrado (Ctrl+`)
make help                    # Ver todos os comandos
make setup                   # Setup do projeto
make migrate-interactive     # Migração interativa
make validate               # Validar dados
make status                 # Status atual
```

## 📊 **Monitoramento Integrado**

### Logs em Tempo Real:
```bash
# Via task
Ctrl+Shift+P > Tasks: Run Task > Migration: View Logs

# Via terminal
make logs-follow
```

### Status Dashboard:
```bash
# Via task
Ctrl+Shift+P > Tasks: Run Task > Migration: Monitor

# Via terminal
make monitor
```

## 🐳 **Ambiente Docker**

### Iniciar Ambiente Completo:
```bash
# Via task
Ctrl+Shift+P > Tasks: Run Task > Migration: Docker Up

# Via terminal
docker-compose up -d
```

### Serviços Disponíveis:
- **PostgreSQL Source**: localhost:5433
- **PostgreSQL Destination**: localhost:5434
- **PostgreSQL Monitoring**: localhost:5435
- **Prometheus**: localhost:9091
- **Grafana**: localhost:3001
- **Redis**: localhost:6379

## 💡 **Dicas de Produtividade**

### Atalhos Essenciais:
- `Ctrl+Shift+P` - Command Palette
- `F5` - Iniciar Debug
- `Ctrl+`` - Terminal Integrado
- `Ctrl+Shift+E` - Explorer
- `Ctrl+Shift+G` - Source Control

### Snippets Customizados:
- Digite `migconfig` para template de configuração
- Digite `migtest` para template de teste
- Digite `migdebug` para código de debug

### IntelliSense Otimizado:
- Autocompletar para APIs PostgreSQL
- Sugestões de código específicas para migração
- Documentação inline dos métodos

## 🔒 **Segurança**

### Proteções Implementadas:
- Pasta `secrets/` excluída da busca
- Arquivos `.env` protegidos
- Logs sensíveis filtrados
- Configurações de debug seguras

## 📚 **Recursos Adicionais**

### Documentação Rápida:
- Hover sobre funções mostra documentação
- `Ctrl+Click` para ir à definição
- `F12` para ir à implementação
- `Shift+F12` para encontrar referências

### Code Actions:
- Organizar imports automaticamente
- Refactoring inteligente
- Correções automáticas de linting
- Formatação de código consistente

---

## 🎯 **Workspace Completo e Otimizado!**

Este workspace transforma o VS Code em um IDE especializado para desenvolvimento do sistema de migração PostgreSQL, com todas as ferramentas e configurações necessárias para máxima produtividade! 🚀
