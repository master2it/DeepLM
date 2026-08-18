"""Daily quota for shared server HF/Groq tokens (IP + browser id)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException, Request

from app.cache import get_redis, redis_reachable
from app.config import get_settings

logger = logging.getLogger(__name__)

CLIENT_ID_HEADER = "X-Client-Id"
QuotaKind = Literal["hf", "groq"]

_LABELS = {"hf": "Hugging Face", "groq": "Groq"}


def uses_default_hf(provider: str | None, hf_api_key: str | None) -> bool:
    return (provider or "") == "huggingface" and not (hf_api_key or "").strip()


def uses_default_groq(provider: str | None, groq_api_key: str | None) -> bool:
    return (provider or "") == "groq" and not (groq_api_key or "").strip()


def default_quota_kind(
    provider: str | None,
    hf_api_key: str | None,
    groq_api_key: str | None,
) -> QuotaKind | None:
    if uses_default_hf(provider, hf_api_key):
        return "hf"
    # Groq free-tier is 30/day even with a pasted token.
    if (provider or "") == "groq":
        return "groq"
    return None


def utc_midnight_ttl() -> tuple[str, int, datetime]:
    now = datetime.now(timezone.utc)
    resets = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) + timedelta(
        days=1
    )
    ttl = max(60, int((resets - now).total_seconds()))
    return now.strftime("%Y-%m-%d"), ttl, resets


def client_ip(request: Request) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def client_id(request: Request) -> str:
    raw = (request.headers.get(CLIENT_ID_HEADER) or "").strip()
    if not raw or len(raw) > 64:
        return "anonymous"
    safe = "".join(ch for ch in raw if ch.isalnum() or ch in "-_")
    return safe or "anonymous"


def _daily_limit(kind: QuotaKind) -> int:
    settings = get_settings()
    if kind == "groq":
        return int(getattr(settings, "groq_default_daily_limit", 30) or 30)
    return int(settings.hf_default_daily_limit or 30)


def _quota_keys(request: Request, kind: QuotaKind) -> tuple[str, str, int]:
    day, ttl, _ = utc_midnight_ttl()
    prefix = "hfquota" if kind == "hf" else "groqquota"
    ip_key = f"deeplm:{prefix}:{day}:ip:{client_ip(request)}"
    cid_key = f"deeplm:{prefix}:{day}:cid:{client_id(request)}"
    return ip_key, cid_key, ttl


def peek_counts(request: Request, kind: QuotaKind) -> tuple[int, int] | None:
    client = get_redis()
    if client is None:
        return None
    ip_key, cid_key, _ = _quota_keys(request, kind)
    try:
        ip_count = int(client.get(ip_key) or 0)
        cid_count = int(client.get(cid_key) or 0)
        return ip_count, cid_count
    except Exception:
        return None


def _kind_snapshot(request: Request, kind: QuotaKind, *, using_default_key: bool) -> dict:
    limit = _daily_limit(kind)
    counts = peek_counts(request, kind)
    used = max(counts) if counts else 0
    remaining = max(0, limit - used)
    return {
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "using_default_key": using_default_key,
    }


def snapshot(
    request: Request,
    *,
    own_hf_key: bool = False,
    own_groq_key: bool = False,
) -> dict:
    _, _, resets = utc_midnight_ttl()
    return {
        "resets_at": resets.isoformat().replace("+00:00", "Z"),
        "redis": redis_reachable(),
        "huggingface": _kind_snapshot(
            request, "hf", using_default_key=not own_hf_key
        ),
        "groq": _kind_snapshot(request, "groq", using_default_key=not own_groq_key),
    }


def assert_can_generate(request: Request, kind: QuotaKind) -> None:
    limit = _daily_limit(kind)
    label = _LABELS[kind]
    if not redis_reachable():
        if kind == "groq":
            detail = (
                "Redis is required to enforce the Groq 30/day limit "
                "(your key or the server key). Try again when Redis is up."
            )
        else:
            detail = (
                f"Redis is required to use the default {label} key. "
                f"Paste your own {label} token in Settings, or try again when Redis is up."
            )
        raise HTTPException(status_code=503, detail=detail)
    counts = peek_counts(request, kind)
    if counts is not None and max(counts) >= limit:
        if kind == "groq":
            detail = (
                f"Daily Groq limit of {limit} generations reached "
                "(your key or the server key). Wait until UTC midnight. "
                "Repeat searches already in cache do not count."
            )
        else:
            detail = (
                f"Daily limit of {limit} default {label} generations reached. "
                f"Paste your own {label} token in Settings or wait until UTC midnight."
            )
        raise HTTPException(status_code=429, detail=detail)


def _incr_with_ttl(client, key: str, ttl: int) -> None:
    # Separate commands (not MULTI/EXEC): clustered Redis rejects pipelines
    # that touch two keys in different slots, which silently dropped quotas.
    client.incr(key)
    client.expire(key, ttl)


def consume(request: Request, kind: QuotaKind) -> None:
    client = get_redis()
    if client is None:
        logger.warning("Quota consume skipped: Redis unavailable")
        return
    ip_key, cid_key, ttl = _quota_keys(request, kind)
    try:
        _incr_with_ttl(client, ip_key, ttl)
        _incr_with_ttl(client, cid_key, ttl)
    except Exception as exc:
        logger.warning("Quota consume failed: %s", exc)
