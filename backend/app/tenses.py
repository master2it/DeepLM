"""English 12-tense generator and German 6-tense generator, with Persian glosses."""

from __future__ import annotations

import json
import re
import unicodedata

from app.constants import (
    DEFAULT_TENSE_LANGUAGE,
    GERMAN_TENSE_KEYS,
    GERMAN_TENSE_LABELS,
    GERMAN_TENSES,
    TENSE_LANGUAGES,
)
from app.jsonutil import extract_json
from app.llm import LLMError, chat

GERMAN_TENSE_RULES = """
German has exactly 6 tenses. Never invent Present Continuous, Past Continuous,
or other English-chart tenses as German categories. Use only:
1. Präsens — now, facts, scheduled/near future with a time expression.
   German has no separate present continuous; Präsens covers both
   "I learn" and "I am learning" (Ich lerne Deutsch).
2. Präteritum (Imperfekt) — written stories, news, reports. In speech mainly
   war, hatte, wurde and modals (konnte, musste, wollte, sollte, durfte, mochte).
   Not the default spoken past for all verbs (Ich lernte Deutsch = written).
3. Perfekt — default spoken past. haben or sein + Partizip II.
   sein with motion/change: gehen, kommen, fahren, fliegen, bleiben, werden,
   sterben, einschlafen, aufwachen. Otherwise haben.
   Ich habe Deutsch gelernt. / Ich bin nach Berlin gefahren.
4. Plusquamperfekt — earlier than another past action (hatte/war + Partizip II).
   Ich hatte Deutsch gelernt. / Nachdem ich Deutsch gelernt hatte, bin ich nach Berlin gezogen.
5. Futur I — intention, prediction, promise, assumption (werden + infinitive).
   Everyday German often uses Präsens + time: Ich lerne morgen Deutsch.
   Also: Ich werde Deutsch lernen. Do not force Futur I for every future meaning.
6. Futur II — completed before a future point, or assumption about the past
   (werden + Partizip II + haben/sein).
   Bis morgen werde ich das Buch gelesen haben.
   Er wird wohl nach Hause gegangen sein.

Keep du/Sie consistent with the input. Keep person/number from the input.
Sentences must be natural, common, and grammatically correct.
Spoken past: prefer Perfekt unless the verb is sein, haben, or a modal.
Do not mix tenses incorrectly in one sentence.
English glosses: clear, not overly literal. Do not claim German has 12 tenses.
""".strip()

ENGLISH_TENSE_LIST = """
Conjugate in ALL 12 English verb tenses, using these labels:
Present Simple, Present Continuous, Present Perfect, Present Perfect Continuous,
Past Simple, Past Continuous, Past Perfect, Past Perfect Continuous,
Future Simple, Future Continuous, Future Perfect, Future Perfect Continuous.
""".strip()

_GERMAN_TENSE_ALIASES = {
    "praesens": "praesens",
    "prasens": "praesens",
    "present": "praesens",
    "present simple": "praesens",
    "present tense": "praesens",
    "praeteritum": "praeteritum",
    "prateritum": "praeteritum",
    "imperfekt": "praeteritum",
    "imperfect": "praeteritum",
    "past simple": "praeteritum",
    "perfekt": "perfekt",
    "perfect": "perfekt",
    "present perfect": "perfekt",
    "plusquamperfekt": "plusquamperfekt",
    "past perfect": "plusquamperfekt",
    "futur i": "futur_i",
    "futur 1": "futur_i",
    "futur1": "futur_i",
    "future simple": "futur_i",
    "futur ii": "futur_ii",
    "futur 2": "futur_ii",
    "futur2": "futur_ii",
    "future perfect": "futur_ii",
}


def normalize_tense_language(language: str | None) -> str:
    name = (language or DEFAULT_TENSE_LANGUAGE).strip()
    if name not in TENSE_LANGUAGES:
        return DEFAULT_TENSE_LANGUAGE
    return name


def _fold_tense_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", (name or "").strip().lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("_", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def canonical_german_tense_key(name: str) -> str | None:
    folded = _fold_tense_name(name)
    if folded in GERMAN_TENSE_KEYS:
        return folded
    return _GERMAN_TENSE_ALIASES.get(folded)


def _label_for_key(key: str) -> str:
    for k, label in GERMAN_TENSES:
        if k == key:
            return label
    return key


def _normalize_items(data, *, language: str) -> list[dict]:
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        data = data["items"]
    if not isinstance(data, list):
        return []
    items = []
    for row in data:
        if not isinstance(row, dict):
            continue
        text = (row.get("text") or row.get("german") or row.get("english") or "").strip()
        item = {
            "tense": (row.get("tense") or "").strip(),
            "text": text,
            "persian": (row.get("persian") or "").strip(),
        }
        english = (row.get("english") or "").strip()
        if english:
            item["english"] = english
        key = (row.get("key") or "").strip()
        if language == "German":
            resolved = canonical_german_tense_key(key or item["tense"])
            if resolved:
                item["key"] = resolved
                item["tense"] = _label_for_key(resolved)
        items.append(item)
    if language != "German":
        return items
    by_key: dict[str, dict] = {}
    for item in items:
        key = item.get("key")
        if key and key not in by_key:
            by_key[key] = item
    ordered = []
    for key in GERMAN_TENSE_KEYS:
        if key in by_key:
            ordered.append(by_key[key])
    return ordered


def get_tenses_from_ai(
    text: str,
    language: str | None = None,
    provider: str | None = None,
    groq_api_key: str | None = None,
    hf_api_key: str | None = None,
) -> dict | list:
    lang = normalize_tense_language(language)
    if lang == "German":
        labels = ", ".join(GERMAN_TENSE_LABELS)
        system_prompt = f"""
You are an expert German teacher for Persian-speaking students and must follow
the 6-tense German model strictly.
The user gives a short phrase (German or English). Identify subject and BASE VERB.
{GERMAN_TENSE_RULES}
Provide a NATURAL Persian translation and a clear English gloss for each sentence.

Output ONLY a valid JSON ARRAY of exactly 6 objects, in this order ({labels}):
[
    {{"key": "praesens", "tense": "Präsens", "text": "German sentence", "english": "English gloss", "persian": "فارسی"}},
    {{"key": "praeteritum", "tense": "Präteritum", "text": "...", "english": "...", "persian": "..."}},
    {{"key": "perfekt", "tense": "Perfekt", "text": "...", "english": "...", "persian": "..."}},
    {{"key": "plusquamperfekt", "tense": "Plusquamperfekt", "text": "...", "english": "...", "persian": "..."}},
    {{"key": "futur_i", "tense": "Futur I", "text": "...", "english": "...", "persian": "..."}},
    {{"key": "futur_ii", "tense": "Futur II", "text": "...", "english": "...", "persian": "..."}}
]
key must be one of: {", ".join(GERMAN_TENSE_KEYS)}.
Never output 12 items or English-chart tense names as German tense labels.
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
            hf_api_key=hf_api_key,
        )
        data = json.loads(extract_json(content))
        if isinstance(data, dict) and "error" in data:
            return data
        return {
            "items": _normalize_items(data, language=lang),
            "provider": used,
            "language": lang,
        }
    except LLMError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def get_tense_explanation_from_ai(
    tense_name: str,
    language: str | None = None,
    provider: str | None = None,
    groq_api_key: str | None = None,
    hf_api_key: str | None = None,
) -> dict:
    lang = normalize_tense_language(language)
    if lang == "German":
        key = canonical_german_tense_key(tense_name)
        label = _label_for_key(key) if key else tense_name.strip()
        system_prompt = f"""
You are an expert German teacher explaining grammar to a Persian student.
Follow the 6-tense German model strictly. German has exactly 6 tenses:
Präsens, Präteritum, Perfekt, Plusquamperfekt, Futur I, Futur II.
Explain the German tense "{label}" (canonical key: {key or "unknown"}).
{GERMAN_TENSE_RULES}
1. Explain WHEN and WHY we use it in simple, natural Persian.
2. Mention spoken vs written usage when it matters (Perfekt vs Präteritum).
3. Provide exactly 3 everyday German examples with English and Persian.

Output ONLY a valid JSON OBJECT:
{{
    "explanation": "توضیح کامل فارسی...",
    "examples": [
        {{"text": "German example 1", "english": "English 1", "fa": "ترجمه فارسی ۱"}},
        {{"text": "German example 2", "english": "English 2", "fa": "ترجمه فارسی ۲"}},
        {{"text": "German example 3", "english": "English 3", "fa": "ترجمه فارسی ۳"}}
    ]
}}
Do not present English continuous tenses as separate German tenses.
If the meaning overlaps with English continuous, say German uses this tense plus context/adverbs.
""".strip()
        user_msg = f"Explain {label} in German"
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
        user_msg = f"Explain {tense_name} in {lang}"
    try:
        content, used = chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
            max_tokens=1500,
            provider=provider,
            groq_api_key=groq_api_key,
            hf_api_key=hf_api_key,
        )
        data = json.loads(extract_json(content))
        if not isinstance(data, dict):
            return {"error": "Unexpected model response."}
        examples = []
        for ex in data.get("examples") or []:
            if not isinstance(ex, dict):
                continue
            row = {
                "text": (ex.get("text") or ex.get("en") or ex.get("de") or "").strip(),
                "fa": (ex.get("fa") or "").strip(),
            }
            english = (ex.get("english") or "").strip()
            if english:
                row["english"] = english
            examples.append(row)
        data["examples"] = examples
        data["provider"] = used
        data["language"] = lang
        if lang == "German":
            data["tense"] = label
            if key:
                data["key"] = key
        return data
    except LLMError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
