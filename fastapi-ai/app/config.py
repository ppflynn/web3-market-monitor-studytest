from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CoinMarketCap Web3 AI 智能分析服务"
    environment: str = "dev"
    api_prefix: str = "/api/ai"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    ai_api_key: str | None = Field(default=None, alias="AI_API_KEY")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    ai_base_url: str = Field(default="https://api.openai.com/v1", alias="AI_BASE_URL")
    ai_model: str = Field(default="gpt-4o-mini", alias="AI_MODEL")
    ai_timeout_seconds: float = Field(default=30.0, alias="AI_TIMEOUT_SECONDS")
    ai_temperature: float = Field(default=0.3, alias="AI_TEMPERATURE")
    ai_max_tokens: int = Field(default=800, alias="AI_MAX_TOKENS")
    ai_stream: bool = Field(default=False, alias="AI_STREAM")
    ai_thinking_enabled: bool = Field(default=False, alias="AI_THINKING_ENABLED")
    ai_reasoning_effort: str | None = Field(default=None, alias="AI_REASONING_EFFORT")
    embedding_api_key: str | None = Field(default=None, alias="EMBEDDING_API_KEY")
    embedding_base_url: str | None = Field(default=None, alias="EMBEDDING_BASE_URL")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_timeout_seconds: float = Field(default=30.0, alias="EMBEDDING_TIMEOUT_SECONDS")
    embedding_batch_size: int = Field(default=48, alias="EMBEDDING_BATCH_SIZE")
    spring_api_base_url: str = Field(default="http://localhost:8080/api", alias="SPRING_API_BASE_URL")
    spring_api_timeout_seconds: float = Field(default=10.0, alias="SPRING_API_TIMEOUT_SECONDS")
    rag_enabled: bool = Field(default=True, alias="RAG_ENABLED")
    rag_root_path: str | None = Field(default=None, alias="RAG_ROOT_PATH")
    rag_include_paths: str = Field(
        default=(
            "README.md,fastapi-ai,src/main/java,src/main/resources,"
            "frontend/coin-market-web/src,scripts"
        ),
        alias="RAG_INCLUDE_PATHS",
    )
    rag_exclude_dirs: str = Field(
        default=".git,.idea,.vscode,.mvn,.venv,venv,target,node_modules,dist,__pycache__",
        alias="RAG_EXCLUDE_DIRS",
    )
    rag_max_files: int = Field(default=120, alias="RAG_MAX_FILES")
    rag_max_file_bytes: int = Field(default=200_000, alias="RAG_MAX_FILE_BYTES")
    rag_chunk_chars: int = Field(default=1400, alias="RAG_CHUNK_CHARS")
    rag_snippet_chars: int = Field(default=1200, alias="RAG_SNIPPET_CHARS")
    rag_max_sources: int = Field(default=5, alias="RAG_MAX_SOURCES")
    rag_min_score: float = Field(default=1.2, alias="RAG_MIN_SCORE")
    rag_reindex_on_start: bool = Field(default=False, alias="RAG_REINDEX_ON_START")
    chroma_persist_dir: str = Field(default="./chroma-data", alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(default="project_rag", alias="CHROMA_COLLECTION_NAME")
    market_tools_enabled: bool = Field(default=True, alias="MARKET_TOOLS_ENABLED")
    market_tool_default_history_days: int = Field(default=7, alias="MARKET_TOOL_DEFAULT_HISTORY_DAYS")
    market_tool_max_history_days: int = Field(default=30, alias="MARKET_TOOL_MAX_HISTORY_DAYS")
    market_tool_max_context_chars: int = Field(default=8000, alias="MARKET_TOOL_MAX_CONTEXT_CHARS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def chat_completions_url(self) -> str:
        return f"{self.ai_base_url.rstrip('/')}/chat/completions"

    @property
    def embeddings_url(self) -> str:
        base_url = self.embedding_base_url or self.ai_base_url
        return f"{base_url.rstrip('/')}/embeddings"

    @property
    def api_key(self) -> str | None:
        return self.ai_api_key or self.deepseek_api_key

    @property
    def embedding_api_key_value(self) -> str | None:
        return self.embedding_api_key or self.api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
