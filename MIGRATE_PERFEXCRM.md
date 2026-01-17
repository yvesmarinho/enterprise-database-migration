# Migração PerfexCRM MySQL

## 📋 Resumo

Migração do banco de dados MySQL do PerfexCRM:
- **Origem**: wf004.vya.digital
- **Destino**: wfdb02.vya.digital
- **Database**: perfexcrm_db
- **Usuários**: perfexcrm_user (RW), perfexcrm_view (RO)

## 🚀 Execução

### Opção 1: Script CLI (Recomendado)
```bash
uv run python cli/migrate_perfexcrm.py
```

### Opção 2: Módulo Python
```bash
uv run python -m app.orchestrators.migrate_perfexcrm_mysql
```

## 📝 O que o script faz

1. **Valida ambiente de origem** (wf004)
   - Verifica conectividade
   - Obtém tamanho do banco e número de tabelas

2. **Cria backup completo**
   - Dump SQL com mysqldump
   - Compactação gzip
   - Armazena em `backup/perfexcrm_YYYYMMDD_HHMMSS/`

3. **Verifica ambiente de destino** (wfdb02)
   - Testa conectividade
   - Alerta se o banco já existe

4. **Cria banco no destino**
   - DROP/CREATE DATABASE (se confirmado)
   - Charset: utf8mb4_unicode_ci

5. **Restaura dados**
   - Importa dump SQL
   - Valida integridade

6. **Configura usuários**
   - `perfexcrm_user`: ALL PRIVILEGES
   - `perfexcrm_view`: SELECT only

7. **Validação final**
   - Compara número de tabelas
   - Compara tamanho dos bancos
   - Testa conexões dos usuários

## 🔑 Credenciais

### Arquivo de Configuração

O script usa o arquivo `secrets/mysql_config.json` com as credenciais do `migration_user`:

```json
{
  "source": {
    "host": "wf004.vya.digital",
    "user": "migration_user",
    "password": "..."
  },
  "destination": {
    "host": "wfdb02.vya.digital",
    "user": "migration_user",
    "password": "..."
  }
}
```

### Credenciais Solicitadas

Durante a execução, o script:

1. **Carrega credenciais do arquivo** (migration_user)
2. **Pergunta se deseja usar** ou fornecer outras
3. **Solicita senhas** para os usuários do PerfexCRM:
   - `perfexcrm_user` (nova senha)
   - `perfexcrm_view` (nova senha)

> 💡 **Dica**: Se o `migration_user` não tiver acesso MySQL, responda 'n' e forneça credenciais alternativas (ex: root)

## 📦 Backup

Todos os backups são armazenados em:
```
backup/perfexcrm_YYYYMMDD_HHMMSS/
├── perfexcrm_db_dump.sql      # Dump SQL completo
├── perfexcrm_db_dump.sql.gz   # Dump compactado
└── migration.log              # Log detalhado
```

## ⚠️ Pré-requisitos

1. Dependências instaladas:
```bash
uv sync
```

2. Acesso aos servidores:
   - MySQL no wf004.vya.digital (porta 3306)
   - MySQL no wfdb02.vya.digital (porta 3306)

3. Permissões MySQL necessárias:
   - Origem: SELECT, LOCK TABLES, SHOW VIEW, TRIGGER
   - Destino: ALL PRIVILEGES (para criar banco e usuários)

## 📊 Verificação Pós-Migração

Após a migração, verifique:

1. **Aplicação PerfexCRM**
   - Atualize a configuração para apontar para wfdb02
   - Teste login e funcionalidades principais

2. **Conectividade**
```bash
mysql -h wfdb02.vya.digital -u perfexcrm_user -p perfexcrm_db
```

3. **Dados**
```sql
-- Verificar tabelas
SHOW TABLES;

-- Verificar registros de uma tabela importante
SELECT COUNT(*) FROM [sua_tabela_principal];
```

## 🔒 Segurança

- ✅ Todas as senhas são solicitadas via prompt (não ficam em arquivos)
- ✅ Dump contém apenas dados (sem senhas de usuários)
- ✅ Backup é criado antes de qualquer alteração
- ⚠️ Guarde as credenciais em local seguro
- ⚠️ Considere rotacionar as senhas após a migração

## 🐛 Troubleshooting

### Erro de conexão
```
✗ Erro ao conectar em wf004.vya.digital
```
**Solução**: Verifique firewall, credenciais e se o MySQL está rodando

### Banco já existe no destino
```
⚠ Banco perfexcrm_db já existe no servidor de destino!
```
**Solução**: O script pedirá confirmação. Digite 'SIM' para sobrescrever

### Erro no mysqldump
```
✗ Falha ao criar dump do banco
```
**Solução**: Verifique permissões do usuário no servidor origem

### Erro na importação
```
✗ Falha ao importar dados
```
**Solução**: Verifique o log em `backup/perfexcrm_*/migration.log`

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique o arquivo de log: `backup/perfexcrm_*/migration.log`
2. Confirme que tem backup antes de qualquer alteração
3. Em caso de falha, os dados originais permanecem intactos no wf004
