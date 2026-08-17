"""HF default-key quota helpers (no Redis)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.quota import uses_default_hf  # noqa: E402


class DefaultHfQuotaTests(unittest.TestCase):
    def test_default_when_huggingface_and_empty_key(self):
        self.assertTrue(uses_default_hf("huggingface", None))
        self.assertTrue(uses_default_hf("huggingface", "  "))

    def test_own_key_skips_quota(self):
        self.assertFalse(uses_default_hf("huggingface", "hf_abc"))
        self.assertFalse(uses_default_hf("groq", None))
        self.assertFalse(uses_default_hf("ollama", None))


if __name__ == "__main__":
    unittest.main()
