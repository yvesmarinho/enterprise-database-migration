# PostgreSQL Enterprise Migration System v4.0.0

Sistema completo e robusto de migração PostgreSQL desenvolvido e validado durante a migração WF004→WFDB02.

## 🌟 Características Principais

- **✅ Sistema 3-Fases**: Extração → Geração → Execução
- **✅ Validado em Produção**: Migrou com sucesso 39 usuários, 29 bases, 105 grants
- **✅ Controle Total**: Dry run, modo interativo, logs detalhados
- **✅ Arquitetura Modular**: Componentes independentes e reutilizáveis
- **✅ Sistema Robusto**: Tratamento de erros, validações, relatórios

## 🏗️ Arquitetura do Sistema

```
main.py                               # 🎛️ Controlador principal (CLI)
├── migration_orchestrator.py         # 🚀 Orquestrador do sistema v4.0.0
├── core/modules/
│   ├── data_extractor.py             # 📤 Fase 1: Extração de dados
│   ├── script_generator.py           # ⚙️ Fase 2: Geração de scripts
│   └── migration_executor.py         # 🎯 Fase 3: Execução controlada
├── config/
│   └── migration_config.json         # ⚙️ Configuração unificada
├── docs/
│   ├── PROGRESS_DOCUMENTATION.md     # 📈 Técnicas desenvolvidas
│   └── CLEANUP_GUIDE.md             # 🧹 Guia de organização
└── secrets/                          # 🔐 Credenciais de conexão
├── secrets/                          # Configurações de conexão
├── logs/                            # Logs de execução
├── reports/                         # Relatórios do desenvolvimento
├── extracted_data/                  # Dados extraídos (JSON)
└── generated_scripts/               # Scripts SQL gerados
```

## 🚀 Instalação e Configuração

### 1. Dependências

```bash
pip install psycopg2-binary
```

### 2. Configuração dos Servidores

Configure os arquivos de conexão:

**`secrets/postgresql_source_config.json`** (Servidor origem):
```json
{
  "server": {
    "host": "wf004.vya.digital",
    "port": 5432
  },
  "authentication": {
    "user": "migration_user",
    "password": "sua_senha_aqui"
  }
}
```

**`secrets/postgresql_destination_config.json`** (Servidor destino):
```json
{
  "server": {
    "host": "wfdb02.vya.digital",
    "port": 5432
  },
  "authentication": {
    "user": "migration_user",
    "password": "sua_senha_aqui"
  }
}
```

### 3. Configuração Principal

O arquivo `config/migration_config.json` contém todas as configurações do sistema. É criado automaticamente com valores padrão na primeira execução.

## 📋 Guia de Uso

### Migração Completa (Recomendado)

```bash
```bash
# Menu interativo completo
python main.py

# Migração completa automatizada
python main.py --complete

# Migração completa com confirmação em cada etapa
python main.py --complete --interactive

# Simulação completa (não faz alterações)
python main.py --complete --dry-run
```

### Execução por Fases

#### Fase 1: Extração de Dados
```bash
# Extrair dados do servidor origem
python main.py --extract --output data_backup.json
```

#### Fase 2: Geração de Scripts
```bash
# Gerar scripts SQL a partir dos dados extraídos
python main.py --generate --input data_backup.json
```

#### Fase 3: Execução
```bash
# Dry run (simular sem alterar)
python main.py --execute --dry-run

# Execução real
python main.py --execute

# Execução interativa
python main.py --execute --interactive
```

## 🔧 Funcionalidades Avançadas

### Sistema de Logs
- Logs automáticos em `logs/migration_YYYYMMDD_HHMMSS.log`
- Saída simultânea no console e arquivo
- Rotação automática de logs
- Níveis configuráveis (DEBUG, INFO, WARNING, ERROR)

### Relatórios Detalhados
```bash
# Gerar relatório completo
python main.py --complete --report
```

### Configurações Customizadas
```bash
# Usar configuração personalizada
python main.py --complete --config minha_config.json
```

### Modo Verbose
```bash
# Saída detalhada para debug
python main.py --complete --verbose
```

## 📊 Componentes do Sistema

### 1. Data Extractor (WF004DataExtractor)
- Conecta ao servidor PostgreSQL origem
- Extrai usuários, bases de dados e grants
- Gera arquivo JSON estruturado
- Validações de integridade

### 2. Script Generator (SQLScriptGenerator)
- Processa dados do JSON
- Gera scripts SQL otimizados
- Remove transações problemáticas
- Corrige encoding e locales
- Filtra usuários do sistema

### 3. Migration Executor (ControlledMigrationExecutor)
- Executa scripts statement por statement
- Suporte a dry run e modo interativo
- Tratamento inteligente de erros
- Validações pós-execução
- Relatórios detalhados

### 4. Migration Orchestrator
- Interface unificada CLI
- Gerenciamento de configurações
- Sistema de logging integrado
- Controle de fluxo completo
- Geração de relatórios

## ⚡ Exemplos Práticos

### Cenário 1: Primeira Migração
```bash
# 1. Fazer backup dos dados
python main.py --extract --output backup_$(date +%Y%m%d).json

# 2. Testar geração de scripts
python main.py --generate --input backup_20251006.json

# 3. Dry run completo
python main.py --execute --dry-run

# 4. Execução real
python main.py --execute
```

### Cenário 2: Re-execução Segura
```bash
# Usar dados já extraídos
python main.py --complete --input backup_existente.json --interactive
```

### Cenário 3: Apenas Validação
```bash
# Apenas validar ambiente de destino
python main.py --execute --dry-run --verbose
```

## 🛠️ Solução de Problemas

### Erros Comuns

#### 1. "role already exists"
- **Solução**: Normal, usuários já existem. O sistema ignora automaticamente.

#### 2. "collation incompatible"
- **Solução**: Sistema usa `pt_BR.UTF-8` e `template0` automaticamente.

#### 3. "zero-length delimited identifier"
- **Solução**: Sistema remove aspas duplas automático nos grants.

#### 4. "connection timeout"
- **Solução**: Verificar conectividade e credenciais nos arquivos `secrets/`.

### Debug Avançado

```bash
# Logs detalhados
python main.py --complete --verbose --report

# Verificar configuração
cat config/migration_config.json

# Verificar logs
tail -f logs/migration_*.log
```

### Validação Manual

```sql
-- Verificar usuários criados
SELECT count(*) FROM pg_roles WHERE rolname NOT LIKE 'pg_%';

-- Verificar bases criadas
SELECT count(*) FROM pg_database WHERE datname NOT IN ('postgres', 'template0', 'template1');

-- Verificar grants aplicados
SELECT d.datname, grantee::regrole::text, privilege_type
FROM pg_database d, aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba)))
WHERE d.datname NOT IN ('postgres', 'template0', 'template1')
ORDER BY d.datname, grantee;
```

## �️ Utilitários Operacionais (`tools/`) — Adicionado 2026-02-19

Ferramentas reutilizáveis para manutenção contínua dos servidores PostgreSQL.

```
tools/
├── README.md              ← documentação completa
├── Makefile               ← atalhos de uso rápido
├── migrate_users/
│   └── migrate_targeted_users_and_db.py   ✅ testado em produção
└── fix_permissions/
    ├── fix_permissions.py          ← corrige ownership/grants declarativamente
    ├── fix_permissions.json        ← config: metabase_db, n8n_db, evolution_api
    └── fix_permissions_wf008.json  ← config: app_workforce (wf008)
```

### migrate_users — Migração de usuários selecionados

```bash
# Listar configs disponíveis
python3 tools/migrate_users/migrate_targeted_users_and_db.py --list-configs

# Executar
python3 tools/migrate_users/migrate_targeted_users_and_db.py \
    --source  wfdb02_source_config.json \
    --destiny home016_destiny_config.json

# Via Makefile (a partir de tools/)
make migrate SOURCE=wfdb02_source_config.json DESTINY=home016_destiny_config.json
make migrate-dry SOURCE=wfdb02_source_config.json DESTINY=home016_destiny_config.json
```

### fix_permissions — Correção declarativa de permissões

```bash
# Dry-run (padrão seguro)
python3 tools/fix_permissions/fix_permissions.py \
    --server postgresql_destination_config.json \
    --database metabase_db

# Executar
python3 tools/fix_permissions/fix_permissions.py \
    --server postgresql_destination_config.json \
    --database metabase_db --execute

# Via Makefile
make -f tools/Makefile fix-dry SERVER=postgresql_destination_config.json DB=metabase_db
make -f tools/Makefile fix     SERVER=postgresql_destination_config.json DB=metabase_db
```

**Migração executada em produção (2026-02-19)**: 8 usuários + banco `app_workforce` migrados de wfdb02→home016 com sucesso.

---

## �📈 Métricas de Sucesso WF004→WFDB02

✅ **39 usuários** migrados com sucesso
✅ **29 bases de dados** criadas (435MB+ de dados)
✅ **105 grants** aplicados corretamente
✅ **0 erros críticos** durante a execução
✅ **100% compatibilidade** PostgreSQL 14→16

## 🔄 Histórico de Versões

### v4.0.0 (Atual)
- Sistema modular completo
- Interface CLI unificada
- Logs e relatórios avançados
- Configuração robusta
- Validado em produção

### v3.0.0 (Desenvolvimento)
- Sistema 3-fases separado
- Correções de encoding/locale
- Tratamento de aspas nos grants

### v2.0.0 (Protótipo)
- SQLAlchemy com controle de fases
- Primeira versão funcional

### v1.0.0 (Inicial)
- Scripts independentes
- Validação de conceito

## � Documentação Adicional

### **📈 Documentação de Progresso**
- [`docs/PROGRESS_DOCUMENTATION.md`](docs/PROGRESS_DOCUMENTATION.md) - Técnicas desenvolvidas, problemas resolvidos e inovações implementadas

### **🔧 Documentação Técnica**
- Análise detalhada dos padrões de design aplicados
- Métricas de performance e robustez obtidas
- Lições aprendidas durante o desenvolvimento
- Roadmap de futuras melhorias

## �📞 Suporte

Para questões específicas do sistema ou implementação em outros ambientes, consulte:

1. **Logs**: Sempre em `core/reports/migration_*.log`
2. **Relatórios**: Gerados em `core/reports/migration_report_*.json`
3. **Configuração**: Documentada em `config/migration_config.json`
4. **Validação**: Scripts de verificação incluídos
5. **Progresso**: Técnicas detalhadas em `docs/PROGRESS_DOCUMENTATION.md`

---

**Desenvolvido e testado com sucesso na migração WF004→WFDB02 (Out/2025)**
**Sistema validado em produção - 100% de sucesso na migração** ✅
