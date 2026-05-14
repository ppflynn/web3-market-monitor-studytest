# CoinMarketCap Web3 Core

这是一个加密货币行情数据项目的核心后端仓库，当前只包含 Spring Boot 后端服务和 Python 数据采集脚本。

本仓库暂不包含：

- Vue 前端项目
- Android 客户端项目
- 本地构建产物
- 本地环境配置和真实数据库密码

## 功能概览

- 采集主流加密货币实时行情数据
- 采集 Fear & Greed 指数
- 采集部分币种的历史价格数据
- 识别 CoinGecko 历史价格接口的常见限流响应
- 将采集结果写入 MySQL
- 通过 Spring Boot 提供 REST API
- 使用 Caffeine 对部分接口数据进行缓存

## 技术栈

- Java 8
- Spring Boot 2.7.18
- Spring Web
- Spring Data JPA
- MySQL
- Caffeine Cache
- Maven
- Python
- requests
- PyMySQL

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
- 历史价格点
- Fear & Greed 指数

## 启动方式

建议启动顺序：

```text
MySQL -> Python collector -> Spring Boot API
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

默认服务地址：

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

## 当前状态

已完成：

- 后端基础 REST API
- MySQL 数据读取
- 实时行情采集
- 历史价格采集
- 历史价格请求状态日志
- CoinGecko 常见限流响应识别
- Fear & Greed 指数采集
- 基础缓存配置

待完善：

- 数据库初始化脚本
- 更完整的异常重试策略
- API 文档
- Docker / docker-compose
- 自动化测试

## 开发记录

### 2026-05 第 1 周

本周主要排查历史数据无法完整显示的问题。  
经过排查，确认数据库和后端接口正常，问题主要来自 Python 采集外部 API 时请求过快，触发限流。  
当前通过减少采集币种数量、增加请求间隔、增加失败日志和重试机制来缓解。

### 2026-05 第 3 周

本次更新继续优化历史价格采集逻辑。  
采集脚本新增 CoinGecko 请求状态码日志，并对 `403`、`429`、`Retry-After` 以及响应内容中的限流提示进行识别。  
当前采集范围先收敛到 `BTC`、`ETH`、`SOL`、`BNB`、`XRP` 五个核心币种，以降低外部 API 限流风险并方便继续排查数据完整性问题。
