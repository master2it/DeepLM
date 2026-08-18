"""Extract JSON from model text."""

from __future__ import annotations

import json
import re


def extract_json(response_text: str) -> str:
    text = (response_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start_obj = text.find("{")
    start_arr = text.find("[")
    if start_obj < 0 and start_arr < 0:
        return text
    if start_arr >= 0 and (start_obj < 0 or start_arr < start_obj):
        start = start_arr
    else:
        start = start_obj
    depth = 0
    in_str = False
    escape = False
    opener = text[start]
    closer = "}" if opener == "{" else "]"
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]


def _escape_raw_controls_in_strings(blob: str) -> str:
    out: list[str] = []
    in_str = False
    escape = False
    for ch in blob:
        if in_str:
            if escape:
                out.append(ch)
                escape = False
                continue
            if ch == "\\":
                out.append(ch)
                escape = True
                continue
            if ch == '"':
                in_str = False
                out.append(ch)
                continue
            if ch == "\n":
                out.append("\\n")
                continue
            if ch == "\r":
                continue
            if ch == "\t":
                out.append("\\t")
                continue
            out.append(ch)
            continue
        if ch == '"':
            in_str = True
        out.append(ch)
    return "".join(out)


def _strip_trailing_commas(blob: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", blob)


def parse_model_json(response_text: str):
    blob = extract_json(response_text)
    candidates = [blob, _escape_raw_controls_in_strings(blob)]
    last_error: Exception | None = None
    for raw in candidates:
        cleaned = _strip_trailing_commas(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            last_error = exc
    raise last_error or json.JSONDecodeError("Invalid JSON", blob, 0)
