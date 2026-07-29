#!/bin/bash
set -e

if [ -z "$DATABASE_URL" ]; then
    DB_SOURCE="/app/backend/database/papers.db"
    DB_TARGET="/data/papers.db"

    if [ ! -f "$DB_TARGET" ]; then
        mkdir -p /data
        if [ -f "$DB_SOURCE" ]; then
            cp "$DB_SOURCE" "$DB_TARGET"
            echo "Copied initial database to $DB_TARGET"
        else
            echo "No initial database found at $DB_SOURCE, starting fresh"
            touch "$DB_TARGET"
        fi
    fi

    export DATABASE_URL="sqlite:///${DB_TARGET}"
    echo "Using SQLite at ${DB_TARGET}"
else
    echo "Using env DATABASE_URL (PostgreSQL)"
fi

exec uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8080}"
