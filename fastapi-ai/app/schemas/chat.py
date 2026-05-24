from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status. ok means healthy.")
    service: str = Field(..., description="Service name.")
    environment: str = Field(..., description="Runtime environment.")
    llm_configured: bool = Field(..., description="Whether an AI API key is configured.")


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(..., description="Message role.")
    content: str = Field(..., min_length=1, max_length=8000, description="Message content.")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Current user question.")
    system_prompt: str | None = Field(default=None, max_length=2000, description="Optional system prompt.")
    history: list[ChatMessage] = Field(default_factory=list, max_length=20, description="Optional chat history.")
    temperature: float | None = Field(default=None, ge=0, le=2, description="Sampling temperature.")
    max_tokens: int | None = Field(default=None, ge=1, le=4000, description="Max answer tokens.")


class RagSource(BaseModel):
    title: str = Field(..., description="Retrieved source title.")
    path: str = Field(..., description="Project-relative file path.")
    snippet: str = Field(..., description="Retrieved text snippet.")
    score: float = Field(..., description="Retriever relevance score.")


class RagSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000, description="RAG search query.")


class RagSearchResponse(BaseModel):
    query: str = Field(..., description="Original search query.")
    sources: list[RagSource] = Field(default_factory=list, description="Matched project snippets.")


class ToolDefinition(BaseModel):
    name: str = Field(..., description="Tool name.")
    description: str = Field(..., description="What the tool does.")
    parameters: dict[str, Any] = Field(default_factory=dict, description="JSON-style parameter description.")


class ToolCallRecord(BaseModel):
    name: str = Field(..., description="Tool name.")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool call arguments.")
    result: Any | None = Field(default=None, description="Structured tool result.")
    error: str | None = Field(default=None, description="Tool execution error, if any.")


class ToolRunRequest(BaseModel):
    query: str | None = Field(default=None, max_length=4000, description="User query for automatic tool selection.")
    tool_name: str | None = Field(default=None, max_length=100, description="Optional specific tool to run.")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments for a specific tool call.")


class ToolRunResponse(BaseModel):
    query: str | None = Field(default=None, description="Original user query, if provided.")
    context: str | None = Field(default=None, description="Tool context text prepared for the LLM.")
    calls: list[ToolCallRecord] = Field(default_factory=list, description="Executed tool calls.")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="AI answer content.")
    model: str = Field(..., description="Model used for this response.")
    provider: str = Field(default="openai-compatible", description="LLM provider type.")
    usage: dict[str, Any] | None = Field(default=None, description="Provider token usage.")
    setup_required: bool = Field(default=False, description="Whether API key setup is still required.")
    sources: list[RagSource] = Field(default_factory=list, description="RAG sources used for this answer.")
    tools: list[ToolCallRecord] = Field(default_factory=list, description="Market tools used for this answer.")
