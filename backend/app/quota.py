"""Daily Hugging Face quota for the shared server token (IP + browser id)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

from app.cache import get_redis, redis_reachable
from app.config import get_settings

CLIENT_ID_HEADER = "X-Client-Id"


def uses_default_hf(provider: str | None, hf_api_key: str | None) -> bool:
    return (provider or "") == "huggingface" and not (hf_api_key or "").strip()


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


def _quota_keys(request: Request) -> tuple[str, str, int]:
    day, ttl, _ = utc_midnight_ttl()
    ip_key = f"deeplm:hfquota:{day}:ip:{client_ip(request)}"
    cid_key = f"deeplm:hfquota:{day}:cid:{client_id(request)}"
    return ip_key, cid_key, ttl


def peek_counts(request: Request) -> tuple[int, int] | None:
    client = get_redis()
    if client is None:
        return None
    ip_key, cid_key, _ = _quota_keys(request)
    try:
        ip_count = int(client.get(ip_key) or 0)
        cid_count = int(client.get(cid_key) or 0)
        return ip_count, cid_count
    except Exception:
        return None


def snapshot(request: Request, *, using_default_key: bool) -> dict:
    limit = int(get_settings().hf_default_daily_limit or 30)
    _, _, resets = utc_midnight_ttl()
    counts = peek_counts(request)
    used = max(counts) if counts else 0
    remaining = max(0, limit - used)
    return {
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "resets_at": resets.isoformat().replace("+00:00", "Z"),
        "using_default_key": using_default_key,
        "redis": redis_reachable(),
    }


def assert_can_generate(request: Request) -> None:
    limit = int(get_settings().hf_default_daily_limit or 30)
    if not redis_reachable():
        raise HTTPException(
            status_code=503,
            detail=(
                "Redis is required to use the default Hugging Face key. "
                "Paste your own HF token in Settings, or try again when Redis is up."
            ),
        )
    counts = peek_counts(request)
    if counts is not None and max(counts) >= limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Daily limit of {limit} default Hugging Face generations reached. "
                "Paste your own HF token in Settings or wait until UTC midnight."
            ),
        )


def consume(request: Request) -> None:
    client = get_redis()
    if client is None:
        return
    ip_key, cid_key, ttl = _quota_keys(request)
    try:
        pipe = client.pipeline()
        pipe.incr(ip_key)
        pipe.expire(ip_key, ttl)
        pipe.incr(cid_key)
        pipe.expire(cid_key, ttl)
        pipe.execute()
    except Exception:
        return
