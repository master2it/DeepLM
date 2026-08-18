"""Canonical-then-style grammar / spell fixer."""

from __future__ import annotations

import json

from app.constants import (
    DEFAULT_GRAMMAR_FROM,
    DEFAULT_GRAMMAR_TO,
    GERMAN_PERSIAN_RULES,
    LEGACY_STYLE_KEYS,
    SEMANTIC_ACCURACY_RULES,
    STRUCTURE_FORMAT_RULES,
    STYLE_VARIANTS,
    TARGET_LANGUAGES,
    TEACHER_EDITOR_INSTRUCTION,
    _GERMAN_READY_FIRST_PERSON_RE,
    _PERSIAN_EXPLICIT_I_RE,
    _PERSIAN_IT_READY_RE,
    _READY_FIRST_PERSON_RE,
    native_target_label,
)
from app.jsonutil import parse_model_json
from app.llm import LLMError, chat


def persian_implies_impersonal_ready(text: str) -> bool:
    if not text:
        return False
    if _PERSIAN_EXPLICIT_I_RE.search(text):
        return False
    return bool(_PERSIAN_IT_READY_RE.search(text))


def english_invents_speaker_ready(text: str) -> bool:
    return bool(text and _READY_FIRST_PERSON_RE.search(text))


def german_invents_speaker_ready(text: str) -> bool:
    return bool(text and _GERMAN_READY_FIRST_PERSON_RE.search(text))


def target_invents_speaker_ready(text: str) -> bool:
    return english_invents_speaker_ready(text) or german_invents_speaker_ready(text)


def collect_style_to_texts(data: dict | None) -> list[str]:
    texts = []
    keys = [key for _label, key in STYLE_VARIANTS] + list(LEGACY_STYLE_KEYS)
    for key in keys:
        item = (data or {}).get(key) or {}
        if isinstance(item, dict):
            t = (item.get("to") or "").strip()
            if t:
                texts.append(t)
        elif isinstance(item, str) and item.strip():
            texts.append(item.strip())
    for extra in ("canonical_meaning", "best_version", "intended_meaning"):
        t = ((data or {}).get(extra) or "").strip()
        if t:
            texts.append(t)
    return texts


def flagged_invented_ready_subject(source_text: str, result: dict) -> bool:
    if not persian_implies_impersonal_ready(source_text):
        return False
    return any(target_invents_speaker_ready(t) for t in collect_style_to_texts(result))


def _style_pair(item) -> dict[str, str]:
    if isinstance(item, str):
        return {"from": item.strip(), "to": ""}
    if not isinstance(item, dict):
        return {"from": "", "to": ""}
    return {
        "from": (item.get("from") or "").strip(),
        "to": (item.get("to") or "").strip(),
    }


def _first_style_pair(data: dict, *keys: str) -> dict[str, str]:
    for key in keys:
        if key in data and data.get(key) not in (None, ""):
            pair = _style_pair(data.get(key))
            if pair["from"] or pair["to"]:
                return pair
    return {"from": "", "to": ""}


def parse_styled_translation_response(
    data, *, src_hint: str, tgt: str, wants_translation: bool
) -> dict:
    if not isinstance(data, dict):
        return {"error": "Unexpected model response."}

    detected = (data.get("detected_lang") or src_hint or "").strip() or src_hint
    native = _first_style_pair(data, "native", "everyday_neutral")
    friendly = _first_style_pair(data, "friendly", "friendly_casual")
    professional = _first_style_pair(data, "professional", "professional_formal")
    literal = _first_style_pair(data, "literal")
    canonical = (data.get("canonical_meaning") or "").strip()
    best_version = (data.get("best_version") or canonical or native.get("from") or "").strip()
    if not canonical:
        canonical = best_version
    if wants_translation:
        if not native["from"]:
            native["from"] = best_version
        if not friendly["from"]:
            friendly["from"] = native["from"] or best_version
        if not professional["from"]:
            professional["from"] = native["from"] or best_version
        if not literal["from"]:
            literal["from"] = native["from"] or best_version
    return {
        "from_lang": detected,
        "to_lang": tgt,
        "wants_translation": wants_translation,
        "intended_meaning": (data.get("intended_meaning") or "").strip(),
        "best_version": best_version,
        "canonical_meaning": canonical,
        "subject_reading": (data.get("subject_reading") or "").strip(),
        "grammar_notes": "",
        "native": native,
        "friendly": friendly,
        "professional": professional,
        "literal": literal,
        "friendly_casual": friendly,
        "professional_formal": professional,
        "everyday_neutral": native,
    }


def build_styled_translation_prompt(
    *,
    src_hint: str,
    tgt: str,
    wants_translation: bool,
    context=None,
    retry_feedback=None,
) -> tuple[str, str]:
    tgt_label = native_target_label(tgt)
    pair = {src_hint, tgt}
    german_persian = pair == {"German", "Persian"}
    pair_rules = f"\n{GERMAN_PERSIAN_RULES}\n" if german_persian else ""

    translation_block = (
        f"Write Native, Friendly, Professional, and Literal in {tgt_label}.\n"
        f'"from" = silently grammar-enhanced {src_hint} (same enhanced source on native/friendly/professional).\n'
        f'"to" = that version in {tgt_label}. Native = how a local would say it; '
        f"Friendly = more relaxed; Professional = natural workplace; Literal = close wording.\n"
        f"Do not explain anything. Same who/what/when in all four. Keep source layout."
        if wants_translation
        else (
            "Stay in the source language. Put each version in \"from\" and set \"to\" to empty.\n"
            "Native / Friendly / Professional / Literal as defined. Do not explain anything."
        )
    )

    context_block = (
        f"Surrounding conversation/context (use only to resolve ambiguous subjects):\n{context}\n"
        if context and str(context).strip()
        else "No extra conversation context was provided.\n"
    )

    retry_block = (
        f"\nPREVIOUS ATTEMPT WAS REJECTED:\n{retry_feedback}\n"
        "Fix the subject/meaning errors. Do not invent a first-person subject.\n"
        if retry_feedback
        else ""
    )

    system_prompt = f"""
{TEACHER_EDITOR_INSTRUCTION}

SEMANTIC ACCURACY (mandatory):
{SEMANTIC_ACCURACY_RULES}

STRUCTURE AND FORMAT (mandatory):
{STRUCTURE_FORMAT_RULES}

Task:
1. Treat the input as {src_hint} (detect if the UI hint is wrong).
2. {translation_block}
{pair_rules}
{context_block}
{retry_block}
Output ONLY valid JSON (no markdown, no commentary, no grammar notes).
Escape every double quote inside string values as \\".
Use \\n for line breaks inside strings — never a raw newline.
{{
    "detected_lang": "<detected language name>",
    "native": {{"from": "<enhanced source>", "to": "<Native {tgt} or empty>"}},
    "friendly": {{"from": "<same enhanced source>", "to": "<Friendly {tgt} or empty>"}},
    "professional": {{"from": "<same enhanced source>", "to": "<Professional {tgt} or empty>"}},
    "literal": {{"from": "<source close to original wording>", "to": "<Literal {tgt} or empty>"}}
}}
""".strip()

    if wants_translation:
        user_msg = (
            f"Rewrite this {src_hint} so it sounds like a native, then give Native, Friendly, "
            f"Professional, and Literal in {tgt_label}. Silent grammar fixes only. "
            "Keep the same structure as the source.\n\n"
            "Text:\n{text}"
        )
    else:
        user_msg = (
            "Rewrite this so it sounds like a native. Give Native, Friendly, Professional, "
            "and Literal in the same language. Silent grammar fixes only.\n\n"
            "Text:\n{text}"
        )

    return system_prompt, user_msg


def get_styled_translations_from_ai(
    text: str,
    from_lang: str = DEFAULT_GRAMMAR_FROM,
    to_lang: str = DEFAULT_GRAMMAR_TO,
    context=None,
    provider: str | None = None,
    groq_api_key: str | None = None,
    hf_api_key: str | None = None,
) -> dict:
    src_hint = from_lang if from_lang in TARGET_LANGUAGES else DEFAULT_GRAMMAR_FROM
    tgt = to_lang if to_lang in TARGET_LANGUAGES else DEFAULT_GRAMMAR_TO
    wants_translation = src_hint != tgt
    used_provider = "huggingface"

    def _once(retry_feedback=None):
        nonlocal used_provider
        system_prompt, user_template = build_styled_translation_prompt(
            src_hint=src_hint,
            tgt=tgt,
            wants_translation=wants_translation,
            context=context,
            retry_feedback=retry_feedback,
        )
        user_msg = user_template.replace("{text}", text)
        content, used_provider = chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.15,
            max_tokens=4096,
            provider=provider,
            groq_api_key=groq_api_key,
            hf_api_key=hf_api_key,
        )
        raw = parse_model_json(content)
        parsed = parse_styled_translation_response(
            raw,
            src_hint=src_hint,
            tgt=tgt,
            wants_translation=wants_translation,
        )
        parsed["provider"] = used_provider
        return parsed

    try:
        result = _once()
        if "error" in result:
            return result
        if wants_translation and flagged_invented_ready_subject(text, result):
            result = _once(
                retry_feedback=(
                    "You translated impersonal Persian 'آماده میشه/می‌شود' as if the SPEAKER "
                    "will be ready ('I'll be ready' / 'ich bin bereit'). That is wrong. "
                    "Use neutral 'it will be ready' / 'it'll be ready' / German 'es wird fertig', "
                    "and for pickup use 'come pick it up' / 'come by to collect it' / 'abholen'."
                )
            )
        result["provider"] = used_provider
        return result
    except json.JSONDecodeError:
        try:
            result = _once(
                retry_feedback=(
                    "Your previous reply was not valid JSON (broken quotes or truncated). "
                    "Reply with one complete JSON object only. Escape quotes as \\\". "
                    "Use \\n for line breaks inside strings."
                )
            )
            if "error" not in result:
                result["provider"] = used_provider
            return result
        except json.JSONDecodeError:
            return {
                "error": (
                    "The model returned invalid JSON for this text. "
                    "Try again, or shorten the input (max 1000 characters)."
                )
            }
    except LLMError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
