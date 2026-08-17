"""Config and LLM fallback tests (no real secrets)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Settings, mask_secret  # noqa: E402
from app.llm import LLMError, chat, provider_route, strip_thinking  # noqa: E402


class MaskSecretTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(mask_secret(""), "(not set)")
        self.assertEqual(mask_secret(None), "(not set)")

    def test_long_masked(self):
        masked = mask_secret("hf_abcdefghijklmnop")
        self.assertNotIn("abcdefghijklmnop", masked)
        self.assertTrue(masked.startswith("hf_a"))


class RedisUrlTests(unittest.TestCase):
    def test_ignores_unresolved_railway_template_and_builds_from_parts(self):
        settings = Settings(
            redis_url="redis://${{REDISUSER}}:${{REDIS_PASSWORD}}@${{REDISHOST}}:${{REDISPORT}}",
            redis_host="redis.railway.internal",
            redis_port=6379,
            redis_user="default",
            redis_password="secret",
        )
        self.assertEqual(
            settings.resolved_redis_url,
            "redis://default:secret@redis.railway.internal:6379/0",
        )


class StripThinkingTests(unittest.TestCase):
    def test_strips_think_block(self):
        raw = "<think>secret reasoning</think>\nIt will be ready."
        self.assertEqual(strip_thinking(raw), "It will be ready.")


class RouteTests(unittest.TestCase):
    def test_selected_first_then_default_order(self):
        self.assertEqual(
            provider_route("huggingface"),
            ["huggingface", "ollama", "groq"],
        )
        self.assertEqual(
            provider_route("groq"),
            ["groq", "ollama", "huggingface"],
        )
        self.assertEqual(provider_route("groq", exclusive=True), ["groq"])


class FallbackTests(unittest.TestCase):
    def test_ollama_success_skips_hf(self):
        with patch("app.llm._skip_reason", return_value=None):
            with patch("app.llm._ollama_chat", return_value="hello from ollama"):
                with patch("app.llm._huggingface_chat") as hf:
                    with patch("app.llm._groq_chat") as groq:
                        content, provider = chat([{"role": "user", "content": "hi"}])
        self.assertEqual(content, "hello from ollama")
        self.assertEqual(provider, "ollama")
        hf.assert_not_called()
        groq.assert_not_called()

    def test_selected_hf_skips_ollama_first(self):
        with patch("app.llm._skip_reason", return_value=None):
            with patch("app.llm._huggingface_chat", return_value="hello from hf") as hf:
                with patch("app.llm._ollama_chat") as ollama:
                    with patch("app.llm._groq_chat") as groq:
                        content, provider = chat(
                            [{"role": "user", "content": "hi"}],
                            provider="huggingface",
                        )
        self.assertEqual(content, "hello from hf")
        self.assertEqual(provider, "huggingface")
        hf.assert_called_once()
        ollama.assert_not_called()
        groq.assert_not_called()

    def test_selected_groq_used_first(self):
        with patch("app.llm._skip_reason", return_value=None):
            with patch("app.llm._groq_chat", return_value="hello from groq"):
                with patch("app.llm._ollama_chat") as ollama:
                    with patch("app.llm._huggingface_chat") as hf:
                        content, provider = chat(
                            [{"role": "user", "content": "hi"}],
                            provider="groq",
                        )
        self.assertEqual(content, "hello from groq")
        self.assertEqual(provider, "groq")
        ollama.assert_not_called()
        hf.assert_not_called()

    def test_ollama_fail_uses_huggingface(self):
        with patch("app.llm._skip_reason", return_value=None):
            with patch("app.llm._ollama_chat", side_effect=ConnectionError("down")):
                with patch("app.llm._huggingface_chat", return_value="hello from hf"):
                    with patch("app.llm._groq_chat") as groq:
                        content, provider = chat([{"role": "user", "content": "hi"}])
        self.assertEqual(content, "hello from hf")
        self.assertEqual(provider, "huggingface")
        groq.assert_not_called()

    def test_selected_fails_does_not_fallback(self):
        with patch("app.llm._skip_reason", return_value=None):
            with patch("app.llm._huggingface_chat", side_effect=RuntimeError("hf down")):
                with patch("app.llm._ollama_chat") as ollama:
                    with patch("app.llm._groq_chat") as groq:
                        with self.assertRaises(LLMError) as ctx:
                            chat(
                                [{"role": "user", "content": "hi"}],
                                provider="huggingface",
                            )
        self.assertIn("huggingface", str(ctx.exception).lower())
        ollama.assert_not_called()
        groq.assert_not_called()

    def test_selected_groq_does_not_use_huggingface(self):
        with patch(
            "app.llm._skip_reason",
            side_effect=lambda name, groq_api_key=None, hf_api_key=None: (
                "GROQ_API_KEY is not configured" if name == "groq" else None
            ),
        ):
            with patch("app.llm._huggingface_chat") as hf:
                with patch("app.llm._ollama_chat") as ollama:
                    with patch("app.llm._groq_chat") as groq:
                        with self.assertRaises(LLMError) as ctx:
                            chat(
                                [{"role": "user", "content": "hi"}],
                                provider="groq",
                            )
        self.assertIn("groq", str(ctx.exception).lower())
        self.assertNotIn("huggingface", str(ctx.exception).lower())
        hf.assert_not_called()
        ollama.assert_not_called()
        groq.assert_not_called()

    def test_all_fail_raises(self):
        with patch("app.llm._skip_reason", return_value=None):
            with patch("app.llm._ollama_chat", side_effect=ConnectionError("down")):
                with patch("app.llm._huggingface_chat", side_effect=RuntimeError("no token")):
                    with patch("app.llm._groq_chat", side_effect=RuntimeError("no key")):
                        with self.assertRaises(LLMError):
                            chat([{"role": "user", "content": "hi"}])

    def test_request_groq_key_enables_groq(self):
        with patch("app.llm.get_settings") as settings:
            settings.return_value.hf_configured = False
            settings.return_value.groq_api_key = ""
            with patch("app.llm._groq_chat", return_value="hello from groq") as groq:
                with patch("app.llm._ollama_chat") as ollama:
                    with patch("app.llm._huggingface_chat") as hf:
                        content, provider = chat(
                            [{"role": "user", "content": "hi"}],
                            provider="groq",
                            groq_api_key="gsk_test_not_a_real_key",
                        )
        self.assertEqual(content, "hello from groq")
        self.assertEqual(provider, "groq")
        groq.assert_called_once()
        self.assertEqual(
            groq.call_args.kwargs.get("groq_api_key"), "gsk_test_not_a_real_key"
        )
        ollama.assert_not_called()
        hf.assert_not_called()

    def test_request_hf_key_enables_huggingface(self):
        with patch("app.llm.get_settings") as settings:
            settings.return_value.hf_token = ""
            settings.return_value.hf_configured = False
            with patch("app.llm._huggingface_chat", return_value="hello from hf") as hf:
                with patch("app.llm._ollama_chat") as ollama:
                    with patch("app.llm._groq_chat") as groq:
                        content, provider = chat(
                            [{"role": "user", "content": "hi"}],
                            provider="huggingface",
                            hf_api_key="hf_test_not_a_real_key",
                        )
        self.assertEqual(content, "hello from hf")
        self.assertEqual(provider, "huggingface")
        hf.assert_called_once()
        self.assertEqual(
            hf.call_args.kwargs.get("hf_api_key"), "hf_test_not_a_real_key"
        )
        ollama.assert_not_called()
        groq.assert_not_called()


if __name__ == "__main__":
    unittest.main()
