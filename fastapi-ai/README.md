# CoinMarketCap Web3 AI Service

This directory contains the independent FastAPI AI service for the project.

The service receives AI chat requests from the Vue frontend, reads market data from the Spring Boot API, builds a market context, and then calls a DeepSeek or OpenAI-compatible Chat Completions API.

## Features

- `GET /api/ai/health` checks service status and whether an API key is configured.
- `POST /api/ai/chat` accepts chat requests and returns model responses.
- Reads project market data from `/api/coins`, `/api/coins/{coinId}/history?days=7`, and `/api/fear-greed`.
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
DEEPSEEK_API_KEY=your_real_api_key

AI_TIMEOUT_SECONDS=30
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=800
AI_STREAM=false
AI_THINKING_ENABLED=true
AI_REASONING_EFFORT=high

SPRING_API_BASE_URL=http://localhost:8080/api
SPRING_API_TIMEOUT_SECONDS=10
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

## API

```text
GET  /api/ai/health
POST /api/ai/chat
```

Request example:

```json
{
  "message": "Please analyze BTC using the project market data.",
  "temperature": 0.3,
  "max_tokens": 800
}
```
