# PostgreSQL Database Clone System v2.0

Sistema completo e profissional para clonagem de bancos de dados PostgreSQL com preservação total de permissões, tablespaces, roles e todas as estruturas.

## 🎯 Características

### ✨ Funcionalidades Principais

- **Clonagem Completa**: Copia estrutura, dados, índices, constraints, triggers
- **Preservação de Permissões**: Mantém todas as permissões de usuários e roles
- **Suporte a Tablespaces**: Respeita configurações de tablespace personalizados
- **Múltiplos Usuários**: Tenta conectar com múltiplas credenciais automaticamente
- **Validação Automática**: Verifica integridade da clonagem ao final
- **Tratamento de Erros**: Sistema robusto com try/except em todas as funções
- **Logging Completo**: Rastreamento detalhado de todas as operações
- **Configuração JSON**: Configuração simples e clara via arquivo JSON

### 🛡️ Segurança e Robustez

- Validação completa de parâmetros
- Tratamento de exceções em todas as funções
- Retorno de `False` em caso de erro (conforme solicitado)
- Documentação completa em reStructuredText
- Doctests em todas as funções públicas
- Suporte a SSL/TLS configurável

## 📋 Requisitos

### Sistema Operacional
- Linux (testado em Ubuntu, Debian, Fedora, Arch)
- Python 3.12 ou superior

### Dependências Python
```bash
pip install psycopg2-binary sqlalchemy