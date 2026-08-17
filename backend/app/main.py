"""FastAPI entrypoint."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import get_settings
from app.constants import (
    DEFAULT_GRAMMAR_FROM,
    DEFAULT_GRAMMAR_TO,
    GRAMMAR_LANGUAGES,
    RTL_TARGETS,
    STYLE_VARIANTS,
)
from app.grammar import get_styled_translations_from_ai
from app.llm import providers_status
from app.tenses import get_tense_explanation_from_ai, get_tenses_from_ai

settings = get_settings()

app = FastAPI(title="DeepLM API", version="2.0.0")
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
    text: str = Field(..., min_length=1)
    from_lang: str = DEFAULT_GRAMMAR_FROM
    to_lang: str = DEFAULT_GRAMMAR_TO
    context: str | None = None
    provider: ProviderField | None = None
    groq_api_key: str | None = None


class TensesRequest(BaseModel):
    text: str = Field(..., min_length=1)
    provider: ProviderField | None = None
    groq_api_key: str | None = None


class TenseExplainRequest(BaseModel):
    tense: str = Field(..., min_length=1)
    provider: ProviderField | None = None
    groq_api_key: str | None = None


@app.get("/health")
def health():
    providers = providers_status()
    by_id = {p["id"]: p for p in providers}
    return {
        "ok": True,
        "ollama": by_id["ollama"]["available"],
        "hf_configured": by_id["huggingface"]["available"],
        "groq_configured": by_id["groq"]["available"],
        "ollama_model": by_id["ollama"]["model"],
        "hf_model": by_id["huggingface"]["model"],
        "groq_model": by_id["groq"]["model"],
        "providers": providers,
        "default_provider": "ollama",
    }


@app.get("/api/providers")
def api_providers():
    return health()


@app.get("/api/languages")
def languages():
    return {
        "languages": GRAMMAR_LANGUAGES,
        "rtl": sorted(RTL_TARGETS),
        "default_from": DEFAULT_GRAMMAR_FROM,
        "default_to": DEFAULT_GRAMMAR_TO,
        "styles": [{"label": label, "key": key} for label, key in STYLE_VARIANTS],
    }


@app.post("/api/grammar")
def grammar(req: GrammarRequest):
    result = get_styled_translations_from_ai(
        req.text.strip(),
        from_lang=req.from_lang,
        to_lang=req.to_lang,
        context=req.context,
        provider=req.provider,
        groq_api_key=req.groq_api_key,
    )
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.post("/api/tenses")
def tenses(req: TensesRequest):
    result = get_tenses_from_ai(
        req.text.strip(), provider=req.provider, groq_api_key=req.groq_api_key
    )
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@app.post("/api/tenses/explain")
def tenses_explain(req: TenseExplainRequest):
    result = get_tense_explanation_from_ai(
        req.tense.strip(), provider=req.provider, groq_api_key=req.groq_api_key
    )
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=502, detail=result["error"])
    return result
