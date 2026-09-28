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

## [1.7.0] — 2026-09-28 — major

### 2026-09-28 — Migrate to a single Next.js OpenAI application
- **Type:** major
- **Version:** 1.7.0
- **Summary:** Replace the FastAPI, Redis, Hugging Face, and Groq stack with same-origin Next.js API routes backed by server-side OpenAI Chat.
- **Why:** feature
- **Files:** `src/app/api/**`, `src/lib/server/**`, `src/lib/api.ts`, `src/app/page.tsx`, `package.json`, `README.md`

---

## [1.6.0] — 2026-08-27 — minor

### 2026-08-27 — Default grammar to_locale to first list option
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** When Locale is unset or not in the list, pick the first option for that language (e.g. American English) and always send it on grammar requests.
- **Why:** bug
- **Files:** `frontend/src/components/grammar-fixer.tsx`, `frontend/src/lib/api.ts`

### 2026-08-27 — Remove header model status badges
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Remove the header chips that showed Qwen / DeepSeek / Groq ready status.
- **Why:** feature
- **Files:** `frontend/src/app/page.tsx`

### 2026-08-27 — Remove model tags in Settings and header
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Drop badge labels (Slower, Groq Free, etc.) from Settings model cards and header status chips; chips show only model name + ready/not set.
- **Why:** feature
- **Files:** `frontend/src/components/settings-panel.tsx`, `frontend/src/app/page.tsx`

### 2026-08-27 — List all Groq models as Settings radios
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Settings shows every Groq Free chat model as its own selectable card (with Qwen/DeepSeek). Choosing one sets provider=groq and that model id; API key stays shared.
- **Why:** feature
- **Files:** `frontend/src/components/settings-panel.tsx`, `frontend/src/lib/api.ts`

### 2026-08-27 — Release 1.6.0
- **Type:** release
- **Version:** 1.6.0
- **Summary:** Ship Unreleased work: remove Ollama, DeepSeek-V4-Flash via HF, Groq Free model picker with RPM/RPD limits, env-only API URL, and related UI/fixes.
- **Why:** release
- **Files:** `VERSION`, `backend/app/version.py`, `frontend/src/lib/version.ts`, `package.json`, `frontend/package.json`, `CHANGELOG.md`, `README.md`

### 2026-08-27 — Groq Free models + RPM/RPD limits
- **Type:** minor
- **Version:** 1.6.0
- **Summary:** Settings lists Groq Free chat models (gpt-oss, Qwen3, compound). Per-model Free RPM/RPD from Groq docs replace the old 30/hour cap. Whisper/Orpheus/Prompt Guard omitted (not chat). Cache schema 21.
- **Why:** feature
- **Files:** `backend/app/groq_models.py`, `quota.py`, `llm.py`, `main.py`, `cache.py`, frontend Settings/Limits/api, tests, docs

### 2026-08-27 — Add DeepSeek-V4-Flash via Hugging Face
- **Type:** minor
- **Version:** 1.6.0
- **Summary:** New Settings provider `deepseek` runs `deepseek-ai/DeepSeek-V4-Flash` through HF Inference Providers (same HF token / 50-day quota). Cache schema 20.
- **Why:** feature
- **Files:** `backend/app/llm.py`, `config.py`, `main.py`, `quota.py`, `cache.py`, frontend Settings/page/api/components, `.env.example`, `docker-compose.yml`

### 2026-08-27 — Avoid duplicate frontend API GETs
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Deduplicate health/languages/changelog/limits GETs; load languages once on the home page and pass into Grammar/Tenses tabs.
- **Why:** bug
- **Files:** `frontend/src/lib/api.ts`, `frontend/src/app/page.tsx`, `grammar-fixer.tsx`, `tenses-generator.tsx`

### 2026-08-27 — Frontend API URL from env only
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** `API_BASE` and the service worker use `NEXT_PUBLIC_API_URL` only (no hardcoded Railway/localhost fallbacks). Added `frontend/.env.development`, `.env.production`, and `.env.example`.
- **Why:** deploy
- **Files:** `frontend/src/lib/api.ts`, `frontend/src/app/sw.ts`, `frontend/.env.*`

### 2026-08-27 — Remove Ollama provider
- **Type:** major
- **Version:** 1.6.0
- **Summary:** Drop Ollama from API, Settings, health, cache keys, Docker, and docs. Only Hugging Face and Groq remain. Saved `ollama` selections migrate to Hugging Face.
- **Why:** feature
- **Files:** `backend/app/llm.py`, `config.py`, `main.py`, `cache.py`, `frontend/src/lib/api.ts`, `settings-panel.tsx`, `page.tsx`, grammar/tenses components, tests, `.env.example`, `docker-compose.yml`, `README.md`, package keywords

### 2026-08-27 — Fix Next.js 16 Turbopack / webpack conflict
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Add empty `turbopack: {}` and pass `--turbopack` on `next dev` so Serwist's webpack plugin no longer crashes Next 16. Production build stays on `--webpack`.
- **Why:** bug
- **Files:** `frontend/next.config.ts`, `frontend/package.json`

### 2026-08-27 — Show model names instead of Groq / Hugging Face
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Settings, header badges, Limits, and result/history labels show model names (e.g. Qwen2.5-72B-Instruct, gpt-oss-120b) instead of Groq / Hugging Face brand names.
- **Why:** feature
- **Files:** `frontend/src/lib/api.ts`, `frontend/src/components/settings-panel.tsx`, `frontend/src/components/limits-panel.tsx`, `frontend/src/components/grammar-fixer.tsx`, `frontend/src/components/tenses-generator.tsx`, `frontend/src/app/page.tsx`

### 2026-08-18 — HF provider auto-select for Qwen 72B
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Hugging Face chat defaults to `HF_PROVIDER=auto` instead of Together. Provider-not-supported errors fall through to other hosts.
- **Why:** bug
- **Files:** `backend/app/llm.py`, `backend/app/config.py`, `.env.example`, `railway.toml`, `docker-compose.yml`, `README.md`

### 2026-08-18 — Groq 30/hour instead of 30/day
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Groq's 30-generation cap (pasted key or server key) now resets every UTC hour. Hugging Face stays 50/day on the shared token.
- **Why:** feature
- **Files:** `backend/app/quota.py`, `backend/app/config.py`, `backend/tests/test_quota.py`, `frontend/src/components/limits-panel.tsx`, `frontend/src/components/settings-panel.tsx`, `frontend/src/lib/api.ts`, `.env.example`, `README.md`

### 2026-08-18 — Two-column tense cards with three click examples
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Tense results show two cards per row. Clicking a card explains that tense and lists three example sentences matching the user's phrase. Cache schema 18.
- **Why:** feature
- **Files:** `frontend/src/components/tenses-generator.tsx`, `frontend/src/lib/api.ts`, `backend/app/tenses.py`, `backend/app/main.py`, `backend/app/cache.py`, `backend/tests/test_tenses.py`, `backend/tests/test_cache.py`

### 2026-08-18 — Collocation intensity + tone-preserving translation
- **Type:** patch
- **Version:** 1.6.0
- **Summary:** Caps Native/Friendly/Professional at 0-2 natural chunks; Friendly cannot be more formal than Native. Each translation matches that version's tone instead of calquing English. Cache schema 17.
- **Why:** bug
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `backend/tests/test_translation_quality.py`

---

## [1.5.0] — 2026-08-18 — minor

### 2026-08-18 — Natural collocations for Native / Friendly / Professional
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Native, Friendly, and Professional prefer common native chunks when they fit; Grammar Fix still only corrects real errors. Cache schema 16.
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `backend/tests/test_translation_quality.py`

### 2026-08-18 — Grammar Fix as a fourth source output
- **Type:** minor
- **Version:** 1.5.0
- **Summary:** Adds Grammar Fix — minimum grammar/spelling correction of the original, then translation of that correction. Native / Friendly / Professional remain independent rewrites. Cache schema 15.
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `backend/tests/test_translation_quality.py`, `frontend/src/components/grammar-fixer.tsx`, `frontend/src/lib/api.ts`

### 2026-08-18 — Tone calibration: everyday casual, modern professional
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Friendly / Casual is natural everyday speech (low slang, no forced wanna/gotta/no worries). Professional is modern coworker English, not formal. Cache schema 14 drops old slang-heavy / overly formal results.
- **Why:** bug
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `backend/tests/test_translation_quality.py`

### 2026-08-18 — Independent source rewrite per tone
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Native, Friendly, and Professional each get their own source-language rewrite; translation runs on that rewrite. Parser no longer copies Native.from onto the other tones.
- **Why:** bug
- **Files:** `backend/app/grammar.py`, `backend/app/constants.py`, `backend/app/cache.py`, `backend/tests/test_translation_quality.py`, `frontend/src/components/grammar-fixer.tsx`, `frontend/src/lib/api.ts`

### 2026-08-18 — Native / Casual / Professional must differ
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Prompt requires three distinct communication goals; near-identical Native/Friendly/Professional results are retried once.
- **Why:** bug
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`

### 2026-08-18 — Fix grammar.py SyntaxError on boot
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Unescaped quotes in an f-string crashed uvicorn (`'(' was never closed`). The translation prompt block is a plain if/else now.
- **Why:** bug
- **Files:** `backend/app/grammar.py`

### 2026-08-18 — Locale selector + structured grammar notes
- **Type:** minor
- **Version:** 1.5.0
- **Summary:** Target locale is separate from language (US/UK/DE/MX, …). Prompt is meaning-first and locale-aware. Grammar notes are structured original/correction/explanation.
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/main.py`, `backend/app/cache.py`, `frontend/src/components/grammar-fixer.tsx`, `frontend/src/lib/api.ts`

### 2026-08-18 — Meaning-first native rewrite + grammar notes
- **Type:** minor
- **Version:** 1.5.0
- **Summary:** Translate infers intended meaning, rewrites as a native speaker would, and returns Native, Friendly / Casual, Professional, plus short Grammar Notes.
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `frontend/src/components/grammar-fixer.tsx`

### 2026-08-18 — Native editor: Native / Friendly / Professional / Literal
- **Type:** minor
- **Version:** 1.5.0
- **Summary:** Translate uses a native-localization prompt and returns Native, Friendly, Professional, and Literal only (silent grammar; no notes).
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `frontend/src/components/grammar-fixer.tsx`, `frontend/src/lib/api.ts`

### 2026-08-18 — Corrected sentence stays in From language
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Corrected sentence is the grammar-enhanced From text. Style cards show that enhanced input, then the translation. Styles change the To text only.
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `frontend/src/components/grammar-fixer.tsx`

### 2026-08-18 — Groq/HF speed labels
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Groq cards are labeled Suggested · fast; Hugging Face is Slower · better text.
- **Why:** feature
- **Files:** `frontend/src/components/settings-panel.tsx`, `frontend/src/components/limits-panel.tsx`, `frontend/src/app/page.tsx`

### 2026-08-18 — Intent-aware native rewrite (not grammar-only)
- **Type:** minor
- **Version:** 1.5.0
- **Summary:** Translate infers what you meant, returns a recommended native best version, and rewrites with target-language best practices instead of grammar-only patches.
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `frontend/src/components/grammar-fixer.tsx`, `frontend/src/lib/api.ts`

### 2026-08-18 — Corrected sentence + numbered styles + grammar notes
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Translate results follow Corrected sentence, then 1 Friendly / 2 Professional / 3 Everyday, then Grammar notes in `"wrong" → "right"` form.
- **Why:** feature
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `frontend/src/components/grammar-fixer.tsx`

### 2026-08-18 — Hugging Face Inference Providers for Qwen 72B
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** HF chat uses Inference Providers (default together, then auto/fireworks/…). Fixes model_not_supported for Qwen/Qwen2.5-72B-Instruct.
- **Why:** bug
- **Files:** `backend/app/llm.py`, `backend/app/config.py`, `.env.example`, `railway.toml`, `docker-compose.yml`

### 2026-08-18 — Tenses cards missing after JSON array parse
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Tense JSON arrays were parsed as a single object, so the API stored empty items and cards did not render. Arrays are extracted correctly now.
- **Why:** bug
- **Files:** `backend/app/jsonutil.py`, `backend/app/tenses.py`, `backend/app/cache.py`, `frontend/src/components/tenses-generator.tsx`

### 2026-08-18 — HF server limit is 50 even if env says 30
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Shared HF daily cap is at least 50. A leftover HF_DEFAULT_DAILY_LIMIT=30 on Railway no longer keeps the UI and 429s at 30.
- **Why:** bug
- **Files:** `backend/app/quota.py`, `backend/app/main.py`, `railway.toml`, `docker-compose.yml`

### 2026-08-18 — Lowercase user text for cache
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Grammar and Tenses inputs are lowercased before cache and generation so mobile Capitalize does not miss Redis and spend another daily token.
- **Why:** bug
- **Files:** `backend/app/cache.py`, `backend/app/main.py`, `frontend/src/lib/api.ts`, `backend/tests/test_cache.py`

### 2026-08-18 — Preserve source layout in Translate
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Translate keeps greetings, paragraphs, and work lists on separate lines instead of flattening them into one paragraph. Results render with line breaks.
- **Why:** bug
- **Files:** `backend/app/constants.py`, `backend/app/grammar.py`, `backend/app/cache.py`, `frontend/src/components/grammar-fixer.tsx`

### 2026-08-18 — Groq 413 payload limit
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Groq chat caps max_tokens at 4096 and retries smaller (2048, then 1024) on HTTP 413 so long Translate requests do not fail.
- **Why:** bug
- **Files:** `backend/app/llm.py`, `backend/app/grammar.py`, `backend/app/config.py`, `.env.example`

### 2026-08-18 — HF server token daily limit 50
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Shared server Hugging Face token allows 50 successful generations per UTC day. Groq stays at 30.
- **Why:** feature
- **Files:** `backend/app/config.py`, `backend/app/quota.py`, `frontend/src/components/limits-panel.tsx`, `frontend/src/components/settings-panel.tsx`, `.env.example`, `README.md`

### 2026-08-18 — Translate tab, 1000-char cap, JSON repair
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Grammar tab is labeled Translate. Input is capped at 1000 characters. Long replies that used to fail with a JSON delimiter error are parsed more reliably (and retried once).
- **Why:** bug
- **Files:** `frontend/src/app/page.tsx`, `frontend/src/components/grammar-fixer.tsx`, `frontend/src/components/tenses-generator.tsx`, `backend/app/jsonutil.py`, `backend/app/grammar.py`, `backend/app/main.py`, `backend/app/constants.py`

### 2026-08-18 — Disable Ollama, default Hugging Face
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Ollama is off (`OLLAMA_ENABLED=false`). Hugging Face is the default provider. Saved Ollama selections switch to HF.
- **Why:** feature
- **Files:** `backend/app/config.py`, `backend/app/llm.py`, `backend/app/main.py`, `frontend/src/lib/api.ts`, `frontend/src/app/page.tsx`, `frontend/src/components/settings-panel.tsx`, `.env.example`, `README.md`

### 2026-08-18 — Grammar and Tenses search history
- **Type:** minor
- **Version:** 1.5.0
- **Summary:** Grammar and Tenses keep recent successful searches in the browser. Click an item to restore the query and last result without calling the API.
- **Why:** feature
- **Files:** `frontend/src/lib/search-history.ts`, `frontend/src/components/search-history.tsx`, `frontend/src/components/grammar-fixer.tsx`, `frontend/src/components/tenses-generator.tsx`, `README.md`

### 2026-08-18 — Groq 30/day with pasted token
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Groq daily limit applies whether the visitor pastes a Groq key or uses the server key. Hugging Face stays uncapped when they paste their own HF token.
- **Why:** feature
- **Files:** `backend/app/quota.py`, `backend/tests/test_quota.py`, `frontend/src/components/limits-panel.tsx`, `frontend/src/components/settings-panel.tsx`, `README.md`

### 2026-08-18 — Align package.json with the public project
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Root and frontend package.json describe DeepLM (demo homepage, accurate keywords). Version bump also updates the root package.
- **Why:** docs
- **Files:** `package.json`, `frontend/package.json`, `scripts/bump_version.py`, `.github/workflows/bump-version.yml`

### 2026-08-18 — Professional open-source README
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** README rewritten for public contributors: demo links, screenshots, architecture, setup, API, deploy, contributing, and license.
- **Why:** docs
- **Files:** `README.md`, `frontend/public/image-1.jpg`, `frontend/public/image-2.jpg`, `frontend/public/image-3.jpg`

### 2026-08-18 — Cache tense explanations
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Tense explanations are stored in Redis like grammar and tenses. Repeat explain requests return the cache and do not count against the daily limit.
- **Why:** feature
- **Files:** `backend/app/main.py`, `backend/app/cache.py`, `backend/tests/test_cache.py`, `README.md`

### 2026-08-18 — Fix default-key quota consume
- **Type:** patch
- **Version:** 1.5.0
- **Summary:** Default HF/Groq daily counts increment with separate Redis commands (cluster-safe). Cache hits return stored results without counting against the 30/day limit.
- **Why:** bug
- **Files:** `backend/app/main.py`, `backend/app/quota.py`, `backend/app/cache.py`, `frontend/src/lib/api.ts`, `frontend/src/components/limits-panel.tsx`

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
