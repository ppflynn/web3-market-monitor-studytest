# CoinMarketCap Web3

这是一个加密货币行情监控项目，包含 Spring Boot 后端、Python 数据采集脚本、Vue 3 前端、Redis 缓存、FastAPI AI 服务和 Docker Compose 一键部署配置。

当前版本不包含 Android 客户端。Android 项目后续会作为独立客户端继续整理。

## 功能概览

- 采集主流加密货币实时行情数据
- 采集 Fear & Greed 指数
- 通过 Gate.io 现货 K 线接口采集部分币种的历史价格数据
- 在历史接口不可用时，使用实时价格快照持续补充历史价格点
- 保留 CoinGecko 历史价格接口作为可选数据源
- 将采集结果写入 MySQL
- 通过 Spring Boot 提供 REST API
- 使用 Redis 缓存币种列表和历史价格等高频读取数据
- 通过 Vue 前端展示币种列表、详情、历史价格图表和 Fear & Greed 指数
- 提供 FastAPI AI 服务，可读取项目行情数据并调用 DeepSeek / OpenAI 兼容大模型生成分析回答
- Vue 前端提供 AI 助手页面，并在币种详情页提供跳转入口
- 提供系统状态接口，展示采集数据量和最近更新时间
- Vue 首页展示系统状态卡片
- 支持 Docker Compose 一键启动完整运行环境

## 技术栈

### 后端

- Java 8
- Spring Boot 2.7.18
- Spring Web
- Spring Data JPA
- MySQL
- Spring Cache
- Redis
- Maven

### 数据采集

- Python
- requests
- PyMySQL

### 前端

- Vue 3
- Vite
- Vue Router
- Axios
- Element Plus
- ECharts / vue-echarts

### AI 服务

- FastAPI
- Uvicorn
- Pydantic Settings
- httpx
- DeepSeek / OpenAI 兼容 Chat Completions API

## 目录结构

```text
.
├─ src/main/java/com/example/coinmarket
│  ├─ config
│  ├─ controller
│  ├─ entity
│  ├─ repository
│  └─ service
├─ src/main/resources
│  └─ application.yml
├─ scripts
│  ├─ coin_collector.py
│  ├─ config.py
│  └─ requirements.txt
├─ frontend/coin-market-web
│  ├─ src
│  ├─ package.json
│  ├─ package-lock.json
│  ├─ vite.config.js
│  ├─ Dockerfile
│  ├─ .dockerignore
│  ├─ nginx.docker.conf
│  └─ nginx.conf
├─ fastapi-ai
│  ├─ app
│  ├─ requirements.txt
│  ├─ Dockerfile
│  ├─ .dockerignore
│  ├─ .env.example
│  └─ README.md
├─ docker-compose.yml
├─ Dockerfile
├─ .dockerignore
├─ DOCKER_GUIDE.md
├─ .mvn
├─ pom.xml
├─ mvnw.cmd
├─ .env.example
└─ README.md
```

## 数据流

```text
Market data:
External APIs
    -> Python collector
    -> MySQL
    -> Spring Boot API
    -> Redis cache
    -> Vue frontend

AI analysis:
Vue /ai page
    -> FastAPI AI service
    -> Spring Boot API
    -> MySQL / Redis market data
    -> DeepSeek / OpenAI-compatible LLM
```

## 环境变量

本仓库不会提交真实密码。请参考 `.env.example` 配置本地环境。

Spring Boot 后端使用：

```text
DB_URL
DB_USER
DB_PASSWORD
SPRING_REDIS_HOST
SPRING_REDIS_PORT
```

Python 采集脚本使用：

```text
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME
```

FastAPI AI 服务使用：

```text
AI_BASE_URL
AI_MODEL
DEEPSEEK_API_KEY
AI_API_KEY
AI_TIMEOUT_SECONDS
AI_TEMPERATURE
AI_MAX_TOKENS
AI_STREAM
AI_THINKING_ENABLED
AI_REASONING_EFFORT
SPRING_API_BASE_URL
SPRING_API_TIMEOUT_SECONDS
```

## 数据库

默认数据库名：

```text
coinmarketdb
```

初始化示例：

```sql
CREATE DATABASE coinmarketdb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

当前核心数据包括：

- 币种基础信息和实时价格
- 历史价格点，包括 K 线接口数据和实时价格快照兜底数据
- Fear & Greed 指数

## Docker 一键启动

克隆仓库：

```powershell
git clone https://github.com/ppflynn/web3-market-monitor-studytest.git
cd web3-market-monitor-studytest
```

推荐复制环境变量模板：

```powershell
copy .env.example .env
```

一键构建并启动 MySQL、Redis、后端、采集脚本、FastAPI AI 服务和前端：

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

查看服务状态：

```powershell
docker compose ps
```

查看日志：

```powershell
docker compose logs -f
```

停止服务：

```powershell
docker compose down
```

更多 Docker 使用说明见 [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)。

## 环境变量和密码

公开仓库中只提供可运行的示例默认值。当前示例数据库密码为：

```text
CmkDb_2026_R9vQ7mT4zP8sL2nX
```

这是公开演示配置，不应作为生产环境密码。正式部署时请复制 `.env.example` 为 `.env` 并修改：

```text
MYSQL_ROOT_PASSWORD
DB_PASSWORD
SPRING_DATASOURCE_PASSWORD
DEEPSEEK_API_KEY
AI_API_KEY
```

`.env` 已被 `.gitignore` 忽略，不会被提交。

## 本地开发启动方式

建议启动顺序：

```text
MySQL -> Python collector -> Spring Boot API -> Vue frontend
```

启用 Redis 缓存时，建议启动顺序为：

```text
MySQL -> Redis -> Python collector -> Spring Boot API -> FastAPI AI service -> Vue frontend
```

### 1. 安装 Python 依赖

```powershell
cd scripts
pip install -r requirements.txt
```

### 2. 运行数据采集脚本

```powershell
python coin_collector.py
```

### 3. 启动 Spring Boot 服务

```powershell
.\mvnw.cmd spring-boot:run
```

默认后端地址：

```text
http://localhost:8080
```

### 4. 启动 FastAPI AI 服务

```powershell
cd fastapi-ai
copy .env.example .env
# 编辑 .env，填入你自己的 DEEPSEEK_API_KEY 或 AI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

默认 AI 服务地址：

```text
http://localhost:8000
http://localhost:8000/docs
```

### 5. 启动 Vue 前端

```powershell
cd frontend\coin-market-web
npm install
npm run dev
```

默认前端地址：

```text
http://localhost:3000
```

开发环境下，前端 `/api` 请求会通过 Vite 代理到后端：

```text
http://localhost:8080
```

开发环境下，前端 `/api/ai` 请求会通过 Vite 代理到 FastAPI AI 服务：

```text
http://localhost:8000
```

## API 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/coins` | 获取币种列表 |
| GET | `/api/coins/{coinId}` | 获取币种详情 |
| GET | `/api/coins/{coinId}/history?days=7` | 获取历史价格 |
| GET | `/api/coins/search?keyword=btc` | 搜索币种 |
| GET | `/api/fear-greed` | 获取 Fear & Greed 指数 |
| GET | `/api/status` | 获取系统数据采集和运行状态 |
| GET | `/api/ai/health` | 获取 FastAPI AI 服务状态 |
| POST | `/api/ai/chat` | 调用 AI 助手，先读取项目行情数据，再请求大模型生成回答 |

## 当前状态

已完成：

- 后端基础 REST API
- MySQL 数据读取
- Redis 缓存
- 实时行情采集
- 历史价格采集
- Gate.io 现货 K 线历史数据源
- 实时价格快照兜底历史数据
- 历史价格请求状态日志
- CoinGecko 常见限流响应识别
- Fear & Greed 指数采集
- 系统状态 REST API
- Vue 前端基础展示
- Vue 首页系统状态卡片
- Vue AI 助手页面
- 币种详情页 AI 助手入口
- 前端开发代理配置
- FastAPI AI 服务
- FastAPI 健康检查和聊天接口
- FastAPI 读取 Spring Boot 行情数据后调用大模型
- Docker Compose 编排
- Redis Docker Compose 服务
- FastAPI AI Docker Compose 服务
- 后端 Docker 镜像构建
- Python 采集脚本 Docker 镜像构建
- Vue 前端 Docker 镜像构建
- 基础缓存配置

待完善：

- 数据库初始化脚本
- 更完整的异常重试策略
- API 文档
- 自动化测试
- Android 客户端接入
- AI 提示词、工具调用和权限控制继续完善

## 版本

### v0.13 - 2026-05-23

新增 FastAPI AI 服务和 Vue AI 助手页面。

本版本在原有 Spring Boot / MySQL / Redis 行情链路旁新增独立 `fastapi-ai` 服务。AI 服务提供 `GET /api/ai/health` 和 `POST /api/ai/chat`，会先从 Spring Boot API 读取币种列表、历史价格和 Fear & Greed 数据，再调用 DeepSeek / OpenAI 兼容大模型生成回答。

Vue 前端新增 `/ai` 页面，并在币种详情页加入 AI 助手入口。Docker Compose 新增 `ai` 服务，Nginx 和 Vite 已将 `/api/ai` 代理到 FastAPI。公开仓库只保留 `.env.example` 占位配置，不提交真实 API Key。

### v0.1.2 - 2026-05-21

新增 Docker Compose 一键启动能力。

本版本补充后端、Python 采集脚本和 Vue 前端的 Dockerfile，并提供 `docker-compose.yml` 统一编排 MySQL、后端 API、采集脚本和前端服务。克隆仓库后复制 `.env.example` 为 `.env`，即可通过 `docker compose up --build -d` 启动完整运行环境。

README 和 `DOCKER_GUIDE.md` 已更新为 Docker 优先的部署说明。公开仓库保留较强的演示默认数据库密码，正式部署时应在 `.env` 中自行替换。

### v0.1.1 - 2026-05-16

历史数据采集接口默认切换为 Gate.io 现货 K 线接口，减少对 CoinGecko 的依赖，缓解部分服务器环境无法访问原历史接口的问题。

采集脚本新增实时价格快照兜底机制：即使历史 K 线接口临时失效，脚本仍会按固定间隔将已有实时行情写入历史价格表，避免历史图表长时间没有新数据。

### v0.1 - 2026-05-16

第一个正式版本。

本版本包含后端 API、Python 数据采集脚本和 Vue 前端展示页面。
项目已去除本地环境路径、明文数据库密码、构建产物和临时文件。

## 开发记录

### 2026-05 第 1 周

本周主要排查历史数据无法完整显示的问题。  
经过排查，确认数据库和后端接口正常，问题主要来自 Python 采集外部 API 时请求过快，触发限流。  
当前通过减少采集币种数量、增加请求间隔、增加失败日志和重试机制来缓解。

### 2026-05 第 3 周

本次更新继续优化历史价格采集逻辑。  
采集脚本新增 CoinGecko 请求状态码日志，并对 `403`、`429`、`Retry-After` 以及响应内容中的限流提示进行识别。  
当前采集范围先收敛到 `BTC`、`ETH`、`SOL`、`BNB`、`XRP` 五个核心币种，以降低外部 API 限流风险并方便继续排查数据完整性问题。

### 2026-05 第 3 周更新 2

历史价格数据源默认从 CoinGecko 切换为 Gate.io 现货 K 线接口。

为了增强稳定性，采集脚本增加实时价格快照兜底逻辑：当外部历史接口不可用时，系统仍会周期性将当前实时价格写入历史价格表，用现有行情数据持续形成可展示的历史数据。

### 2026-05-20

本次更新补充系统运行状态能力。

后端新增 `GET /api/status` 接口，用于返回币种数量、历史价格点数量、最近币种更新时间、最近历史价格更新时间、Fear & Greed 当前值和整体运行状态。

Vue 首页新增系统状态卡片，展示系统状态、币种数量、历史价格点数量和最近历史价格更新时间。状态卡片和币种列表一样会定时刷新，接口失败时只记录错误，不阻断原有币种列表展示。

### 2026-05-21

本次更新完成 Docker 化整理。

新增 Docker Compose 编排，可以一次启动 MySQL、Spring Boot 后端、Python 采集脚本和 Vue 前端。新增后端、采集脚本和前端 Dockerfile，并补充 `DOCKER_GUIDE.md`。

数据库连接配置改为环境变量优先，公开仓库提供较强的演示默认密码，同时支持通过 `.env` 覆盖。`.env` 不会提交到仓库。

后端 `Coin` 实体补充数据库列名映射，避免 JPA 自动命名和 Python 写入字段不一致。

### 2026-05-23

本次更新新增 Redis 缓存层，用于优化后端高频读取接口。

后端引入 `spring-boot-starter-data-redis`，并通过 Spring Cache 使用 Redis 作为缓存实现。当前缓存内容包括币种列表和历史价格结果，可减少重复查询 MySQL 的次数。

Docker Compose 新增 `redis` 服务，后端容器通过 `SPRING_REDIS_HOST=redis` 和 `SPRING_REDIS_PORT=6379` 连接 Redis。README、`.env.example` 和 Docker 配置已同步更新。

### 2026-05-23 更新 2

本次更新新增 FastAPI AI 第一阶段能力。

新增 `fastapi-ai` 独立服务，包含 FastAPI 应用入口、配置层、路由层、schema 层、service 层和 prompt 文件。AI 服务支持健康检查和聊天接口，聊天时会先读取 Spring Boot 暴露的真实行情数据，再调用 DeepSeek / OpenAI 兼容大模型生成回答。

Vue 前端新增 AI 助手页面，币种详情页新增 AI 助手入口。开发环境下 Vite 会将 `/api/ai` 代理到 FastAPI，Docker 环境下 Nginx 会将 `/api/ai` 转发到 `ai:8000`。本次同步只提交 `.env.example`，真实 API Key 保留在本地 `.env` 中。
