# Migration Files Index

## 📦 Core Scripts
- `sqlalchemy_migration.py` - Migração principal usando SQLAlchemy ⭐
- `complete_migration_fixed.py` - Migração com psycopg2 corrigida
- `migration_structure.py` - Migração estruturas apenas
- `migrate_users.py` - Migração específica usuários
- `complete_migration.py` - Script de migração completa
- `requirements.migration.txt` - Dependências específicas

### Reports
- `reports/migration_execution_*.log` - Logs de execução históricos

## 🔧 Utils
- `discover_users.py` - Descoberta de usuários
- `analyze_password.py` - Análise senhas SCRAM
- `debug_connection.py` - Debug conexões

## ⚙️ Config
- `migration_rules.json` - Regras de migração
- `setup_migration.sh` - Setup inicial
- `source_config.json` - Config servidor origem
- `destination_config.json` - Config servidor destino

## 🧪 Validation
- `check_scram_auth.py` - Validação SCRAM-SHA-256
- `test_wfdb02_*.py` - Testes conexão WFDB02 (5 arquivos)
- `test_migration.py` - Teste migração
- `check_wfdb02_status.py` - Status WFDB02
- `tst_connection_psql.py` - Teste conexão PostgreSQL

## 🚀 Uso Recomendado

### Migração Completa
```bash
python3 src/migration/core/sqlalchemy_migration.py
```

### Validação
```bash
python3 src/migration/validation/check_scram_auth.py
```
