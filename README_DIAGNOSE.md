# 🔍 Diagnóstico de Permissões - PostgreSQL 18 journey_system

## ⚡ Quick Start

```bash
# 1. Verificar credenciais
cat secrets/wfdb02_user_journey.txt

# 2. Executar diagnóstico
python3 validation/diagnose_journey_permissions.py

# 3. Revisar resultados (console + JSON + SQL recomendado)
```

## 📖 Documentação Completa

- **Como usar**: [validation/README_DIAGNOSE_JOURNEY.md](validation/README_DIAGNOSE_JOURNEY.md)
- **Checklist**: [DIAGNOSE_CHECKLIST.md](DIAGNOSE_CHECKLIST.md)
- **Mudanças**: [docs/DIAGNOSE_CHANGES_20251211.md](docs/DIAGNOSE_CHANGES_20251211.md)
- **Resumo**: [docs/DIAGNOSE_SUMMARY_20251211.md](docs/DIAGNOSE_SUMMARY_20251211.md)

## 🔧 Script Principal

- **Arquivo**: `validation/diagnose_journey_permissions.py`
- **Credenciais**: Carregadas de `secrets/wfdb02_user_journey.txt`
- **Saída**: Console colorido + JSON + SQL recomendado

## 🎯 O que foi criado

✅ Script com SQLAlchemy para diagnóstico completo
✅ Carregamento seguro de credenciais de arquivo
✅ Análise de roles, schemas, tabelas e tablespaces
✅ Relatório JSON detalhado
✅ Recomendações SQL para correções
✅ Documentação completa e checklist prático

## 🚫 Problema investigado

O usuário `journey_system` não consegue ler tabelas apesar de ter grants de banco de dados.

**Possíveis causas**:
- Falta de permissão USAGE no schema
- Falta de permissão SELECT nas tabelas
- Problema com grant do tablespace
- Problemas com roles/memberships

## ✅ Começar agora

1. Prepare credenciais em `secrets/wfdb02_user_journey.txt`
2. Execute: `python3 validation/diagnose_journey_permissions.py`
3. Revise os problemas encontrados
4. Aplique as correções SQL recomendadas
5. Re-execute para validar

Veja [DIAGNOSE_CHECKLIST.md](DIAGNOSE_CHECKLIST.md) para instruções passo a passo.
