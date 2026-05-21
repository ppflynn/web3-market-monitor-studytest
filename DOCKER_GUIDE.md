# Docker 部署指南

本项目已经整理为 Docker Compose 部署方式，可以一次启动 MySQL、Spring Boot 后端、Python 数据采集脚本和 Vue 前端。

## 服务组成

```text
mysql      MySQL 8 数据库
backend    Spring Boot REST API
collector  Python 行情数据采集脚本
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
MySQL: localhost:3307
```

## 环境变量

`.env.example` 提供了一组可以直接运行的示例配置。

默认示例密码：

```text
CmWeb3_Docker_9Kq2pX7m_2026
```

这是公开仓库中的演示默认值，不应作为生产环境密码。正式部署时请复制 `.env.example` 为 `.env` 并修改：

```text
MYSQL_ROOT_PASSWORD
DB_PASSWORD
SPRING_DATASOURCE_PASSWORD
```

`.env` 已被 `.gitignore` 忽略，不会被提交。

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

执行 `docker compose down` 不会删除该数据卷。若要连同数据库数据一起清理：

```powershell
docker compose down -v
```

请谨慎执行 `-v`，它会删除数据库数据。

## 端口说明

```text
3000 -> frontend
8080 -> backend
3307 -> mysql
```

容器内部访问 MySQL 使用：

```text
mysql:3306
```

本机访问 MySQL 使用：

```text
localhost:3307
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
```

## 注意事项

- 不要提交真实 `.env` 文件。
- 公开仓库中的密码只是演示默认值，正式部署请修改。
- 如果本机已经有 MySQL 占用 `3307`，请在 `.env` 中修改 `MYSQL_PORT`。
- 如果本机已经有服务占用 `3000` 或 `8080`，请在 `.env` 中修改 `FRONTEND_PORT` 或 `BACKEND_PORT`。
