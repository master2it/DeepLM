"""Runtime settings. HF_TOKEN is optional (Ollama is primary)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    root = Path(__file__).resolve().parents[2]
    backend = Path(__file__).resolve().parents[1]
    files = []
    for p in (root / ".env", backend / ".env"):
        if p.is_file():
            files.append(str(p))
    return tuple(files)


def _usable_redis_url(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    if "${{" in text or "{{" in text:
        return False
    return text.startswith("redis://") or text.startswith("rediss://")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    ollama_enabled: bool = False
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "deepseek-r1"
    ollama_timeout_seconds: float = 120.0
    hf_token: str = ""
    hf_chat_model: str = "Qwen/Qwen2.5-72B-Instruct"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_max_tokens: int = 4096
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "https://deep-lm.vercel.app"
    )
    cors_origin_regex: str = r"https://([a-z0-9-]+\.)*(vercel\.app|up\.railway\.app)"
    redis_url: str = Field(
        default="",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )
    redis_private_url: str = Field(
        default="",
        validation_alias=AliasChoices(
            "REDIS_PRIVATE_URL", "redis_private_url"
        ),
    )
    redis_host: str = Field(
        default="",
        validation_alias=AliasChoices("REDISHOST", "REDIS_HOST", "redis_host"),
    )
    redis_port: int = Field(
        default=6379,
        validation_alias=AliasChoices("REDISPORT", "REDIS_PORT", "redis_port"),
    )
    redis_user: str = Field(
        default="",
        validation_alias=AliasChoices("REDISUSER", "REDIS_USER", "redis_user"),
    )
    redis_password: str = Field(
        default="",
        validation_alias=AliasChoices(
            "REDIS_PASSWORD", "REDISPASSWORD", "redis_password"
        ),
    )
    redis_ttl_seconds: int = 43200
    hf_default_daily_limit: int = 50
    groq_default_daily_limit: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def resolved_redis_url(self) -> str:
        for candidate in (self.redis_private_url, self.redis_url):
            if _usable_redis_url(candidate):
                return candidate.strip()
        host = self.redis_host.strip()
        if not host or "${{" in host:
            return ""
        user = quote(self.redis_user.strip() or "default", safe="")
        password = quote(self.redis_password, safe="")
        auth = f"{user}:{password}@" if self.redis_password else ""
        return f"redis://{auth}{host}:{int(self.redis_port)}/0"

    @property
    def hf_configured(self) -> bool:
        return bool(self.hf_token.strip())

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


def mask_secret(value: str | None) -> str:
    if not value:
        return "(not set)"
    text = str(value).strip()
    if not text:
        return "(not set)"
    if len(text) <= 8:
        return "***"
    return f"{text[:4]}…{text[-4:]} ({len(text)} chars)"
