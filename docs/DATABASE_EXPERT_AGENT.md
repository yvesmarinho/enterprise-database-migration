# Database Expert Agent v1.0.0

## 🤖 Visão Geral

Agente especializado com profundo conhecimento e experiência em **MySQL** e **PostgreSQL**, fornecendo:

- 🔍 **Análise profunda** de bancos de dados
- 📋 **Planejamento de migração** MySQL → PostgreSQL
- 🔧 **Otimização de queries** SQL
- ✅ **Validação de integridade** de dados
- 📊 **Relatórios detalhados** e recomendações

## 🎯 Características Principais

### 1. Análise de Banco de Dados

Análise em 4 níveis de profundidade:
- **QUICK**: Análise superficial rápida
- **STANDARD**: Análise padrão completa
- **DEEP**: Análise profunda detalhada
- **FORENSIC**: Análise forense exaustiva

### 2. Base de Conhecimento

O agente possui extensa base de conhecimento incluindo:

- ✅ **70+ mapeamentos de tipos** MySQL → PostgreSQL
- ✅ **20+ mapeamentos de funções** SQL
- ✅ **18 incompatibilidades** conhecidas
- ✅ **10 melhores práticas** PostgreSQL
- ✅ **10 melhores práticas** MySQL
- ✅ **10 armadilhas comuns** de migração

### 3. Capacidades

```python
capabilities = {
    'postgresql': True,  # Requer psycopg2
    'mysql': True,       # Requer pymysql
}
```

## 📦 Instalação

### Dependências

```bash
# PostgreSQL support
pip install psycopg2-binary

# MySQL support
pip install pymysql

# Ou instalar todas as dependências do projeto
pip install -r requirements.txt
```

## 🚀 Uso Rápido

### Exemplo 1: Criar Agente

```python
from app.agents import DatabaseExpertAgent
import logging

# Criar agente
agent = DatabaseExpertAgent(log_level=logging.INFO)

print(f"Agent version: {agent.version}")
print(f"Capabilities: {agent.capabilities}")
```

### Exemplo 2: Analisar Banco MySQL

```python
from app.agents.database_expert_agent import (
    DatabaseExpertAgent,
    DatabaseType,
    AnalysisLevel
)

# Criar agente
agent = DatabaseExpertAgent()

# Parâmetros de conexão MySQL
mysql_params = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'senha',
    'database': 'perfexcrm',
    'charset': 'utf8mb4'
}

# Analisar banco (análise padrão)
analysis = agent.analyze_database(
    connection_params=mysql_params,
    db_type=DatabaseType.MYSQL,
    analysis_level=AnalysisLevel.STANDARD
)

# Resultados
print(f"Database: {analysis.database_info.db_type.value}")
print(f"Version: {analysis.database_info.version}")
print(f"Size: {analysis.database_info.size_mb:.2f} MB")
print(f"Tables: {analysis.database_info.table_count}")
print(f"Encoding: {analysis.database_info.encoding}")
print(f"\nRecommendations: {len(analysis.recommendations)}")
for rec in analysis.recommendations[:5]:
    print(f"  - {rec}")
```

### Exemplo 3: Analisar Banco PostgreSQL

```python
# Parâmetros de conexão PostgreSQL
pg_params = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'senha',
    'database': 'mydb'
}

# Analisar banco (análise profunda)
analysis = agent.analyze_database(
    connection_params=pg_params,
    db_type=DatabaseType.POSTGRESQL,
    analysis_level=AnalysisLevel.DEEP
)

print(f"PostgreSQL {analysis.database_info.version}")
print(f"Size: {analysis.database_info.size_mb:.2f} MB")
```

### Exemplo 4: Planejar Migração MySQL → PostgreSQL

```python
# 1. Analisar banco MySQL de origem
mysql_analysis = agent.analyze_database(
    connection_params=mysql_params,
    db_type=DatabaseType.MYSQL,
    analysis_level=AnalysisLevel.STANDARD
)

# 2. Planejar migração
strategy = agent.plan_migration(
    source_analysis=mysql_analysis,
    target_db_type=DatabaseType.POSTGRESQL,
    options={
        'chunk_size': 1000,
        'parallel_tables': 4
    }
)

# 3. Revisar plano
print(f"\n=== Migration Strategy ===")
print(f"Strategy: {strategy.strategy_name}")
print(f"Complexity: {strategy.complexity}")
print(f"Duration: {strategy.estimated_duration}")
print(f"\nRisks ({len(strategy.risks)}):")
for risk in strategy.risks[:3]:
    print(f"  ⚠️ {risk}")

print(f"\nSteps ({len(strategy.steps)}):")
for step in strategy.steps:
    print(f"  {step}")

print(f"\nCompatibility Issues ({len(strategy.compatibility_issues)}):")
for issue in strategy.compatibility_issues[:5]:
    print(f"  🔧 {issue['feature']}: {issue['mysql']} → {issue['postgresql']}")
```

### Exemplo 5: Otimizar Query

```python
# Query para otimizar
query = """
SELECT * FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active' OR u.created_at > '2024-01-01'
ORDER BY u.created_at DESC
"""

# Analisar e otimizar
optimization = agent.optimize_query(
    query=query,
    db_type=DatabaseType.POSTGRESQL,
    context={'table_size': 1000000}
)

print(f"\n=== Query Optimization ===")
print(f"Issues found: {len(optimization['issues'])}")
for issue in optimization['issues']:
    print(f"  ⚠️ {issue['type']} ({issue['severity']}): {issue['description']}")

print(f"\nSuggestions:")
for suggestion in optimization['suggestions']:
    print(f"  💡 {suggestion}")
```

### Exemplo 6: Validar Integridade de Dados

```python
# Validar dados migrados
validation = agent.validate_data_integrity(
    source_conn_params=mysql_params,
    target_conn_params=pg_params,
    source_type=DatabaseType.MYSQL,
    target_type=DatabaseType.POSTGRESQL,
    tables=['users', 'orders', 'products']
)

print(f"\n=== Data Integrity Validation ===")
print(f"Tables validated: {validation['tables_validated']}")
print(f"Tables matched: {validation['tables_matched']}")
print(f"Tables mismatched: {validation['tables_mismatched']}")
print(f"Validation passed: {validation['validation_passed']}")
```

### Exemplo 7: Gerar Relatório de Migração

```python
from pathlib import Path

# Gerar relatório completo
agent.generate_migration_report(
    analysis=mysql_analysis,
    strategy=strategy,
    output_file=Path('reports/migration_plan.json')
)

print("✅ Migration report generated: reports/migration_plan.json")
```

### Exemplo 8: Exportar Base de Conhecimento

```python
# Exportar toda a base de conhecimento
agent.export_knowledge_base(Path('knowledge_base.json'))

print("✅ Knowledge base exported")
```

## 📊 Estrutura de Dados

### DatabaseInfo

```python
@dataclass
class DatabaseInfo:
    db_type: DatabaseType          # MYSQL, POSTGRESQL, MARIADB
    version: str                    # Ex: "PostgreSQL 14.5"
    server_info: str                # Info do servidor
    encoding: str                   # Ex: "UTF8"
    collation: str                  # Ex: "en_US.UTF-8"
    size_mb: float                  # Tamanho em MB
    table_count: int                # Número de tabelas
    total_rows: int                 # Total de registros
    index_count: int                # Número de índices
    constraints_count: int          # Número de constraints
    users_count: int                # Número de usuários
    metadata: Dict[str, Any]        # Metadados adicionais
```

### MigrationStrategy

```python
@dataclass
class MigrationStrategy:
    strategy_name: str                           # Nome da estratégia
    description: str                             # Descrição
    complexity: str                              # low, medium, high, critical
    estimated_duration: str                      # Duração estimada
    risks: List[str]                            # Lista de riscos
    steps: List[str]                            # Passos da migração
    recommendations: List[str]                  # Recomendações
    compatibility_issues: List[Dict[str, str]]  # Issues de compatibilidade
    required_transformations: List[Dict]        # Transformações necessárias
```

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    timestamp: datetime                    # Timestamp da análise
    analysis_level: AnalysisLevel         # Nível usado
    database_info: DatabaseInfo           # Info do banco
    schema_analysis: Dict[str, Any]       # Análise do schema
    data_quality: Dict[str, Any]          # Qualidade de dados
    performance_metrics: Dict[str, Any]   # Métricas de performance
    security_assessment: Dict[str, Any]   # Avaliação de segurança
    recommendations: List[str]            # Recomendações
    warnings: List[str]                   # Avisos
    errors: List[str]                     # Erros encontrados
```

## 🧠 Base de Conhecimento

### Mapeamentos de Tipos (MySQL → PostgreSQL)

```python
type_mappings = {
    'TINYINT': 'SMALLINT',
    'TINYINT(1)': 'BOOLEAN',
    'MEDIUMINT': 'INTEGER',
    'INT': 'INTEGER',
    'BIGINT': 'BIGINT',
    'FLOAT': 'REAL',
    'DOUBLE': 'DOUBLE PRECISION',
    'DECIMAL': 'NUMERIC',
    'CHAR': 'CHAR',
    'VARCHAR': 'VARCHAR',
    'TEXT': 'TEXT',
    'MEDIUMTEXT': 'TEXT',
    'LONGTEXT': 'TEXT',
    'BLOB': 'BYTEA',
    'DATE': 'DATE',
    'DATETIME': 'TIMESTAMP',
    'TIMESTAMP': 'TIMESTAMP WITH TIME ZONE',
    'JSON': 'JSONB',
    'ENUM': 'VARCHAR',  # Ou criar tipo ENUM customizado
    'SET': 'VARCHAR[]'
}
```

### Mapeamentos de Funções (MySQL → PostgreSQL)

```python
function_mappings = {
    'NOW()': 'CURRENT_TIMESTAMP',
    'CURDATE()': 'CURRENT_DATE',
    'IFNULL': 'COALESCE',
    'IF': 'CASE WHEN',
    'CONCAT': '||',
    'GROUP_CONCAT': 'STRING_AGG',
    'SUBSTRING': 'SUBSTR',
    'LIMIT offset, count': 'LIMIT count OFFSET offset'
}
```

### Incompatibilidades Conhecidas

1. **AUTO_INCREMENT** → SERIAL/IDENTITY
2. **UNSIGNED** → CHECK constraint
3. **ZEROFILL** → lpad() formatting
4. **Backticks** → Double quotes
5. **Case Sensitivity** → Case-sensitive by default
6. **ENGINE=InnoDB** → N/A (remover)

## 🔧 Integração com Projeto

### Usar no Orquestrador

```python
from app.agents import DatabaseExpertAgent
from app.core.migration_orchestrator import MigrationOrchestrator

class EnhancedMigrationOrchestrator(MigrationOrchestrator):
    def __init__(self, config_file):
        super().__init__(config_file)
        self.expert_agent = DatabaseExpertAgent()
    
    def analyze_source(self):
        """Analisa banco de origem usando o expert agent."""
        analysis = self.expert_agent.analyze_database(
            connection_params=self.source_config,
            db_type=DatabaseType.MYSQL,
            analysis_level=AnalysisLevel.STANDARD
        )
        return analysis
```

### Usar em Scripts CLI

```python
# cli/expert_analysis.py
from app.agents import DatabaseExpertAgent
from app.agents.database_expert_agent import DatabaseType, AnalysisLevel

def main():
    agent = DatabaseExpertAgent()
    
    # Carregar config
    import json
    with open('secrets/mysql_config.json') as f:
        config = json.load(f)
    
    # Analisar
    analysis = agent.analyze_database(
        connection_params=config,
        db_type=DatabaseType.MYSQL,
        analysis_level=AnalysisLevel.STANDARD
    )
    
    # Planejar migração
    strategy = agent.plan_migration(
        source_analysis=analysis,
        target_db_type=DatabaseType.POSTGRESQL
    )
    
    # Gerar relatório
    agent.generate_migration_report(
        analysis=analysis,
        strategy=strategy,
        output_file=Path('reports/migration_plan.json')
    )

if __name__ == '__main__':
    main()
```

## 📈 Roadmap

### v1.1.0 (Próxima versão)
- [ ] Implementação completa de análise de schema
- [ ] Validação de integridade com checksums
- [ ] Detecção automática de stored procedures
- [ ] Conversão de triggers MySQL → PostgreSQL

### v1.2.0
- [ ] Suporte para Oracle
- [ ] Suporte para SQL Server
- [ ] Análise de performance em tempo real
- [ ] Machine learning para otimização de queries

### v2.0.0
- [ ] Interface web para visualização
- [ ] Migração automática end-to-end
- [ ] Rollback automático em caso de falha

## 🐛 Troubleshooting

### Erro: psycopg2 not available

```bash
pip install psycopg2-binary
```

### Erro: pymysql not available

```bash
pip install pymysql
```

### Erro de conexão MySQL

Verifique:
- Host e porta corretos
- Usuário tem permissões adequadas
- Firewall permite conexão
- MySQL está rodando

### Erro de conexão PostgreSQL

Verifique:
- `pg_hba.conf` permite conexão do host
- PostgreSQL está escutando no IP correto
- Senha está correta

## 📚 Referências

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MySQL Reference Manual](https://dev.mysql.com/doc/)
- [PostgreSQL vs MySQL: Difference You Should Know](https://www.postgresql.org/about/)
- [Migrating from MySQL to PostgreSQL](https://wiki.postgresql.org/wiki/Converting_from_other_Databases_to_PostgreSQL)

## 📝 Licença

Propriedade de Vya.Digital - Uso interno

## 👥 Autor

**Vya.Digital DevOps Team**
Data: 2026-04-06

---

**🤖 Database Expert Agent** - Especialista em MySQL e PostgreSQL com IA
