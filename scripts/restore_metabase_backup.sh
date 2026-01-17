#!/bin/bash
# ==============================================================================
# Restaura backup do Metabase de 2026-01-16 09:31:54
# ==============================================================================

set -e  # Parar em caso de erro

BACKUP_FILE="/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-database-migration/temp/20260116_093154_postgresql_metabase_db.sql"
DB_HOST="wfdb02.vya.digital"
DB_USER="yves_marinho"
DB_NAME="metabase_db"

echo "🔄 Iniciando restauração do backup..."
echo "📁 Arquivo: $BACKUP_FILE"
echo "🗄️  Banco: $DB_NAME @ $DB_HOST"
echo ""

# 1. Aviso para parar o Metabase
echo "⚠️  IMPORTANTE: O container Metabase está no servidor externo!"
echo "⚠️  Você deve parar o Metabase manualmente antes de continuar:"
echo ""
echo "    No servidor Docker remoto, execute:"
echo "    docker-compose stop dashboard"
echo ""
echo "⚠️  Este processo irá DROPAR e RECRIAR o banco de dados metabase_db"
echo ""
echo "Pressione ENTER após parar o Metabase, ou Ctrl+C para cancelar..."
read

# 2. Dropar e recriar o banco
echo ""
echo "�️  Dropando banco existente (forçando desconexão de todas as sessões)..."
psql -h $DB_HOST -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME WITH (FORCE);"

echo "📦 Criando banco limpo..."
psql -h $DB_HOST -U $DB_USER -d postgres -c "
CREATE DATABASE $DB_NAME
    WITH TEMPLATE = template0
    OWNER = metabase_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;"

# 3. Restaurar o backup
echo ""
echo "📥 Restaurando backup (formato custom dump)..."
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME --verbose --no-owner --no-acl "$BACKUP_FILE" 2>&1 | grep -E "processing|creating|restoring" | tail -20

echo ""
echo "✅ Restauração concluída!"
echo ""
echo "📊 Verificando estado do banco..."
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT
    schemaname,
    COUNT(*) as total_tables
FROM pg_tables
WHERE schemaname = 'public'
GROUP BY schemaname;

SELECT COUNT(*) as total_migrations
FROM databasechangelog;
"

echo ""
echo "🚀 Reinicie o Metabase no servidor Docker remoto:"
echo "    docker-compose start dashboard"
