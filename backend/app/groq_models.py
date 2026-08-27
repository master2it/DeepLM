"""Groq Free plan chat models and rate limits.

Source: https://console.groq.com/docs/rate-limits (Free Plan).
Audio/TTS/moderation-only IDs are omitted — DeepLM needs chat completions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class GroqFreeModel:
    id: str
    label: str
    rpm: int  # requests per minute
    rpd: int  # requests per day (UTC)
    tpm: int | None  # tokens per minute
    tpd: int | None  # tokens per day
    tag: str = ""


# Free-plan chat / text models from Groq docs (excludes Whisper, Orpheus, Prompt Guard).
GROQ_FREE_MODELS: tuple[GroqFreeModel, ...] = (
    GroqFreeModel(
        id="openai/gpt-oss-120b",
        label="gpt-oss-120b",
        rpm=30,
        rpd=1000,
        tpm=8000,
        tpd=200_000,
        tag="Default",
    ),
    GroqFreeModel(
        id="openai/gpt-oss-20b",
        label="gpt-oss-20b",
        rpm=30,
        rpd=1000,
        tpm=8000,
        tpd=200_000,
    ),
    GroqFreeModel(
        id="openai/gpt-oss-safeguard-20b",
        label="gpt-oss-safeguard-20b",
        rpm=30,
        rpd=1000,
        tpm=8000,
        tpd=200_000,
    ),
    GroqFreeModel(
        id="qwen/qwen3.6-27b",
        label="qwen3.6-27b",
        rpm=30,
        rpd=1000,
        tpm=8000,
        tpd=200_000,
    ),
    GroqFreeModel(
        id="qwen/qwen3.8-27b",
        label="qwen3.8-27b",
        rpm=30,
        rpd=1000,
        tpm=8000,
        tpd=2_000_000,
    ),
    GroqFreeModel(
        id="groq/compound",
        label="compound",
        rpm=30,
        rpd=250,
        tpm=70_000,
        tpd=None,
        tag="Agentic",
    ),
    GroqFreeModel(
        id="groq/compound-mini",
        label="compound-mini",
        rpm=30,
        rpd=250,
        tpm=70_000,
        tpd=None,
        tag="Agentic",
    ),
)

_BY_ID = {m.id: m for m in GROQ_FREE_MODELS}
DEFAULT_GROQ_MODEL_ID = GROQ_FREE_MODELS[0].id


def groq_model_ids() -> frozenset[str]:
    return frozenset(_BY_ID)


def resolve_groq_model(model_id: str | None, fallback: str | None = None) -> GroqFreeModel:
    raw = (model_id or "").strip()
    if raw in _BY_ID:
        return _BY_ID[raw]
    fb = (fallback or "").strip()
    if fb in _BY_ID:
        return _BY_ID[fb]
    return _BY_ID[DEFAULT_GROQ_MODEL_ID]


def groq_models_payload() -> list[dict[str, Any]]:
    return [asdict(m) for m in GROQ_FREE_MODELS]
