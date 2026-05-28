# Docker 部署指南

本项目已经整理为 Docker Compose 部署方式，可以一次启动 MySQL、Redis、Spring Boot 后端、Python 数据采集脚本、FastAPI AI 服务和 Vue 前端。

## 服务组成

```text
mysql      MySQL 8 数据库
redis      Redis 7 缓存服务
backend    Spring Boot REST API
collector  Python 行情数据采集脚本
ai         FastAPI AI 智能分析服务
frontend   Vue 前端 + Nginx
```

## 快速启动

克隆仓库后进入项目目录：

```powershell
git clone https://github.com/ppflynn/web3-market-monitor-studytest.git
cd web3-market-monitor-studytest
```

推荐先复制环境变量模板：

```powershell
copy .env.example .env
```

然后一键构建并启动：

```powershell
docker compose up --build -d
```

启动后访问：

```text
前端页面: http://localhost:3000
后端接口: http://localhost:8080
AI 服务: http://localhost:8000
AI 页面: http://localhost:3000/ai
MySQL: localhost:3307
Redis: localhost:6379
```

## 环境变量

`.env.example` 提供了一组可以直接运行的示例配置。

默认示例密码：

```text
CmkDb_2026_R9vQ7mT4zP8sL2nX
```

这是公开仓库中的演示默认值，不应作为生产环境密码。正式部署时请复制 `.env.example` 为 `.env` 并修改：

```text
MYSQL_ROOT_PASSWORD
DB_PASSWORD
SPRING_DATASOURCE_PASSWORD
SPRING_REDIS_HOST
SPRING_REDIS_PORT
DEEPSEEK_API_KEY
AI_API_KEY
EMBEDDING_API_KEY
EMBEDDING_BASE_URL
RAG_ENABLED
RAG_ROOT_PATH
RAG_REINDEX_ON_START
CHROMA_PERSIST_DIR
CHROMA_COLLECTION_NAME
MARKET_TOOLS_ENABLED
```

`.env` 已被 `.gitignore` 忽略，不会被提交。

AI 服务可以不配置真实 API Key 启动，但聊天接口会提示需要设置 Key。需要调用大模型时，请在本地 `.env` 中填写 `DEEPSEEK_API_KEY` 或 `AI_API_KEY`。

AI 服务默认启用本地项目 RAG 和结构化行情工具层。Docker Compose 会把项目目录只读挂载到 AI 容器的 `/workspace`，并设置 `RAG_ROOT_PATH=/workspace`。RAG 会按 `.env.example` 中的 `RAG_INCLUDE_PATHS` 和 `RAG_EXCLUDE_DIRS` 检索公开仓库源码，不会扫描 `.git`、`.env`、`node_modules`、`target`、`dist` 等目录。

当前 RAG 使用 Embedding + Chroma 持久化向量检索。需要调用 RAG 时，请确保 `.env` 中配置了可用的 `DEEPSEEK_API_KEY` / `AI_API_KEY`，或单独配置支持 OpenAI-compatible `/embeddings` 的 `EMBEDDING_API_KEY` 和 `EMBEDDING_BASE_URL`。

## 常用命令

查看服务状态：

```powershell
docker compose ps
```

查看全部日志：

```powershell
docker compose logs -f
```

查看单个服务日志：

```powershell
docker compose logs -f backend
docker compose logs -f collector
docker compose logs -f frontend
docker compose logs -f mysql
docker compose logs -f redis
docker compose logs -f ai
```

停止服务：

```powershell
docker compose down
```

停止服务但保留数据库数据卷：

```powershell
docker compose stop
```

重新启动：

```powershell
docker compose start
```

## 数据持久化

MySQL 数据保存在 Docker volume 中：

```text
coinmarket-mysql-data
```

Chroma 向量库数据保存在 Docker volume 中：

```text
coinmarket-chroma-data
```

执行 `docker compose down` 不会删除这些数据卷。若要连同数据库和 Chroma 数据一起清理：

```powershell
docker compose down -v
```

请谨慎执行 `-v`，它会删除数据库数据。

## 端口说明

```text
3000 -> frontend
8080 -> backend
8000 -> ai
3307 -> mysql
6379 -> redis
```

容器内部访问 MySQL 使用：

```text
mysql:3306
```

本机访问 MySQL 使用：

```text
localhost:3307
```

容器内部访问 Redis 使用：

```text
redis:6379
```

本机访问 Redis 使用：

```text
localhost:6379
```

容器内部访问 AI 服务使用：

```text
ai:8000
```

本机访问 AI 服务使用：

```text
localhost:8000
```

AI 容器内的 RAG 项目目录：

```text
/workspace
```

AI 容器内的 Chroma 持久化目录：

```text
/data/chroma
```

AI 调试接口：

```text
GET  http://localhost:8000/api/ai/tools
POST http://localhost:8000/api/ai/tools/run
POST http://localhost:8000/api/ai/rag/search
POST http://localhost:8000/api/ai/rag/reindex?reset=true
```

首次启动或源码变更后，重建 RAG 向量库：

```powershell
docker exec coinmarket-ai python -m app.scripts.ingest_rag
```

## 部署文件

```text
docker-compose.yml
Dockerfile
.dockerignore
scripts/Dockerfile
scripts/.dockerignore
frontend/coin-market-web/Dockerfile
frontend/coin-market-web/.dockerignore
frontend/coin-market-web/nginx.docker.conf
fastapi-ai/Dockerfile
fastapi-ai/.dockerignore
fastapi-ai/.env.example
```

## 注意事项

- 不要提交真实 `.env` 文件。
- 不要提交真实大模型 API Key。
- 公开仓库中的密码只是演示默认值，正式部署请修改。
- 如果本机已经有 MySQL 占用 `3307`，请在 `.env` 中修改 `MYSQL_PORT`。
- 如果本机已经有服务占用 `3000`、`8000` 或 `8080`，请在 `.env` 中修改 `FRONTEND_PORT`、`AI_PORT` 或 `BACKEND_PORT`。
