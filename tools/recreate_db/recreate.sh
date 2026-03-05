#!/bin/bash
# Script de conveniência para executar o recreate_database.py

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SECRETS_DIR="$SCRIPT_DIR/../../secrets"

echo "========================================"
echo "Database Recreator - Script Helper"
echo "========================================"
echo ""

# Função para listar configs disponíveis
list_configs() {
    echo "Arquivos de configuração disponíveis em secrets/:"
    echo ""
    ls -1 "$SECRETS_DIR"/*.json 2>/dev/null | while read -r file; do
        basename "$file"
    done
    echo ""
}

# Função para executar recriação
run_recreate() {
    local config="$1"
    local database="$2"
    local force="$3"

    # Adiciona caminho completo se não tiver
    if [[ ! "$config" =~ ^/ ]]; then
        config="$SECRETS_DIR/$config"
    fi

    # Verifica se arquivo existe
    if [ ! -f "$config" ]; then
        echo "❌ Erro: Arquivo de configuração não encontrado: $config"
        exit 1
    fi

    # Monta comando
    cmd="python3 $SCRIPT_DIR/recreate_database.py --config $config --database $database --verbose"

    if [ "$force" = "true" ]; then
        cmd="$cmd --force"
    fi

    echo "Executando: $cmd"
    echo ""

    eval "$cmd"
}

# Parse de argumentos
case "${1:-}" in
    list|ls|-l)
        list_configs
        ;;
    help|-h|--help)
        echo "Uso: $0 [comando] [opções]"
        echo ""
        echo "Comandos:"
        echo "  list, ls         Lista arquivos de configuração disponíveis"
        echo "  help             Mostra esta ajuda"
        echo "  [sem comando]    Modo interativo"
        echo ""
        echo "Modo direto:"
        echo "  $0 <config.json> <database> [--force]"
        echo ""
        echo "Exemplos:"
        echo "  $0 list"
        echo "  $0 mysql_config.json perfexcrm_db"
        echo "  $0 postgresql_source_config.json app_workforce --force"
        ;;
    *)
        # Modo direto
        if [ ! -z "${1:-}" ] && [ ! -z "${2:-}" ]; then
            force="false"
            if [ "${3:-}" = "--force" ]; then
                force="true"
            fi
            run_recreate "$1" "$2" "$force"
        else
            # Modo interativo
            echo "=== MODO INTERATIVO ==="
            echo ""
            list_configs

            read -p "Nome do arquivo de config (ou caminho completo): " config
            read -p "Nome do banco de dados: " database
            read -p "Forçar desconexão de clientes? (s/N): " force_input

            force="false"
            if [[ "$force_input" =~ ^[Ss]$ ]]; then
                force="true"
            fi

            echo ""
            run_recreate "$config" "$database" "$force"
        fi
        ;;
esac
