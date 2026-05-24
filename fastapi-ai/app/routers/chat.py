from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    RagSearchRequest,
    RagSearchResponse,
    ToolDefinition,
    ToolRunRequest,
    ToolRunResponse,
)
from app.services.llm_service import LLMService
from app.services.market_tool_service import MarketToolService
from app.services.rag_service import RagService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check whether the FastAPI AI service is running and whether an LLM API key is configured.",
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
    summary="LLM chat with market data and project RAG",
    description="Answer user questions with Spring Boot market context and local project RAG snippets.",
)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    service = LLMService(settings)
    return await service.chat(request)


@router.post(
    "/rag/search",
    response_model=RagSearchResponse,
    summary="Search local project RAG corpus",
    description="Return the project files and snippets that would be used as RAG context.",
)
async def rag_search(
    request: RagSearchRequest,
    settings: Settings = Depends(get_settings),
) -> RagSearchResponse:
    sources = RagService(settings).search(request.query)
    return RagSearchResponse(query=request.query, sources=sources)


@router.get(
    "/tools",
    response_model=list[ToolDefinition],
    summary="List market tools",
    description="Return available market-data tools backed by the Spring Boot API.",
)
async def list_tools(settings: Settings = Depends(get_settings)) -> list[ToolDefinition]:
    tools = MarketToolService(settings).list_tools()
    return [ToolDefinition(**tool) for tool in tools]


@router.post(
    "/tools/run",
    response_model=ToolRunResponse,
    summary="Run market tools",
    description="Run a specific market tool or auto-select tools from a user query.",
)
async def run_tools(
    request: ToolRunRequest,
    settings: Settings = Depends(get_settings),
) -> ToolRunResponse:
    service = MarketToolService(settings)
    if request.tool_name:
        result = await service.call_tool(request.tool_name, request.arguments)
    else:
        result = await service.execute_for_question(request.query or "")
    return ToolRunResponse(query=request.query, context=result.context_text, calls=result.calls)
