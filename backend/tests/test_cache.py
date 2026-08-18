"""Redis cache key tests (no Redis server required)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.cache import make_cache_key  # noqa: E402


class CacheKeyTests(unittest.TestCase):
    def test_same_input_same_key(self):
        a = make_cache_key("grammar", {"text": "Hello  world", "from_lang": "English", "to_lang": "Persian", "provider": "groq"})
        b = make_cache_key("grammar", {"text": "Hello world", "from_lang": "English", "to_lang": "Persian", "provider": "groq"})
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("deeplm:grammar:"))

    def test_case_does_not_change_key(self):
        a = make_cache_key("grammar", {"text": "Hi, Yesterday", "from_lang": "English", "to_lang": "Persian", "provider": "groq"})
        b = make_cache_key("grammar", {"text": "hi, yesterday", "from_lang": "English", "to_lang": "Persian", "provider": "groq"})
        self.assertEqual(a, b)

    def test_provider_changes_key(self):
        a = make_cache_key("tenses", {"text": "I work", "language": "English", "provider": "groq"})
        b = make_cache_key("tenses", {"text": "I work", "language": "English", "provider": "huggingface"})
        self.assertNotEqual(a, b)

    def test_explain_key_uses_tense_and_language(self):
        a = make_cache_key(
            "tenses_explain",
            {"tense": "Present Simple", "language": "English", "provider": "groq"},
        )
        b = make_cache_key(
            "tenses_explain",
            {"tense": "Present Perfect", "language": "English", "provider": "groq"},
        )
        c = make_cache_key(
            "tenses_explain",
            {"tense": "Present Simple", "language": "German", "provider": "groq"},
        )
        self.assertTrue(a.startswith("deeplm:tenses_explain:"))
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)

    def test_does_not_embed_groq_key(self):
        key = make_cache_key(
            "grammar",
            {"text": "hi", "from_lang": "English", "to_lang": "Persian", "provider": "groq"},
        )
        self.assertNotIn("gsk_", key)

    def test_locale_changes_key(self):
        a = make_cache_key(
            "grammar",
            {
                "text": "hi",
                "from_lang": "English",
                "to_lang": "English",
                "to_locale": "American English",
                "provider": "groq",
            },
        )
        b = make_cache_key(
            "grammar",
            {
                "text": "hi",
                "from_lang": "English",
                "to_lang": "English",
                "to_locale": "British English",
                "provider": "groq",
            },
        )
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
