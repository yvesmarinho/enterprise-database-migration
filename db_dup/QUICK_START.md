# ⚡ Quick Start - PostgreSQL Database Clone System

## 🚀 Início Rápido em 5 Minutos

### Pré-requisitos
```bash
# Verificar Python
python3 --version  # Deve ser 3.12+

# Verificar PostgreSQL
psql --version
```

### Passo  1: Instalar Dependências
```bash
pip3 install psycopg2-binary sqlalchemy
```

### Passo 2: Criar Configuração
```bash
cd db_dup
cp config_example_Version2.json meu_config.json
nano meu_config.json
```

**Edite no mínimo:**
- `host`: Endereço do PostgreSQL
- `possible_users`: Usuário e senha
- `db_source`: Nome do banco de origem
- `db_destiny`: Nome do banco de destino

### Passo 3: Executar Clonagem
```bash
# Clonagem básica
python3 clone_database_Version2.py meu_config.json

# Com sobrescrita do banco destino
python3 clone_database_Version2.py meu_config.json --drop-if-exists

# Modo verboso (recomendado na primeira vez)
python3 clone_database_Version2.py meu_config.json --drop-if-exists --verbose
```

---

## ✅ Checklist de Verificação

### Antes de Executar
- [ ] PostgreSQL rodando
- [ ] Credenciais válidas configuradas
- [ ] Usuário tem permissões `CREATEDB`
- [ ] Espaço em disco suficiente
- [ ] Backup do banco original (se crítico)

### Durante Execução
- [ ] Logs aparecem sem erros
- [ ] Progresso visível (tabelas sendo copiadas)
- [ ] Sem mensagens de timeout

### Após Execução
- [ ] Mensagem "SUCESSO" apareceu
- [ ] Banco de destino criado
- [ ] Dados presentes no destino
- [ ] Permissões preservadas

---

## 🔧 Comandos Úteis

### Testar Conexão Manualmente
```bash
psql -h localhost -U postgres -d postgres -c "SELECT version();"
```

### Listar Bancos
```bash
psql -h localhost -U postgres -l
```

### Verificar Tamanho do Banco
```sql
SELECT
  pg_database.datname,
  pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'seu_banco';
```

### Dropar Banco (Cuidado!)
```bash
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS banco_destino;"
```

---

## 🐛 Resolução Rápida de Erros

### Erro: Module not found
```bash
pip3 install psycopg2-binary sqlalchemy
```

### Erro: Connection refused
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Erro: Permission denied
```sql
-- Conceder permissão de criar banco
ALTER USER seu_usuario CREATEDB;
```

### Erro: Database already exists
```bash
# Usar flag --drop-if-exists
python3 clone_database_Version2.py config.json --drop-if-exists
```

---

## 📋 Exemplo de Configuração Mínima

```json
{
  "host": "localhost",
  "port": 5432,
  "ssl_mode": "false",
  "possible_users": [
    {
      "username": "postgres",
      "password": "sua_senha",
      "priority": 0
    }
  ],
  "db_source": "banco_origem",
  "db_destiny": "banco_destino"
}
```

---

## 📚 Comandos Mais Usados

```bash
# Clonagem padrão
python3 clone_database_Version2.py config.json --drop-if-exists

# Apenas estrutura (sem dados)
python3 clone_database_Version2.py config.json --no-data

# Com log em arquivo
python3 clone_database_Version2.py config.json --verbose --log-file clone.log

# Salvar metadados
python3 clone_database_Version2.py config.json --save-metadata metadata.json

# Ver todas as opções
python3 clone_database_Version2.py --help
```

---

## 🎯 Casos de Uso Comuns

### 1. Backup Rápido
```bash
python3 clone_database_Version2.py backup_config.json --drop-if-exists
```

### 2. Ambiente de Teste
```bash
python3 clone_database_Version2.py teste_config.json --drop-if-exists --verbose
```

### 3. Clone para Análise (Só Estrutura)
```bash
python3 clone_database_Version2.py config.json --no-data
```

---

## 🆘 Precisa de Mais Ajuda?

Consulte a documentação completa: **[HOW_TO_USE.md](HOW_TO_USE.md)**

---

**Status do Código:** ✅ PRONTO PARA USO
**Versão:** 2.0.0
**Última Atualização:** 10/02/2026
