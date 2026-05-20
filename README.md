# CoinMarketCap Web3

`v0.1.1` 在第一个正式版本基础上更新了历史数据采集逻辑，项目包含 Spring Boot 后端、Python 数据采集脚本和 Vue 3 前端。

当前版本不包含 Android 客户端。Android 项目后续会作为独立客户端继续整理。

## 功能概览

- 采集主流加密货币实时行情数据
- 采集 Fear & Greed 指数
- 通过 Gate.io 现货 K 线接口采集部分币种的历史价格数据
- 在历史接口不可用时，使用实时价格快照持续补充历史价格点
- 保留 CoinGecko 历史价格接口作为可选数据源
- 将采集结果写入 MySQL
- 通过 Spring Boot 提供 REST API
- 通过 Vue 前端展示币种列表、详情、历史价格图表和 Fear & Greed 指数
- 提供系统状态接口，展示采集数据量和最近更新时间
- Vue 首页展示系统状态卡片
- 使用 Caffeine 对部分接口数据进行缓存

## 技术栈

### 后端

- Java 8
- Spring Boot 2.7.18
- Spring Web
- Spring Data JPA
- MySQL
- Caffeine Cache
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
│  └─ nginx.conf
├─ .mvn
├─ pom.xml
├─ mvnw.cmd
├─ .env.example
└─ README.md
```

## 数据流

```text
External APIs
    -> Python collector
    -> MySQL
    -> Spring Boot API
    -> Vue frontend
```

## 环境变量

本仓库不会提交真实密码。请参考 `.env.example` 配置本地环境。

Spring Boot 后端使用：

```text
DB_URL
DB_USER
DB_PASSWORD
```

Python 采集脚本使用：

```text
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME
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

## 启动方式

建议启动顺序：

```text
MySQL -> Python collector -> Spring Boot API -> Vue frontend
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

### 4. 启动 Vue 前端

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

## API 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/coins` | 获取币种列表 |
| GET | `/api/coins/{coinId}` | 获取币种详情 |
| GET | `/api/coins/{coinId}/history?days=7` | 获取历史价格 |
| GET | `/api/coins/search?keyword=btc` | 搜索币种 |
| GET | `/api/fear-greed` | 获取 Fear & Greed 指数 |
| GET | `/api/status` | 获取系统数据采集和运行状态 |

## 当前状态

已完成：

- 后端基础 REST API
- MySQL 数据读取
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
- 前端开发代理配置
- 基础缓存配置

待完善：

- 数据库初始化脚本
- 更完整的异常重试策略
- API 文档
- Docker / docker-compose
- 自动化测试
- Android 客户端接入

## 版本

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
