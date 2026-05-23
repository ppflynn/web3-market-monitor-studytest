from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse
from app.services.llm_service import LLMService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查 FastAPI AI 服务是否正常运行，并返回当前是否已经配置 LLM API Key。",
)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
        llm_configured=bool(settings.api_key),
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="LLM 聊天中转",
    description="接收用户问题，统一转发到 OpenAI 兼容的大模型接口，并返回 AI 回答。",
)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    service = LLMService(settings)
    return await service.chat(request)
