#!/usr/bin/env python3
"""
Script de teste para verificar o carregamento de configurações.

Testa se as funções de carregamento de configuração estão funcionando
corretamente para MySQL e PostgreSQL.
"""

from setup_database_user_permissions import (
    extract_connection_info,
    get_default_config_path,
    load_config_file,
)


def test_mysql_config():
    """Testa carregamento de configuração MySQL."""
    print('=' * 70)
    print('TESTE DE CONFIGURAÇÃO MYSQL')
    print('=' * 70)

    mysql_path = get_default_config_path('mysql')
    print(f'📂 Caminho padrão MySQL: {mysql_path}')

    if not mysql_path:
        print('❌ Arquivo de configuração MySQL não encontrado')
        return False

    config = load_config_file(mysql_path)
    if not config:
        print('❌ Falha ao carregar configuração MySQL')
        return False

    conn_info = extract_connection_info(config, 'mysql')
    if not conn_info:
        print('❌ Falha ao extrair informações de conexão MySQL')
        return False

    print('\n✅ Conexão MySQL extraída com sucesso:')
    print(f'   • Host: {conn_info["host"]}')
    print(f'   • Porta: {conn_info["port"]}')
    print(f'   • Usuário: {conn_info["admin_user"]}')
    print(f'   • Senha: {"*" * len(conn_info["admin_password"])} (oculta)')

    return True


def test_postgresql_config():
    """Testa carregamento de configuração PostgreSQL."""
    print()
    print('=' * 70)
    print('TESTE DE CONFIGURAÇÃO POSTGRESQL')
    print('=' * 70)

    pg_path = get_default_config_path('postgresql')
    print(f'📂 Caminho padrão PostgreSQL: {pg_path}')

    if not pg_path:
        print('❌ Arquivo de configuração PostgreSQL não encontrado')
        return False

    config = load_config_file(pg_path)
    if not config:
        print('❌ Falha ao carregar configuração PostgreSQL')
        return False

    conn_info = extract_connection_info(config, 'postgresql')
    if not conn_info:
        print('❌ Falha ao extrair informações de conexão PostgreSQL')
        return False

    print('\n✅ Conexão PostgreSQL extraída com sucesso:')
    print(f'   • Host: {conn_info["host"]}')
    print(f'   • Porta: {conn_info["port"]}')
    print(f'   • Usuário: {conn_info["admin_user"]}')
    print(f'   • Senha: {"*" * len(conn_info["admin_password"])} (oculta)')

    return True


def main():
    """Função principal."""
    print('\n🔍 TESTE DE CARREGAMENTO DE CONFIGURAÇÕES\n')

    mysql_ok = test_mysql_config()
    pg_ok = test_postgresql_config()

    print()
    print('=' * 70)
    print('RESUMO DOS TESTES')
    print('=' * 70)
    print(f'MySQL: {"✅ OK" if mysql_ok else "❌ FALHOU"}')
    print(f'PostgreSQL: {"✅ OK" if pg_ok else "❌ FALHOU"}')
    print('=' * 70)

    if mysql_ok and pg_ok:
        print('\n✅ Todos os testes passaram!')
        return 0
    else:
        print('\n❌ Alguns testes falharam')
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
