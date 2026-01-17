#!/bin/bash
# ==============================================================================
# Atualiza Metabase v0.58.1 para v0.58.2+ (correção do bug de migrations)
# ==============================================================================

echo "🔄 Atualização do Metabase v0.58.1 → v0.58.2"
echo "=" * 60

# Verificar versões disponíveis
echo ""
echo "📦 Verificando versões disponíveis do Metabase..."
echo ""
echo "Versões recomendadas:"
echo "  - v0.58.2 (correção de bugs da v0.58.1)"
echo "  - v0.51.4 (LTS - Long Term Support, mais estável)"
echo ""

# Solicitar versão
read -p "Digite a versão desejada (ex: v0.58.2 ou v0.51.4): " VERSION

if [ -z "$VERSION" ]; then
    echo "❌ Versão não informada"
    exit 1
fi

echo ""
echo "⚠️  IMPORTANTE: Execute estes comandos NO SERVIDOR DOCKER REMOTO"
echo "=" * 60
echo ""
echo "1️⃣  Parar o container Metabase:"
echo "   docker-compose stop dashboard"
echo ""
echo "2️⃣  Atualizar a imagem no docker-compose.yml:"
echo "   Altere a linha:"
echo "     image: metabase/metabase:v0.58.1"
echo "   Para:"
echo "     image: metabase/metabase:$VERSION"
echo ""
echo "3️⃣  Fazer backup da imagem atual (opcional mas recomendado):"
echo "   docker tag metabase/metabase:v0.58.1 metabase/metabase:v0.58.1-backup"
echo ""
echo "4️⃣  Baixar nova versão:"
echo "   docker pull metabase/metabase:$VERSION"
echo ""
echo "5️⃣  Reiniciar com nova versão:"
echo "   docker-compose up -d dashboard"
echo ""
echo "6️⃣  Monitorar logs:"
echo "   docker-compose logs -f dashboard"
echo ""
echo "=" * 60
echo ""
echo "⚠️  Notas Importantes:"
echo "  • O banco de dados já está correto após a restauração"
echo "  • A versão $VERSION deve corrigir o bug do cast ::text para ::jsonb"
echo "  • As 33 migrações pendentes devem completar com sucesso"
echo "  • Se houver problemas, volte para v0.58.1-backup"
echo ""
echo "🔍 Para verificar versões disponíveis:"
echo "   https://hub.docker.com/r/metabase/metabase/tags"
