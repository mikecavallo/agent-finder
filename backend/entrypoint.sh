#!/bin/bash

# Run database migrations
python -c "from app.database import create_db_and_tables; create_db_and_tables()"

# Start the Uvicorn server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug