# Formato de Log - Setup de Permissões do Usuário Backup

## Informações sobre Logging

### Configuração
O logging é configurado automaticamente a partir do arquivo:
```
secrets/postgresql_destination_config.json
```

Seção relevante:
```json
{
  "logging": {
    "level": "DEBUG",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "reports/destination_migration.log"
  }
}
```

### Localização dos Logs
Os logs são salvos em:
```
reports/destination_migration_YYYYMMDD_HHMMSS.log
```

Exemplo:
```
reports/destination_migration_20251222_143045.log
```

### Níveis de Log

- **DEBUG**: Informações detalhadas, incluindo cada comando SQL executado
- **INFO**: Informações gerais sobre o progresso
- **WARNING**: Avisos sobre situações não ideais
- **ERROR**: Erros que ocorreram durante a execução

### Exemplo de Saída de Log

```
2025-12-22 14:30:45 - __main__ - INFO - ======================================================================
2025-12-22 14:30:45 - __main__ - INFO - SETUP DE PERMISSÕES - USUÁRIO BACKUP
2025-12-22 14:30:45 - __main__ - INFO - ======================================================================
2025-12-22 14:30:45 - __main__ - INFO - Arquivo de log: /path/to/reports/destination_migration_20251222_143045.log
2025-12-22 14:30:45 - __main__ - INFO - Nível de log: DEBUG
2025-12-22 14:30:45 - __main__ - INFO - Servidor: wfdb02.vya.digital
2025-12-22 14:30:45 - __main__ - INFO - Modo: APLICAÇÃO
2025-12-22 14:30:45 - __main__ - INFO - Conexão administrativa estabelecida com sucesso
2025-12-22 14:30:45 - __main__ - INFO - Verificando existência do usuário 'backup'
2025-12-22 14:30:46 - __main__ - INFO - Usuário 'backup' já existe no sistema
2025-12-22 14:30:46 - __main__ - INFO - Coletando lista de bases de dados
2025-12-22 14:30:46 - __main__ - INFO - Encontradas 15 bases de dados: app_workforce, botpress_db, ai_process_db, ...
2025-12-22 14:30:46 - __main__ - INFO - Iniciando processamento de permissões
2025-12-22 14:30:46 - __main__ - INFO - [1/15] Processando database: app_workforce
2025-12-22 14:30:46 - __main__ - INFO - Database 'app_workforce': permissões já configuradas
2025-12-22 14:30:47 - __main__ - INFO - [2/15] Processando database: botpress_db
2025-12-22 14:30:47 - __main__ - DEBUG - Database 'botpress_db': encontrados 2 schemas: public, extensions
2025-12-22 14:30:47 - __main__ - INFO - Aplicando 11 permissões em 'botpress_db'
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: GRANT CONNECT ON DATABASE botpress_db TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: GRANT USAGE ON SCHEMA public TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: GRANT USAGE ON SCHEMA extensions TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: GRANT SELECT ON ALL TABLES IN SCHEMA extensions TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: GRANT SELECT ON ALL SEQUENCES IN SCHEMA extensions TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: ALTER DEFAULT PRIVILEGES IN SCHEMA extensions GRANT SELECT ON TABLES TO backup
2025-12-22 14:30:47 - __main__ - DEBUG - Executando: ALTER DEFAULT PRIVILEGES IN SCHEMA extensions GRANT SELECT ON SEQUENCES TO backup
2025-12-22 14:30:48 - __main__ - INFO - ✓ 11 permissões aplicadas com sucesso em 'botpress_db'
...
2025-12-22 14:31:20 - __main__ - INFO - ======================================================================
2025-12-22 14:31:20 - __main__ - INFO - RESUMO FINAL
2025-12-22 14:31:20 - __main__ - INFO - ======================================================================
2025-12-22 14:31:20 - __main__ - INFO - Total de databases processadas: 15
2025-12-22 14:31:20 - __main__ - INFO - Sucessos: 15
2025-12-22 14:31:20 - __main__ - INFO - Falhas: 0
2025-12-22 14:31:20 - __main__ - INFO - Conexões fechadas
2025-12-22 14:31:20 - __main__ - INFO - Execução concluída
2025-12-22 14:31:20 - __main__ - INFO - Log completo salvo em: /path/to/reports/destination_migration_20251222_143045.log
2025-12-22 14:31:20 - __main__ - INFO - ======================================================================
```

### Exemplo com Erros

```
2025-12-22 14:35:10 - __main__ - INFO - [5/15] Processando database: problem_db
2025-12-22 14:35:10 - __main__ - DEBUG - Database 'problem_db': encontrados 3 schemas: public, custom, legacy
2025-12-22 14:35:10 - __main__ - INFO - Aplicando 16 permissões em 'problem_db'
2025-12-22 14:35:10 - __main__ - DEBUG - Executando: GRANT CONNECT ON DATABASE problem_db TO backup
2025-12-22 14:35:10 - __main__ - ERROR - Erro ao aplicar permissões em 'problem_db': permission denied for database problem_db
Traceback (most recent call last):
  File "/path/to/script.py", line 145, in apply_backup_permissions
    conn.execute(text(stmt))
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.InsufficientPrivilege) permission denied for database problem_db
2025-12-22 14:35:10 - __main__ - WARNING - Databases com falha:
2025-12-22 14:35:10 - __main__ - WARNING -   - problem_db
```

## Uso

### Executar com Logging Normal (INFO)
```bash
python scripts/setup_backup_permissions_simple.py
```

### Executar com Logging Detalhado (DEBUG)
Já configurado por padrão no arquivo `secrets/postgresql_destination_config.json`

### Executar em Modo Dry-Run com Logging
```bash
python scripts/setup_backup_permissions_simple.py --dry-run
```

### Visualizar Log em Tempo Real
```bash
# Em outro terminal
tail -f reports/destination_migration_*.log
```

### Buscar Erros nos Logs
```bash
grep -i error reports/destination_migration_*.log
grep -i warning reports/destination_migration_*.log
```

### Analisar Logs de Uma Database Específica
```bash
grep "botpress_db" reports/destination_migration_*.log
```

## Benefícios

1. **Rastreabilidade Completa**: Cada ação é registrada com timestamp
2. **Debug Facilitado**: Modo DEBUG mostra cada comando SQL executado
3. **Auditoria**: Histórico completo de todas as operações
4. **Análise de Falhas**: Stack traces completos de erros
5. **Performance**: Análise de tempo de execução por database
6. **Arquivamento**: Logs com timestamp permitem manter histórico

## Retenção de Logs

Recomenda-se:
- Manter logs dos últimos 30 dias para análise
- Arquivar logs antigos em storage de longo prazo
- Implementar rotação de logs se o volume for muito grande

## Integração com Sistemas de Monitoramento

Os logs podem ser integrados com:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Prometheus + Grafana
- AWS CloudWatch
- Azure Monitor
