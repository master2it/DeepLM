# English AI Assistant

## Setup (development)

```bash
uv venv
.venv\Scripts\activate
uv pip install -r requirements-language.txt
copy .env.example .env
```

Edit `.env` (local only — never commit) and set:

- `HF_TOKEN` — required ([create a token](https://huggingface.co/settings/tokens))

Optional:

- `HF_CHAT_MODEL` — default `Qwen/Qwen2.5-72B-Instruct` (12 Tenses + Grammar/Spell Fixer)

## Run (source)

```bash
python language.py
```

Loads `HF_TOKEN` from the process environment, with optional `.env` via `python-dotenv` (project folder only — not CWD).

## Packaged Windows `.exe` (no `.env`)

Build (does **not** bundle `.env`):

```bash
pyinstaller language.spec
```

Output: `dist\translator.exe`

Configure auth with a **Windows user environment variable** (not a `.env` file):

```cmd
setx HF_TOKEN "hf_your_token_here"
```

Then **restart** CMD/PowerShell and the app so `setx` is picked up. Verify:

```cmd
echo %HF_TOKEN%
```

Run:

```cmd
dist\translator.exe
```

### Security

- Do **not** embed `HF_TOKEN` in the `.exe`, source, or PyInstaller datas.
- Anything shipped inside a distributed binary can be extracted.
- For public distribution, prefer a backend that holds the Hugging Face credential.

## Tests

```bash
python -m unittest tests.test_config tests.test_translation_quality -v
```

Live model checks (optional):

```bash
set RUN_LIVE_TRANSLATION_TESTS=1
python -m unittest tests.test_translation_quality.LivePersianEnglishTests -v
```

## Features

- **12 Tenses** — HuggingFace chat model
- **Grammar/Spell Fixer** — default tab; Persian → natural American English (B2); 3 styles; grammar notes

## Translation architecture

| Path | Model | How |
|------|--------|-----|
| Grammar/Spell Fixer | `HF_CHAT_MODEL` (LLM chat) | Detect → analyze implicit subjects → **canonical_meaning** → style variants from that meaning |

- Context can be passed as `context=` to `get_styled_translations_from_ai` (UI does not yet); each turn is independent by default.
- Styles are **not** three independent translations: they must share one canonical reading (tone/register only).
- A heuristic retry catches Persian impersonal «آماده میشه» wrongly rendered as English «I'll be ready».
