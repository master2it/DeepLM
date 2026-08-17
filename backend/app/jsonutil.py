"""Extract JSON from model text."""

from __future__ import annotations

import re


def extract_json(response_text: str) -> str:
    try:
        match = re.search(r"(\{.*\}|\[.*\])", response_text, re.DOTALL)
        if match:
            return match.group(0)
        return response_text
    except Exception:
        return response_text
