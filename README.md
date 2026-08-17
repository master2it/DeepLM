# DeepLM (FastAPI + Next.js)

Grammar/Spell Fixer and 12 Tenses in the browser. Pick **Ollama**, **Hugging Face**, or **Groq** in Settings. The API tries that provider first, then falls back: Ollama → Hugging Face → Groq.

## Prerequisites

- Docker Desktop
- [Ollama](https://ollama.com) on the host (not in Docker) if you use the local model

```bash
ollama pull deepseek-r1
ollama serve
```

Ollama must listen on port `11434`.

## Setup

```bash
copy .env.example .env
```

Optional Hugging Face key on the server. Groq can also be pasted in the Settings tab:

```env
HF_TOKEN=hf_your_token_here
GROQ_API_KEY=gsk_your_key_here
```

## Versioning

App version lives in [`VERSION`](VERSION) and is shown in the UI (`v…`) and on `GET /health`. Each push to `main` runs `.github/workflows/bump-version.yml`, which increments the patch number (for example `1.0.0` → `1.0.1`) and tags `v1.0.1`. Commits that already say `chore: bump version` are skipped so the bot does not loop.

## Deploy (Railpack)

The repo root is a monorepo. Railpack builds the **FastAPI backend**. Deploy the Next.js app separately (for example Vercel) with `NEXT_PUBLIC_API_URL` pointing at this API.

Set these on the host:

```env
CORS_ORIGINS=https://deep-lm.vercel.app,http://localhost:3000
HF_TOKEN=
GROQ_API_KEY=
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

`railpack.json` starts `uvicorn` from `backend/`. Do not set the service root directory to `frontend/`, and do not set a custom `start.sh` unless that file exists.

```bash
docker compose up --build
```

- App: http://localhost:3000
- API: http://localhost:8000
- Health: http://localhost:8000/health

## Local development (without Docker)

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set OLLAMA_BASE_URL=http://127.0.0.1:11434
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

## Tests

```bash
cd backend
python -m unittest tests.test_config tests.test_translation_quality -v
```

## Features

- **Grammar/Spell Fixer** — default tab; Persian, German, English, and other pairs; three styles (German ↔ Persian uses du/Sie and تو/شما)
- **12 Tenses** — conjugate a short English phrase with Persian glosses
- **Settings** — choose Ollama / Hugging Face / Groq; paste a Groq API key (saved in the browser)

## LLM routing

1. Use the provider selected in Settings
2. If it fails or is not configured, try the remaining providers in order: Ollama (`think: false`), Hugging Face (`Qwen/Qwen2.5-72B-Instruct`), Groq (`llama-3.3-70b-versatile`)
3. Strip leftover `<think>` blocks from replies

Keys are not required at startup. A request fails only if every provider fails.
