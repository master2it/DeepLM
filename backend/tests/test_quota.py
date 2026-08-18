"""Default-key quota helpers (no Redis)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.quota import default_quota_kind, uses_default_groq, uses_default_hf  # noqa: E402


class DefaultKeyQuotaTests(unittest.TestCase):
    def test_default_when_huggingface_and_empty_key(self):
        self.assertTrue(uses_default_hf("huggingface", None))
        self.assertTrue(uses_default_hf("huggingface", "  "))

    def test_default_when_groq_and_empty_key(self):
        self.assertTrue(uses_default_groq("groq", None))
        self.assertTrue(uses_default_groq("groq", "  "))

    def test_own_key_skips_quota(self):
        self.assertFalse(uses_default_hf("huggingface", "hf_abc"))
        self.assertFalse(uses_default_groq("groq", "gsk_abc"))
        self.assertFalse(uses_default_hf("groq", None))
        self.assertFalse(uses_default_groq("huggingface", None))
        self.assertFalse(uses_default_hf("ollama", None))

    def test_quota_kind(self):
        self.assertEqual(default_quota_kind("huggingface", None, None), "hf")
        self.assertEqual(default_quota_kind("groq", None, None), "groq")
        self.assertIsNone(default_quota_kind("huggingface", "hf_x", None))
        self.assertIsNone(default_quota_kind("groq", None, "gsk_x"))
        self.assertIsNone(default_quota_kind("ollama", None, None))


if __name__ == "__main__":
    unittest.main()
