from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    service_name: str = "mongolian-language-service"
    environment: str = "local"
    log_level: str = "INFO"

    provider: str = "mock"
    production_model: str = "Qwen3-32B-MN-Lendex"
    teacher_model: str = "Qwen3-235B-A22B-Instruct-2507"

    openai_base_url: str | None = None
    openai_api_key: str | None = None
    vllm_base_url: str | None = None
    vllm_api_key: str | None = None

    redis_url: str = "redis://redis:6379/0"
    database_url: str = "postgresql://mongolian:language@postgres:5432/mongolian_language"

    glossary_dir: Path = Path("app/glossaries")
    cache_ttl_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("ENVIRONMENT", "local"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        provider=os.getenv("MODEL_PROVIDER", "mock"),
        production_model=os.getenv("PRODUCTION_MODEL", "Qwen3-32B-MN-Lendex"),
        teacher_model=os.getenv("TEACHER_MODEL", "Qwen3-235B-A22B-Instruct-2507"),
        openai_base_url=os.getenv("OPENAI_BASE_URL") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        vllm_base_url=os.getenv("VLLM_BASE_URL") or None,
        vllm_api_key=os.getenv("VLLM_API_KEY") or None,
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql://mongolian:language@postgres:5432/mongolian_language",
        ),
        glossary_dir=Path(os.getenv("GLOSSARY_DIR", "app/glossaries")),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600")),
    )
