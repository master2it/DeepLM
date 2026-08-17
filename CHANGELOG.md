# Changelog

Log every AI-assisted change here **in the same PR/commit** as the fix. Newest entries go at the top.

## How to log

1. Add a new `###` heading under `[Unreleased]` using the template below.
2. Pick **one** bump type (this is the version class for that change):
   - **major** — breaking API/UI, dropped features, data/format changes users must adapt to
   - **minor** — new feature that stays backward compatible
   - **patch** — bug fix, copy, styling, deploy/config fix (no new capability)
   - **release** — ship a named production cut (copy Unreleased into `## [x.y.z]`)
3. Fill **Type**, **Summary**, **Why**, **Files**. Mention the model/tool if useful (e.g. Cursor).
4. When you merge to `main`, the GitHub Action still bumps the **patch** in `VERSION`. If this change was **minor** or **major**, bump that part of `VERSION` yourself (or ask the agent to) **before** merge so the tag matches the log.

### Template (copy)

```markdown
### YYYY-MM-DD — short title
- **Type:** major | minor | patch | release
- **Version:** x.y.z (or Unreleased)
- **Summary:** what changed
- **Why:** bug / feature / deploy
- **Files:** paths touched
```

---

## [Unreleased]

---

## [1.2.0] — 2026-08-17 — minor

### 2026-08-17 — Changelog tab in the UI
- **Type:** minor
- **Version:** 1.2.0
- **Summary:** Added a Changelog / Versions tab that loads releases from `GET /api/changelog` (parsed from CHANGELOG.md) and shows app + API versions with major/minor/patch/release badges.
- **Why:** feature
- **Files:** `backend/app/changelog.py`, `frontend/src/components/changelog-panel.tsx`, `frontend/src/app/page.tsx`

---

## [1.1.0] — 2026-08-17 — minor

### 2026-08-17 — 12 tenses language selector (English / German)
- **Type:** minor
- **Version:** 1.1.0
- **Summary:** 12 Tenses tab lets the user pick English or German. German uses the same 12-tense chart mapped to Präsens/Perfekt/Präteritum/Plusquamperfekt/Futur, with Persian glosses. Info dialog explains the selected language.
- **Why:** feature
- **Files:** `backend/app/tenses.py`, `backend/app/main.py`, `frontend/src/components/tenses-generator.tsx`, `frontend/src/lib/api.ts`

### 2026-08-17 — AI changelog process
- **Type:** patch
- **Version:** 1.1.0
- **Summary:** Added this changelog so each AI fix is recorded with a major/minor/patch/release class.
- **Why:** process
- **Files:** `CHANGELOG.md`, `README.md`

---

## [1.0.0] — 2026-08-17 — release

First web release of DeepLM (FastAPI + Next.js).

### 2026-08-17 — German ↔ Persian
- **Type:** minor
- **Version:** 1.0.0
- **Summary:** Grammar fixer prompts and UI copy support German ↔ Persian (du/Sie, تو/شما, impersonal «آماده می‌شه» → *es wird fertig*).
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `frontend/src/components/grammar-fixer.tsx`

### 2026-08-17 — CORS and Railway API URL
- **Type:** patch
- **Version:** 1.0.0
- **Summary:** Frontend production API defaults to `https://deeplm.up.railway.app`. CORS allows Vercel/Railway origins and strips trailing slashes.
- **Why:** bug (cross-origin blocked `/api/languages`)
- **Files:** `backend/app/config.py`, `backend/app/main.py`, `frontend/src/lib/api.ts`

### 2026-08-17 — Railpack / Vercel build
- **Type:** patch
- **Version:** 1.0.0
- **Summary:** Python detect + pip deps at repo root for Railpack; Next `standalone` output only when `OUTPUT_STANDALONE=1` so Vercel can build.
- **Why:** deploy bugs
- **Files:** `railpack.json`, `requirements.txt`, `frontend/next.config.ts`, `frontend/Dockerfile`

### 2026-08-17 — Mobile layout
- **Type:** patch
- **Version:** 1.0.0
- **Summary:** Responsive tabs, stacked language controls, wrapping cards, mobile viewport.
- **Why:** UI
- **Files:** `frontend/src/app/*`, `frontend/src/components/**`

### 2026-08-17 — Groq token in Settings
- **Type:** minor
- **Version:** 1.0.0
- **Summary:** User can paste a Groq API key when Groq is selected; key stored in the browser and sent with requests.
- **Why:** feature
- **Files:** `frontend/src/components/settings-panel.tsx`, `backend/app/llm.py`, `backend/app/main.py`

### 2026-08-17 — Provider settings (HF / Ollama / Groq)
- **Type:** minor
- **Version:** 1.0.0
- **Summary:** Settings tab picks preferred provider; API tries that first then falls back Ollama → Hugging Face → Groq.
- **Why:** feature
- **Files:** `backend/app/llm.py`, `frontend/src/app/page.tsx`

### 2026-08-17 — FastAPI + Next.js + Docker
- **Type:** major
- **Version:** 1.0.0
- **Summary:** Replaced the PySide desktop app with FastAPI, Next.js (shadcn), and Docker Compose. Ollama on the host; Hugging Face fallback.
- **Why:** architecture
- **Files:** `backend/`, `frontend/`, `docker-compose.yml`
