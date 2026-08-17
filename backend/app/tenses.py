"""12 English tenses generator and explanations."""

from __future__ import annotations

import json

from app.jsonutil import extract_json
from app.llm import LLMError, chat


def get_tenses_from_ai(
    text: str, provider: str | None = None, groq_api_key: str | None = None
) -> dict | list:
    system_prompt = """
    You are an expert English teacher. The user will give you a short text.
    1. Identify subject and BASE VERB.
    2. Conjugate in ALL 12 English verb tenses.
    3. Provide NATURAL Persian translation (Never translate "do" to "میکنم" standalone. Use "انجام دادن").

    Output ONLY a valid JSON ARRAY like this:
    [
        {"tense": "Present Simple", "english": "...", "persian": "..."},
        ...
    ]
    """
    try:
        content, provider = chat(
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
        if isinstance(data, list):
            return {"items": data, "provider": provider}
        if isinstance(data, dict) and "error" in data:
            return data
        return {"items": data, "provider": provider}
    except LLMError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def get_tense_explanation_from_ai(
    tense_name: str, provider: str | None = None, groq_api_key: str | None = None
) -> dict:
    system_prompt = f"""
    You are an expert English teacher explaining grammar to a Persian student.
    Explain the English tense "{tense_name}".
    1. Explain WHEN and WHY we use it in simple, natural Persian.
    2. Provide exactly 3 everyday conversational English examples with their Persian translations.

    Output ONLY a valid JSON OBJECT:
    {{
        "explanation": "توضیح کامل فارسی در مورد کاربرد این زمان...",
        "examples": [
            {{"en": "English example 1", "fa": "ترجمه فارسی ۱"}},
            {{"en": "English example 2", "fa": "ترجمه فارسی ۲"}},
            {{"en": "English example 3", "fa": "ترجمه فارسی ۳"}}
        ]
    }}
    """
    try:
        content, provider = chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Explain {tense_name}"},
            ],
            temperature=0.2,
            max_tokens=1500,
            provider=provider,
            groq_api_key=groq_api_key,
        )
        data = json.loads(extract_json(content))
        if isinstance(data, dict):
            data["provider"] = provider
        return data
    except LLMError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
