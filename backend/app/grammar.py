"""Canonical-then-style grammar / spell fixer."""

from __future__ import annotations

import json

from app.constants import (
    DEFAULT_GRAMMAR_FROM,
    DEFAULT_GRAMMAR_TO,
    GERMAN_PERSIAN_RULES,
    GRAMMAR_FIX_RULES,
    COLLOCATION_CHUNK_RULES,
    LEGACY_STYLE_KEYS,
    SEMANTIC_ACCURACY_RULES,
    STRUCTURE_FORMAT_RULES,
    STYLE_DIFFERENTIATION_RULES,
    STYLE_VARIANTS,
    TARGET_LANGUAGES,
    native_editor_instruction,
    native_target_label,
    resolve_locale,
    _GERMAN_READY_FIRST_PERSON_RE,
    _PERSIAN_EXPLICIT_I_RE,
    _PERSIAN_IT_READY_RE,
    _READY_FIRST_PERSON_RE,
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


def _with_aliases(pair: dict[str, str]) -> dict[str, str]:
    src = (pair.get("from") or "").strip()
    tgt = (pair.get("to") or "").strip()
    return {
        "from": src,
        "to": tgt,
        "grammarEnhanced": src,
        "translated": tgt,
    }


def _style_source_text(pair: dict | None) -> str:
    item = pair or {}
    return (
        item.get("from")
        or item.get("grammarEnhanced")
        or ""
    ).strip()


def _style_translated_text(pair: dict | None) -> str:
    item = pair or {}
    return (
        item.get("to")
        or item.get("translated")
        or ""
    ).strip()


def _norm_style(text: str) -> str:
    return " ".join((text or "").lower().split())


def _near_duplicate(a: str, b: str) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return False
    overlap = len(sa & sb) / len(sa | sb)
    shorter = min(len(a), len(b))
    longer = max(len(a), len(b))
    if shorter < 24:
        return a == b
    return overlap >= 0.9 and shorter / longer >= 0.85


def _dup_feedback(native: str, friendly: str, professional: str, *, kind: str) -> str | None:
    if max(len(native), len(friendly), len(professional)) < 24:
        return None
    layer = "source-language rewrite (from / grammarEnhanced)" if kind == "source" else "translation (to)"
    if _near_duplicate(native, friendly):
        return (
            f"HARD RULE FAILED: Native and Friendly/Casual {layer} are identical or nearly "
            "identical. Independently rewrite Friendly/Casual from the ORIGINAL input as "
            "medium-casual everyday speech (low slang; do not force wanna/gotta/no worries). "
            "Do NOT copy Native.from. Then translate each source rewrite separately. "
            "Keep the same meaning."
        )
    if _near_duplicate(native, professional):
        return (
            f"HARD RULE FAILED: Native and Professional {layer} are identical or nearly "
            "identical. Independently rewrite Professional from the ORIGINAL input as "
            "clear polite coworker English, not formal (no unable to / kindly / prior to). "
            "Do NOT copy Native.from. Then translate each source rewrite separately. "
            "Keep the same meaning."
        )
    if _near_duplicate(friendly, professional):
        return (
            f"HARD RULE FAILED: Friendly/Casual and Professional {layer} are nearly identical. "
            "Rewrite each from the ORIGINAL input independently, then translate each. Same meaning."
        )
    return None


def styles_too_similar_feedback(result: dict, *, wants_translation: bool) -> str | None:
    native_src = _norm_style(_style_source_text(result.get("native")))
    friendly_src = _norm_style(_style_source_text(result.get("friendly")))
    professional_src = _norm_style(_style_source_text(result.get("professional")))
    source_issue = _dup_feedback(
        native_src, friendly_src, professional_src, kind="source"
    )
    if source_issue:
        return source_issue
    if not wants_translation:
        return None
    return _dup_feedback(
        _norm_style(_style_translated_text(result.get("native"))),
        _norm_style(_style_translated_text(result.get("friendly"))),
        _norm_style(_style_translated_text(result.get("professional"))),
        kind="translated",
    )


def _style_pair(item) -> dict[str, str]:
    if isinstance(item, str):
        return _with_aliases({"from": item.strip(), "to": ""})
    if not isinstance(item, dict):
        return _with_aliases({"from": "", "to": ""})
    src = (item.get("from") or item.get("grammarEnhanced") or "").strip()
    tgt = (item.get("to") or item.get("translated") or "").strip()
    return _with_aliases({"from": src, "to": tgt})


def _first_style_pair(data: dict, *keys: str) -> dict[str, str]:
    for key in keys:
        if key in data and data.get(key) not in (None, ""):
            pair = _style_pair(data.get(key))
            if pair["from"] or pair["to"]:
                return pair
    return _with_aliases({"from": "", "to": ""})


def _parse_grammar_notes(raw) -> tuple[list[dict[str, str]], str]:
    payload = raw.get("grammarNotes") if isinstance(raw, dict) else None
    if payload is None and isinstance(raw, dict):
        payload = raw.get("grammar_notes")
    items: list[dict[str, str]] = []
    if isinstance(payload, list):
        for row in payload:
            if isinstance(row, dict):
                original = str(row.get("original") or "").strip()
                correction = str(
                    row.get("correction") or row.get("fixed") or ""
                ).strip()
                explanation = str(
                    row.get("explanation") or row.get("why") or ""
                ).strip()
                if original or correction or explanation:
                    items.append(
                        {
                            "original": original,
                            "correction": correction,
                            "explanation": explanation,
                        }
                    )
            elif isinstance(row, str) and row.strip():
                items.append(
                    {"original": "", "correction": "", "explanation": row.strip()}
                )
    elif isinstance(payload, str) and payload.strip():
        items.append(
            {"original": "", "correction": "", "explanation": payload.strip()}
        )
    lines = []
    for note in items:
        if note["original"] and note["correction"]:
            line = f'"{note["original"]}" → "{note["correction"]}"'
            if note["explanation"]:
                line += f': {note["explanation"]}'
            lines.append(line)
        elif note["explanation"]:
            lines.append(note["explanation"])
    return items, "\n".join(lines)


def parse_styled_translation_response(
    data, *, src_hint: str, tgt: str, wants_translation: bool, locale: str = ""
) -> dict:
    if not isinstance(data, dict):
        return {"error": "Unexpected model response."}

    detected = (data.get("detected_lang") or src_hint or "").strip() or src_hint
    grammar_fix = _first_style_pair(data, "grammarFix", "grammar_fix")
    native = _first_style_pair(data, "native", "everyday_neutral")
    friendly = _first_style_pair(data, "friendly", "friendly_casual")
    professional = _first_style_pair(data, "professional", "professional_formal")
    notes, notes_text = _parse_grammar_notes(data)
    canonical = (data.get("canonical_meaning") or "").strip()
    best_version = (
        data.get("best_version")
        or canonical
        or grammar_fix.get("from")
        or native.get("from")
        or ""
    ).strip()
    if not canonical:
        canonical = best_version
    grammar_fix = _with_aliases(grammar_fix)
    native = _with_aliases(native)
    friendly = _with_aliases(friendly)
    professional = _with_aliases(professional)
    return {
        "from_lang": detected,
        "to_lang": tgt,
        "to_locale": locale,
        "wants_translation": wants_translation,
        "intended_meaning": (data.get("intended_meaning") or "").strip(),
        "best_version": best_version,
        "canonical_meaning": canonical,
        "subject_reading": (data.get("subject_reading") or "").strip(),
        "grammar_notes": notes_text,
        "grammarNotes": notes,
        "grammarFix": grammar_fix,
        "native": native,
        "friendly": friendly,
        "professional": professional,
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
    locale: str | None = None,
) -> tuple[str, str]:
    loc = resolve_locale(tgt, locale)
    tgt_label = native_target_label(tgt, loc)
    editor = native_editor_instruction(
        source_language=src_hint,
        target_language=tgt,
        target_locale=loc,
    )
    pair = {src_hint, tgt}
    german_persian = pair == {"German", "Persian"}
    pair_rules = f"\n{GERMAN_PERSIAN_RULES}\n" if german_persian else ""

    if wants_translation:
        translation_block = (
            f"Pipeline: (1) Grammar Fix the ORIGINAL {src_hint} with minimum edits, "
            f"then translate THAT corrected text into {tgt} / {loc} as grammarFix.to. "
            f"Do not translate the uncorrected original for Grammar Fix.\n"
            f"(2) Independently rewrite the ORIGINAL {src_hint} three times "
            f"(Native / Friendly / Professional). Each of those \"from\" fields MUST "
            f"be its own source-language rewrite — never copy Native "
            f"into Friendly or Professional, and never copy Grammar Fix into the rewrites.\n"
            f'Then translate EACH rewrite separately into {tgt} / {loc} as that tone\'s '
            '"to". Do not translate one shared sentence four times.\n'
            "grammar_notes: analyze the ORIGINAL user input only, not the generated versions.\n"
            "Same who/what/when. Keep source layout. Short input → short output."
        )
    else:
        translation_block = (
            f"Stay in {src_hint} / {loc}. "
            'Put Grammar Fix (min-edit correction, or the original if already correct) '
            'in grammarFix.from. Put each independent rewrite in "from". Set all "to" empty.\n'
            "Native, Friendly, and Professional from fields must each be independently "
            "generated from the original input. Do not copy Grammar Fix or Native."
        )

    context_block = (
        f"Surrounding conversation/context (use it to infer intended meaning):\n{context}\n"
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
{editor}

STYLE DIFFERENTIATION (mandatory):
{STYLE_DIFFERENTIATION_RULES}

GRAMMAR FIX (mandatory, not a rewrite):
{GRAMMAR_FIX_RULES}

NATURAL COLLOCATIONS AND CHUNKS (Native / Friendly / Professional only):
{COLLOCATION_CHUNK_RULES}

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
Output ONLY valid JSON (no markdown).
Escape every double quote inside string values as \\".
Use \\n for line breaks inside strings — never a raw newline.
{{
    "detected_lang": "<detected language name>",
    "grammarFix": {{"from": "<minimum grammar/spelling correction of the ORIGINAL {src_hint}, or unchanged if already correct>", "to": "<translation of THAT corrected text, or empty>"}},
    "native": {{"from": "<independent Native {src_hint} rewrite>", "to": "<translation of THAT Native rewrite, or empty>"}},
    "friendly": {{"from": "<independent Friendly {src_hint} rewrite>", "to": "<translation of THAT Friendly rewrite, or empty>"}},
    "professional": {{"from": "<independent Professional {src_hint} rewrite>", "to": "<translation of THAT Professional rewrite, or empty>"}},
    "grammar_notes": [
        {{"original": "<wrong fragment>", "correction": "<natural fix>", "explanation": "<why>"}}
    ]
}}
""".strip()

    if wants_translation:
        user_msg = (
            f"Understand what this {src_hint} means, then express it naturally in {tgt} "
            f"({loc}). First Grammar Fix the original (minimum edits), then translate "
            "that correction. Independently rewrite Native, Friendly / Casual, and "
            "Professional from the original, then translate EACH rewrite. "
            "Grammar Notes cover the original input only. "
            "Keep the same structure as the source.\n\n"
            "Text:\n{text}"
        )
    else:
        user_msg = (
            f"Understand what this means, then express it naturally in {tgt} ({loc}). "
            "Return Grammar Fix, Native, Friendly / Casual, Professional, and Grammar Notes.\n\n"
            "Text:\n{text}"
        )

    return system_prompt, user_msg


def get_styled_translations_from_ai(
    text: str,
    from_lang: str = DEFAULT_GRAMMAR_FROM,
    to_lang: str = DEFAULT_GRAMMAR_TO,
    to_locale: str | None = None,
    context=None,
    provider: str | None = None,
    groq_api_key: str | None = None,
    hf_api_key: str | None = None,
) -> dict:
    src_hint = from_lang if from_lang in TARGET_LANGUAGES else DEFAULT_GRAMMAR_FROM
    tgt = to_lang if to_lang in TARGET_LANGUAGES else DEFAULT_GRAMMAR_TO
    loc = resolve_locale(tgt, to_locale)
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
            locale=loc,
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
            locale=loc,
        )
        parsed["provider"] = used_provider
        parsed["to_locale"] = loc
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
        similar = styles_too_similar_feedback(
            result, wants_translation=wants_translation
        )
        if similar and "error" not in result:
            result = _once(retry_feedback=similar)
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
