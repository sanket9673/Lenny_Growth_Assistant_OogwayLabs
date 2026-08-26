# The Lenny Growth Assistant

An enterprise-ready AI search assistant and artifact generation engine powered by Lenny Rachitsky's podcast transcript corpus.

## Quick Start (One-Command Setup)

Run the automated bootstrapping script:

```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

Or run via make:

```bash
make setup
make start
```

Access the frontend application at [http://localhost:3000](http://localhost:3000) and API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### Prerequisites
- Docker & Docker Compose (v2.0+)
- Python 3.11+ (for optional local non-Docker development)
- Ollama (Optional for zero-cost local LLM execution)

### Environment & Provider Configuration
Copy `.env.example` to `.env` and configure optional cloud credentials:

```bash
# Cloud Providers (Optional - System defaults to local Ollama if missing)
ANTHROPIC_API_KEY=sk-ant-xxx
GROQ_API_KEY=gsk_xxx

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=lenny_growth

# Ollama Endpoint
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Running Local LLMs with Ollama
1. Install Ollama: [ollama.ai](https://ollama.ai)
2. Pull the default model:
   ```bash
   ollama pull llama3.2
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```

### Testing & Operational Commands
Execute the test suite across the backend container:
```bash
make test
```

Inspect container streaming logs:
```bash
make logs
```

Clean database and volume mounts:
```bash
make clean
```

### Troubleshooting & FAQ
- **Q: Vector retrieval returns no results or throws refusal errors.**
  - **Solution:** Ensure the vector embedding index has been populated by executing `make ingest`.
- **Q: Local Ollama connection refused inside Docker.**
  - **Solution:** Verify Ollama is bound to host IP `0.0.0.0` or `127.0.0.1` and `OLLAMA_BASE_URL` is set to `http://host.docker.internal:11434`.
