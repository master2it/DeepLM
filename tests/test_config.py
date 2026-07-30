"""Regression tests for HF_TOKEN / config loading (no real secrets)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402


class MaskSecretTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(config.mask_secret(""), "(not set)")
        self.assertEqual(config.mask_secret(None), "(not set)")

    def test_short(self):
        self.assertEqual(config.mask_secret("hf_abc"), "***")

    def test_long_masked(self):
        masked = config.mask_secret("hf_abcdefghijklmnop")
        self.assertNotIn("abcdefghijklmnop", masked)
        self.assertTrue(masked.startswith("hf_a"))
        self.assertIn("chars", masked)


class GetHfTokenTests(unittest.TestCase):
    def setUp(self):
        config._DOTENV_LOADED = False

    def tearDown(self):
        config._DOTENV_LOADED = False

    def test_reads_os_environ(self):
        with patch.dict(os.environ, {"HF_TOKEN": "hf_test_token_value_xx"}, clear=False):
            with patch.object(config, "load_development_dotenv", return_value=False):
                self.assertEqual(config.get_hf_token(), "hf_test_token_value_xx")

    def test_missing_required_raises_clear_message(self):
        env = {k: v for k, v in os.environ.items() if k != "HF_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            with patch.object(config, "load_development_dotenv", return_value=False):
                with self.assertRaises(config.ConfigError) as ctx:
                    config.get_hf_token(required=True)
        msg = str(ctx.exception)
        self.assertIn("HF_TOKEN is not configured", msg)
        self.assertIn("setx HF_TOKEN", msg)
        self.assertIn("echo %HF_TOKEN%", msg)
        self.assertNotIn("hf_test", msg.lower())

    def test_missing_optional_returns_empty(self):
        env = {k: v for k, v in os.environ.items() if k != "HF_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            with patch.object(config, "load_development_dotenv", return_value=False):
                self.assertEqual(config.get_hf_token(required=False), "")

    def test_strips_whitespace(self):
        with patch.dict(os.environ, {"HF_TOKEN": "  hf_spaced_token_xx  "}, clear=False):
            with patch.object(config, "load_development_dotenv", return_value=False):
                self.assertEqual(config.get_hf_token(), "hf_spaced_token_xx")


class FrozenModeTests(unittest.TestCase):
    def setUp(self):
        config._DOTENV_LOADED = False

    def tearDown(self):
        config._DOTENV_LOADED = False

    def test_frozen_skips_dotenv(self):
        with patch.object(config, "is_frozen", return_value=True):
            self.assertFalse(config.load_development_dotenv())

    def test_frozen_still_reads_windows_env(self):
        with patch.object(config, "is_frozen", return_value=True):
            with patch.dict(os.environ, {"HF_TOKEN": "hf_from_windows_env_xx"}, clear=False):
                # Even if a .env existed, frozen mode must not load it;
                # token comes from OS env only.
                with patch.object(config, "load_development_dotenv", wraps=config.load_development_dotenv) as load:
                    token = config.get_hf_token()
                self.assertEqual(token, "hf_from_windows_env_xx")
                load.assert_called()

    def test_status_never_includes_raw_token(self):
        with patch.dict(os.environ, {"HF_TOKEN": "hf_secret_should_not_leak_zz"}, clear=False):
            with patch.object(config, "load_development_dotenv", return_value=False):
                status = config.hf_token_status()
        blob = str(status)
        self.assertNotIn("hf_secret_should_not_leak_zz", blob)
        self.assertTrue(status["hf_token_set"])
        self.assertIn("…", status["hf_token_masked"])


class RequireHfClientMessageTests(unittest.TestCase):
    def test_language_require_uses_config_error(self):
        import language

        language._hf_client = None
        env = {k: v for k, v in os.environ.items() if k != "HF_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            with patch.object(config, "load_development_dotenv", return_value=False):
                # Reset dotenv flag so get_hf_token does not think dotenv already ran
                config._DOTENV_LOADED = True
                with self.assertRaises(config.ConfigError) as ctx:
                    language.require_hf_client()
        self.assertIn("setx HF_TOKEN", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
