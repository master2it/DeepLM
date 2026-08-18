"""Daily quota for shared server HF/Groq tokens (IP + browser id)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException, Request

from app.cache import get_redis, redis_reachable
from app.config import get_settings

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
    if uses_default_groq(provider, groq_api_key):
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
        raise HTTPException(
            status_code=503,
            detail=(
                f"Redis is required to use the default {label} key. "
                f"Paste your own {label} token in Settings, or try again when Redis is up."
            ),
        )
    counts = peek_counts(request, kind)
    if counts is not None and max(counts) >= limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Daily limit of {limit} default {label} generations reached. "
                f"Paste your own {label} token in Settings or wait until UTC midnight."
            ),
        )


def consume(request: Request, kind: QuotaKind) -> None:
    client = get_redis()
    if client is None:
        return
    ip_key, cid_key, ttl = _quota_keys(request, kind)
    try:
        pipe = client.pipeline()
        pipe.incr(ip_key)
        pipe.expire(ip_key, ttl)
        pipe.incr(cid_key)
        pipe.expire(cid_key, ttl)
        pipe.execute()
    except Exception:
        return
