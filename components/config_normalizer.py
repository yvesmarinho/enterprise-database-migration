#!/usr/bin/env python3
"""
Config Normalizer for PostgreSQL Migration
==========================================

Utilitário para normalizar acesso aos dados de configuração dos arquivos JSON.
Garante compatibilidade entre diferentes estruturas de configuração.

Autor: GitHub Copilot
Data: 03/10/2025
"""

def normalize_server_config(config):
    """
    Normaliza configuração de servidor para um formato padrão.

    Args:
        config (dict): Configuração completa do servidor

    Returns:
        dict: Configuração normalizada
    """
    if not config or 'server' not in config:
        raise ValueError("Configuração inválida: seção 'server' não encontrada")

    server = config['server']
    auth = config.get('authentication', {})
    conn_settings = config.get('connection_settings', {})

    # Normalizar porta (usar 'port' ou 'port_direct', fallback para 5432)
    port = server.get('port', server.get('port_direct', 5432))

    # Normalizar SSL mode
    ssl_mode = server.get('ssl_mode', 'prefer')

    # Configuração normalizada
    normalized = {
        'host': server.get('host'),
        'port': port,
        'ssl_mode': ssl_mode,
        'user': auth.get('user'),
        'password': auth.get('password'),
        'connection_timeout': conn_settings.get('connection_timeout', 30),
        'query_timeout': conn_settings.get('query_timeout', 300),
        'max_connections': conn_settings.get('max_connections', 10),
        'pool_size': conn_settings.get('pool_size', 5)
    }

    # Validar campos obrigatórios
    required_fields = ['host', 'user', 'password']
    missing_fields = [field for field in required_fields if not normalized.get(field)]

    if missing_fields:
        raise ValueError(f"Campos obrigatórios faltando: {', '.join(missing_fields)}")

    return normalized

def get_connection_string(config, database='postgres'):
    """
    Gera string de conexão PostgreSQL normalizada.

    Args:
        config (dict): Configuração completa do servidor
        database (str): Nome do banco de dados

    Returns:
        str: String de conexão PostgreSQL
    """
    norm_config = normalize_server_config(config)

    return (
        f"host={norm_config['host']} "
        f"port={norm_config['port']} "
        f"dbname={database} "
        f"user={norm_config['user']} "
        f"password={norm_config['password']} "
        f"sslmode={norm_config['ssl_mode']} "
        f"connect_timeout={norm_config['connection_timeout']}"
    )

def get_sqlalchemy_url(config, database='postgres'):
    """
    Gera URL SQLAlchemy normalizada.

    Args:
        config (dict): Configuração completa do servidor
        database (str): Nome do banco de dados

    Returns:
        str: URL SQLAlchemy
    """
    norm_config = normalize_server_config(config)

    return (
        f"postgresql://"
        f"{norm_config['user']}:{norm_config['password']}@"
        f"{norm_config['host']}:{norm_config['port']}/"
        f"{database}"
        f"?sslmode={norm_config['ssl_mode']}"
    )

def validate_config_compatibility(source_config, dest_config):
    """
    Valida compatibilidade entre configurações de origem e destino.

    Args:
        source_config (dict): Configuração do servidor origem
        dest_config (dict): Configuração do servidor destino

    Returns:
        tuple: (is_valid, issues_list)
    """
    issues = []

    try:
        source_norm = normalize_server_config(source_config)
        dest_norm = normalize_server_config(dest_config)

        # Verificar se são o mesmo servidor
        if (source_norm['host'] == dest_norm['host'] and
            source_norm['port'] == dest_norm['port']):
            issues.append("⚠️ Origem e destino são o mesmo servidor!")

        # Verificar credenciais
        if source_norm['user'] != dest_norm['user']:
            issues.append(f"ℹ️ Usuários diferentes: {source_norm['user']} → {dest_norm['user']}")

        return len(issues) == 0 or "⚠️" not in str(issues), issues

    except Exception as e:
        issues.append(f"❌ Erro na validação: {e}")
        return False, issues

# Exemplos de uso
if __name__ == "__main__":
    print("🧪 Testando Config Normalizer...")

    # Teste básico seria executado aqui
    print("✅ Config Normalizer carregado com sucesso!")
