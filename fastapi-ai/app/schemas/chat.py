from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="服务状态，正常时为 ok。")
    service: str = Field(..., description="服务名称。")
    environment: str = Field(..., description="当前运行环境。")
    llm_configured: bool = Field(..., description="是否已经配置 AI_API_KEY。")


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(..., description="消息角色。")
    content: str = Field(..., min_length=1, max_length=8000, description="消息内容。")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="用户本次输入的问题。")
    system_prompt: str | None = Field(default=None, max_length=2000, description="可选的系统提示词。")
    history: list[ChatMessage] = Field(default_factory=list, max_length=20, description="可选的历史对话。")
    temperature: float | None = Field(default=None, ge=0, le=2, description="生成随机性，越低越稳定。")
    max_tokens: int | None = Field(default=None, ge=1, le=4000, description="回答最大 token 数。")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="AI 回答内容。")
    model: str = Field(..., description="实际使用的模型名称。")
    provider: str = Field(default="openai-compatible", description="大模型接口类型。")
    usage: dict[str, Any] | None = Field(default=None, description="模型调用用量信息。")
    setup_required: bool = Field(default=False, description="是否还需要配置 API Key。")
