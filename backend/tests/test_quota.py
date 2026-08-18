"""Default-key quota helpers (no Redis)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from unittest.mock import MagicMock, patch

from app.quota import (  # noqa: E402
    consume,
    default_quota_kind,
    uses_default_groq,
    uses_default_hf,
)


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


class FakeRedis:
    def __init__(self):
        self.store: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.store[key] = int(self.store.get(key) or 0) + 1
        return self.store[key]

    def expire(self, key: str, ttl: int) -> bool:
        return True

    def get(self, key: str):
        value = self.store.get(key)
        return None if value is None else str(value)

    def ping(self) -> bool:
        return True

    def pipeline(self):
        raise RuntimeError("CROSSSLOT Keys in request don't hash to the same slot")


class ConsumeQuotaTests(unittest.TestCase):
    def test_consume_increments_ip_and_client_without_pipeline(self):
        fake = FakeRedis()
        request = MagicMock()
        request.headers.get.side_effect = lambda name, default="": {
            "x-forwarded-for": "203.0.113.9",
            "X-Client-Id": "browser-1",
        }.get(name, default)

        with patch("app.quota.get_redis", return_value=fake):
            consume(request, "groq")
            consume(request, "groq")

        self.assertEqual(len(fake.store), 2)
        self.assertTrue(all(count == 2 for count in fake.store.values()))


class RunGenerationQuotaTests(unittest.TestCase):
    def test_cache_hit_skips_llm_and_quota(self):
        from app.main import _run_generation

        producer = MagicMock(return_value={"items": []})
        with (
            patch("app.main.get_cached", return_value={"items": [1], "cached": True}),
            patch("app.main.consume") as consume_mock,
            patch("app.main.assert_can_generate") as assert_mock,
            patch("app.main.save_cached") as save_mock,
        ):
            result = _run_generation(
                MagicMock(),
                "groq",
                None,
                None,
                kind="tenses",
                parts={"text": "I work", "language": "English", "provider": "groq"},
                producer=producer,
            )
        producer.assert_not_called()
        consume_mock.assert_not_called()
        assert_mock.assert_not_called()
        save_mock.assert_not_called()
        self.assertEqual(result["items"], [1])

    def test_cache_miss_consumes_quota_once(self):
        from app.main import _run_generation

        producer = MagicMock(return_value={"items": []})
        with (
            patch("app.main.get_cached", return_value=None),
            patch("app.main.consume") as consume_mock,
            patch("app.main.assert_can_generate") as assert_mock,
            patch("app.main.save_cached") as save_mock,
        ):
            _run_generation(
                MagicMock(),
                "huggingface",
                None,
                None,
                kind="grammar",
                parts={"text": "Hi", "from_lang": "English", "to_lang": "Persian", "provider": "huggingface"},
                producer=producer,
            )
        producer.assert_called_once()
        consume_mock.assert_called_once()
        assert_mock.assert_called_once()
        save_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
