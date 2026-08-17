"""Config and LLM fallback tests (no real secrets)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import mask_secret  # noqa: E402
from app.llm import LLMError, chat, strip_thinking  # noqa: E402


class MaskSecretTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(mask_secret(""), "(not set)")
        self.assertEqual(mask_secret(None), "(not set)")

    def test_long_masked(self):
        masked = mask_secret("hf_abcdefghijklmnop")
        self.assertNotIn("abcdefghijklmnop", masked)
        self.assertTrue(masked.startswith("hf_a"))


class StripThinkingTests(unittest.TestCase):
    def test_strips_think_block(self):
        raw = "<think>secret reasoning</think>\nIt will be ready."
        self.assertEqual(strip_thinking(raw), "It will be ready.")


class FallbackTests(unittest.TestCase):
    def test_ollama_success_skips_hf(self):
        with patch("app.llm._ollama_chat", return_value="hello from ollama"):
            with patch("app.llm._huggingface_chat") as hf:
                content, provider = chat([{"role": "user", "content": "hi"}])
        self.assertEqual(content, "hello from ollama")
        self.assertEqual(provider, "ollama")
        hf.assert_not_called()

    def test_ollama_fail_uses_huggingface(self):
        with patch("app.llm._ollama_chat", side_effect=ConnectionError("down")):
            with patch("app.llm._huggingface_chat", return_value="hello from hf"):
                content, provider = chat([{"role": "user", "content": "hi"}])
        self.assertEqual(content, "hello from hf")
        self.assertEqual(provider, "huggingface")

    def test_both_fail_raises(self):
        with patch("app.llm._ollama_chat", side_effect=ConnectionError("down")):
            with patch("app.llm._huggingface_chat", side_effect=RuntimeError("no token")):
                with self.assertRaises(LLMError):
                    chat([{"role": "user", "content": "hi"}])


if __name__ == "__main__":
    unittest.main()
