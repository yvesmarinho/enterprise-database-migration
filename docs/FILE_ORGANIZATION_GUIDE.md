# 📁 Guia de Organização de Arquivos - Enterprise Database Migration

Este documento explica como criar arquivos nas pastas corretas automaticamente usando as configurações do workspace.

## 🎯 Estrutura de Pastas e Tipos de Arquivo

### 📂 **core/**
- **Arquivos:** `*migration*.py`, `*.sql`, componentes principais
- **Snippet:** Digite `new-migration` para criar um componente de migração
- **Exemplo:** `user_migration.py`, `table_migration.sql`

### 📂 **orchestrators/**
- **Arquivos:** `*orchestrator*.py`, orquestradores de processo
- **Snippet:** Digite `new-orchestrator` para criar um orquestrador
- **Exemplo:** `database_orchestrator.py`, `migration_orchestrator.py`

### 📂 **validation/**
- **Arquivos:** `*validator*.py`, `*validation*.py`
- **Snippet:** Digite `new-validator` para criar um validador
- **Exemplo:** `data_validator.py`, `schema_validation.py`

### 📂 **utils/**
- **Arquivos:** `*util*.py`, `*helper*.py`, utilitários gerais
- **Snippet:** Digite `new-util` para criar um utilitário
- **Exemplo:** `database_util.py`, `file_helper.py`

### 📂 **components/**
- **Arquivos:** `*component*.py`, componentes modulares
- **Snippet:** Digite `new-migration` (adaptável)
- **Exemplo:** `auth_component.py`, `logging_component.py`

### 📂 **cli/**
- **Arquivos:** `*cli*.py`, `*command*.py`, interfaces CLI
- **Snippet:** Use templates Python básicos
- **Exemplo:** `migration_cli.py`, `status_command.py`

### 📂 **cleanup/**
- **Arquivos:** `*cleanup*.py`, scripts de limpeza
- **Snippet:** Use templates Python básicos
- **Exemplo:** `database_cleanup.py`, `temp_cleanup.py`

### 📂 **src/**
- **Arquivos:** Código Python geral (padrão)
- **Uso:** Arquivos Python que não se encaixam em outras categorias

### 📂 **config/**
- **Arquivos:** `*.json`, `*.yaml`, `*.yml`, `*config*.*`
- **Snippet:** Digite `new-config` para criar configuração
- **Exemplo:** `database_config.json`, `migration_rules.yaml`

### 📂 **secrets/**
- **Arquivos:** `*secret*.json`, `*credentials*.*`, `*auth*.*`
- **Uso:** Arquivos sensíveis (configurações de conexão, chaves)
- **Exemplo:** `db_credentials.json`, `api_secrets.json`

### 📂 **docs/**
- **Arquivos:** `*.md`, `*.txt` (exceto requirements), documentação
- **Snippet:** Digite `new-doc` para criar documentação
- **Exemplo:** `installation.md`, `api_guide.md`

### 📂 **scripts/**
- **Arquivos:** `*.sh`, `*.bash`, scripts shell
- **Uso:** Scripts de automação e deployment
- **Exemplo:** `deploy.sh`, `backup.sh`

### 📂 **legacy/**
- **Arquivos:** Código antigo sendo migrado
- **Uso:** Arquivos em processo de refatoração

## 🚀 Como Usar os Snippets

### 1. **Criar Componente de Migração**
```
1. Abra a pasta core/
2. Crie novo arquivo: Ctrl+N
3. Digite: new-migration
4. Pressione Tab
5. Preencha os campos solicitados
```

### 2. **Criar Orquestrador**
```
1. Abra a pasta orchestrators/
2. Crie novo arquivo: Ctrl+N
3. Digite: new-orchestrator
4. Pressione Tab
5. Defina nome e funcionalidade
```

### 3. **Criar Validador**
```
1. Abra a pasta validation/
2. Crie novo arquivo: Ctrl+N
3. Digite: new-validator
4. Pressione Tab
5. Configure validação
```

### 4. **Criar Documentação**
```
1. Abra a pasta docs/
2. Crie novo arquivo: Ctrl+N
3. Digite: new-doc
4. Pressione Tab
5. Preencha template de documentação
```

### 5. **Criar Configuração**
```
1. Abra a pasta config/
2. Crie novo arquivo: Ctrl+N
3. Digite: new-config
4. Pressione Tab
5. Configure JSON estruturado
```

## 📋 Convenções de Nomenclatura

### **Arquivos Python:**
- `*_migration.py` → core/
- `*_orchestrator.py` → orchestrators/
- `*_validator.py` → validation/
- `*_util.py` → utils/
- `*_component.py` → components/
- `*_cli.py` → cli/
- `*_cleanup.py` → cleanup/

### **Arquivos de Configuração:**
- `*_config.json` → config/
- `*_secrets.json` → secrets/
- `*_template.json` → config/
- `*.yaml` → config/

### **Documentação:**
- `*.md` → docs/
- `README*.txt` → docs/
- Outros `*.txt` → docs/

### **Scripts:**
- `*.sh` → scripts/
- `*.bash` → scripts/

## 🔧 Associações de Arquivo Configuradas

O workspace está configurado com as seguintes associações automáticas:

- **Python:** Sintaxe e linting otimizados
- **JSON/JSONC:** Configurações com schema validation
- **YAML:** Configurações estruturadas
- **Dockerfile:** Containers e deployment
- **Shell Scripts:** Automação
- **Markdown:** Documentação rica

## 💡 Dicas Práticas

1. **Use Ctrl+Shift+P** → "File: New File" para criar arquivos
2. **Snippets aparecem automaticamente** quando você digita os prefixos
3. **Nomes de arquivo influenciam** onde o VS Code sugere salvá-los
4. **Use Tab** para navegar entre campos dos snippets
5. **Escape** cancela o snippet ativo

## 🎨 Personalização

Para adicionar novos snippets:
1. Edite `.vscode/snippets.code-snippets`
2. Siga o padrão existente
3. Recarregue o workspace

---

*Este guia é parte do sistema de organização automática do projeto Enterprise Database Migration.*
