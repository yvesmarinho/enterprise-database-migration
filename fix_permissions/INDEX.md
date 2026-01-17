# Index - Fix Permissions

## Estrutura de Arquivos

```
fix_permissions/
├── README.md                                    # Documentação completa
├── fix_permissions.json                         # Configuração JSON
├── fix_permissions.py                           # Script principal (executável)
├── verify_metabase_permissions.py               # Script de verificação legado
├── fix_metabase_permissions.sql                 # Script SQL manual (legado)
└── fix_metabase_ownership_restored.sql          # Script SQL pós-restauração (legado)
```

## Arquivos Principais

### 1. fix_permissions.py
**Propósito**: Script Python principal para correção automatizada de permissões
**Status**: ✅ Ativo
**Execução**:
```bash
python3 fix_permissions/fix_permissions.py --help
```
**Features**:
- Lê configuração de `fix_permissions.json`
- Modos: dry-run, execute, verify
- Suporte a múltiplos bancos
- Verificações automáticas
- Logs detalhados com timestamps

### 2. fix_permissions.json
**Propósito**: Configuração declarativa das operações
**Status**: ✅ Ativo
**Formato**: JSON
**Conteúdo**:
- Definições de bancos de dados
- Operações de ownership e privileges
- Configuração de conexão
- Regras de verificação

### 3. README.md
**Propósito**: Documentação completa do sistema
**Status**: ✅ Ativo
**Conteúdo**:
- Guia de uso
- Exemplos práticos
- Troubleshooting
- Referências técnicas

## Arquivos Legados

### verify_metabase_permissions.py
**Propósito**: Script antigo de verificação (read-only)
**Status**: 📦 Legado (substituído por `--verify` no script principal)
**Uso**: Ainda funcional para verificação isolada

### fix_metabase_permissions.sql
**Propósito**: Script SQL manual original
**Status**: 📦 Legado (substituído pelo sistema automatizado)
**Histórico**: Usado na correção inicial (2026-01-16)

### fix_metabase_ownership_restored.sql
**Propósito**: Script SQL pós-restauração de backup
**Status**: 📦 Legado (substituído pelo sistema automatizado)
**Histórico**: Criado após restauração do backup v56

## Fluxo de Trabalho

### Novo Problema de Permissões

1. **Adicionar configuração** em `fix_permissions.json`:
   ```json
   {
     "name": "novo_banco",
     "owner": "novo_user",
     "operations": [...]
   }
   ```

2. **Testar com dry-run**:
   ```bash
   python3 fix_permissions/fix_permissions.py --database novo_banco --dry-run --verbose
   ```

3. **Executar correções**:
   ```bash
   python3 fix_permissions/fix_permissions.py --database novo_banco --execute
   ```

4. **Verificar resultado**:
   ```bash
   python3 fix_permissions/fix_permissions.py --database novo_banco --verify
   ```

### Auditoria Periódica

```bash
# Verificar todos os bancos
python3 fix_permissions/fix_permissions.py --all --verify --verbose
```

### Correção em Massa

```bash
# Aplicar correções em todos os bancos configurados
python3 fix_permissions/fix_permissions.py --all --execute --verbose
```

## Histórico de Desenvolvimento

### 2026-01-16 - Sessão de Troubleshooting Metabase

**Contexto**: Metabase v0.58.1 → v0.56.19.1 após problemas com migrações

**Problemas Encontrados**:
1. ❌ Metabase v0.58.1 com bug em migração de jsonb
2. ❌ Backup tinha migrações v56, não compatível com v0.54.9
3. ❌ Após restauração, ownership de 141 tabelas estava errado (yves_marinho)
4. ❌ metabase_user sem privilégios nas tabelas

**Soluções Desenvolvidas**:
1. ✅ `fix_metabase_permissions.sql` - Correção manual inicial
2. ✅ `verify_metabase_permissions.py` - Script de verificação
3. ✅ `fix_metabase_ownership_restored.sql` - Correção pós-restauração
4. ✅ **Sistema automatizado completo** (fix_permissions.py + JSON)

**Resultado Final**:
- ✅ Metabase v0.56.19.1 funcionando
- ✅ 141 tabelas com ownership correto
- ✅ 154 objetos com privilégios corretos
- ✅ Sistema reutilizável para futuros casos

## Aprendizados e Conhecimento Adquirido

### 1. Gestão de Permissões PostgreSQL
- Transfer ownership: `ALTER TABLE ... OWNER TO`
- Grant privileges: `GRANT ... ON ... TO`
- Default privileges: `ALTER DEFAULT PRIVILEGES`
- Verificação: `pg_tables`, `information_schema.table_privileges`

### 2. Troubleshooting de Aplicações
- Logs do Metabase indicaram problemas de ownership
- Necessidade de verificar ANTES e DEPOIS
- Importância de dry-run antes de executar

### 3. Arquitetura de Solução
- JSON para configuração declarativa
- Python para lógica de execução
- Separação entre dry-run e execute
- Verificações automáticas integradas

### 4. Boas Práticas
- Sempre fazer backup antes de modificar
- Documentar estado inicial e final
- Logs detalhados com timestamps
- Modo verbose para debugging

## Integração com Outros Sistemas

### scripts/restore_metabase_backup.py
Após executar restauração de backup:
```bash
python3 scripts/restore_metabase_backup.py
python3 fix_permissions/fix_permissions.py --database metabase_db --execute
```

### scripts/check_metabase_version.py
Verificar versão e compatibilidade antes de aplicar correções:
```bash
python3 scripts/check_metabase_version.py
```

## Manutenção

### Adicionar Novo Banco

1. Editar `fix_permissions.json`
2. Adicionar entry com operações necessárias
3. Testar com `--dry-run`
4. Documentar em README.md

### Atualizar Operações Existentes

1. Modificar `operations` no JSON
2. Testar com `--dry-run` no banco real
3. Comparar output com estado esperado
4. Executar com `--execute`

### Debugging

```bash
# Modo verbose para ver todos os SQLs
python3 fix_permissions/fix_permissions.py --database metabase_db --dry-run --verbose

# Verificar conexão
python3 fix_permissions/fix_permissions.py --database metabase_db --verify

# Testar apenas uma operação (editar JSON temporariamente)
```

## Referências

- [README.md](README.md) - Documentação detalhada
- [fix_permissions.json](fix_permissions.json) - Configuração
- [PostgreSQL Docs - GRANT](https://www.postgresql.org/docs/current/sql-grant.html)
- [PostgreSQL Docs - ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)

## Contato e Suporte

Para dúvidas ou problemas:
1. Consultar README.md
2. Executar com `--verify` para diagnóstico
3. Usar `--dry-run --verbose` para simular
4. Verificar logs do PostgreSQL

---

**Última atualização**: 2026-01-16
**Versão**: 1.0.0
**Status**: ✅ Produção
