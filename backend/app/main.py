"""FastAPI entrypoint."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.constants import (
    MAX_INPUT_CHARS,
    DEFAULT_GRAMMAR_FROM,
    DEFAULT_GRAMMAR_TO,
    DEFAULT_TENSE_LANGUAGE,
    GERMAN_TENSES,
    GRAMMAR_LANGUAGES,
    LANGUAGE_LOCALES,
    RTL_TARGETS,
    STYLE_VARIANTS,
    TENSE_COUNTS,
    TENSE_LANGUAGES,
    resolve_locale,
)
from app.cache import fold_user_text, get_cached, redis_reachable, save_cached
from app.changelog import load_changelog
from app.grammar import get_styled_translations_from_ai
from app.llm import providers_status
from app.quota import (
    assert_can_generate,
    consume,
    default_quota_kind,
    snapshot,
    _daily_limit,
)
from app.tenses import get_tense_explanation_from_ai, get_tenses_from_ai
from app.version import APP_VERSION

settings = get_settings()

app = FastAPI(title="DeepLM API", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ProviderField = Literal["ollama", "huggingface", "groq"]


class GrammarRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_INPUT_CHARS)
    from_lang: str = DEFAULT_GRAMMAR_FROM
    to_lang: str = DEFAULT_GRAMMAR_TO
    to_locale: str | None = None
    context: str | None = None
    provider: ProviderField | None = None
    groq_api_key: str | None = None
    hf_api_key: str | None = None


class TensesRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_INPUT_CHARS)
    language: str = DEFAULT_TENSE_LANGUAGE
    provider: ProviderField | None = None
    groq_api_key: str | None = None
    hf_api_key: str | None = None


class TenseExplainRequest(BaseModel):
    tense: str = Field(..., min_length=1)
    language: str = DEFAULT_TENSE_LANGUAGE
    provider: ProviderField | None = None
    groq_api_key: str | None = None
    hf_api_key: str | None = None


@app.get("/health")
def health():
    providers = providers_status()
    by_id = {p["id"]: p for p in providers}
    return {
        "ok": True,
        "version": APP_VERSION,
        "ollama": by_id["ollama"]["available"],
        "ollama_enabled": get_settings().ollama_enabled,
        "default_provider": "huggingface",
        "hf_configured": by_id["huggingface"]["available"],
        "groq_configured": by_id["groq"]["available"],
        "ollama_model": by_id["ollama"]["model"],
        "hf_model": by_id["huggingface"]["model"],
        "groq_model": by_id["groq"]["model"],
        "providers": providers,
        "hf_default_daily_limit": _daily_limit("hf"),
        "groq_default_daily_limit": _daily_limit("groq"),
        "redis": redis_reachable(),
    }


@app.get("/api/providers")
def api_providers():
    return health()


@app.get("/api/changelog")
def changelog():
    return load_changelog()


@app.get("/api/languages")
def languages():
    return {
        "max_input_chars": MAX_INPUT_CHARS,
        "languages": GRAMMAR_LANGUAGES,
        "rtl": sorted(RTL_TARGETS),
        "default_from": DEFAULT_GRAMMAR_FROM,
        "default_to": DEFAULT_GRAMMAR_TO,
        "locales": {lang: list(opts) for lang, opts in LANGUAGE_LOCALES.items()},
        "default_locales": {lang: opts[0] for lang, opts in LANGUAGE_LOCALES.items()},
        "styles": [{"label": label, "key": key} for label, key in STYLE_VARIANTS],
        "tense_languages": TENSE_LANGUAGES,
        "default_tense_language": DEFAULT_TENSE_LANGUAGE,
        "tense_counts": TENSE_COUNTS,
        "german_tenses": [
            {"key": key, "label": label} for key, label in GERMAN_TENSES
        ],
    }


def _run_generation(
    http_request: Request,
    provider: str | None,
    hf_api_key: str | None,
    groq_api_key: str | None,
    *,
    kind: str | None,
    parts: dict | None,
    producer,
):
    quota_kind = default_quota_kind(provider, hf_api_key, groq_api_key)
    if kind and parts is not None:
        hit = get_cached(kind, parts)
        if hit is not None:
            return hit
    if quota_kind:
        assert_can_generate(http_request, quota_kind)
    result = producer()
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])
    if isinstance(result, dict):
        result.pop("cached", None)
    if kind and parts is not None and isinstance(result, dict):
        save_cached(kind, parts, result)
    if quota_kind:
        consume(http_request, quota_kind)
    return result


@app.get("/api/limits")
def api_limits(
    request: Request,
    own_hf_key: bool = False,
    own_groq_key: bool = False,
):
    return JSONResponse(
        snapshot(request, own_hf_key=own_hf_key, own_groq_key=own_groq_key),
        headers={"Cache-Control": "no-store"},
    )


@app.post("/api/grammar")
def grammar(req: GrammarRequest, request: Request):
    text = fold_user_text(req.text)
    locale = resolve_locale(req.to_lang, req.to_locale)
    return _run_generation(
        request,
        req.provider,
        req.hf_api_key,
        req.groq_api_key,
        kind="grammar",
        parts={
            "text": text,
            "from_lang": req.from_lang,
            "to_lang": req.to_lang,
            "to_locale": locale,
            "context": req.context or "",
            "provider": req.provider or "",
        },
        producer=lambda: get_styled_translations_from_ai(
            text,
            from_lang=req.from_lang,
            to_lang=req.to_lang,
            to_locale=locale,
            context=req.context,
            provider=req.provider,
            groq_api_key=req.groq_api_key,
            hf_api_key=req.hf_api_key,
        ),
    )


@app.post("/api/tenses")
def tenses(req: TensesRequest, request: Request):
    text = fold_user_text(req.text)
    return _run_generation(
        request,
        req.provider,
        req.hf_api_key,
        req.groq_api_key,
        kind="tenses",
        parts={
            "text": text,
            "language": req.language,
            "provider": req.provider or "",
        },
        producer=lambda: get_tenses_from_ai(
            text,
            language=req.language,
            provider=req.provider,
            groq_api_key=req.groq_api_key,
            hf_api_key=req.hf_api_key,
        ),
    )


@app.post("/api/tenses/explain")
def tenses_explain(req: TenseExplainRequest, request: Request):
    return _run_generation(
        request,
        req.provider,
        req.hf_api_key,
        req.groq_api_key,
        kind="tenses_explain",
        parts={
            "tense": req.tense.strip(),
            "language": req.language,
            "provider": req.provider or "",
        },
        producer=lambda: get_tense_explanation_from_ai(
            req.tense.strip(),
            language=req.language,
            provider=req.provider,
            groq_api_key=req.groq_api_key,
            hf_api_key=req.hf_api_key,
        ),
    )
