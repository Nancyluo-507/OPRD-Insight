#!/bin/bash

if [ -z "$DATABASE_URL" ]; then
    DB_PATH="/data/papers.db"
    if [ ! -f "$DB_PATH" ]; then
        mkdir -p /data 2>/dev/null
    fi
    export DATABASE_URL="sqlite:///${DB_PATH}"
fi

exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8080}"
