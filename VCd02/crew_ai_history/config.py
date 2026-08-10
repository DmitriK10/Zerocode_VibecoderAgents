# config.py
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # LLM
    openai_api_key: str
    openai_api_base: str
    openai_model_name: str

    # Telegram
    bot_token: str

    # LogTail
    logtail_source_token: Optional[str] = None

    # Таймауты и повторные попытки
    llm_timeout: int = 600
    llm_max_retries: int = 3
    retry_delay: int = 2
    retry_backoff: int = 2
    retry_max_attempts: int = 3

    # Кэш
    seo_cache_ttl: int = 86400  # 1 сутки

    # Безопасность
    max_custom_query_length: int = 500

    # Прочее
    crewai_telemetry_enabled: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            openai_api_base=os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1"),
            openai_model_name=os.getenv("OPENAI_MODEL_NAME", "llama3.2:3b"),
            bot_token=os.getenv("BOT_TOKEN", ""),
            logtail_source_token=os.getenv("LOGTAIL_SOURCE_TOKEN"),
            llm_timeout=int(os.getenv("LLM_TIMEOUT", "600")),
            llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("RETRY_DELAY", "2")),
            retry_backoff=int(os.getenv("RETRY_BACKOFF", "2")),
            retry_max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
            seo_cache_ttl=int(os.getenv("SEO_CACHE_TTL", "86400")),
            max_custom_query_length=int(os.getenv("MAX_CUSTOM_QUERY_LENGTH", "500")),
            crewai_telemetry_enabled=os.getenv("CREWAI_TELEMETRY_ENABLED", "false").lower() == "true",
        )


# Глобальный экземпляр (для упрощения)
settings = Settings.from_env()