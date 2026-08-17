# DeepLM (FastAPI + Next.js)

Grammar/Spell Fixer and 12 Tenses in the browser. The API tries **local Ollama** (`deepseek-r1`, thinking off) first, then **Hugging Face** if Ollama fails.

## Prerequisites

- Docker Desktop
- [Ollama](https://ollama.com) on the host (not in Docker)

```bash
ollama pull deepseek-r1
ollama serve
```

Ollama must listen on port `11434`.

## Setup

```bash
copy .env.example .env
```

Optional: set `HF_TOKEN` in `.env` so the API can fall back when Ollama is down.

```env
HF_TOKEN=hf_your_token_here
```

## Run with Docker

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

- **Grammar/Spell Fixer** — default tab; Persian → natural American English (B2); three styles
- **12 Tenses** — conjugate a short English phrase with Persian glosses

## LLM routing

1. Ollama `POST /api/chat` with `think: false`
2. Strip leftover `<think>` blocks
3. Hugging Face `Qwen/Qwen2.5-72B-Instruct` if Ollama errors

`HF_TOKEN` is not required at startup. Requests fail only if both providers fail.
