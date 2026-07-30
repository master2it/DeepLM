"""
Application configuration — HF token and related settings.

Loading strategy:
  - Development (running from source): optionally load `.env` via python-dotenv
    from the project directory (NOT the process CWD).
  - Packaged PyInstaller `.exe`: do NOT load `.env`; use Windows / OS
    environment variables only (e.g. set via `setx HF_TOKEN "..."`).

Never hardcode secrets. Never log or print raw token values.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_DOTENV_LOADED = False


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


MISSING_HF_TOKEN_MESSAGE = """HF_TOKEN is not configured.

Development (python language.py):
  1. Copy .env.example to .env next to language.py
  2. Set: HF_TOKEN=hf_your_token_here
  3. Run: python language.py

Packaged Windows app (translator.exe):
  Do NOT use a .env file next to the .exe.
  Set a Windows user environment variable:

    setx HF_TOKEN "hf_your_token_here"

  Then close and reopen CMD/PowerShell (and restart the app) so the new
  variable is available. Verify with:

    echo %HF_TOKEN%

Create a token at: https://huggingface.co/settings/tokens

Security: never embed HF_TOKEN inside the .exe or commit it to git.
"""


def is_frozen() -> bool:
    """True when running inside a PyInstaller (or similar) frozen bundle."""
    return bool(getattr(sys, "frozen", False))


def project_dir() -> Path:
    """Directory of the source package (config.py / language.py), not CWD."""
    return Path(__file__).resolve().parent


def executable_dir() -> Path:
    """Directory containing the running .exe (frozen) or project dir (source)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return project_dir()


def load_development_dotenv() -> bool:
    """
    Load `.env` for local development only.

    Returns True if a .env file was found and load_dotenv was called.
    Never loads .env when frozen (packaged .exe).
    Does not override variables already set in the OS environment.
    """
    global _DOTENV_LOADED
    if is_frozen():
        return False
    if _DOTENV_LOADED:
        return False

    env_path = project_dir() / ".env"
    _DOTENV_LOADED = True
    if not env_path.is_file():
        return False

    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    # override=False: real OS env (or setx) wins over .env
    load_dotenv(env_path, override=False)
    return True


def mask_secret(value: str | None) -> str:
    """Safe display form for secrets (never the full token)."""
    if not value:
        return "(not set)"
    text = str(value).strip()
    if not text:
        return "(not set)"
    if len(text) <= 8:
        return "***"
    return f"{text[:4]}…{text[-4:]} ({len(text)} chars)"


def get_hf_token(*, required: bool = False) -> str:
    """
    Return HF_TOKEN from the environment.

    Development: loads project `.env` first (if present), then reads os.environ.
    Packaged .exe: reads Windows/OS environment only.
    """
    load_development_dotenv()
    token = (os.getenv("HF_TOKEN") or "").strip()
    if required and not token:
        raise ConfigError(MISSING_HF_TOKEN_MESSAGE)
    return token


def get_hf_chat_model() -> str:
    load_development_dotenv()
    return (
        os.getenv("HF_CHAT_MODEL") or "Qwen/Qwen2.5-72B-Instruct"
    ).strip()


def get_hf_translate_model() -> str:
    load_development_dotenv()
    return (
        os.getenv("HF_TRANSLATE_MODEL") or "facebook/nllb-200-distilled-600M"
    ).strip()


def hf_token_status() -> dict:
    """Debug-friendly status without exposing the raw token."""
    load_development_dotenv()
    token = (os.getenv("HF_TOKEN") or "").strip()
    return {
        "frozen": is_frozen(),
        "dotenv_used": (not is_frozen()) and (project_dir() / ".env").is_file(),
        "hf_token_set": bool(token),
        "hf_token_masked": mask_secret(token),
        "chat_model": get_hf_chat_model(),
        "translate_model": get_hf_translate_model(),
    }
