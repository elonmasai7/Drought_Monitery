#!/bin/bash

# Drought Warning System Backup Script
set -e

# Configuration
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"
MEDIA_BACKUP_FILE="$BACKUP_DIR/media_backup_$DATE.tar.gz"

echo "📦 Starting backup process..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Database backup
echo "🗄️  Backing up database..."
docker-compose exec -T db pg_dump -U ${DB_USER:-postgres} ${DB_NAME:-drought_warning_db} > $DB_BACKUP_FILE
echo "✅ Database backup saved to: $DB_BACKUP_FILE"

# Media files backup
echo "📁 Backing up media files..."
docker-compose exec -T web tar -czf - -C /app media/ > $MEDIA_BACKUP_FILE
echo "✅ Media backup saved to: $MEDIA_BACKUP_FILE"

# Clean up old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find $BACKUP_DIR -name "db_backup_*.sql" -type f -mtime +7 -delete
find $BACKUP_DIR -name "media_backup_*.tar.gz" -type f -mtime +7 -delete

echo "🎉 Backup completed successfully!"
echo "📊 Backup files:"
echo "  Database: $(du -h $DB_BACKUP_FILE | cut -f1) - $DB_BACKUP_FILE"
echo "  Media: $(du -h $MEDIA_BACKUP_FILE | cut -f1) - $MEDIA_BACKUP_FILE"
