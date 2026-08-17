"""Chat via local Ollama (deepseek-r1, thinking off), then Hugging Face fallback."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from huggingface_hub import InferenceClient

from app.config import get_settings

logger = logging.getLogger(__name__)

THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


class LLMError(RuntimeError):
    """Both Ollama and Hugging Face failed, or no provider could run."""


def strip_thinking(text: str) -> str:
    if not text:
        return ""
    cleaned = THINK_BLOCK_RE.sub("", text)
    return cleaned.strip()


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
) -> str:
    settings = get_settings()
    token = settings.hf_token.strip()
    if not token:
        raise LLMError(
            "Ollama failed and HF_TOKEN is not configured. "
            "Start Ollama with deepseek-r1, or set HF_TOKEN for fallback."
        )
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


def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> tuple[str, str]:
    """Return (content, provider) where provider is 'ollama' or 'huggingface'."""
    try:
        return _ollama_chat(messages, temperature=temperature, max_tokens=max_tokens), "ollama"
    except Exception as exc:
        logger.warning("Ollama chat failed, trying Hugging Face: %s", exc)

    try:
        return _huggingface_chat(
            messages, temperature=temperature, max_tokens=max_tokens
        ), "huggingface"
    except LLMError:
        raise
    except Exception as exc:
        raise LLMError(
            f"Ollama failed and Hugging Face fallback also failed: {exc}"
        ) from exc


def ollama_reachable() -> bool:
    settings = get_settings()
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(url)
            return response.status_code < 500
    except Exception:
        return False
