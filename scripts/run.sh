#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo " Starting Lenny Growth Assistant Environment Check"
echo "=================================================="

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
  echo "ERROR: Docker is not running. Please start Docker engine and retry."
  exit 1
fi

# Check Ollama status on localhost
echo "==> Checking Ollama status..."
OLLAMA_HOST="${OLLAMA_BASE_URL:-http://localhost:11434}"
if curl -s --connect-timeout 3 "$OLLAMA_HOST/api/tags" > /dev/null; then
  echo "✓ Ollama service is reachable at $OLLAMA_HOST"
else
  echo "⚠️ WARNING: Ollama service not detected at $OLLAMA_HOST."
  echo "    If using local LLM inference, run 'ollama serve' and 'ollama pull llama3.2'."
fi

# Initialize .env file
if [ ! -f .env ]; then
  echo "==> Copying .env.example to .env..."
  cp .env.example .env
fi

# Bring up Docker services
echo "==> Building and starting containerized services..."
docker-compose up -d --build

# Wait for backend health check
echo "==> Waiting for backend container readiness..."
MAX_ATTEMPTS=30
COUNT=0
# Note: we grep for status healthy or ok, to support both standard and custom health schemas
until curl -s http://localhost:8000/api/v1/health | grep -qE '"status":\s*"(ok|healthy)"' || [ $COUNT -eq $MAX_ATTEMPTS ]; do
  sleep 2
  COUNT=$((COUNT + 1))
  echo "    Waiting for API ($COUNT/$MAX_ATTEMPTS)..."
done

if [ $COUNT -eq $MAX_ATTEMPTS ]; then
  echo "ERROR: Backend service failed to become healthy."
  docker-compose logs backend
  exit 1
fi

echo "✓ Backend API healthy."

# Run auto-ingestion check
echo "==> Verifying vector store database state..."
docker-compose exec -T backend python -c "
from app.db.session import SessionLocal
from app.models.models import TranscriptChunk
db = SessionLocal()
count = db.query(TranscriptChunk).count()
print(f'CHUNK_COUNT={count}')
db.close()
" > /tmp/chunk_check.txt || true

# If the command failed inside docker-compose (e.g. SessionLocal / models structure mismatch),
# let's fallback to executing via the proper paths in app
if [ ! -f /tmp/chunk_check.txt ] || ! grep -q "CHUNK_COUNT" /tmp/chunk_check.txt; then
  docker-compose exec -T backend python -c "
from app.core.database import AsyncSessionLocal
from app.models.schema import TranscriptChunk
import asyncio
async def get_count():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import func, select
        res = await db.execute(select(func.count(TranscriptChunk.id)))
        print(f'CHUNK_COUNT={res.scalar()}')
asyncio.run(get_count())
" > /tmp/chunk_check.txt || true
fi

CHUNK_COUNT=$(grep CHUNK_COUNT /tmp/chunk_check.txt | cut -d'=' -f2 || echo "0")
if [ "${CHUNK_COUNT:-0}" -eq 0 ]; then
  echo "==> Database empty. Triggering automated ingestion sequence..."
  docker-compose exec -T backend python -m app.ingestion.ingest_transcripts
else
  echo "✓ Vector store populated with $CHUNK_COUNT chunks."
fi

echo "=================================================="
echo " 🎉 Lenny Growth Assistant ready!"
echo "    UI:  http://localhost:3000"
echo "    API: http://localhost:8000/docs"
echo "=================================================="
