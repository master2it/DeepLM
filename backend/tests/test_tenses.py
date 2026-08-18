"""German 6-tense canonicalization tests (no LLM)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.tenses import (
    canonical_german_tense_key,
    _normalize_items,
    build_tense_explanation_prompt,
)  # noqa: E402


class GermanTenseCanonicalTests(unittest.TestCase):
    def test_display_names(self):
        self.assertEqual(canonical_german_tense_key("Präsens"), "praesens")
        self.assertEqual(canonical_german_tense_key("Präteritum"), "praeteritum")
        self.assertEqual(canonical_german_tense_key("Imperfekt"), "praeteritum")
        self.assertEqual(canonical_german_tense_key("Futur I"), "futur_i")
        self.assertEqual(canonical_german_tense_key("Futur II"), "futur_ii")

    def test_rejects_english_continuous_as_german_tense(self):
        self.assertIsNone(canonical_german_tense_key("Present Continuous"))
        self.assertIsNone(canonical_german_tense_key("Past Continuous"))

    def test_normalize_keeps_six_in_order(self):
        raw = [
            {"tense": "Perfekt", "text": "Ich habe gelernt.", "persian": "آ"},
            {"tense": "Präsens", "text": "Ich lerne.", "persian": "ب"},
            {"key": "futur_ii", "tense": "Futur II", "text": "Ich werde gelernt haben.", "persian": "ج"},
        ]
        items = _normalize_items(raw, language="German")
        self.assertEqual([i["tense"] for i in items], ["Präsens", "Perfekt", "Futur II"])
        self.assertEqual([i["key"] for i in items], ["praesens", "perfekt", "futur_ii"])


class ExplainPromptTests(unittest.TestCase):
    def test_prompt_asks_for_exactly_three_examples(self):
        system, user = build_tense_explanation_prompt("Past Simple", language="English")
        self.assertIn("exactly 3", system)
        self.assertIn("Past Simple", system)
        self.assertIn("Explain Past Simple", user)

    def test_prompt_includes_student_phrase(self):
        system, user = build_tense_explanation_prompt(
            "Past Simple",
            language="English",
            source_text="I did",
            example="I did",
        )
        self.assertIn("exactly 3", system)
        self.assertIn("I did", system)
        self.assertIn("same subject and meaning", system)
        self.assertIn("I did", user)

    def test_german_prompt_includes_phrase(self):
        system, user = build_tense_explanation_prompt(
            "Perfekt",
            language="German",
            source_text="Ich arbeite",
            example="Ich habe gearbeitet.",
        )
        self.assertIn("exactly 3", system)
        self.assertIn("Ich arbeite", system)
        self.assertIn("Ich habe gearbeitet.", system)
        self.assertIn("Ich arbeite", user)


if __name__ == "__main__":
    unittest.main()
