from typing import Any

import httpx
from fastapi import HTTPException

from app.config import Settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.market_tool_service import MarketToolService
from app.services.rag_service import RagService


DEFAULT_SYSTEM_PROMPT = (
    "You are the AI assistant for the CoinMarketCap Web3 project. "
    "Answer in the same language as the user. Be accurate and concise. "
    "For market analysis, prioritize project data and remind the user that the content is for "
    "information analysis only and is not investment advice. "
    "When Market tool context is provided, treat it as the authoritative source for current prices, "
    "rankings, history, and sentiment. "
    "For project/code questions, use the Project RAG context when it is relevant. "
    "Do not invent files, APIs, or implementation details that are not present in the context."
)


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def chat(self, request: ChatRequest) -> ChatResponse:
        rag_result = RagService(self.settings).build_context(request.message)
        tool_result = await MarketToolService(self.settings).execute_for_question(request.message)

        if not self.settings.api_key:
            return ChatResponse(
                answer=(
                    "FastAPI AI 服务已经启动，但还没有配置 API Key。请复制 "
                    "fastapi-ai/.env.example 为 fastapi-ai/.env，并填写 AI_API_KEY "
                    "或 DEEPSEEK_API_KEY 后重试。"
                ),
                model=self.settings.ai_model,
                setup_required=True,
                sources=rag_result.sources,
                tools=tool_result.calls,
            )

        payload = self._build_payload(
            request=request,
            market_context=tool_result.context_text,
            rag_context=rag_result.context_text,
        )
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.ai_timeout_seconds) as client:
                response = await client.post(
                    self.settings.chat_completions_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._safe_error_detail(exc.response)
            raise HTTPException(status_code=502, detail=detail) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"LLM provider request failed: {exc.__class__.__name__}",
            ) from exc

        data = response.json()
        answer = self._extract_answer(data)
        return ChatResponse(
            answer=answer,
            model=data.get("model", self.settings.ai_model),
            usage=data.get("usage"),
            sources=rag_result.sources,
            tools=tool_result.calls,
        )

    def _build_payload(
        self,
        request: ChatRequest,
        market_context: str | None = None,
        rag_context: str | None = None,
    ) -> dict[str, Any]:
        system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if market_context:
            messages.append({"role": "system", "content": market_context})
        if rag_context:
            messages.append({"role": "system", "content": rag_context})
        messages.extend(message.model_dump() for message in request.history)
        messages.append({"role": "user", "content": request.message})

        payload: dict[str, Any] = {
            "model": self.settings.ai_model,
            "messages": messages,
            "temperature": request.temperature
            if request.temperature is not None
            else self.settings.ai_temperature,
            "max_tokens": request.max_tokens or self.settings.ai_max_tokens,
            "stream": self.settings.ai_stream,
        }

        if self.settings.ai_thinking_enabled:
            payload["thinking"] = {"type": "enabled"}

        if self.settings.ai_reasoning_effort:
            payload["reasoning_effort"] = self.settings.ai_reasoning_effort

        return payload

    def _extract_answer(self, data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise HTTPException(status_code=502, detail="LLM provider returned no choices.")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise HTTPException(status_code=502, detail="LLM provider returned an empty answer.")

        return str(content).strip()

    def _safe_error_detail(self, response: httpx.Response) -> str:
        text = response.text[:500]
        return f"LLM provider returned HTTP {response.status_code}: {text}"
