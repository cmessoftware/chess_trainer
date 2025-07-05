sqlite3 db.sqlite .dump > dump.sql
psql -h localhost -U user -d appdb -f dump.sql
#   echo "Importing new games..."
#!/bin/bash
#   python /app/src/scripts/import_games.py "$@"
#!/bin/bash
# Script to migrate SQLite database to PostgreSQL
set -e
DB_FILE="/app/src/data/chess_trainer.db"
PG_HOST="localhost
PG_PORT="5432"
PG_USER="user"
PG_DB="appdb"
PG_PASSWORD="password"
export PGPASSWORD="$PG_PASSWORD"
if [ ! -f "$DB_FILE" ]; then
    echo "❌ Database file $DB_FILE not found."
    exit 1
fi
echo "🔄 Migrating SQLite database to PostgreSQL..."
sqlite3 "$DB_FILE" .dump | psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB"
echo "✅ Migration completed successfully."
