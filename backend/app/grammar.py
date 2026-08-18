"""Canonical-then-style grammar / spell fixer."""

from __future__ import annotations

import json

from app.constants import (
    DEFAULT_GRAMMAR_FROM,
    DEFAULT_GRAMMAR_TO,
    GERMAN_PERSIAN_RULES,
    INTENT_AND_PRACTICE_RULES,
    GRAMMAR_NOTES_RULES,
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
    for _label, key in STYLE_VARIANTS:
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


def parse_styled_translation_response(
    data, *, src_hint: str, tgt: str, wants_translation: bool
) -> dict:
    if not isinstance(data, dict):
        return {"error": "Unexpected model response."}

    detected = (data.get("detected_lang") or src_hint or "").strip() or src_hint
    canonical = (data.get("canonical_meaning") or "").strip()
    best_version = (data.get("best_version") or canonical).strip()
    if not canonical:
        canonical = best_version
    intended = (data.get("intended_meaning") or "").strip()
    if not canonical:
        for _label, key in STYLE_VARIANTS:
            item = data.get(key) or {}
            if isinstance(item, dict):
                src = (item.get("from") or "").strip()
                if src:
                    canonical = src
                    if not best_version:
                        best_version = src
                    break
    return {
        "from_lang": detected,
        "to_lang": tgt,
        "wants_translation": wants_translation,
        "intended_meaning": intended,
        "best_version": best_version,
        "canonical_meaning": canonical,
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
    tgt_label = native_target_label(tgt)
    pair = {src_hint, tgt}
    german_persian = pair == {"German", "Persian"}
    pair_rules = f"\n{GERMAN_PERSIAN_RULES}\n" if german_persian else ""

    translation_block = (
        f"The user asks for {tgt_label} output.\n"
        f"1) intended_meaning: what they were trying to say (short, in {src_hint} or {tgt}).\n"
        f"2) best_version and canonical_meaning: grammar-enhanced {src_hint} ONLY "
        f"(the corrected input). Same facts and layout as the source. Not a translation. "
        f"Not a Friendly/Formal/Neutral rewrite of the source.\n"
        f'3) For every style, "from" MUST be identical to best_version.\n'
        f'   "to" = translate that enhanced {src_hint} into {tgt_label} in that tone '
        f"(Friendly/casual, Professional/formal, or Everyday/neutral).\n"
        f"All three \"to\" texts keep the same who/what/when as the enhanced source.\n"
        f"Do not merge a list of works into one consecutive paragraph."
        if wants_translation
        else (
            "No target-language translation was requested. Stay in the source language.\n"
            "1) intended_meaning: what they were trying to say.\n"
            "2) best_version and canonical_meaning: grammar-enhanced source (one corrected input).\n"
            '3) Style variants go in "from"; set "to" to an empty string.\n'
            "Styles change tone only; facts and line breaks must match best_version."
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

INTENT AND BEST LANGUAGE PRACTICE (mandatory):
{INTENT_AND_PRACTICE_RULES}

GRAMMAR NOTES FORMAT (mandatory):
{GRAMMAR_NOTES_RULES}

SEMANTIC ACCURACY (mandatory):
{SEMANTIC_ACCURACY_RULES}

STRUCTURE AND FORMAT (mandatory):
{STRUCTURE_FORMAT_RULES}

Pipeline you MUST follow (internally, then output JSON only):
1. Treat the input as {src_hint} (detect if the UI hint is wrong).
2. Infer intended_meaning (what they wanted to say), including implicit subjects/objects.
3. Write best_version / canonical_meaning in {src_hint}: grammar-enhanced input only.
   Never put {tgt} in best_version when translating.
4. Copy that same enhanced source into every style "from". Change tone only in "to".
5. {translation_block}
{pair_rules}
{context_block}
{retry_block}
Also:
- "from" must be the grammar-enhanced source (same as best_version when translating).
- best_version is the "Corrected sentence" in {src_hint}, never in {tgt} when translating.
- grammar_notes: "original" → "fixed". Reason. One issue per line. Never omit if you changed the text.
- subject_reading: short note like "implicit inanimate 'it' (will be ready)" or "explicit speaker".

Output ONLY valid JSON (no markdown, no commentary).
Escape every double quote inside string values as \\".
Use \\n for line breaks inside strings — never a raw newline.
Keep each "from"/"to" value complete; do not truncate JSON.
{{
    "detected_lang": "<detected language name>",
    "subject_reading": "<how you read omitted/explicit subjects>",
    "intended_meaning": "<what they were trying to say>",
    "best_version": "<grammar-enhanced SOURCE / From language, same layout>",
    "canonical_meaning": "<same as best_version, still SOURCE language>",
    "grammar_notes": "<each line: \\"wrong\\" → \\"right\\". Reason.>",
    "friendly_casual": {{"from": "<same grammar-enhanced source as best_version>", "to": "<Friendly/casual {tgt} or empty>"}},
    "professional_formal": {{"from": "<same grammar-enhanced source as best_version>", "to": "<Professional/formal {tgt} or empty>"}},
    "everyday_neutral": {{"from": "<same grammar-enhanced source as best_version>", "to": "<Everyday/neutral {tgt} or empty>"}}
}}
""".strip()

    if wants_translation:
        user_msg = (
            f"Improve this {src_hint} (grammar-enhanced input only — do not translate best_version). "
            f"Then translate that enhanced sentence into {tgt_label} as 1 Friendly, 2 Professional, "
            f"3 Everyday. Keep all three \"from\" fields identical to best_version. "
            "Keep the same structure as the source (greeting, paragraph, then one list item per line). "
            'Always add Grammar notes as \\"wrong\\" → \\"right\\". Reason.\n\n'
            "Text:\n{text}"
        )
    else:
        user_msg = (
            "Infer what this text is trying to say, then rewrite it with best native-language "
            "practices (not grammar-only). Give a Corrected sentence (best_version), then "
            "1 Friendly / 2 Professional / 3 Everyday (same language). "
            'Always add Grammar notes as \\"wrong\\" → \\"right\\". Reason.\n\n'
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
