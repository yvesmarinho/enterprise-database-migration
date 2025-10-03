# 📚 Documentação do Sistema de Migração PostgreSQL Modular

## 🚀 Visão Geral

O sistema de migração PostgreSQL foi completamente convertido para uma arquitetura modular em Python puro com logs integrados. Esta documentação descreve como usar e entender o novo sistema.

### 🎯 Características Principais

- **100% Python**: Elimina dependência de scripts bash
- **Arquitetura Modular**: Componentes reutilizáveis e testáveis
- **Logs Integrados**: Sistema de logging avançado com cores
- **Interface CLI**: Menu interativo e modo automático
- **Tratamento de Erros**: Gestão robusta de exceções
- **Relatórios Detalhados**: JSON, Markdown e logs estruturados

## 📁 Estrutura do Projeto

```
enterprise-database-install/
├── run_migration.py                    # 🚀 Launcher principal
├── exemplos_uso.py                     # 📖 Exemplos de uso
└── src/migration/
    ├── orchestrator_pure_python.py     # 🎯 Orquestrador principal
    ├── base_component.py               # 🏗️ Módulo base para componentes
    ├── migration_orchestrator.py       # 📋 Orquestrador original (backup)
    ├── quick_migration.py              # ⚡ CLI simplificado
    ├── core/
    │   ├── sqlalchemy_migration.py     # 🔄 Motor de migração SQLAlchemy
    │   └── reports/                    # 📊 Relatórios gerados
    ├── validation/
    │   ├── check_scram_auth.py         # 🔐 Validação SCRAM (modularizado)
    │   └── test_wfdb02_connection.py   # 🔗 Testes de conexão
    ├── utils/
    │   ├── discover_users.py           # 👥 Descoberta de usuários
    │   └── analyze_password.py         # 🔑 Análise de senhas
    └── config/
        ├── migration_rules.json        # ⚙️ Regras de migração
        ├── source_config.json          # 📡 Configuração origem
        └── destination_config.json     # 🎯 Configuração destino
```

## 🎮 Como Usar

### 1. 🚀 Execução Básica (Recomendado)

```bash
# Launcher principal com menu interativo
python3 run_migration.py

# Migração automática completa
python3 run_migration.py --auto

# Modo verbose (logs detalhados)
python3 run_migration.py --auto --verbose
```

### 2. ⚡ Execução Rápida

```bash
# Usar orquestrador diretamente
python3 src/migration/orchestrator_pure_python.py

# Migração automática
python3 src/migration/orchestrator_pure_python.py --auto

# Simulação (dry-run)
python3 src/migration/orchestrator_pure_python.py --dry-run
```

### 3. 🔧 Testes Específicos

```bash
# Testar apenas ambiente
python3 src/migration/orchestrator_pure_python.py --test-env

# Testar apenas módulos
python3 src/migration/orchestrator_pure_python.py --test-modules

# CLI simplificado
python3 src/migration/quick_migration.py test
```

### 4. 📖 Exemplos Interativos

```bash
# Executar exemplos de uso
python3 exemplos_uso.py
```

## 🏗️ Arquitetura Modular

### 📦 Componentes Base

O sistema usa uma hierarquia de classes base definida em `base_component.py`:

```python
MigrationComponent          # Base para todos os componentes
├── DatabaseComponent       # Para componentes de banco
├── ValidationComponent     # Para componentes de validação
└── UtilityComponent       # Para utilitários
```

### 🔧 Como Criar Novos Componentes

```python
from base_component import ValidationComponent, ComponentResult, component_method

class MeuNovoComponente(ValidationComponent):
    def __init__(self, logger=None):
        super().__init__("meu_componente", logger)

    def _setup(self):
        """Inicialização específica"""
        self.log_info("Meu componente inicializando...")

    @component_method
    def validate(self, data):
        """Implementar validação"""
        # Sua lógica aqui
        return ComponentResult(True, "Validação OK")
```

## 📊 Sistema de Logging

### 🎨 Níveis de Log com Cores

- 🔍 **DEBUG**: Informações técnicas detalhadas
- ℹ️ **INFO**: Informações gerais
- ✅ **SUCCESS**: Operações bem-sucedidas
- ⚠️ **WARNING**: Avisos importantes
- ❌ **ERROR**: Erros recuperáveis
- 💥 **CRITICAL**: Falhas críticas

### 📝 Arquivos de Log

Os logs são salvos automaticamente em:
```
src/migration/core/reports/migration_YYYYMMDD_HHMMSS.log
```

### 🔧 Exemplo de Logging

```python
# No orquestrador
orchestrator.logger.info("Mensagem informativa")
orchestrator.logger.success("Operação bem-sucedida")
orchestrator.logger.error("Erro encontrado")

# Em componentes
self.log_info("Mensagem do componente")
self.log_success("Sucesso no componente")
```

## 📋 Fluxo de Execução

### 🔄 Passos da Migração

1. **validate_environment** - Validar ambiente e dependências
2. **load_configurations** - Carregar configurações
3. **check_modules** - Verificar módulos carregados
4. **test_connectivity** - Testar conectividade
5. **discover_source** - Descobrir estrutura origem
6. **analyze_compatibility** - Analisar compatibilidade SCRAM
7. **pre_migration_backup** - Backup pré-migração (opcional)
8. **execute_migration** - Migração principal
9. **validate_migration** - Validar resultado
10. **test_connections** - Testar conexões pós-migração
11. **generate_report** - Gerar relatório final

### 🎛️ Controle de Fluxo

```python
# Parar em erro crítico
"error_handling": {"continue_on_error": false}

# Continuar mesmo com erros
"error_handling": {"continue_on_error": true}
```

## 📊 Relatórios Gerados

### 📄 Tipos de Relatório

1. **JSON Report**: `migration_report_YYYYMMDD_HHMMSS.json`
   - Dados estruturados completos
   - Estatísticas detalhadas
   - Logs integrados

2. **Markdown Report**: `migration_report_YYYYMMDD_HHMMSS.md`
   - Formato legível
   - Resumos visuais
   - Status dos passos

3. **Log File**: `migration_YYYYMMDD_HHMMSS.log`
   - Log completo da execução
   - Timestamps precisos
   - Níveis de log detalhados

### 📈 Exemplo de Estatísticas

```json
{
  "statistics": {
    "total_steps": 11,
    "completed_steps": 9,
    "failed_steps": 1,
    "skipped_steps": 1
  }
}
```

## 🔐 Integração SCRAM

### 🆕 Versão Modular

O módulo `check_scram_auth.py` foi atualizado com uma classe modular:

```python
from src.migration.validation.check_scram_auth import ScramAuthChecker

# Usar como componente
scram_checker = ScramAuthChecker()
result = scram_checker.validate()

# Verificação rápida
is_supported = scram_checker.check_scram_support()
```

### 🔧 Configuração

```json
{
  "host": "servidor.exemplo.com",
  "port": 5432,
  "ssl_mode": "require",
  "possible_users": ["postgres", "admin"]
}
```

## ⚙️ Configurações

### 📝 migration_rules.json

```json
{
  "migration_rules": {
    "structure_migration": {"enabled": true},
    "user_migration": {"enabled": true},
    "data_migration": {"enabled": false}
  },
  "error_handling": {
    "continue_on_error": false,
    "max_retries": 3,
    "timeout": 300
  }
}
```

### 🔌 Configurações de Servidor

- `source_config.json`: Servidor origem
- `destination_config.json`: Servidor destino

## 🐛 Tratamento de Erros

### 🛡️ Estratégias de Erro

1. **Fail-Fast**: Para em erros críticos
2. **Continue-on-Error**: Prossegue mesmo com falhas
3. **Retry Logic**: Tentativas automáticas
4. **Graceful Degradation**: Funcionalidade reduzida

### 🔧 Exemplo de Tratamento

```python
try:
    result = orchestrator.run_complete_migration()
    if result:
        print("✅ Sucesso!")
    else:
        print("⚠️ Concluído com avisos")
except Exception as e:
    print(f"❌ Erro: {e}")
```

## 🚦 Códigos de Saída

- `0`: Sucesso completo
- `1`: Erro geral ou falha crítica
- `130`: Interrompido pelo usuário (Ctrl+C)

## 📚 Exemplos Práticos

### 🎯 Migração Básica

```python
from src.migration.orchestrator_pure_python import PostgreSQLMigrationOrchestrator

orchestrator = PostgreSQLMigrationOrchestrator()
success = orchestrator.run_complete_migration()
```

### 🔍 Validação de Ambiente

```python
orchestrator = PostgreSQLMigrationOrchestrator(verbose=True)
if orchestrator.validate_environment():
    print("✅ Ambiente válido")
```

### 📊 Acesso aos Logs

```python
# Após execução
log_summary = orchestrator.logger.get_log_summary()
print(f"Total de entradas: {log_summary['total_entries']}")
```

## 🔧 Solução de Problemas

### ❌ Problemas Comuns

1. **Módulos não encontrados**
   ```bash
   # Executar a partir da raiz do projeto
   cd enterprise-database-install
   python3 run_migration.py
   ```

2. **Dependências faltando**
   ```bash
   pip install sqlalchemy psycopg2-binary colorama
   ```

3. **Configurações não encontradas**
   - Verificar `src/migration/config/`
   - Usar configurações padrão se necessário

4. **Problemas de conectividade**
   - Verificar configurações de servidor
   - Testar credenciais manualmente

### 🔍 Debug Avançado

```bash
# Modo super verboso
python3 run_migration.py --verbose --test-env

# Verificar módulos específicos
python3 -c "from src.migration.validation.check_scram_auth import ScramAuthChecker; print('OK')"
```

## 🚀 Melhorias Futuras

### 📋 Roadmap

- [ ] Interface Web (Flask/FastAPI)
- [ ] Métricas Prometheus
- [ ] Testes automatizados (pytest)
- [ ] Documentação API (Sphinx)
- [ ] Docker containerização
- [ ] CI/CD integração

### 🤝 Contribuições

Para contribuir com o projeto:

1. Seguir a arquitetura modular
2. Usar o sistema de logging integrado
3. Implementar tratamento de erros
4. Adicionar testes unitários
5. Documentar mudanças

## 📞 Suporte

Para questões técnicas:

1. **Logs**: Verificar `src/migration/core/reports/`
2. **Verbose**: Usar `--verbose` para detalhes
3. **Exemplos**: Executar `python3 exemplos_uso.py`
4. **Debug**: Usar `--test-env` ou `--test-modules`

---

**📅 Última atualização**: 03/10/2025
**🏷️ Versão**: 3.0.0 (Modular)
**👨‍💻 Autor**: GitHub Copilot Enterprise
