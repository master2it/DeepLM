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

### 2026-08-18 — Professional open-source README
- **Type:** patch
- **Version:** Unreleased
- **Summary:** README rewritten for public contributors: demo links, screenshots, architecture, setup, API, deploy, contributing, and license.
- **Why:** docs
- **Files:** `README.md`, `frontend/public/image-1.jpg`, `frontend/public/image-2.jpg`, `frontend/public/image-3.jpg`

### 2026-08-18 — Cache tense explanations
- **Type:** patch
- **Version:** Unreleased
- **Summary:** Tense explanations are stored in Redis like grammar and tenses. Repeat explain requests return the cache and do not count against the daily limit.
- **Why:** feature
- **Files:** `backend/app/main.py`, `backend/app/cache.py`, `backend/tests/test_cache.py`, `README.md`

### 2026-08-18 — Fix default-key quota consume
- **Type:** patch
- **Version:** Unreleased
- **Summary:** Default HF/Groq daily counts increment with separate Redis commands (cluster-safe). Cache hits return stored results without counting against the 30/day limit.
- **Why:** bug
- **Files:** `backend/app/main.py`, `backend/app/quota.py`, `backend/app/cache.py`, `frontend/src/lib/api.ts`, `frontend/src/components/limits-panel.tsx`

---

## [1.5.0] — 2026-08-18 — minor

### 2026-08-18 — Provider badge colors
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Header provider tags use green for ready and red for offline / not set.
- **Why:** copy
- **Files:** `frontend/src/app/page.tsx`

### 2026-08-18 — Prefer Railway REDIS_PRIVATE_URL
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Redis connection prefers REDIS_PRIVATE_URL (Railway private network) over REDIS_URL.
- **Why:** deploy
- **Files:** `backend/app/config.py`, `railway.toml`

### 2026-08-18 — Groq default-key daily limit
- **Type:** minor
- **Version:** 1.5.0
- **Summary:** Empty Groq key in Settings uses server GROQ_API_KEY with a 30/day cap (browser id + IP, Redis), same as Hugging Face. Limits tab shows both HF and Groq usage. Own Groq key is uncapped.
- **Why:** feature
- **Files:** `backend/app/quota.py`, `backend/app/main.py`, `frontend/src/components/limits-panel.tsx`

### 2026-08-18 — Hugging Face key and daily default-key limits
- **Type:** minor
- **Version:** 1.5.0
- **Summary:** Settings accepts a Hugging Face API key (browser-only). Empty field uses server HF_TOKEN with a 30/day cap per browser id and IP (Redis). Cache hits do not count. Limits tab shows used/remaining. Own HF token is uncapped.
- **Why:** feature
- **Files:** `backend/app/quota.py`, `backend/app/llm.py`, `backend/app/main.py`, `frontend/src/components/limits-panel.tsx`, `frontend/src/components/settings-panel.tsx`

---

## [1.4.0] — 2026-08-17 — minor

### 2026-08-17 — Redis cache TTL 12 hours
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Grammar and tenses Redis cache TTL is 12 hours (43200 seconds).
- **Why:** feature
- **Files:** `backend/app/config.py`, `backend/app/cache.py`, `docker-compose.yml`, `railway.toml`

### 2026-08-17 — Railway Redis env aliases
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Redis settings accept Railway plugin names (REDISHOST, REDISPORT, REDISUSER, REDISPASSWORD). Unresolved `${{...}}` REDIS_URL templates are ignored and the URL is built from host/user/password instead.
- **Why:** deploy
- **Files:** `backend/app/config.py`

### 2026-08-17 — Redis cache for grammar and tenses
- **Type:** minor
- **Version:** 1.4.0
- **Summary:** Grammar and tenses generations are cached in Redis (12-hour TTL). Local Redis runs via Docker Compose; Railway uses REDIS_URL from the Redis plugin. Groq keys are not stored. Cache misses if Redis is down.
- **Why:** feature
- **Files:** `backend/app/cache.py`, `backend/app/main.py`, `docker-compose.yml`, `railway.toml`

### 2026-08-17 — Show tense count per language
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Tenses language picker and copy show how many tenses each language has (English 12, German 6).
- **Why:** copy
- **Files:** `frontend/src/components/tenses-generator.tsx`, `backend/app/constants.py`, `backend/app/main.py`

### 2026-08-17 — German 6-tense model
- **Type:** minor
- **Version:** 1.4.0
- **Summary:** German Tenses now uses exactly six tenses (Präsens, Präteritum, Perfekt, Plusquamperfekt, Futur I, Futur II) with canonical keys, English glosses, and teacher rules for spoken Perfekt vs written Präteritum. English still uses 12 tenses.
- **Why:** feature
- **Files:** `backend/app/tenses.py`, `backend/app/constants.py`, `frontend/src/components/tenses-generator.tsx`

### 2026-08-17 — Remove Install from Settings
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Removed the Install DeepLM block from Settings. The header Install app button remains.
- **Why:** copy
- **Files:** `frontend/src/components/settings-panel.tsx`, `README.md`

### 2026-08-17 — Rename tenses tab
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Desktop tab label is now Tenses (was 12 Tenses Generator).
- **Why:** copy
- **Files:** `frontend/src/app/page.tsx`

### 2026-08-17 — Default grammar pair English → Persian
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Grammar/Spell Fixer now defaults from English to Persian.
- **Why:** feature
- **Files:** `backend/app/constants.py`, `frontend/src/components/grammar-fixer.tsx`, `README.md`

### 2026-08-17 — Groq model openai/gpt-oss-120b
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Default Groq model is now `openai/gpt-oss-120b` (was `llama-3.3-70b-versatile`).
- **Why:** feature
- **Files:** `backend/app/config.py`, `.env.example`, `docker-compose.yml`

### 2026-08-17 — Honor selected LLM provider
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Grammar, tenses, and explain use only the Settings provider. Switching to Groq no longer falls back to Hugging Face if Groq is skipped or fails.
- **Why:** bug
- **Files:** `backend/app/llm.py`, `frontend/src/components/settings-panel.tsx`

### 2026-08-17 — Sync pnpm lockfile for Serwist
- **Type:** patch
- **Version:** 1.4.0
- **Summary:** Updated `frontend/pnpm-lock.yaml` so Vercel `pnpm install` (frozen lockfile) includes `@serwist/next`, `serwist`, and `@serwist/cli`.
- **Why:** deploy
- **Files:** `frontend/pnpm-lock.yaml`

---

## [1.3.0] — 2026-08-17 — minor

### 2026-08-17 — Mobile bottom tab bar
- **Type:** patch
- **Version:** 1.3.0
- **Summary:** On small screens, primary tabs sit in a fixed bottom action bar (icon + label, safe-area padding). Desktop keeps the top tab list.
- **Why:** feature / mobile UI
- **Files:** `frontend/src/app/page.tsx`, `frontend/src/components/ui/tabs.tsx`

### 2026-08-17 — Progressive Web App
- **Type:** minor
- **Version:** 1.3.0
- **Summary:** Added web app manifest, PNG icons, Serwist service worker (API network-only), `/offline` fallback, and an Install app button (plus iOS Add to Home Screen hint).
- **Why:** feature
- **Files:** `frontend/src/app/manifest.ts`, `frontend/src/app/sw.ts`, `frontend/src/components/install-button.tsx`, `frontend/next.config.ts`

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
