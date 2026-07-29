#!/bin/bash

# DATABASE_URL not set? settings.py defaults to sqlite:///app/backend/database/papers.db
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8080}"
