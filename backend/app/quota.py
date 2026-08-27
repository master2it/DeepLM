"""Daily HF quota and Groq Free RPM/RPD quotas (IP + browser id)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException, Request

from app.cache import get_redis, redis_reachable
from app.config import get_settings
from app.groq_models import DEFAULT_GROQ_MODEL_ID, resolve_groq_model

logger = logging.getLogger(__name__)

CLIENT_ID_HEADER = "X-Client-Id"
QuotaKind = Literal["hf", "groq"]
HF_SERVER_DAILY_FLOOR = 50
GROQ_SERVER_DAILY_DEFAULT = 1000  # Free-plan RPD for most chat models

_LABELS = {"hf": "Hugging Face", "groq": "Groq"}


def uses_default_hf(provider: str | None, hf_api_key: str | None) -> bool:
    return (provider or "") in ("huggingface", "deepseek") and not (
        hf_api_key or ""
    ).strip()


def uses_default_groq(provider: str | None, groq_api_key: str | None) -> bool:
    return (provider or "") == "groq" and not (groq_api_key or "").strip()


def default_quota_kind(
    provider: str | None,
    hf_api_key: str | None,
    groq_api_key: str | None,
) -> QuotaKind | None:
    if uses_default_hf(provider, hf_api_key):
        return "hf"
    # Groq Free RPM/RPD apply with pasted key or server key.
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


def utc_hour_ttl() -> tuple[str, int, datetime]:
    now = datetime.now(timezone.utc)
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    resets = hour_start + timedelta(hours=1)
    ttl = max(60, int((resets - now).total_seconds()))
    return now.strftime("%Y-%m-%dT%H"), ttl, resets


def utc_minute_ttl() -> tuple[str, int, datetime]:
    now = datetime.now(timezone.utc)
    minute_start = now.replace(second=0, microsecond=0)
    resets = minute_start + timedelta(minutes=1)
    ttl = max(60, int((resets - now).total_seconds()) + 5)
    return now.strftime("%Y-%m-%dT%H:%M"), ttl, resets


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


def _daily_limit(kind: QuotaKind, *, groq_model: str | None = None) -> int:
    settings = get_settings()
    if kind == "groq":
        model = resolve_groq_model(groq_model, settings.groq_model)
        return int(model.rpd or GROQ_SERVER_DAILY_DEFAULT)
    configured = int(settings.hf_default_daily_limit or HF_SERVER_DAILY_FLOOR)
    return max(HF_SERVER_DAILY_FLOOR, configured)


def _rpm_limit(groq_model: str | None = None) -> int:
    settings = get_settings()
    model = resolve_groq_model(groq_model, settings.groq_model)
    return int(model.rpm or 30)


def _model_slug(groq_model: str | None) -> str:
    settings = get_settings()
    model = resolve_groq_model(groq_model, settings.groq_model)
    return model.id.replace("/", "_")


def _hf_quota_keys(request: Request) -> tuple[str, str, int]:
    bucket, ttl, _ = utc_midnight_ttl()
    ip_key = f"deeplm:hfquota:{bucket}:ip:{client_ip(request)}"
    cid_key = f"deeplm:hfquota:{bucket}:cid:{client_id(request)}"
    return ip_key, cid_key, ttl


def _groq_day_keys(
    request: Request, groq_model: str | None
) -> tuple[str, str, int]:
    bucket, ttl, _ = utc_midnight_ttl()
    slug = _model_slug(groq_model)
    ip_key = f"deeplm:groqquota:day:{bucket}:m:{slug}:ip:{client_ip(request)}"
    cid_key = f"deeplm:groqquota:day:{bucket}:m:{slug}:cid:{client_id(request)}"
    return ip_key, cid_key, ttl


def _groq_minute_keys(
    request: Request, groq_model: str | None
) -> tuple[str, str, int]:
    bucket, ttl, _ = utc_minute_ttl()
    slug = _model_slug(groq_model)
    ip_key = f"deeplm:groqquota:min:{bucket}:m:{slug}:ip:{client_ip(request)}"
    cid_key = f"deeplm:groqquota:min:{bucket}:m:{slug}:cid:{client_id(request)}"
    return ip_key, cid_key, ttl


def _quota_keys(
    request: Request, kind: QuotaKind, *, groq_model: str | None = None
) -> tuple[str, str, int]:
    """Legacy helper used by tests — HF day keys or Groq day keys."""
    if kind == "groq":
        return _groq_day_keys(request, groq_model)
    return _hf_quota_keys(request)


def peek_counts(request: Request, kind: QuotaKind, *, groq_model: str | None = None) -> tuple[int, int] | None:
    client = get_redis()
    if client is None:
        return None
    if kind == "groq":
        ip_key, cid_key, _ = _groq_day_keys(request, groq_model)
    else:
        ip_key, cid_key, _ = _hf_quota_keys(request)
    try:
        ip_count = int(client.get(ip_key) or 0)
        cid_count = int(client.get(cid_key) or 0)
        return ip_count, cid_count
    except Exception:
        return None


def peek_rpm_counts(
    request: Request, *, groq_model: str | None = None
) -> tuple[int, int] | None:
    client = get_redis()
    if client is None:
        return None
    ip_key, cid_key, _ = _groq_minute_keys(request, groq_model)
    try:
        return int(client.get(ip_key) or 0), int(client.get(cid_key) or 0)
    except Exception:
        return None


def _kind_snapshot(
    request: Request,
    kind: QuotaKind,
    *,
    using_default_key: bool,
    groq_model: str | None = None,
) -> dict:
    if kind == "groq":
        settings = get_settings()
        model = resolve_groq_model(groq_model, settings.groq_model)
        day_limit = int(model.rpd)
        rpm_limit = int(model.rpm)
        day_counts = peek_counts(request, "groq", groq_model=model.id)
        rpm_counts = peek_rpm_counts(request, groq_model=model.id)
        day_used = max(day_counts) if day_counts else 0
        rpm_used = max(rpm_counts) if rpm_counts else 0
        _, _, day_resets = utc_midnight_ttl()
        _, _, minute_resets = utc_minute_ttl()
        return {
            "limit": day_limit,
            "used": day_used,
            "remaining": max(0, day_limit - day_used),
            "using_default_key": using_default_key,
            "period": "day",
            "resets_at": day_resets.isoformat().replace("+00:00", "Z"),
            "model": model.id,
            "rpm_limit": rpm_limit,
            "rpm_used": rpm_used,
            "rpm_remaining": max(0, rpm_limit - rpm_used),
            "rpm_resets_at": minute_resets.isoformat().replace("+00:00", "Z"),
            "tpm": model.tpm,
            "tpd": model.tpd,
        }

    limit = _daily_limit("hf")
    counts = peek_counts(request, "hf")
    used = max(counts) if counts else 0
    remaining = max(0, limit - used)
    _, _, resets = utc_midnight_ttl()
    return {
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "using_default_key": using_default_key,
        "period": "day",
        "resets_at": resets.isoformat().replace("+00:00", "Z"),
    }


def snapshot(
    request: Request,
    *,
    own_hf_key: bool = False,
    own_groq_key: bool = False,
    groq_model: str | None = None,
) -> dict:
    _, _, resets = utc_midnight_ttl()
    return {
        "resets_at": resets.isoformat().replace("+00:00", "Z"),
        "redis": redis_reachable(),
        "huggingface": _kind_snapshot(
            request, "hf", using_default_key=not own_hf_key
        ),
        "groq": _kind_snapshot(
            request,
            "groq",
            using_default_key=not own_groq_key,
            groq_model=groq_model,
        ),
    }


def assert_can_generate(
    request: Request,
    kind: QuotaKind,
    *,
    groq_model: str | None = None,
) -> None:
    label = _LABELS[kind]
    if not redis_reachable():
        if kind == "groq":
            detail = (
                "Redis is required to enforce Groq Free plan RPM/RPD limits "
                "(your key or the server key). Try again when Redis is up."
            )
        else:
            detail = (
                f"Redis is required to use the default {label} key. "
                f"Paste your own {label} token in Settings, or try again when Redis is up."
            )
        raise HTTPException(status_code=503, detail=detail)

    if kind == "groq":
        settings = get_settings()
        model = resolve_groq_model(groq_model, settings.groq_model)
        day_limit = int(model.rpd)
        rpm_limit = int(model.rpm)
        day_counts = peek_counts(request, "groq", groq_model=model.id)
        if day_counts is not None and max(day_counts) >= day_limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Groq Free daily limit of {day_limit} requests for {model.label} "
                    "reached (your key or the server key). Wait until UTC midnight. "
                    "Cached repeats do not count. "
                    "See https://console.groq.com/docs/rate-limits"
                ),
            )
        rpm_counts = peek_rpm_counts(request, groq_model=model.id)
        if rpm_counts is not None and max(rpm_counts) >= rpm_limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Groq Free rate limit of {rpm_limit} requests/minute for "
                    f"{model.label} reached. Wait a minute and try again. "
                    "See https://console.groq.com/docs/rate-limits"
                ),
            )
        return

    limit = _daily_limit("hf")
    counts = peek_counts(request, "hf")
    if counts is not None and max(counts) >= limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Daily limit of {limit} default {label} generations reached. "
                f"Paste your own {label} token in Settings or wait until UTC midnight."
            ),
        )


def _incr_with_ttl(client, key: str, ttl: int) -> None:
    # Separate commands (not MULTI/EXEC): clustered Redis rejects pipelines
    # that touch two keys in different slots, which silently dropped quotas.
    client.incr(key)
    client.expire(key, ttl)


def consume(
    request: Request,
    kind: QuotaKind,
    *,
    groq_model: str | None = None,
) -> None:
    client = get_redis()
    if client is None:
        logger.warning("Quota consume skipped: Redis unavailable")
        return
    try:
        if kind == "groq":
            day_ip, day_cid, day_ttl = _groq_day_keys(request, groq_model)
            min_ip, min_cid, min_ttl = _groq_minute_keys(request, groq_model)
            _incr_with_ttl(client, day_ip, day_ttl)
            _incr_with_ttl(client, day_cid, day_ttl)
            _incr_with_ttl(client, min_ip, min_ttl)
            _incr_with_ttl(client, min_cid, min_ttl)
            return
        ip_key, cid_key, ttl = _hf_quota_keys(request)
        _incr_with_ttl(client, ip_key, ttl)
        _incr_with_ttl(client, cid_key, ttl)
    except Exception as exc:
        logger.warning("Quota consume failed: %s", exc)
