# CoinMarketCap Web3 AI Service

This directory contains the independent FastAPI AI service for the project.

The service receives AI chat requests from the Vue frontend, retrieves project snippets through local RAG, calls structured market tools backed by the Spring Boot API, and then calls a DeepSeek or OpenAI-compatible Chat Completions API.

## Features

- `GET /api/ai/health` checks service status and whether an API key is configured.
- `POST /api/ai/chat` accepts chat requests and returns model responses, RAG sources, and tool calls.
- `POST /api/ai/rag/search` previews project files that would be used as RAG context.
- `GET /api/ai/tools` lists available market tools.
- `POST /api/ai/tools/run` runs one market tool or auto-selects tools from a query.
- Reads project market data from `/api/coins`, `/api/coins/{coinId}`, `/api/coins/{coinId}/history?days=7`, `/api/fear-greed`, and search endpoints.
- Supports `DEEPSEEK_API_KEY` or a generic `AI_API_KEY`.
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

SPRING_API_BASE_URL=http://localhost:8080/api
SPRING_API_TIMEOUT_SECONDS=10

RAG_ENABLED=true
RAG_ROOT_PATH=
RAG_INCLUDE_PATHS=README.md,fastapi-ai,src/main/java,src/main/resources,frontend/coin-market-web/src,scripts
RAG_EXCLUDE_DIRS=.git,.idea,.vscode,.mvn,.venv,venv,target,node_modules,dist,__pycache__
RAG_MAX_SOURCES=5

MARKET_TOOLS_ENABLED=true
MARKET_TOOL_DEFAULT_HISTORY_DAYS=7
MARKET_TOOL_MAX_HISTORY_DAYS=30
MARKET_TOOL_MAX_CONTEXT_CHARS=8000
```

If both `AI_API_KEY` and `DEEPSEEK_API_KEY` are set, `AI_API_KEY` takes priority.

## Local Startup

```powershell
cd fastapi-ai
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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
```

## API

```text
GET  /api/ai/health
POST /api/ai/chat
POST /api/ai/rag/search
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

Tool run example:

```json
{
  "query": "Analyze BTC for the last 14 days."
}
```
