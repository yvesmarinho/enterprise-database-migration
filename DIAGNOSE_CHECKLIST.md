# ✅ CHECKLIST - Diagnóstico de Permissões

## Antes de Executar

- [ ] Arquivo `secrets/wfdb02_user_journey.txt` existe?
  ```bash
  ls -la secrets/wfdb02_user_journey.txt
  ```

- [ ] Arquivo `secrets/destination_config.txt` existe?
  ```bash
  ls -la secrets/destination_config.txt
  ```

- [ ] Arquivo de credenciais está protegido?
  ```bash
  chmod 600 secrets/wfdb02_user_journey.txt
  ```

- [ ] SQLAlchemy está instalado?
  ```bash
  python3 -c "import sqlalchemy; print(sqlalchemy.__version__)"
  ```

- [ ] Arquivo de credenciais contém dados corretos?
  ```bash
  cat secrets/wfdb02_user_journey.txt
  # Deve mostrar:
  # user=journey_system
  # password=...
  ```

## Executando o Diagnóstico

```bash
# Navegar para o diretório
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration

# Executar script
python3 validation/diagnose_journey_permissions.py
```

## Interpretando Resultados

### Conectado com Sucesso?
```
[✓] Conectado com sucesso como 'journey_system'
```
- ✅ Credenciais estão corretas
- ✅ Servidor está acessível

### Problemas Encontrados?
```
1. [CRITICAL] SCHEMA
   Descrição: Usuário não tem permissão USAGE no schema 'public'
   Recomendação: GRANT USAGE ON SCHEMA public TO journey_system;
```

### Sem Problemas?
```
✓ Nenhum problema encontrado!
```

## Resultados

### Arquivo JSON
```bash
# Localização
reports/diagnosis_journey_system_YYYYMMDD_HHMMSS.json

# Ver conteúdo
cat reports/diagnosis_journey_system_*.json | python3 -m json.tool
```

### Comandos SQL Recomendados
Procure por `➜ 7. Comandos SQL Recomendados` na saída do console

## Aplicando Correções

### 1. Conectar como superuser postgres
```bash
psql -h wfdb02.vya.digital -U postgres -d postgres
```

### 2. Executar comandos recomendados
```sql
-- Exemplo:
GRANT USAGE ON SCHEMA public TO journey_system;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO journey_system;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO journey_system;
```

### 3. Re-validar
```bash
python3 validation/diagnose_journey_permissions.py
```

## Troubleshooting

### Erro: "Arquivo de credenciais não encontrado"

```
ERRO ao carregar credenciais: Arquivo de credenciais não encontrado: ...
```

**Solução**:
```bash
# Criar arquivo
cat > secrets/wfdb02_user_journey.txt << EOF
user=journey_system
password=bra-Lhudri5ubikeDrin
EOF
```

### Erro: "ModuleNotFoundError: No module named 'sqlalchemy'"

**Solução**:
```bash
pip install sqlalchemy>=2.0
# ou
pip install -r requirements.txt
```

### Erro: "Não conseguiu fazer USAGE no schema public"

**Causa**: Usuário não tem permissão USAGE

**Solução**:
```sql
-- Como postgres:
GRANT USAGE ON SCHEMA public TO journey_system;
```

### Erro: "Falha ao conectar"

**Causa**:
- Servidor não está acessível
- Credenciais incorretas
- Firewall bloqueando conexão

**Solução**:
1. Verificar credenciais em `secrets/wfdb02_user_journey.txt`
2. Testar conectividade: `ping wfdb02.vya.digital`
3. Verificar firewall

## Segurança

- [ ] Arquivo `secrets/wfdb02_user_journey.txt` não foi commitado?
  ```bash
  git status secrets/
  # Não deve mostrar wfdb02_user_journey.txt
  ```

- [ ] Arquivo está no `.gitignore`?
  ```bash
  grep wfdb02_user_journey .gitignore
  ```

- [ ] Nunca compartilhar arquivo de credenciais
- [ ] Nunca fazer commit de credenciais
- [ ] Usar permissões restritas: `chmod 600`

## Documentação

- [Diagnóstico de Permissões](../validation/README_DIAGNOSE_JOURNEY.md)
- [Sumário de Mudanças](../docs/DIAGNOSE_CHANGES_20251211.md)
- [Resumo Executivo](../docs/DIAGNOSE_SUMMARY_20251211.md)

## Contatos e Referências

**PostgreSQL 18**:
- Docs: https://www.postgresql.org/docs/18/
- Permissões: https://www.postgresql.org/docs/18/ddl-priv.html

**Script**:
- Localização: `validation/diagnose_journey_permissions.py`
- Mantido por: Sistema MCP
- Versão: 1.0.0

---

**Última atualização**: 11 de Dezembro de 2025
**Status**: ✅ READY TO USE
