"""JSON cache for grammar, tenses, and tense explanations. Redis is optional."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

CACHE_SCHEMA = 3
_client = None
_client_failed = False


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def make_cache_key(kind: str, parts: dict[str, Any]) -> str:
    settings = get_settings()
    payload = {
        "v": CACHE_SCHEMA,
        "kind": kind,
        "text": _normalize_text(str(parts.get("text") or "")),
        "from_lang": parts.get("from_lang") or "",
        "to_lang": parts.get("to_lang") or "",
        "language": parts.get("language") or "",
        "tense": parts.get("tense") or "",
        "context": _normalize_text(str(parts.get("context") or "")),
        "provider": parts.get("provider") or "",
        "ollama_model": settings.ollama_model,
        "hf_model": settings.hf_chat_model,
        "groq_model": settings.groq_model,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"deeplm:{kind}:{digest}"


def redis_enabled() -> bool:
    return bool(get_settings().resolved_redis_url)


def get_redis():
    global _client, _client_failed
    if _client_failed:
        return None
    if _client is not None:
        return _client
    url = get_settings().resolved_redis_url
    if not url:
        return None
    try:
        import redis

        client = redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=1.5,
            socket_timeout=1.5,
        )
        client.ping()
        _client = client
        return _client
    except Exception as exc:
        logger.warning("Redis unavailable: %s", exc)
        _client_failed = True
        return None


def redis_reachable() -> bool:
    client = get_redis()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except Exception:
        return False


def cache_get(key: str) -> dict | None:
    client = get_redis()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.warning("Redis get failed: %s", exc)
    return None


def cache_set(key: str, value: dict) -> None:
    client = get_redis()
    if client is None:
        return
    ttl = max(60, int(get_settings().redis_ttl_seconds or 43200))
    try:
        payload = {k: v for k, v in value.items() if k != "cached"}
        client.set(key, json.dumps(payload, ensure_ascii=False), ex=ttl)
    except Exception as exc:
        logger.warning("Redis set failed: %s", exc)


def get_cached(kind: str, parts: dict[str, Any]) -> dict | None:
    hit = cache_get(make_cache_key(kind, parts))
    if hit is None:
        return None
    hit["cached"] = True
    return hit


def save_cached(kind: str, parts: dict[str, Any], result: dict) -> None:
    if result.get("error"):
        return
    cache_set(make_cache_key(kind, parts), result)


def cached_result(kind: str, parts: dict[str, Any], producer):
    """Return cached dict or call producer(). Never stores Groq keys or errors."""
    hit = get_cached(kind, parts)
    if hit is not None:
        return hit
    result = producer()
    if isinstance(result, dict):
        save_cached(kind, parts, result)
    return result
