#!/bin/bash
set -e

# Start backend (FastAPI)
cd /app/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Serve frontend (static build) using simple HTTP server
cd /app/frontend-dist
python3 /app/spa_server.py 8080 /app/frontend-dist
