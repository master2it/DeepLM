"""Chat via the selected provider. Fallback only when none is specified."""

from __future__ import annotations

import logging
import re
from typing import Any, Literal

import httpx
from huggingface_hub import InferenceClient

from app.config import get_settings
from app.groq_models import groq_models_payload, resolve_groq_model

logger = logging.getLogger(__name__)

THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
# DeepSeek non-think mode may leave a lone closing tag.
THINK_CLOSE_RE = re.compile(r"</think>", re.IGNORECASE)

ProviderName = Literal["huggingface", "deepseek", "groq"]
PROVIDERS: tuple[ProviderName, ...] = ("huggingface", "deepseek", "groq")
_ALIASES = {
    "hf": "huggingface",
    "hugging_face": "huggingface",
    "deepseek-v4-flash": "deepseek",
    "deepseek_flash": "deepseek",
    "hf-deepseek": "deepseek",
}
_HF_FAMILY = frozenset({"huggingface", "deepseek"})


def default_order() -> list[ProviderName]:
    return ["huggingface", "deepseek", "groq"]


class LLMError(RuntimeError):
    """All configured providers failed, or no provider could run."""


def strip_thinking(text: str) -> str:
    if not text:
        return ""
    cleaned = THINK_BLOCK_RE.sub("", text)
    cleaned = THINK_CLOSE_RE.sub("", cleaned)
    return cleaned.strip()


def normalize_provider(provider: str | None) -> ProviderName:
    if not provider or not str(provider).strip():
        return "huggingface"
    name = str(provider).strip().lower()
    name = _ALIASES.get(name, name)
    if name == "ollama":
        raise LLMError(
            "Ollama is no longer supported. Use huggingface, deepseek, or groq."
        )
    if name not in PROVIDERS:
        raise LLMError(
            f"Unknown provider '{provider}'. Use huggingface, deepseek, or groq."
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
        # Some hosts put reasoning in a separate field.
        reasoning = getattr(message, "reasoning_content", None) or getattr(
            message, "reasoning", None
        )
        if reasoning and not content:
            return strip_thinking(str(reasoning))
    except Exception:
        pass
    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content") or ""
            if content:
                return strip_thinking(content)
            reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
            if reasoning:
                return strip_thinking(str(reasoning))
    return strip_thinking(str(response))


def _skip_reason(
    name: ProviderName,
    *,
    groq_api_key: str | None = None,
    hf_api_key: str | None = None,
) -> str | None:
    if name in _HF_FAMILY and not _resolve_hf_key(hf_api_key):
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


def _clean_hf_model(value: str) -> str:
    return (value or "").strip().strip('"').strip("'")


def _split_hf_model(value: str) -> tuple[str, str | None]:
    """Support HF_CHAT_MODEL=Qwen/Qwen2.5-72B-Instruct:auto"""
    model = _clean_hf_model(value)
    if ":" in model and not model.startswith("http"):
        base, maybe_provider = model.rsplit(":", 1)
        if "/" in base and maybe_provider and "/" not in maybe_provider:
            return base, maybe_provider.strip().lower()
    return model, None


def _hf_provider_candidates(explicit: str | None) -> list[str]:
    ordered: list[str] = []
    for name in (
        (explicit or "").strip().lower(),
        (get_settings().hf_provider or "").strip().lower(),
        "auto",
        "novita",
        "fireworks-ai",
        "nebius",
        "deepinfra",
        "together",
        "sambanova",
        "hf-inference",
    ):
        if name and name not in ordered:
            ordered.append(name)
    return ordered


def _make_hf_client(token: str, provider: str):
    try:
        return InferenceClient(provider=provider, api_key=token)
    except TypeError:
        try:
            return InferenceClient(provider=provider, token=token)
        except TypeError:
            return InferenceClient(token=token)


def _hf_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    model_setting: str,
    label: str,
    hf_api_key: str | None = None,
) -> str:
    token = _resolve_hf_key(hf_api_key)
    if not token:
        raise LLMError("HF_TOKEN is not configured.")
    model, model_provider = _split_hf_model(model_setting)
    last_error: Exception | None = None
    for provider in _hf_provider_candidates(model_provider):
        try:
            api = _make_hf_client(token, provider)
            response = api.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = _hf_chat_content(response)
            if not content.strip():
                raise LLMError(f"{label} returned empty content.")
            if provider != "auto":
                logger.info(
                    "%s chat via provider=%s model=%s", label, provider, model
                )
            return content
        except LLMError:
            raise
        except Exception as exc:
            text = str(exc).lower()
            unsupported = (
                "model_not_supported" in text
                or "not supported by any provider" in text
                or "not supported by provider" in text
            )
            if unsupported:
                logger.warning(
                    "HF model %s not on provider %s: %s", model, provider, exc
                )
                last_error = exc
                continue
            last_error = exc
            break
    hint = (
        " Enable a host for this model at https://huggingface.co/settings/inference-providers "
        "or set HF_PROVIDER=auto so the router can pick a supported host."
    )
    raise LLMError(
        str(last_error) + hint if last_error else f"{label} chat failed." + hint
    )


def _huggingface_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    hf_api_key: str | None = None,
) -> str:
    return _hf_chat(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model_setting=get_settings().hf_chat_model,
        label="Hugging Face",
        hf_api_key=hf_api_key,
    )


def _deepseek_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    hf_api_key: str | None = None,
) -> str:
    return _hf_chat(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        model_setting=get_settings().hf_deepseek_model,
        label="DeepSeek",
        hf_api_key=hf_api_key,
    )


def _groq_chat(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    groq_api_key: str | None = None,
    groq_model: str | None = None,
) -> str:
    settings = get_settings()
    key = _resolve_groq_key(groq_api_key)
    if not key:
        raise LLMError("GROQ_API_KEY is not configured.")
    model = resolve_groq_model(groq_model, settings.groq_model)
    url = settings.groq_base_url.rstrip("/") + "/chat/completions"
    cap = max(256, int(getattr(settings, "groq_max_tokens", 4096) or 4096))
    if model.tpm:
        # Keep a single request under Free-plan TPM headroom.
        cap = min(cap, max(256, int(model.tpm) // 2))
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
    timeout = float(getattr(settings, "request_timeout_seconds", 120.0) or 120.0)
    for attempt in attempts:
        payload = {
            "model": model.id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": attempt,
        }
        with httpx.Client(timeout=timeout) as client:
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
    groq_model: str | None = None,
) -> tuple[str, str]:
    """Return (content, provider). Explicit Settings choice is exclusive."""
    exclusive = bool(provider and str(provider).strip())
    preferred = normalize_provider(provider)
    handlers = {
        "huggingface": _huggingface_chat,
        "deepseek": _deepseek_chat,
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
                kwargs["groq_model"] = groq_model
            if name in _HF_FAMILY:
                kwargs["hf_api_key"] = hf_api_key
            content = handlers[name](messages, **kwargs)
            return content, name
        except Exception as exc:
            logger.warning("%s chat failed: %s", name, exc)
            errors.append(f"{name}: {exc}")

    prefix = "Provider failed: " if exclusive else "All providers failed: "
    raise LLMError(prefix + "; ".join(errors))


def providers_status() -> list[dict[str, Any]]:
    settings = get_settings()
    default_groq = resolve_groq_model(settings.groq_model)
    return [
        {
            "id": "huggingface",
            "label": "Hugging Face",
            "available": settings.hf_configured,
            "model": settings.hf_chat_model,
        },
        {
            "id": "deepseek",
            "label": "DeepSeek",
            "available": settings.hf_configured,
            "model": settings.hf_deepseek_model,
        },
        {
            "id": "groq",
            "label": "Groq",
            "available": settings.groq_configured,
            "model": default_groq.id,
            "models": groq_models_payload(),
        },
    ]
