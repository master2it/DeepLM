"""JSON extraction from messy LLM output."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.jsonutil import extract_json, parse_model_json  # noqa: E402


class ExtractJsonTests(unittest.TestCase):
    def test_balanced_object_not_greedy(self):
        raw = 'prefix {"a": "x { y}", "b": 1} trailing {nope}'
        self.assertEqual(extract_json(raw), '{"a": "x { y}", "b": 1}')

    def test_strips_markdown_fence(self):
        raw = '```json\n{"ok": true}\n```'
        self.assertEqual(parse_model_json(raw), {"ok": True})

    def test_raw_newline_inside_string(self):
        raw = '{"from": "Hello,\nworld", "to": "ok"}'
        data = parse_model_json(raw)
        self.assertEqual(data["from"], "Hello,\nworld")

    def test_trailing_comma(self):
        raw = '{"a": 1, "b": {"c": 2,},}'
        self.assertEqual(parse_model_json(raw)["a"], 1)


if __name__ == "__main__":
    unittest.main()
