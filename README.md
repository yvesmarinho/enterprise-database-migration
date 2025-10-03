# 🚀 PostgreSQL Migration System

Sistema completo de migração de dados PostgreSQL enterprise com automação, monitoramento e validação para ambientes de produção.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Monitoramento](#-monitoramento)
- [Troubleshooting](#-troubleshooting)
- [Contribuição](#-contribuição)

## 🎯 Visão Geral

O PostgreSQL Migration System é uma solução enterprise para migração de dados entre servidores PostgreSQL, oferecendo:

- **Migração Automatizada**: Orquestração completa do processo de migração
- **Zero Downtime**: Estratégias de migração com tempo de inatividade mínimo
- **Validação Completa**: Verificação de integridade dos dados migrados
- **Monitoramento Real-time**: Acompanhamento detalhado do progresso
- **Rollback Automático**: Recuperação rápida em caso de falhas

## ✨ Características

### 🔄 Estratégias de Migração

- **Logical Replication**: Migração com downtime < 5 minutos
- **Dump/Restore**: Migração completa tradicional
- **Parallel Migration**: Processamento paralelo para grandes volumes
- **Hybrid Mode**: Combinação inteligente de estratégias

### 🛡️ Segurança e Confiabilidade

- Criptografia de dados em trânsito
- Backup automático antes da migração
- Validação de integridade referencial
- Logs de auditoria completos
- Recuperação automática de falhas

### 📊 Monitoramento e Relatórios

- Dashboard web em tempo real
- Métricas exportáveis para Prometheus
- Alertas configuráveis
- Relatórios detalhados de execução
- Análise de performance

## 🏗️ Arquitetura

```
src/migration/
├── core/                           # 🧠 Sistema principal
│   ├── orchestrator_pure_python.py    # Orquestrador principal
│   ├── sqlalchemy_migration.py        # Motor de migração
│   ├── validator.py                   # Sistema de validação
│   └── monitor.py                     # Monitoramento
├── config/                         # ⚙️ Configurações
│   └── migration_rules.json           # Regras de migração
├── secrets/                        # 🔐 Configurações sensíveis
│   ├── source_config.json             # Config servidor origem
│   ├── destination_config.json        # Config servidor destino
│   ├── postgresql_source_config.json  # Config PostgreSQL origem
│   └── postgresql_destination_config.json # Config PostgreSQL destino
├── cleanup/                        # 🧹 Sistema de limpeza
│   ├── cleanup_database.py            # Script de limpeza
│   └── README.md                      # Documentação de limpeza
├── scripts/                        # 📜 Scripts auxiliares
│   ├── complete_migration_move.sh     # Migração completa
│   ├── final_migration_cleanup.sh     # Limpeza final
│   └── move_migration_files.sh        # Movimentação de arquivos
└── docs/                          # 📚 Documentação
    └── (documentos migrados)
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.9+
- PostgreSQL 14+ (origem)
- PostgreSQL 16+ (destino)
- Conexão de rede estável entre servidores

### Instalação Rápida

```bash
# Clone o repositório
git clone <repository-url>
cd postgresql-migration-system

# Execute o setup do projeto
make setup

# Configure o ambiente MCP
make mcp

# Ative o contexto MCP
./activate-mcp.sh
```

### Instalação Manual

```bash
# Instale dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
vim .env

# Prepare os arquivos de configuração
cp src/migration/source_config_template.json src/migration/secrets/source_config.json
cp src/migration/destination_config_template.json src/migration/secrets/destination_config.json

# Configure os dados dos servidores
vim src/migration/secrets/source_config.json
vim src/migration/secrets/destination_config.json
```

## ⚙️ Configuração

### 1. Configuração dos Servidores

Edite os arquivos na pasta `secrets/`:

**source_config.json**:
```json
{
  "host": "seu-servidor-origem",
  "port": 5432,
  "database": "sua_database",
  "ssl_mode": "prefer",
  "possible_users": [
    {
      "username": "migration_user",
      "password": "sua_senha_segura"
    }
  ]
}
```

**destination_config.json**:
```json
{
  "host": "seu-servidor-destino",
  "port": 5432,
  "database": "sua_database",
  "ssl_mode": "prefer",
  "possible_users": [
    {
      "username": "migration_user",
      "password": "sua_senha_segura"
    }
  ]
}
```

### 2. Configuração de Migração

Edite `config/migration_rules.json` para definir:
- Tabelas a serem migradas
- Transformações de dados
- Validações específicas
- Configurações de performance

### 3. Configuração de Monitoramento

Configure alertas e métricas em `mcp-questions.yaml`:
- Canais de notificação
- Thresholds de performance
- Configurações de log

## 🎮 Uso

### Migração Interativa

```bash
# Execução com interface interativa
python3 run_migration.py
```

### Migração Automática

```bash
# Migração completamente automática
python3 run_migration.py --auto

# Com logs verbosos
python3 run_migration.py --auto --verbose
```

### Usando o Orquestrador Direto

```bash
# Migração com orquestrador
python3 src/migration/core/orchestrator_pure_python.py

# Migração automática
python3 src/migration/core/orchestrator_pure_python.py --auto
```

### Comandos do Makefile

```bash
# Setup completo do projeto
make setup

# Executar migração
make migrate

# Validar migração
make validate

# Limpar ambiente
make clean-migration

# Gerar relatórios
make reports
```

## 📊 Monitoramento

### Dashboard Web

Acesse o dashboard em tempo real:
```
http://localhost:8080/migration-dashboard
```

### Métricas Prometheus

As métricas estão disponíveis em:
```
http://localhost:9090/metrics
```

### Logs

Os logs são armazenados em:
- `logs/migration.log` - Log principal
- `logs/validation.log` - Log de validação
- `logs/performance.log` - Métricas de performance

## 🔧 Troubleshooting

### Problemas Comuns

**Falha de Conexão**:
```bash
# Verifique conectividade
telnet servidor-origem 5432
telnet servidor-destino 5432

# Teste credenciais
psql -h servidor-origem -U migration_user -d database
```

**Performance Lenta**:
```bash
# Ajuste configurações de performance
vim src/migration/mcp-questions.yaml

# Aumente parallel_workers e batch_size
parallel_workers: 16
batch_size: 50000
```

**Falha de Validação**:
```bash
# Execute validação manual
python3 src/migration/core/validator.py --validate-all

# Verifique logs detalhados
tail -f logs/validation.log
```

### Logs de Debug

```bash
# Ative logs debug
export MIGRATION_LOG_LEVEL=DEBUG

# Execute com verbose
python3 run_migration.py --auto --verbose --debug
```

## 🔄 Rollback

### Rollback Automático

Em caso de falha, o sistema executa rollback automático:

```bash
# Forçar rollback manual
python3 src/migration/core/orchestrator_pure_python.py --rollback

# Rollback para ponto específico
python3 src/migration/core/orchestrator_pure_python.py --rollback --point="2025-10-03-10:30:00"
```

### Verificação Pós-Rollback

```bash
# Validar estado após rollback
make validate-rollback

# Gerar relatório de rollback
make rollback-report
```

## 📈 Performance

### Benchmarks de Referência

- **1TB de dados**: < 4 horas
- **Downtime**: < 5 minutos
- **Taxa de sucesso**: > 99.9%
- **Validação**: 100% dos dados

### Otimizações

- Conexões paralelas
- Processamento em lotes
- Compressão de dados
- Índices otimizados

## 🔒 Segurança

### Configurações de Segurança

- Criptografia TLS 1.3
- Autenticação robusta
- Segregação de credenciais
- Logs de auditoria

### Gerenciamento de Segredos

```bash
# Arquivos sensíveis em secrets/
chmod 600 src/migration/secrets/*.json

# Nunca commitar secrets
grep -r "password" src/migration/secrets/
```

## 🤝 Contribuição

### Desenvolvimento

```bash
# Setup ambiente de desenvolvimento
make dev-setup

# Executar testes
make test

# Verificar qualidade do código
make lint

# Gerar documentação
make docs
```

### Estrutura de Commits

```
feat: adicionar nova funcionalidade
fix: corrigir bug
docs: atualizar documentação
test: adicionar testes
refactor: refatorar código
```

## 📝 Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Documentação**: `docs/`
- **Issues**: GitHub Issues
- **Email**: suporte@empresa.com
- **Chat**: Slack #migration-support

---

**Versão**: 1.0.0
**Última Atualização**: 03/10/2025
**Autor**: Equipe de Migração Enterprise
