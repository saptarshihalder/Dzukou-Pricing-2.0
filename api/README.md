# Price Optim AI — FastAPI backend

## Quickstart

1. Install and run Ollama with the required model:

```bash
# Install Ollama (https://ollama.com/download)
ollama pull gemma3:4b
ollama serve  # Start the Ollama server
```

2. Create .env with your Postgres connection string (or use default). If Postgres is unreachable, the API will fallback to SQLite (`./priceoptim.db`):

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/priceoptim
# Optional: override the fallback SQLite path
# SQLITE_URL=sqlite+aiosqlite:///./priceoptim.db

# Optional: Ollama configuration (defaults shown)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

3. Install dependencies (uv recommended):

```
uv sync
```

Or using pip in the bundled venv:

```
. .venv/bin/activate
pip install -e .
```

4. Run the API:

```
fastapi dev api/main.py
```

The app exposes endpoints under `/routes/*`.

## Endpoints

- GET /routes/health
- POST /routes/start-scraping → { run_id }
- GET /routes/scraping-progress/{run_id}
- GET /routes/scraping-results/{run_id}
- GET /routes/runs/{run_id}/export.csv
- POST /routes/optimize-price
- POST /routes/optimize-batch
