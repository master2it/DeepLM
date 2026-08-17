"""12 tenses generator (English or German) with Persian glosses."""

from __future__ import annotations

import json

from app.constants import DEFAULT_TENSE_LANGUAGE, TENSE_LANGUAGES
from app.jsonutil import extract_json
from app.llm import LLMError, chat

GERMAN_TENSE_MAP = """
Use these 12 labels (same names as English teaching charts) with NATURAL German:
1. Present Simple → Präsens (Ich arbeite.)
2. Present Continuous → Präsens with gerade / dabei sein (Ich arbeite gerade.)
3. Present Perfect → Perfekt (Ich habe gearbeitet.)
4. Present Perfect Continuous → Perfekt + seit/schon (Ich habe schon lange gearbeitet.)
5. Past Simple → Präteritum (Ich arbeitete.)
6. Past Continuous → Präteritum / war dabei (Ich arbeitete gerade. / Ich war dabei zu arbeiten.)
7. Past Perfect → Plusquamperfekt (Ich hatte gearbeitet.)
8. Past Perfect Continuous → Plusquamperfekt + seit (Ich hatte schon lange gearbeitet.)
9. Future Simple → Futur I (Ich werde arbeiten.)
10. Future Continuous → Futur I + gerade (Ich werde gerade arbeiten.)
11. Future Perfect → Futur II (Ich werde gearbeitet haben.)
12. Future Perfect Continuous → Futur II + seit (Ich werde schon lange gearbeitet haben.)
Use du/Sie consistently with the input. Keep person/number from the input.
""".strip()

ENGLISH_TENSE_LIST = """
Conjugate in ALL 12 English verb tenses, using these labels:
Present Simple, Present Continuous, Present Perfect, Present Perfect Continuous,
Past Simple, Past Continuous, Past Perfect, Past Perfect Continuous,
Future Simple, Future Continuous, Future Perfect, Future Perfect Continuous.
""".strip()


def normalize_tense_language(language: str | None) -> str:
    name = (language or DEFAULT_TENSE_LANGUAGE).strip()
    if name not in TENSE_LANGUAGES:
        return DEFAULT_TENSE_LANGUAGE
    return name


def _normalize_items(data) -> list[dict]:
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        data = data["items"]
    if not isinstance(data, list):
        return []
    items = []
    for row in data:
        if not isinstance(row, dict):
            continue
        text = (row.get("text") or row.get("english") or row.get("german") or "").strip()
        items.append(
            {
                "tense": (row.get("tense") or "").strip(),
                "text": text,
                "persian": (row.get("persian") or "").strip(),
            }
        )
    return items


def get_tenses_from_ai(
    text: str,
    language: str | None = None,
    provider: str | None = None,
    groq_api_key: str | None = None,
) -> dict | list:
    lang = normalize_tense_language(language)
    if lang == "German":
        system_prompt = f"""
You are an expert German teacher for Persian-speaking students.
The user gives a short phrase (German or English). Identify subject and BASE VERB.
{GERMAN_TENSE_MAP}
Provide a NATURAL Persian translation of each German sentence.
Never translate English "do" as Persian «میکنم» standalone; use «انجام دادن» if needed.

Output ONLY a valid JSON ARRAY:
[
    {{"tense": "Present Simple", "text": "German sentence", "persian": "فارسی"}},
    ...
]
Exactly 12 objects, in the order listed above.
""".strip()
    else:
        system_prompt = f"""
You are an expert English teacher for Persian-speaking students.
The user gives a short text. Identify subject and BASE VERB.
{ENGLISH_TENSE_LIST}
Provide a NATURAL Persian translation of each English sentence.
Never translate "do" to «میکنم» standalone. Use «انجام دادن».

Output ONLY a valid JSON ARRAY:
[
    {{"tense": "Present Simple", "text": "English sentence", "persian": "فارسی"}},
    ...
]
Exactly 12 objects, in the order listed above.
""".strip()
    try:
        content, used = chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=2500,
            provider=provider,
            groq_api_key=groq_api_key,
        )
        data = json.loads(extract_json(content))
        if isinstance(data, dict) and "error" in data:
            return data
        return {"items": _normalize_items(data), "provider": used, "language": lang}
    except LLMError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def get_tense_explanation_from_ai(
    tense_name: str,
    language: str | None = None,
    provider: str | None = None,
    groq_api_key: str | None = None,
) -> dict:
    lang = normalize_tense_language(language)
    if lang == "German":
        system_prompt = f"""
You are an expert German teacher explaining grammar to a Persian student.
Explain how German expresses the English-chart tense "{tense_name}"
(Präsens / Perfekt / Präteritum / Plusquamperfekt / Futur I / Futur II as appropriate).
1. Explain WHEN and WHY we use it in simple, natural Persian.
2. Provide exactly 3 everyday German examples with Persian translations.

Output ONLY a valid JSON OBJECT:
{{
    "explanation": "توضیح کامل فارسی...",
    "examples": [
        {{"text": "German example 1", "fa": "ترجمه فارسی ۱"}},
        {{"text": "German example 2", "fa": "ترجمه فارسی ۲"}},
        {{"text": "German example 3", "fa": "ترجمه فارسی ۳"}}
    ]
}}
""".strip()
    else:
        system_prompt = f"""
You are an expert English teacher explaining grammar to a Persian student.
Explain the English tense "{tense_name}".
1. Explain WHEN and WHY we use it in simple, natural Persian.
2. Provide exactly 3 everyday conversational English examples with Persian translations.

Output ONLY a valid JSON OBJECT:
{{
    "explanation": "توضیح کامل فارسی در مورد کاربرد این زمان...",
    "examples": [
        {{"text": "English example 1", "fa": "ترجمه فارسی ۱"}},
        {{"text": "English example 2", "fa": "ترجمه فارسی ۲"}},
        {{"text": "English example 3", "fa": "ترجمه فارسی ۳"}}
    ]
}}
""".strip()
    try:
        content, used = chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Explain {tense_name} in {lang}"},
            ],
            temperature=0.2,
            max_tokens=1500,
            provider=provider,
            groq_api_key=groq_api_key,
        )
        data = json.loads(extract_json(content))
        if not isinstance(data, dict):
            return {"error": "Unexpected model response."}
        examples = []
        for ex in data.get("examples") or []:
            if not isinstance(ex, dict):
                continue
            examples.append(
                {
                    "text": (ex.get("text") or ex.get("en") or ex.get("de") or "").strip(),
                    "fa": (ex.get("fa") or "").strip(),
                }
            )
        data["examples"] = examples
        data["provider"] = used
        data["language"] = lang
        return data
    except LLMError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
