#!/bin/bash

# Script de backup automatizado
set -e

# Configurações
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Criar diretório de backup
mkdir -p "$BACKUP_DIR/$TIMESTAMP"

# Backup PostgreSQL
backup_postgres() {
    log "Iniciando backup do PostgreSQL..."
    
    if [ -z "$DATABASE_URL" ]; then
        error "DATABASE_URL não configurada"
        return 1
    fi
    
    # Extrair informações da URL
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\(.*\)/\1/p')
    DB_USER=$(echo $DATABASE_URL | sed -n 's/postgresql:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DATABASE_URL | sed -n 's/postgresql:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    
    export PGPASSWORD=$DB_PASS
    
    # Backup completo
    pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        --verbose --no-owner --no-acl \
        -f "$BACKUP_DIR/$TIMESTAMP/postgres_full.sql"
    
    # Backup só estrutura
    pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        --schema-only --verbose --no-owner --no-acl \
        -f "$BACKUP_DIR/$TIMESTAMP/postgres_schema.sql"
    
    # Comprimir
    gzip "$BACKUP_DIR/$TIMESTAMP/postgres_full.sql"
    gzip "$BACKUP_DIR/$TIMESTAMP/postgres_schema.sql"
    
    log "Backup PostgreSQL concluído"
}

# Backup Redis
backup_redis() {
    log "Iniciando backup do Redis..."
    
    if [ -f "/data/redis/dump.rdb" ]; then
        cp /data/redis/dump.rdb "$BACKUP_DIR/$TIMESTAMP/redis_dump.rdb"
        gzip "$BACKUP_DIR/$TIMESTAMP/redis_dump.rdb"
        log "Backup Redis concluído"
    else
        warning "Arquivo Redis dump.rdb não encontrado"
    fi
}

# Backup ChromaDB
backup_chromadb() {
    log "Iniciando backup do ChromaDB..."
    
    if [ -d "/data/chroma" ]; then
        tar -czf "$BACKUP_DIR/$TIMESTAMP/chromadb.tar.gz" -C /data chroma
        log "Backup ChromaDB concluído"
    else
        warning "Diretório ChromaDB não encontrado"
    fi
}

# Upload para S3
upload_to_s3() {
    if [ -n "$S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
        log "Fazendo upload para S3..."
        
        aws s3 cp "$BACKUP_DIR/$TIMESTAMP" \
            "s3://$S3_BUCKET/backups/$TIMESTAMP" \
            --recursive
        
        log "Upload para S3 concluído"
    else
        warning "S3 não configurado, mantendo apenas backup local"
    fi
}

# Limpeza de backups antigos
cleanup_old_backups() {
    log "Removendo backups antigos..."
    
    # Local
    find "$BACKUP_DIR" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true
    
    # S3
    if [ -n "$S3_BUCKET" ] && [ -n "$AWS_ACCESS_KEY_ID" ]; then
        aws s3 ls "s3://$S3_BUCKET/backups/" | \
        while read -r line; do
            createDate=$(echo $line | awk '{print $1" "$2}')
            createDate=$(date -d "$createDate" +%s)
            olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
            if [[ $createDate -lt $olderThan ]]; then
                fileName=$(echo $line | awk '{print $4}')
                if [ ! -z "$fileName" ]; then
                    aws s3 rm "s3://$S3_BUCKET/backups/$fileName" --recursive
                fi
            fi
        done
    fi
    
    log "Limpeza concluída"
}

# Função principal
main() {
    log "=== Iniciando processo de backup ==="
    
    # Executar backups
    backup_postgres
    backup_redis
    backup_chromadb
    
    # Criar arquivo de metadados
    cat > "$BACKUP_DIR/$TIMESTAMP/metadata.json" <<EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "components": ["postgres", "redis", "chromadb"],
    "retention_days": $RETENTION_DAYS,
    "size": "$(du -sh $BACKUP_DIR/$TIMESTAMP | cut -f1)"
}
EOF
    
    # Upload
    upload_to_s3
    
    # Limpeza
    cleanup_old_backups
    
    log "=== Backup concluído com sucesso ==="
}

# Executar
main