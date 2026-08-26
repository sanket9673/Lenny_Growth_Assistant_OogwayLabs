.PHONY: setup ingest start test logs stop clean

setup:
	@echo "==> Checking local dependencies..."
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting."; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || command -v docker >/dev/null 2>&1 || { echo "Docker Compose required. Aborting."; exit 1; }
	@if [ ! -f .env ]; then \
		echo "==> Creating .env from .env.example..."; \
		cp .env.example .env; \
	else \
		echo "==> .env file already exists."; \
	fi
	@echo "==> Setup complete."

ingest:
	@echo "==> Running vector ingestion script..."
	docker-compose exec backend python -m app.ingestion.ingest_transcripts

start:
	@echo "==> Starting containers..."
	docker-compose up -d --build
	@echo "==> Application running at http://localhost:3000"

test:
	@echo "==> Running backend test suite..."
	docker-compose exec backend pytest -v --tb=short tests/

logs:
	docker-compose logs -f

stop:
	docker-compose down

clean:
	docker-compose down -v
	rm -rf backend/__pycache__ backend/app/__pycache__
