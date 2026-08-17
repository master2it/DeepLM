"""Canonical-then-style grammar / spell fixer."""

from __future__ import annotations

import json

from app.constants import (
    DEFAULT_GRAMMAR_FROM,
    DEFAULT_GRAMMAR_TO,
    SEMANTIC_ACCURACY_RULES,
    STYLE_VARIANTS,
    TARGET_LANGUAGES,
    TEACHER_EDITOR_INSTRUCTION,
    _PERSIAN_EXPLICIT_I_RE,
    _PERSIAN_IT_READY_RE,
    _READY_FIRST_PERSON_RE,
)
from app.jsonutil import extract_json
from app.llm import LLMError, chat


def persian_implies_impersonal_ready(text: str) -> bool:
    if not text:
        return False
    if _PERSIAN_EXPLICIT_I_RE.search(text):
        return False
    return bool(_PERSIAN_IT_READY_RE.search(text))


def english_invents_speaker_ready(text: str) -> bool:
    return bool(text and _READY_FIRST_PERSON_RE.search(text))


def collect_style_to_texts(data: dict | None) -> list[str]:
    texts = []
    for _label, key in STYLE_VARIANTS:
        item = (data or {}).get(key) or {}
        if isinstance(item, dict):
            t = (item.get("to") or "").strip()
            if t:
                texts.append(t)
        elif isinstance(item, str) and item.strip():
            texts.append(item.strip())
    canon = ((data or {}).get("canonical_meaning") or "").strip()
    if canon:
        texts.append(canon)
    return texts


def flagged_invented_ready_subject(source_text: str, result: dict) -> bool:
    if not persian_implies_impersonal_ready(source_text):
        return False
    return any(english_invents_speaker_ready(t) for t in collect_style_to_texts(result))


def _style_pair(item) -> dict[str, str]:
    if isinstance(item, str):
        return {"from": item.strip(), "to": ""}
    if not isinstance(item, dict):
        return {"from": "", "to": ""}
    return {
        "from": (item.get("from") or "").strip(),
        "to": (item.get("to") or "").strip(),
    }


def parse_styled_translation_response(
    data, *, src_hint: str, tgt: str, wants_translation: bool
) -> dict:
    if not isinstance(data, dict):
        return {"error": "Unexpected model response."}

    detected = (data.get("detected_lang") or src_hint or "").strip() or src_hint
    return {
        "from_lang": detected,
        "to_lang": tgt,
        "wants_translation": wants_translation,
        "canonical_meaning": (data.get("canonical_meaning") or "").strip(),
        "subject_reading": (data.get("subject_reading") or "").strip(),
        "grammar_notes": (data.get("grammar_notes") or "").strip(),
        "friendly_casual": _style_pair(data.get("friendly_casual")),
        "professional_formal": _style_pair(data.get("professional_formal")),
        "everyday_neutral": _style_pair(data.get("everyday_neutral")),
    }


def build_styled_translation_prompt(
    *,
    src_hint: str,
    tgt: str,
    wants_translation: bool,
    context=None,
    retry_feedback=None,
) -> tuple[str, str]:
    translation_block = (
        f"The user asks for American English ({tgt}) output at B2 level.\n"
        f"1) Write canonical_meaning: one accurate neutral American English sentence (B2).\n"
        f'2) For each style, "from" = corrected/cleaned source-language text in that tone;\n'
        f'   "to" = the SAME meaning as canonical_meaning, restyled in natural US English '
        f"(Friendly/casual, Professional/formal, or Everyday/neutral).\n"
        f"All three \"to\" lines must preserve identical who/what/when facts as canonical_meaning.\n"
        f"Sound natural as spoken in the US — not stiff or word-for-word."
        if wants_translation
        else (
            "No target-language translation was requested. Keep styled rewrites in the source language.\n"
            "1) Write canonical_meaning in the source language (neutral accurate reading).\n"
            '2) Put each styled corrected version in "from" and set "to" to an empty string.\n'
            "Styles change tone only; meaning must match canonical_meaning."
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

Pipeline you MUST follow (internally, then output JSON only):
1. Treat the input as Persian when it is Persian (UI hint may be {src_hint}).
2. Analyze whether subjects/objects are explicit or implicit.
3. Decide a single canonical_meaning in natural American English (B2) when translating.
4. Derive all style variants FROM that canonical meaning (tone only — no meaning drift).
5. {translation_block}

{context_block}
{retry_block}
Also:
- "from" must be grammar-fixed source text, never the raw broken input if errors exist.
- grammar_notes: briefly explain grammar mistakes (or "").
- subject_reading: short note like "implicit inanimate 'it' (will be ready)" or "explicit speaker".

Output ONLY valid JSON (no markdown, no commentary):
{{
    "detected_lang": "<detected language name>",
    "subject_reading": "<how you read omitted/explicit subjects>",
    "canonical_meaning": "<one accurate neutral American English reading (B2)>",
    "grammar_notes": "<brief notes or empty>",
    "friendly_casual": {{"from": "<corrected casual source>", "to": "<Friendly/casual US English or empty>"}},
    "professional_formal": {{"from": "<corrected formal source>", "to": "<Professional/formal US English or empty>"}},
    "everyday_neutral": {{"from": "<corrected neutral source>", "to": "<Everyday/neutral US English or empty>"}}
}}
""".strip()

    if wants_translation:
        user_msg = (
            "Translate and fix this Persian into natural American English (B2). "
            f"Then give Friendly/casual, Professional/formal, and Everyday/neutral versions in {tgt}. "
            "Explain grammar briefly in grammar_notes if needed.\n\n"
            "Text:\n{text}"
        )
    else:
        user_msg = (
            "Correct and improve this text, then provide 3 style variants "
            "(same language, no translation).\n\n"
            "Text:\n{text}"
        )

    return system_prompt, user_msg


def get_styled_translations_from_ai(
    text: str,
    from_lang: str = DEFAULT_GRAMMAR_FROM,
    to_lang: str = DEFAULT_GRAMMAR_TO,
    context=None,
) -> dict:
    src_hint = from_lang if from_lang in TARGET_LANGUAGES else DEFAULT_GRAMMAR_FROM
    tgt = to_lang if to_lang in TARGET_LANGUAGES else DEFAULT_GRAMMAR_TO
    wants_translation = src_hint != tgt
    provider = "ollama"

    def _once(retry_feedback=None):
        nonlocal provider
        system_prompt, user_template = build_styled_translation_prompt(
            src_hint=src_hint,
            tgt=tgt,
            wants_translation=wants_translation,
            context=context,
            retry_feedback=retry_feedback,
        )
        user_msg = user_template.replace("{text}", text)
        content, provider = chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.15,
            max_tokens=3000,
        )
        raw = json.loads(extract_json(content))
        parsed = parse_styled_translation_response(
            raw,
            src_hint=src_hint,
            tgt=tgt,
            wants_translation=wants_translation,
        )
        parsed["provider"] = provider
        return parsed

    try:
        result = _once()
        if "error" in result:
            return result
        if wants_translation and flagged_invented_ready_subject(text, result):
            result = _once(
                retry_feedback=(
                    "You translated impersonal Persian 'آماده میشه/می‌شود' as if the SPEAKER "
                    "will be ready ('I'll be ready'). That is wrong. Use neutral 'it will be ready' "
                    "/ 'it'll be ready', and for pickup use 'come pick it up' / 'come by to collect it'."
                )
            )
        result["provider"] = provider
        return result
    except LLMError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
