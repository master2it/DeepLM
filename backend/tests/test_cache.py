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

    def test_provider_changes_key(self):
        a = make_cache_key("tenses", {"text": "I work", "language": "English", "provider": "groq"})
        b = make_cache_key("tenses", {"text": "I work", "language": "English", "provider": "huggingface"})
        self.assertNotEqual(a, b)

    def test_does_not_embed_groq_key(self):
        key = make_cache_key(
            "grammar",
            {"text": "hi", "from_lang": "English", "to_lang": "Persian", "provider": "groq"},
        )
        self.assertNotIn("gsk_", key)


if __name__ == "__main__":
    unittest.main()
