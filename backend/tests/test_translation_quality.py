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
        self.assertIn("grammarFix", system)
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
        self.assertIn("natural contemporary phrasing", de_fa)
        self.assertIn("German", user_de)
        self.assertIn("Persian", user_de)

        fa_de, user_fa = grammar.build_styled_translation_prompt(
            src_hint="Persian",
            tgt="German",
            wants_translation=True,
        )
        self.assertIn("German ↔ Persian", fa_de)
        self.assertIn("natural contemporary phrasing", fa_de)
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
        self.assertIn("Do NOT simply copy Native", system)
        self.assertIn("HARD RULE", system)
        self.assertIn("independent Native", system)
        self.assertIn("ORIGINAL user input", system)
        self.assertNotIn("same enhanced source", system)
        self.assertIn("natural everyday conversation", system)
        self.assertIn("maximum slang", system)
        self.assertIn("Professional ≠ formal", system)
        self.assertIn("Professional = clear", system)
        self.assertIn("wanna", system)
        self.assertIn("no worries", system)
        self.assertIn("prior to", system)
        self.assertIn("unable to do so", system)
        self.assertIn("MINIMUM possible changes", system)
        self.assertIn("correction layer", system)
        self.assertIn("natural collocations", system)
        self.assertIn("Do NOT force chunks", system)
        self.assertIn("Do NOT apply this rule to Grammar Fix", system)
        self.assertIn("I hope this message finds you well", system)
        self.assertIn("make a decision", system)
        self.assertNotIn("Slack/WhatsApp", system)

        translating, user = grammar.build_styled_translation_prompt(
            src_hint="English",
            tgt="Persian",
            wants_translation=True,
            locale="Iranian Persian",
        )
        self.assertNotIn("same enhanced source", translating)
        self.assertIn("Independently rewrite the ORIGINAL", translating)
        self.assertIn("never copy Native", translating)
        self.assertIn("translate EACH", translating)
        self.assertIn("independent Friendly", translating)
        self.assertIn("independent Professional", translating)
        self.assertIn("grammarFix", translating)
        self.assertIn("MINIMUM possible changes", translating)
        self.assertIn("correction layer", translating)
        self.assertIn("Independently rewrite Native", user)


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


class StyleDifferentiationTests(unittest.TestCase):
    def test_flags_identical_native_and_friendly(self):
        result = {
            "native": {"from": "", "to": "Could you send me the file today please."},
            "friendly": {"from": "", "to": "Could you send me the file today please."},
            "professional": {
                "from": "",
                "to": "Please send the file today so I can review it before the meeting.",
            },
        }
        feedback = grammar.styles_too_similar_feedback(
            result, wants_translation=True
        )
        self.assertIsNotNone(feedback)
        self.assertIn("Friendly", feedback)

    def test_allows_distinct_versions(self):
        result = {
            "native": {
                "from": "",
                "to": "Hey, I wanted to ask if you could send me the file today?",
            },
            "friendly": {
                "from": "",
                "to": "Hey, can you send me the file today? I need to look it over before tomorrow's meeting.",
            },
            "professional": {
                "from": "",
                "to": "Could you send the file today? I need to review it before tomorrow's meeting. If you can't, please let me know.",
            },
        }
        self.assertIsNone(
            grammar.styles_too_similar_feedback(result, wants_translation=True)
        )

    def test_skips_very_short_texts(self):
        result = {
            "native": {"from": "Thanks.", "to": ""},
            "friendly": {"from": "Thanks.", "to": ""},
            "professional": {"from": "Thank you.", "to": ""},
        }
        self.assertIsNone(
            grammar.styles_too_similar_feedback(result, wants_translation=False)
        )

    def test_flags_identical_source_even_when_translations_differ(self):
        shared = (
            "Hey, I wanted to ask if you could send me the file today? "
            "I need to look it over before our meeting tomorrow."
        )
        result = {
            "native": {"from": shared, "to": "نسخه طبیعی فارسی متفاوت."},
            "friendly": {"from": shared, "to": "نسخه خودمونی کاملا جدا."},
            "professional": {
                "from": "Could you send the file today? I need to review it before tomorrow's meeting. If you can't, please let me know.",
                "to": "نسخه اداری جداگانه.",
            },
        }
        feedback = grammar.styles_too_similar_feedback(
            result, wants_translation=True
        )
        self.assertIsNotNone(feedback)
        self.assertIn("from / grammarEnhanced", feedback)

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

    def test_parse_does_not_copy_native_from_onto_other_tones(self):
        raw = {
            "detected_lang": "English",
            "native": {
                "from": "Hey, could you send me the file today?",
                "to": "سلام، می‌تونی فایل رو امروز بفرستی؟",
            },
            "friendly": {
                "from": "Hey, can you send me the file today? No worries if not.",
                "to": "هی، می‌تونی امروز فایل رو بفرستی؟ نگران نباش اگر نشد.",
            },
            "professional": {
                "from": "Could you please send me the file today?",
                "to": "لطفاً فایل را امروز برایم بفرستید.",
            },
            "grammarNotes": [
                {
                    "original": "if you can send",
                    "correction": "if you could send",
                    "explanation": "more natural for a polite request.",
                }
            ],
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="English", tgt="Persian", wants_translation=True
        )
        self.assertNotEqual(parsed["native"]["from"], parsed["friendly"]["from"])
        self.assertNotEqual(parsed["native"]["from"], parsed["professional"]["from"])
        self.assertNotEqual(parsed["friendly"]["from"], parsed["professional"]["from"])
        self.assertEqual(parsed["native"]["grammarEnhanced"], parsed["native"]["from"])
        self.assertEqual(parsed["friendly"]["translated"], parsed["friendly"]["to"])
        self.assertEqual(parsed["grammarNotes"][0]["original"], "if you can send")

    def test_parse_does_not_fill_missing_from_from_native(self):
        raw = {
            "detected_lang": "English",
            "native": {"from": "Could you send the file today?", "to": "a"},
            "friendly": {"from": "", "to": "b"},
            "professional": {"from": "", "to": "c"},
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="English", tgt="Persian", wants_translation=True
        )
        self.assertEqual(parsed["native"]["from"], "Could you send the file today?")
        self.assertEqual(parsed["friendly"]["from"], "")
        self.assertEqual(parsed["professional"]["from"], "")
        self.assertEqual(parsed["grammarFix"]["from"], "")

    def test_parse_preserves_grammar_fix_separately(self):
        raw = {
            "detected_lang": "English",
            "grammarFix": {
                "from": "Can you send me the file today because I need to check it before the meeting tomorrow?",
                "to": "grammar-fix-fa",
            },
            "native": {
                "from": "Could you send me the file today? I need to review it before tomorrow's meeting.",
                "to": "native-fa",
            },
            "friendly": {
                "from": "Hey, can you send me the file today? I need to look it over before tomorrow's meeting.",
                "to": "friendly-fa",
            },
            "professional": {
                "from": "Could you send the file today? I need to review it before tomorrow's meeting.",
                "to": "professional-fa",
            },
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="English", tgt="Persian", wants_translation=True
        )
        self.assertEqual(
            parsed["grammarFix"]["from"],
            "Can you send me the file today because I need to check it before the meeting tomorrow?",
        )
        self.assertEqual(parsed["grammarFix"]["to"], "grammar-fix-fa")
        self.assertEqual(
            parsed["grammarFix"]["grammarEnhanced"], parsed["grammarFix"]["from"]
        )
        self.assertEqual(parsed["grammarFix"]["translated"], "grammar-fix-fa")
        self.assertNotEqual(parsed["grammarFix"]["from"], parsed["native"]["from"])
        self.assertEqual(parsed["best_version"], parsed["grammarFix"]["from"])

    def test_parse_reads_grammar_fix_snake_case_key(self):
        raw = {
            "detected_lang": "English",
            "grammar_fix": {"from": "I want to tell him that I can't come tomorrow.", "to": ""},
            "native": {"from": "I want to tell him I can't make it tomorrow.", "to": ""},
            "friendly": {"from": "I want to let him know I can't make it tomorrow.", "to": ""},
            "professional": {"from": "I want to let him know I won't be able to make it tomorrow.", "to": ""},
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="English", tgt="English", wants_translation=False
        )
        self.assertEqual(
            parsed["grammarFix"]["from"],
            "I want to tell him that I can't come tomorrow.",
        )

    def test_grammar_fix_matching_native_does_not_flag_similarity(self):
        same = (
            "I want to tell him that I can't come tomorrow because I have some work."
        )
        result = {
            "grammarFix": {"from": same, "to": "الف"},
            "native": {"from": same, "to": "ب"},
            "friendly": {
                "from": "Hey, can you let him know I can't make it tomorrow? I have some work.",
                "to": "ج",
            },
            "professional": {
                "from": "Could you let him know I won't be able to make it tomorrow? I have some work to finish.",
                "to": "د",
            },
        }
        self.assertIsNone(
            grammar.styles_too_similar_feedback(result, wants_translation=True)
        )

    def test_parse_reads_grammarEnhanced_translated_keys(self):
        raw = {
            "detected_lang": "English",
            "native": {
                "grammarEnhanced": "Could you send the file today?",
                "translated": "native-fa",
            },
            "friendly": {
                "grammarEnhanced": "Hey, can you send the file today?",
                "translated": "friendly-fa",
            },
            "professional": {
                "grammarEnhanced": "Please send the file today.",
                "translated": "professional-fa",
            },
        }
        parsed = grammar.parse_styled_translation_response(
            raw, src_hint="English", tgt="Persian", wants_translation=True
        )
        self.assertEqual(parsed["native"]["from"], "Could you send the file today?")
        self.assertEqual(parsed["friendly"]["from"], "Hey, can you send the file today?")
        self.assertEqual(parsed["professional"]["from"], "Please send the file today.")
        self.assertEqual(parsed["native"]["to"], "native-fa")
        self.assertEqual(parsed["friendly"]["to"], "friendly-fa")
        self.assertEqual(parsed["professional"]["to"], "professional-fa")
        self.assertEqual(parsed["native"]["grammarEnhanced"], parsed["native"]["from"])
        self.assertEqual(parsed["friendly"]["translated"], "friendly-fa")


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

    def test_preserves_independent_source_rewrites(self):
        payload = {
            "detected_lang": "English",
            "grammarFix": {
                "from": "Can you send me the file today because I need to check it before the meeting tomorrow?",
                "to": "grammar-fix-fa",
            },
            "native": {
                "from": "Hey, I wanted to ask if you could send me the file today?",
                "to": "native-fa",
            },
            "friendly": {
                "from": "Hey, can you send me the file today? I need to look it over.",
                "to": "friendly-fa",
            },
            "professional": {
                "from": "Could you send the file today? I need to review it.",
                "to": "professional-fa",
            },
            "grammarNotes": [
                {
                    "original": "if you can send",
                    "correction": "if you could send",
                    "explanation": "more natural for a polite request.",
                }
            ],
        }

        def fake_chat(*_args, **_kwargs):
            return json.dumps(payload), "groq"

        with patch.object(grammar, "chat", side_effect=fake_chat):
            result = grammar.get_styled_translations_from_ai(
                "Hey, I wanted to ask if you can send me the file today",
                from_lang="English",
                to_lang="Persian",
            )

        self.assertNotIn("error", result)
        self.assertEqual(result["native"]["from"], payload["native"]["from"])
        self.assertEqual(result["friendly"]["from"], payload["friendly"]["from"])
        self.assertEqual(result["professional"]["from"], payload["professional"]["from"])
        self.assertEqual(result["grammarFix"]["from"], payload["grammarFix"]["from"])
        self.assertEqual(result["grammarFix"]["to"], "grammar-fix-fa")
        self.assertEqual(result["native"]["to"], "native-fa")
        self.assertEqual(result["friendly"]["to"], "friendly-fa")
        self.assertEqual(result["professional"]["to"], "professional-fa")
        self.assertNotEqual(result["native"]["from"], result["friendly"]["from"])
        self.assertNotEqual(result["native"]["from"], result["professional"]["from"])
        self.assertEqual(result["grammarNotes"][0]["original"], "if you can send")

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
