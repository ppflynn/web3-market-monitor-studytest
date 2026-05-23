from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.routers import chat


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="独立的 FastAPI AI 功能层，负责 LLM 聊天中转、后续币价分析、工具调用和 RAG 文档问答。",
        version="0.1.0",
        openapi_tags=[
            {
                "name": "AI 基础接口",
                "description": "第一阶段接口：健康检查和 LLM 聊天中转。",
            }
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def index() -> HTMLResponse:
        return HTMLResponse(
            """
            <!doctype html>
            <html lang="zh-CN">
              <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>CoinMarketCap Web3 AI 智能分析服务</title>
                <style>
                  body {
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    color: #172033;
                    background: #f6f8fb;
                  }
                  main {
                    max-width: 880px;
                    margin: 0 auto;
                    padding: 56px 24px;
                  }
                  h1 {
                    margin: 0 0 12px;
                    font-size: 32px;
                    line-height: 1.25;
                  }
                  p {
                    margin: 0 0 24px;
                    color: #526071;
                    line-height: 1.8;
                  }
                  .actions {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 12px;
                  }
                  a {
                    display: inline-flex;
                    align-items: center;
                    min-height: 40px;
                    padding: 0 16px;
                    border-radius: 6px;
                    color: #fff;
                    background: #1677ff;
                    text-decoration: none;
                    font-weight: 600;
                  }
                  a.secondary {
                    color: #172033;
                    background: #e8edf5;
                  }
                </style>
              </head>
              <body>
                <main>
                  <h1>CoinMarketCap Web3 AI 智能分析服务</h1>
                  <p>
                    这是项目旁边独立运行的 FastAPI AI 服务。
                    第一阶段已经提供健康检查和 LLM 聊天中转接口，后续会继续接入币价分析、工具调用和 RAG 文档问答。
                  </p>
                  <div class="actions">
                    <a href="/docs">打开接口文档</a>
                    <a class="secondary" href="/api/ai/health">查看健康检查</a>
                  </div>
                </main>
              </body>
            </html>
            """
        )

    app.include_router(chat.router, prefix=settings.api_prefix, tags=["AI 基础接口"])
    return app


app = create_app()
