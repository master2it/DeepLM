"""Chat via the selected provider. Fallback only when none is specified."""

from __future__ import annotations

import logging
import re
from typing import Any, Literal

import httpx
from huggingface_hub import InferenceClient

from app.config import get_settings

logger = logging.getLogger(__name__)

THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

ProviderName = Literal["ollama", "huggingface", "groq"]
PROVIDERS: tuple[ProviderName, ...] = ("ollama", "huggingface", "groq")
_ALIASES = {"hf": "huggingface", "hugging_face": "huggingface"}


def default_order() -> list[ProviderName]:
    order: list[ProviderName] = ["huggingface", "groq"]
    if get_settings().ollama_enabled:
        order.insert(1, "ollama")
    return order


class LLMError(RuntimeError):
    """All configured providers failed, or no provider could run."""


def strip_thinking(text: str) -> str:
    if not text:
        return ""
    cleaned = THINK_BLOCK_RE.sub("", text)
    return cleaned.strip()


def normalize_provider(provider: str | None) -> ProviderName:
    if not provider or not str(provider).strip():
        return "huggingface"
    name = str(provider).strip().lower()
    name = _ALIASES.get(name, name)
    if name not in PROVIDERS:
        raise LLMError(
            f"Unknown provider '{provider}'. Use ollama, huggingface, or groq."
        )
    return name  # type: ignore[return-value]


def provider_route(
    preferred: ProviderName, *, exclusive: bool = False
) -> list[ProviderName]:
    if exclusive:
        return [preferred]
    order = default_order()
    return [preferred] + [p for p in order if p != preferred]


def _hf_chat_content(response: Any) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return strip_thinking(response)
    try:
        choice = response.choices[0]
        message = choice.message
        content = getattr(message, "content", None)
        if content:
            return strip_thinking(content)
    except Exception:
        pass
    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            return strip_thinking(msg.get("content") or "")
    return strip_thinking(str(response))


def _skip_reason(
    name: ProviderName,
    *,
    groq_api_key: str | None = None,
    hf_api_key: str | None = None,
) -> str | None:
    if name == "ollama" and not get_settings().ollama_enabled:
        return "Ollama is temporarily disabled"
    if name == "huggingface" and not _resolve_hf_key(hf_api_key):
        return "HF_TOKEN is not configured"
    if name == "groq" and not _resolve_groq_key(groq_api_key):
        return "GROQ_API_KEY is not configured"
    return None


def _resolve_groq_key(groq_api_key: str | None) -> str:
    override = (groq_api_key or "").strip()
    if override:
        return override
    return get_settings().groq_api_key.strip()


def _resolve_hf_key(hf_api_key: str | None) -> str:
    override = (hf_api_key or "").strip()
    if override:
        return override
    return get_settings().hf_token.strip()


def _ollama_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
) -> str:
    settings = get_settings()
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    with httpx.Client(timeout=settings.ollama_timeout_seconds) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
    message = data.get("message") or {}
    content = message.get("content") or data.get("response") or ""
    content = strip_thinking(content)
    if not content.strip():
        raise LLMError("Ollama returned empty content.")
    return content


def _huggingface_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    hf_api_key: str | None = None,
) -> str:
    settings = get_settings()
    token = _resolve_hf_key(hf_api_key)
    if not token:
        raise LLMError("HF_TOKEN is not configured.")
    api = InferenceClient(token=token)
    response = api.chat_completion(
        messages=messages,
        model=settings.hf_chat_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = _hf_chat_content(response)
    if not content.strip():
        raise LLMError("Hugging Face returned empty content.")
    return content


def _groq_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    groq_api_key: str | None = None,
) -> str:
    settings = get_settings()
    key = _resolve_groq_key(groq_api_key)
    if not key:
        raise LLMError("GROQ_API_KEY is not configured.")
    url = settings.groq_base_url.rstrip("/") + "/chat/completions"
    cap = max(256, int(getattr(settings, "groq_max_tokens", 4096) or 4096))
    tokens = min(max(1, int(max_tokens)), cap)
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    attempts: list[int] = []
    for size in (tokens, min(2048, tokens), min(1024, tokens)):
        if size not in attempts:
            attempts.append(size)
    last_response: httpx.Response | None = None
    for attempt in attempts:
        payload = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": attempt,
        }
        with httpx.Client(timeout=settings.ollama_timeout_seconds) as client:
            last_response = client.post(url, json=payload, headers=headers)
        if last_response.status_code == 413 and attempt != attempts[-1]:
            logger.warning(
                "Groq 413 Payload Too Large with max_tokens=%s; retrying smaller",
                attempt,
            )
            continue
        last_response.raise_for_status()
        data = last_response.json()
        content = _hf_chat_content(data)
        if not content.strip():
            raise LLMError("Groq returned empty content.")
        return content
    if last_response is not None:
        last_response.raise_for_status()
    raise LLMError("Groq request failed.")


def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    provider: str | None = None,
    groq_api_key: str | None = None,
    hf_api_key: str | None = None,
) -> tuple[str, str]:
    """Return (content, provider). Explicit Settings choice is exclusive."""
    exclusive = bool(provider and str(provider).strip())
    preferred = normalize_provider(provider)
    handlers = {
        "ollama": _ollama_chat,
        "huggingface": _huggingface_chat,
        "groq": _groq_chat,
    }
    errors: list[str] = []
    for name in provider_route(preferred, exclusive=exclusive):
        skip = _skip_reason(
            name, groq_api_key=groq_api_key, hf_api_key=hf_api_key
        )
        if skip:
            errors.append(f"{name}: {skip}")
            continue
        try:
            kwargs: dict[str, Any] = {
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if name == "groq":
                kwargs["groq_api_key"] = groq_api_key
            if name == "huggingface":
                kwargs["hf_api_key"] = hf_api_key
            content = handlers[name](messages, **kwargs)
            return content, name
        except Exception as exc:
            logger.warning("%s chat failed: %s", name, exc)
            errors.append(f"{name}: {exc}")

    prefix = "Provider failed: " if exclusive else "All providers failed: "
    raise LLMError(prefix + "; ".join(errors))


def ollama_reachable() -> bool:
    settings = get_settings()
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(url)
            return response.status_code < 500
    except Exception:
        return False


def providers_status() -> list[dict[str, Any]]:
    settings = get_settings()
    return [
        {
            "id": "ollama",
            "label": "Ollama",
            "available": settings.ollama_enabled and ollama_reachable(),
            "enabled": settings.ollama_enabled,
            "model": settings.ollama_model,
        },
        {
            "id": "huggingface",
            "label": "Hugging Face",
            "available": settings.hf_configured,
            "model": settings.hf_chat_model,
        },
        {
            "id": "groq",
            "label": "Groq",
            "available": settings.groq_configured,
            "model": settings.groq_model,
        },
    ]
