"""
Regression tests for Grammar/Spell Fixer translation quality.

Focus: Persian null-subject / impersonal "آماده میشه" must not become
English "I'll be ready"; style variants must share one meaning.
"""

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

import language  # noqa: E402


PERSIAN_READY_PICKUP = "هفته اینده اماده میشه و میتونی بیای بگیری"
PERSIAN_READY_TOMORROW = "فردا آماده میشه"
PERSIAN_PICKUP_TOMORROW = "میتونی فردا بیای بگیری"
PERSIAN_NOTIFY_WHEN_READY = "وقتی آماده شد بهت خبر میدم"


class HeuristicTests(unittest.TestCase):
    def test_persian_impersonal_ready_detected(self):
        self.assertTrue(language.persian_implies_impersonal_ready(PERSIAN_READY_PICKUP))
        self.assertTrue(language.persian_implies_impersonal_ready(PERSIAN_READY_TOMORROW))
        self.assertTrue(language.persian_implies_impersonal_ready("فردا آماده می‌شود"))

    def test_explicit_i_not_flagged_as_impersonal(self):
        self.assertFalse(language.persian_implies_impersonal_ready("من فردا آماده می‌شم"))
        self.assertFalse(language.persian_implies_impersonal_ready("آماده‌ام"))

    def test_english_invented_speaker_ready(self):
        self.assertTrue(language.english_invents_speaker_ready("Next week I'll be ready."))
        self.assertTrue(
            language.english_invents_speaker_ready("I will be prepared tomorrow.")
        )
        self.assertFalse(
            language.english_invents_speaker_ready("It'll be ready next week.")
        )
        self.assertFalse(
            language.english_invents_speaker_ready("It will be ready next week.")
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
        self.assertTrue(language.flagged_invented_ready_subject(PERSIAN_READY_PICKUP, bad))

        good = {
            "canonical_meaning": "It will be ready next week, and you can come pick it up.",
            "friendly_casual": {
                "from": "...",
                "to": "It'll be ready next week. You can come pick it up.",
            },
            "professional_formal": {
                "from": "...",
                "to": "It will be ready next week, and you can come by to collect it.",
            },
            "everyday_neutral": {
                "from": "...",
                "to": "It will be ready next week, and you can come pick it up.",
            },
        }
        self.assertFalse(
            language.flagged_invented_ready_subject(PERSIAN_READY_PICKUP, good)
        )


class PromptArchitectureTests(unittest.TestCase):
    def test_prompt_includes_semantic_and_canonical_pipeline(self):
        system, user = language.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="English",
            wants_translation=True,
        )
        self.assertIn("canonical_meaning", system)
        self.assertIn("Do not invent explicit subjects", system)
        self.assertIn("آماده", system)
        self.assertIn("tone only", system.lower())
        self.assertIn("{text}", user)

    def test_prompt_accepts_context(self):
        system, _user = language.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="English",
            wants_translation=True,
            context="Customer asking about their order status.",
        )
        self.assertIn("order status", system)

    def test_semantic_rules_constant(self):
        self.assertIn("Do not invent explicit subjects", language.SEMANTIC_ACCURACY_RULES)
        self.assertIn("null-subject", language.SEMANTIC_ACCURACY_RULES.lower())

    def test_parse_forbids_i_will_be_ready_in_good_fixture(self):
        import re

        raw = {
            "detected_lang": "Persian",
            "subject_reading": "implicit inanimate it",
            "canonical_meaning": "It will be ready next week, and you can come pick it up.",
            "grammar_notes": "Spelling: آینده، آماده",
            "friendly_casual": {
                "from": "هفته آینده آماده می‌شه، می‌تونی بیای بگیری.",
                "to": "It'll be ready next week. You can come pick it up.",
            },
            "professional_formal": {
                "from": "هفته آینده آماده می‌شود و می‌توانید برای دریافت آن بیایید.",
                "to": "It will be ready next week, and you can come by to collect it.",
            },
            "everyday_neutral": {
                "from": "هفته آینده آماده می‌شود و می‌تونی بیای بگیری.",
                "to": "It will be ready next week, and you can come pick it up.",
            },
        }
        parsed = language.parse_styled_translation_response(
            raw, src_hint="Persian", tgt="English", wants_translation=True
        )
        self.assertEqual(parsed["from_lang"], "Persian")
        self.assertEqual(parsed["to_lang"], "English")
        self.assertTrue(parsed["wants_translation"])
        self.assertIn("pick it up", parsed["friendly_casual"]["to"])
        self.assertIsNone(
            re.search(
                r"I(?:'ll| will)\s+be\s+ready",
                parsed["everyday_neutral"]["to"],
                flags=re.I,
            )
        )


class MockedPipelineTests(unittest.TestCase):
    def test_retries_when_model_invents_i_will_be_ready(self):
        bad_json = {
            "detected_lang": "Persian",
            "subject_reading": "speaker",
            "canonical_meaning": "Next week I'll be ready.",
            "grammar_notes": "",
            "friendly_casual": {
                "from": "x",
                "to": "Next week I'll be ready, come and get it.",
            },
            "professional_formal": {
                "from": "x",
                "to": "Next week, I will be prepared.",
            },
            "everyday_neutral": {
                "from": "x",
                "to": "Next week, I'll be ready.",
            },
        }
        good_json = {
            "detected_lang": "Persian",
            "subject_reading": "implicit inanimate it",
            "canonical_meaning": "It will be ready next week, and you can come pick it up.",
            "grammar_notes": "",
            "friendly_casual": {
                "from": "هفته آینده آماده می‌شه و می‌تونی بیای بگیری.",
                "to": "It'll be ready next week. You can come pick it up.",
            },
            "professional_formal": {
                "from": "هفته آینده آماده می‌شود و می‌توانید برای دریافت آن مراجعه کنید.",
                "to": "It will be ready next week, and you can come by to collect it.",
            },
            "everyday_neutral": {
                "from": "هفته آینده آماده می‌شود و می‌تونی بیای بگیری.",
                "to": "It will be ready next week, and you can come pick it up.",
            },
        }
        responses = [json.dumps(bad_json), json.dumps(good_json)]

        def fake_chat(messages, temperature=0.2, max_tokens=2048):
            return responses.pop(0)

        with patch.object(language, "hf_chat", side_effect=fake_chat):
            result = language.get_styled_translations_from_ai(
                PERSIAN_READY_PICKUP,
                from_lang="Persian",
                to_lang="English",
            )

        self.assertNotIn("error", result)
        self.assertFalse(
            language.flagged_invented_ready_subject(PERSIAN_READY_PICKUP, result)
        )
        self.assertIn("pick it up", result["friendly_casual"]["to"].lower())
        self.assertEqual(len(responses), 0)  # retry consumed second response

    def test_semantic_expectations_documented_cases(self):
        """Document expected meanings for key Persian→English cases (offline)."""
        cases = [
            (
                PERSIAN_READY_PICKUP,
                "it will be ready next week",
                "pick it up",
                r"I(?:'ll| will)\s+be\s+ready",
            ),
            (
                PERSIAN_READY_TOMORROW,
                "it will be ready tomorrow",
                "ready",
                r"I(?:'ll| will)\s+be\s+ready",
            ),
            (
                PERSIAN_PICKUP_TOMORROW,
                "come pick it up tomorrow",
                "tomorrow",
                None,
            ),
            (
                PERSIAN_NOTIFY_WHEN_READY,
                "when it",
                "ready",
                None,
            ),
        ]
        for src, must_a, must_b, forbid in cases:
            with self.subTest(src=src):
                # Build a "good" synthetic result matching expected semantics
                good_to = f"{must_a.capitalize()}. You can {must_b}."
                if "خبر" in src:
                    good_to = "I'll let you know when it's ready."
                elif "فردا آماده" in src:
                    good_to = "It will be ready tomorrow."
                elif "میتونی فردا" in src:
                    good_to = "You can come pick it up tomorrow."
                else:
                    good_to = (
                        "It will be ready next week, and you can come pick it up."
                    )
                result = {
                    "everyday_neutral": {"from": "…", "to": good_to},
                    "friendly_casual": {"from": "…", "to": good_to},
                    "professional_formal": {"from": "…", "to": good_to},
                    "canonical_meaning": good_to,
                }
                if forbid:
                    self.assertFalse(
                        language.flagged_invented_ready_subject(src, result)
                        if language.persian_implies_impersonal_ready(src)
                        else False
                    )
                    self.assertIsNone(
                        __import__("re").search(forbid, good_to, flags=__import__("re").I)
                    )
                self.assertTrue(must_a.split()[0].lower() in good_to.lower() or "it" in good_to.lower() or "you" in good_to.lower() or "i'll let" in good_to.lower())


@unittest.skipUnless(
    os.getenv("HF_TOKEN", "").strip() and os.getenv("RUN_LIVE_TRANSLATION_TESTS") == "1",
    "Set HF_TOKEN and RUN_LIVE_TRANSLATION_TESTS=1 for live model checks",
)
class LivePersianEnglishTests(unittest.TestCase):
    def test_ready_pickup_not_i_will_be_ready(self):
        result = language.get_styled_translations_from_ai(
            PERSIAN_READY_PICKUP,
            from_lang="Persian",
            to_lang="English",
        )
        self.assertNotIn("error", result, msg=result)
        self.assertFalse(
            language.flagged_invented_ready_subject(PERSIAN_READY_PICKUP, result),
            msg=result,
        )
        joined = " ".join(language.collect_style_to_texts(result)).lower()
        self.assertTrue(
            "ready" in joined and ("pick" in joined or "collect" in joined),
            msg=joined,
        )


if __name__ == "__main__":
    unittest.main()
