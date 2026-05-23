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
    spring_api_base_url: str = Field(default="http://localhost:8080/api", alias="SPRING_API_BASE_URL")
    spring_api_timeout_seconds: float = Field(default=10.0, alias="SPRING_API_TIMEOUT_SECONDS")

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
    def api_key(self) -> str | None:
        return self.ai_api_key or self.deepseek_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
