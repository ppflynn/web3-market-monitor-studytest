# CoinMarketCap Web3 AI Service

This directory contains the independent FastAPI AI service for the project.

The service receives AI chat requests from the Vue frontend, retrieves project snippets through Embedding + Chroma RAG, calls structured market tools backed by the Spring Boot API, and then calls a DeepSeek or OpenAI-compatible Chat Completions API.

## Features

- `GET /api/ai/health` checks service status and whether an API key is configured.
- `POST /api/ai/chat` accepts chat requests and returns model responses, RAG sources, and tool calls.
- `POST /api/ai/rag/search` previews Chroma matches that would be used as RAG context.
- `POST /api/ai/rag/reindex?reset=true` reads configured project files, generates embeddings, and writes chunks to Chroma.
- `GET /api/ai/tools` lists available market tools.
- `POST /api/ai/tools/run` runs one market tool or auto-selects tools from a query.
- Reads project market data from `/api/coins`, `/api/coins/{coinId}`, `/api/coins/{coinId}/history?days=7`, `/api/fear-greed`, and search endpoints.
- Supports `DEEPSEEK_API_KEY` or a generic `AI_API_KEY`.
- Supports separate `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` settings when the chat model provider does not expose `/embeddings`.
- Persists RAG chunks in a Chroma collection with source metadata such as `filename`, `chunk_index`, `path`, `content_hash`, and `source_type`.
- Keeps real model provider keys outside the repository.

## Configuration

Copy the example file and fill in your own provider key:

```powershell
cd fastapi-ai
copy .env.example .env
```

Example values:

```env
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-pro
DEEPSEEK_API_KEY=

AI_TIMEOUT_SECONDS=30
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=800
AI_STREAM=false
AI_THINKING_ENABLED=true
AI_REASONING_EFFORT=high

EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_TIMEOUT_SECONDS=30
EMBEDDING_BATCH_SIZE=48

SPRING_API_BASE_URL=http://localhost:8080/api
SPRING_API_TIMEOUT_SECONDS=10

RAG_ENABLED=true
RAG_ROOT_PATH=
RAG_INCLUDE_PATHS=README.md,fastapi-ai,src/main/java,src/main/resources,frontend/coin-market-web/src,scripts
RAG_EXCLUDE_DIRS=.git,.idea,.vscode,.mvn,.venv,venv,target,node_modules,dist,__pycache__
RAG_MAX_FILES=120
RAG_MAX_FILE_BYTES=200000
RAG_CHUNK_CHARS=1400
RAG_SNIPPET_CHARS=1200
RAG_MAX_SOURCES=5
RAG_MIN_SCORE=1.2
RAG_REINDEX_ON_START=false
CHROMA_PERSIST_DIR=./chroma-data
CHROMA_COLLECTION_NAME=project_rag

MARKET_TOOLS_ENABLED=true
MARKET_TOOL_DEFAULT_HISTORY_DAYS=7
MARKET_TOOL_MAX_HISTORY_DAYS=30
MARKET_TOOL_MAX_CONTEXT_CHARS=8000
```

If both `AI_API_KEY` and `DEEPSEEK_API_KEY` are set, `AI_API_KEY` takes priority.

If `EMBEDDING_API_KEY` is empty, the service falls back to `AI_API_KEY` / `DEEPSEEK_API_KEY` for embeddings.

## Local Startup

```powershell
cd fastapi-ai
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Build or rebuild the local Chroma index after the first startup or after source changes:

```powershell
python -m app.scripts.ingest_rag
```

Local URLs:

```text
http://localhost:8000/
http://localhost:8000/docs
http://localhost:8000/api/ai/health
```

## Docker Compose

The root `docker-compose.yml` includes an `ai` service. Copy the root `.env.example` to `.env`, fill in a real AI key, and start the whole stack:

```powershell
copy .env.example .env
docker compose up --build -d
```

Inside Docker Compose, the AI service reads Spring Boot data through:

```text
http://backend:8080/api
```

Docker Compose also mounts the project into the AI container as read-only:

```text
./:/workspace:ro
```

and sets:

```text
RAG_ROOT_PATH=/workspace
CHROMA_PERSIST_DIR=/data/chroma
```

Chroma data is stored in the `coinmarket-chroma-data` Docker volume, while the project mount remains read-only.

Rebuild the RAG index inside Docker:

```powershell
docker exec coinmarket-ai python -m app.scripts.ingest_rag
```

## API

```text
GET  /api/ai/health
POST /api/ai/chat
POST /api/ai/rag/search
POST /api/ai/rag/reindex?reset=true
GET  /api/ai/tools
POST /api/ai/tools/run
```

Request example:

```json
{
  "message": "Please analyze BTC using the project market data.",
  "temperature": 0.3,
  "max_tokens": 800
}
```

RAG search example:

```json
{
  "query": "How does the AI chat endpoint use Spring Boot market data?"
}
```

RAG reindex example:

```text
POST /api/ai/rag/reindex?reset=true
```

Ingestion flow:

```text
Read RAG_INCLUDE_PATHS
  -> split files into chunks
  -> call an OpenAI-compatible Embeddings API
  -> write chunks and metadata to Chroma
  -> query Chroma during /api/ai/chat and /api/ai/rag/search
```

Tool run example:

```json
{
  "query": "Analyze BTC for the last 14 days."
}
```
