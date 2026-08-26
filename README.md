# Lenny Growth Assistant 🚀

An agentic RAG system built on top of Lenny's Podcast transcripts for product strategy, growth frameworks, and career advice.

## 🏗️ Tech Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, AsyncPG, SQLAlchemy 2.0
- **Vector DB:** PostgreSQL 16 + `pgvector` (HNSW Indexing)
- **Embeddings:** FastEmbed (`BAAI/bge-small-en-v1.5`, 384 dimensions)
- **Frontend:** Vite, React, TypeScript, Tailwind CSS

## ⚡ Quick Start

### 1. Infrastructure Setup
Start PostgreSQL with pgvector:
```bash
docker compose up -d
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Run Ingestion Pipeline (CLI)
Index all markdown transcripts located in `data/transcripts/`:
```bash
python -m app.ingestion.cli
```

### 4. Run API Server & Test Suite
```bash
# Run tests
pytest -v

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Access interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs).
