#!/bin/bash

# Função para comparar conteúdo de arquivos e escolher o mais completo
# Uso: compare_content arquivo1 arquivo2
# Retorna: 1 se arquivo1 for mais completo, 2 se arquivo2 for mais completo, 0 se iguais
compare_content() {
    local file1="$1"
    local file2="$2"
    
    # Se um dos arquivos não existir, retorna o que existe
    if [ ! -f "$file1" ] && [ -f "$file2" ]; then
        echo 2
        return
    elif [ -f "$file1" ] && [ ! -f "$file2" ]; then
        echo 1
        return
    elif [ ! -f "$file1" ] && [ ! -f "$file2" ]; then
        echo 0
        return
    fi
    
    # Verificar tamanho dos arquivos
    local size1=$(wc -c < "$file1")
    local size2=$(wc -c < "$file2")
    
    # Se os tamanhos forem muito diferentes, o maior provavelmente tem mais conteúdo
    local size_diff=$((size1 - size2))
    if [ "${size_diff#-}" -gt 500 ]; then  # Diferença absoluta > 500 bytes
        if [ $size1 -gt $size2 ]; then
            echo 1
            return
        else
            echo 2
            return
        fi
    fi
    
    # Contar linhas não vazias para medir complexidade
    local lines1=$(grep -v '^\s*$' "$file1" | wc -l)
    local lines2=$(grep -v '^\s*$' "$file2" | wc -l)
    
    # Se a diferença de linhas for significativa
    local lines_diff=$((lines1 - lines2))
    if [ "${lines_diff#-}" -gt 5 ]; then  # Diferença absoluta > 5 linhas
        if [ $lines1 -gt $lines2 ]; then
            echo 1
            return
        else
            echo 2
            return
        fi
    fi
    
    # Verificar datas de modificação como critério final
    if [ "$file1" -nt "$file2" ]; then
        echo 1
    elif [ "$file2" -nt "$file1" ]; then
        echo 2
    else
        # Se tudo mais for igual, considere os arquivos equivalentes
        echo 0
    fi
}

# Função para copiar arquivos com base em conteúdo e data
# Uso: smart_copy arquivo_origem arquivo_destino [force]
# O parâmetro force, se presente, força a cópia mesmo se o destino for mais completo
smart_copy() {
    local source="$1"
    local dest="$2"
    local force="$3"
    
    # Se o arquivo de origem não existir, não fazer nada
    if [ ! -f "$source" ]; then
        echo "  Origem não encontrada: $source"
        return
    fi
    
    # Criar diretório de destino se não existir
    mkdir -p "$(dirname "$dest")"
    
    # Se o arquivo de destino não existir, copiar diretamente
    if [ ! -f "$dest" ]; then
        echo "  Copiando $source para $dest"
        cp "$source" "$dest"
        return
    fi
    
    # Se force estiver definido, sobrescrever
    if [ "$force" = "true" ]; then
        echo "  Forçando cópia de $source para $dest"
        cp "$source" "$dest"
        return
    fi
    
    # Comparar conteúdo
    local comparison=$(compare_content "$source" "$dest")
    
    if [ "$comparison" = "1" ]; then
        echo "  Atualizando $dest (origem tem mais conteúdo)"
        cp "$source" "$dest"
    elif [ "$comparison" = "2" ]; then
        echo "  Mantendo $dest (destino tem mais conteúdo)"
    else
        # Se forem equivalentes, verificar data
        if [ "$source" -nt "$dest" ]; then
            echo "  Atualizando $dest (origem é mais recente)"
            cp "$source" "$dest"
        else
            echo "  Mantendo $dest (destino é mais recente ou igual)"
        fi
    fi
}

# Exemplo de uso
# smart_copy "README.md" "template/README.md"

# Ponto de entrada principal do script
if [ "$#" -lt 2 ]; then
    echo "Uso: $0 <arquivo_origem> <arquivo_destino> [force]"
    echo "  - arquivo_origem: Caminho para o arquivo de origem"
    echo "  - arquivo_destino: Caminho para o arquivo de destino"
    echo "  - force: (opcional) Se 'true', força a cópia mesmo se o destino for mais completo"
    exit 1
fi

source="$1"
dest="$2"
force="$3"

# Executar a função smart_copy com os argumentos fornecidos
smart_copy "$source" "$dest" "$force"
