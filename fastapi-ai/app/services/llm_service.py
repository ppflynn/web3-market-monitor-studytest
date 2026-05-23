from typing import Any

import httpx
from fastapi import HTTPException

from app.config import Settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.spring_api_service import SpringApiService


DEFAULT_SYSTEM_PROMPT = (
    "你是 CoinMarketCap Web3 项目的 AI 助手。"
    "回答要准确、简洁，遇到行情相关问题时提醒用户内容仅用于信息分析，"
    "不能作为投资建议。"
)


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def chat(self, request: ChatRequest) -> ChatResponse:
        if not self.settings.api_key:
            return ChatResponse(
                answer=(
                    "FastAPI AI 服务已经启动，但还没有配置 API Key。"
                    "请复制 .env.example 为 .env，并填写 DEEPSEEK_API_KEY 或 AI_API_KEY、"
                    "AI_BASE_URL、AI_MODEL 后重试。"
                ),
                model=self.settings.ai_model,
                setup_required=True,
            )

        data_context = await SpringApiService(self.settings).build_market_context(request.message)
        payload = self._build_payload(request, data_context)
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
        )

    def _build_payload(self, request: ChatRequest, data_context: str | None = None) -> dict[str, Any]:
        system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if data_context:
            messages.append({"role": "system", "content": data_context})
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
