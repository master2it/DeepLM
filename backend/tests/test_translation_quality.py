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

    def test_german_invented_speaker_ready(self):
        self.assertTrue(grammar.german_invents_speaker_ready("Nächste Woche ich werde bereit sein."))
        self.assertTrue(grammar.german_invents_speaker_ready("Ich bin fertig morgen."))
        self.assertFalse(grammar.german_invents_speaker_ready("Es wird nächste Woche fertig."))

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
        german_bad = {
            "canonical_meaning": "Nächste Woche ich bin bereit.",
            "friendly_casual": {"from": "...", "to": "Ich werde bereit sein."},
            "professional_formal": {"from": "...", "to": "Es wird fertig."},
            "everyday_neutral": {"from": "...", "to": "Es wird fertig."},
        }
        self.assertTrue(
            grammar.flagged_invented_ready_subject(PERSIAN_READY_PICKUP, german_bad)
        )


class PromptArchitectureTests(unittest.TestCase):
    def test_prompt_includes_semantic_and_canonical_pipeline(self):
        system, user = grammar.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="English",
            wants_translation=True,
        )
        self.assertIn("native", system)
        self.assertIn("friendly", system)
        self.assertIn("professional", system)
        self.assertIn("grammar_notes", system)
        self.assertIn("understand what the user MEANS", system)
        self.assertIn("Do not invent explicit subjects", system)
        self.assertIn("Never flatten", system)
        self.assertIn("American English", system)
        self.assertIn("Grammar Notes", user)
        self.assertIn("{text}", user)
        self.assertIn("I can't make it", system)

    def test_german_persian_prompt_both_directions(self):
        de_fa, user_de = grammar.build_styled_translation_prompt(
            src_hint="German",
            tgt="Persian",
            wants_translation=True,
        )
        self.assertIn("German ↔ Persian", de_fa)
        self.assertIn("natural contemporary Persian", de_fa)
        self.assertIn("German", user_de)
        self.assertIn("Persian", user_de)

        fa_de, user_fa = grammar.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="German",
            wants_translation=True,
        )
        self.assertIn("German ↔ Persian", fa_de)
        self.assertIn("natural contemporary German", fa_de)
        self.assertIn("es wird fertig", fa_de)
        self.assertIn("Persian", user_fa)
        self.assertIn("German", user_fa)

    def test_prompt_accepts_context(self):
        system, _user = grammar.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="English",
            wants_translation=True,
            context="Customer asking about their order status.",
        )
        self.assertIn("order status", system)


    def test_locale_is_in_prompt_and_unknown_falls_back(self):
        from app.constants import resolve_locale

        self.assertEqual(resolve_locale("English", None), "American English")
        self.assertEqual(resolve_locale("English", ""), "American English")
        self.assertEqual(resolve_locale("English", "not-a-locale"), "American English")
        self.assertEqual(resolve_locale("English", "british english"), "British English")
        self.assertEqual(resolve_locale("German", None), "German (Germany)")
        self.assertEqual(resolve_locale("Spanish", "Mexican Spanish"), "Mexican Spanish")

        us, _ = grammar.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="English",
            wants_translation=True,
            locale="American English",
        )
        uk, user_uk = grammar.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="English",
            wants_translation=True,
            locale="British English",
        )
        de, _ = grammar.build_styled_translation_prompt(
            src_hint="English",
            tgt="German",
            wants_translation=True,
            locale="German (Germany)",
        )
        es, _ = grammar.build_styled_translation_prompt(
            src_hint="English",
            tgt="Spanish",
            wants_translation=True,
            locale="Mexican Spanish",
        )
        self.assertIn("American English", us)
        self.assertIn("British English", uk)
        self.assertIn("British English", user_uk)
        self.assertIn("grab coffee", us)
        self.assertIn("fancy grabbing", uk)
        self.assertIn("German (Germany)", de)
        self.assertIn("Mexican Spanish", es)
        self.assertNotEqual(us, uk)

    def test_prompt_requires_distinct_outputs(self):
        system, _ = grammar.build_styled_translation_prompt(
            src_hint="English",
            tgt="English",
            wants_translation=False,
            locale="American English",
        )
        self.assertIn("MUST be meaningfully different", system)
        self.assertIn("do NOT auto-casualize", system)


class ParseContractTests(unittest.TestCase):
    def test_parse_preserves_ui_keys(self):
        raw = {
            "detected_lang": "Persian",
            "native": {"from": "هفته آینده آماده می‌شه", "to": "It'll be ready next week."},
            "friendly": {"from": "هفته آینده آماده می‌شه", "to": "It'll be ready next week."},
            "professional": {
                "from": "هفته آینده آماده می‌شه",
                "to": "It will be ready next week.",
            },
            "grammar_notes": '"اماده" → "آماده": missing hamza/alef in spelling.',
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="Persian", tgt="English", wants_translation=True
        )
        self.assertEqual(parsed["from_lang"], "Persian")
        self.assertTrue(parsed["wants_translation"])
        self.assertEqual(parsed["native"]["to"], "It'll be ready next week.")
        self.assertEqual(parsed["friendly"]["to"], parsed["friendly_casual"]["to"])
        self.assertIn("آماده", parsed["grammar_notes"])
        self.assertTrue(parsed["grammarNotes"])

    def test_parses_structured_grammar_notes(self):
        raw = {
            "detected_lang": "English",
            "native": {"from": "I agree.", "to": ""},
            "friendly": {"from": "Yeah, I agree.", "to": ""},
            "professional": {"from": "I agree.", "to": ""},
            "grammarNotes": [
                {
                    "original": "I am agree",
                    "correction": "I agree",
                    "explanation": '"agree" is a verb, so "am" is not needed.',
                }
            ],
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="English", tgt="English", wants_translation=False
        )
        self.assertEqual(parsed["grammarNotes"][0]["original"], "I am agree")
        self.assertIn("I agree", parsed["grammar_notes"])

    def test_best_version_falls_back_to_canonical(self):
        raw = {
            "detected_lang": "English",
            "canonical_meaning": "I agree with you.",
            "native": {"from": "I agree with you.", "to": ""},
            "friendly": {"from": "I agree with you.", "to": ""},
            "professional": {"from": "I agree with you.", "to": ""},
            "literal": {"from": "I agree with you.", "to": ""},
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="English", tgt="English", wants_translation=False
        )
        self.assertEqual(parsed["best_version"], "I agree with you.")
        self.assertEqual(parsed["canonical_meaning"], "I agree with you.")
        self.assertEqual(parsed["native"]["from"], "I agree with you.")


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

        def fake_chat(messages, temperature=0.2, max_tokens=2048, provider=None, groq_api_key=None, hf_api_key=None):
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
        self.assertIn("pick it up", result["friendly"]["to"].lower())
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
