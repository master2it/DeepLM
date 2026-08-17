"""Regression tests for Grammar/Spell Fixer translation quality."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import grammar  # noqa: E402


PERSIAN_READY_PICKUP = "هفته اینده اماده میشه و میتونی بیای بگیری"
PERSIAN_READY_TOMORROW = "فردا آماده میشه"
PERSIAN_PICKUP_TOMORROW = "میتونی فردا بیای بگیری"
PERSIAN_NOTIFY_WHEN_READY = "وقتی آماده شد بهت خبر میدم"


class HeuristicTests(unittest.TestCase):
    def test_persian_impersonal_ready_detected(self):
        self.assertTrue(grammar.persian_implies_impersonal_ready(PERSIAN_READY_PICKUP))
        self.assertTrue(grammar.persian_implies_impersonal_ready(PERSIAN_READY_TOMORROW))
        self.assertTrue(grammar.persian_implies_impersonal_ready("فردا آماده می‌شود"))

    def test_explicit_i_not_flagged_as_impersonal(self):
        self.assertFalse(grammar.persian_implies_impersonal_ready("من فردا آماده می‌شم"))
        self.assertFalse(grammar.persian_implies_impersonal_ready("آماده‌ام"))

    def test_english_invented_speaker_ready(self):
        self.assertTrue(grammar.english_invents_speaker_ready("Next week I'll be ready."))
        self.assertTrue(
            grammar.english_invents_speaker_ready("I will be prepared tomorrow.")
        )
        self.assertFalse(
            grammar.english_invents_speaker_ready("It'll be ready next week.")
        )

    def test_flag_bad_ready_subject_on_result(self):
        bad = {
            "canonical_meaning": "Next week I'll be ready.",
            "friendly_casual": {
                "from": "...",
                "to": "Next week I'll be ready, come and get it.",
            },
            "professional_formal": {"from": "...", "to": "I will be prepared."},
            "everyday_neutral": {"from": "...", "to": "I'll be ready."},
        }
        self.assertTrue(grammar.flagged_invented_ready_subject(PERSIAN_READY_PICKUP, bad))


class PromptArchitectureTests(unittest.TestCase):
    def test_prompt_includes_semantic_and_canonical_pipeline(self):
        system, user = grammar.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="English",
            wants_translation=True,
        )
        self.assertIn("canonical_meaning", system)
        self.assertIn("Do not invent explicit subjects", system)
        self.assertIn("American English", system)
        self.assertIn("{text}", user)

    def test_prompt_accepts_context(self):
        system, _user = grammar.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="English",
            wants_translation=True,
            context="Customer asking about their order status.",
        )
        self.assertIn("order status", system)


class ParseContractTests(unittest.TestCase):
    def test_parse_preserves_ui_keys(self):
        raw = {
            "detected_lang": "Persian",
            "canonical_meaning": "It will be ready next week.",
            "grammar_notes": "",
            "friendly_casual": {"from": "x", "to": "It'll be ready next week."},
            "professional_formal": {"from": "x", "to": "It will be ready next week."},
            "everyday_neutral": {"from": "x", "to": "It will be ready next week."},
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="Persian", tgt="English", wants_translation=True
        )
        self.assertEqual(parsed["from_lang"], "Persian")
        self.assertTrue(parsed["wants_translation"])


class MockedPipelineTests(unittest.TestCase):
    def test_retries_when_model_invents_i_will_be_ready(self):
        bad_json = {
            "detected_lang": "Persian",
            "canonical_meaning": "Next week I'll be ready.",
            "grammar_notes": "",
            "friendly_casual": {"from": "x", "to": "Next week I'll be ready, come and get it."},
            "professional_formal": {"from": "x", "to": "Next week, I will be prepared."},
            "everyday_neutral": {"from": "x", "to": "Next week, I'll be ready."},
        }
        good_json = {
            "detected_lang": "Persian",
            "canonical_meaning": "It will be ready next week, and you can come pick it up.",
            "grammar_notes": "",
            "friendly_casual": {
                "from": "x",
                "to": "It'll be ready next week. You can come pick it up.",
            },
            "professional_formal": {
                "from": "x",
                "to": "It will be ready next week, and you can come by to collect it.",
            },
            "everyday_neutral": {
                "from": "x",
                "to": "It will be ready next week, and you can come pick it up.",
            },
        }
        responses = [json.dumps(bad_json), json.dumps(good_json)]

        def fake_chat(messages, temperature=0.2, max_tokens=2048, provider=None, groq_api_key=None):
            return responses.pop(0), "ollama"

        with patch.object(grammar, "chat", side_effect=fake_chat):
            result = grammar.get_styled_translations_from_ai(
                PERSIAN_READY_PICKUP,
                from_lang="Persian",
                to_lang="English",
            )

        self.assertNotIn("error", result)
        self.assertFalse(
            grammar.flagged_invented_ready_subject(PERSIAN_READY_PICKUP, result)
        )
        self.assertIn("pick it up", result["friendly_casual"]["to"].lower())
        self.assertEqual(result["provider"], "ollama")

    def test_semantic_expectations_documented_cases(self):
        cases = [
            PERSIAN_READY_PICKUP,
            PERSIAN_READY_TOMORROW,
            PERSIAN_PICKUP_TOMORROW,
            PERSIAN_NOTIFY_WHEN_READY,
        ]
        for src in cases:
            with self.subTest(src=src):
                if "خبر" in src:
                    good_to = "I'll let you know when it's ready."
                elif "فردا آماده" in src:
                    good_to = "It will be ready tomorrow."
                elif "میتونی فردا" in src:
                    good_to = "You can come pick it up tomorrow."
                else:
                    good_to = "It will be ready next week, and you can come pick it up."
                result = {
                    "everyday_neutral": {"from": "…", "to": good_to},
                    "friendly_casual": {"from": "…", "to": good_to},
                    "professional_formal": {"from": "…", "to": good_to},
                    "canonical_meaning": good_to,
                }
                if grammar.persian_implies_impersonal_ready(src):
                    self.assertFalse(
                        grammar.flagged_invented_ready_subject(src, result)
                    )


@unittest.skipUnless(
    os.getenv("HF_TOKEN", "").strip() and os.getenv("RUN_LIVE_TRANSLATION_TESTS") == "1",
    "Set HF_TOKEN and RUN_LIVE_TRANSLATION_TESTS=1 for live model checks",
)
class LivePersianEnglishTests(unittest.TestCase):
    def test_ready_pickup_not_i_will_be_ready(self):
        result = grammar.get_styled_translations_from_ai(
            PERSIAN_READY_PICKUP,
            from_lang="Persian",
            to_lang="English",
        )
        self.assertNotIn("error", result, msg=result)
        self.assertFalse(
            grammar.flagged_invented_ready_subject(PERSIAN_READY_PICKUP, result),
            msg=result,
        )


if __name__ == "__main__":
    unittest.main()
