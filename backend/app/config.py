"""Runtime settings. HF_TOKEN is optional (Ollama is primary)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    root = Path(__file__).resolve().parents[2]
    backend = Path(__file__).resolve().parents[1]
    files = []
    for p in (root / ".env", backend / ".env"):
        if p.is_file():
            files.append(str(p))
    return tuple(files)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "deepseek-r1"
    ollama_timeout_seconds: float = 120.0
    hf_token: str = ""
    hf_chat_model: str = "Qwen/Qwen2.5-72B-Instruct"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "https://deep-lm.vercel.app"
    )
    cors_origin_regex: str = r"https://([a-z0-9-]+\.)*(vercel\.app|up\.railway\.app)"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

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
