#!/bin/bash
# ==============================================================================
# ArogyaSaathi Backend Runner Script
# Starts FastAPI gateway, TimescaleDB, PostGIS, pgvector, Redis, and MinIO
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo " ArogyaSaathi: Frontline Healthcare & Public Health Backend"
echo "=================================================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Mode check: Docker or Local
if [ "$1" == "--docker" ]; then
    echo "Starting full backend stack with Docker..."
    docker compose up --build -d
    echo "Services running:"
    docker compose ps
    echo "API docs available at: http://localhost:8000/docs"
elif [ "$1" == "--test" ]; then
    echo "Running Phase 1 Verification Suite..."
    python3 tests/verify_phase1.py
else
    echo "Starting FastAPI gateway locally..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
