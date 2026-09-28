const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

export type ProviderId = "huggingface" | "deepseek" | "groq";

export const PROVIDER_STORAGE_KEY = "deeplm.provider";
export const GROQ_KEY_STORAGE_KEY = "deeplm.groq_api_key";
export const GROQ_MODEL_STORAGE_KEY = "deeplm.groq_model";
export const HF_KEY_STORAGE_KEY = "deeplm.hf_api_key";
export const CLIENT_ID_STORAGE_KEY = "deeplm.client_id";
export const TENSE_LANG_STORAGE_KEY = "deeplm.tense_language";

export const DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b";

export type GroqFreeModel = {
  id: string;
  label: string;
  rpm: number;
  rpd: number;
  tpm: number | null;
  tpd: number | null;
  tag?: string;
};

/** Local catalog so Settings always lists Groq Free chat models (API may refine). */
export const GROQ_FREE_MODELS: GroqFreeModel[] = [
  {
    id: "openai/gpt-oss-120b",
    label: "gpt-oss-120b",
    rpm: 30,
    rpd: 1000,
    tpm: 8000,
    tpd: 200000,
    tag: "Default",
  },
  {
    id: "openai/gpt-oss-20b",
    label: "gpt-oss-20b",
    rpm: 30,
    rpd: 1000,
    tpm: 8000,
    tpd: 200000,
  },
  {
    id: "openai/gpt-oss-safeguard-20b",
    label: "gpt-oss-safeguard-20b",
    rpm: 30,
    rpd: 1000,
    tpm: 8000,
    tpd: 200000,
  },
  {
    id: "qwen/qwen3.6-27b",
    label: "qwen3.6-27b",
    rpm: 30,
    rpd: 1000,
    tpm: 8000,
    tpd: 200000,
  },
  {
    id: "qwen/qwen3.8-27b",
    label: "qwen3.8-27b",
    rpm: 30,
    rpd: 1000,
    tpm: 8000,
    tpd: 2000000,
  },
  {
    id: "groq/compound",
    label: "compound",
    rpm: 30,
    rpd: 250,
    tpm: 70000,
    tpd: null,
    tag: "Agentic",
  },
  {
    id: "groq/compound-mini",
    label: "compound-mini",
    rpm: 30,
    rpd: 250,
    tpm: 70000,
    tpd: null,
    tag: "Agentic",
  },
];

export function resolveGroqModels(
  fromHealth?: GroqFreeModel[] | null
): GroqFreeModel[] {
  if (fromHealth && fromHealth.length > 0) return fromHealth;
  return GROQ_FREE_MODELS;
}

/** Short model id for UI (hide org / provider brand). */
export function shortModelName(model?: string | null, fallback = "Model"): string {
  const raw = (model || "").trim();
  if (!raw) return fallback;
  const base = raw.includes(":") ? raw.split(":")[0] : raw;
  const parts = base.split("/");
  return parts[parts.length - 1] || base;
}

/** User-facing label for a backend provider id — model name, not Groq / Hugging Face. */
export function providerModelLabel(
  provider?: string | null,
  models?: {
    hf?: string | null;
    deepseek?: string | null;
    groq?: string | null;
  }
): string {
  const id = (provider || "").trim().toLowerCase();
  if (id === "huggingface" || id === "hf") {
    return shortModelName(models?.hf, "Qwen2.5-72B-Instruct");
  }
  if (id === "deepseek") {
    return shortModelName(models?.deepseek, "DeepSeek-V4-Flash");
  }
  if (id === "groq") {
    return shortModelName(models?.groq, "gpt-oss-120b");
  }
  return provider?.trim() || "Model";
}

export type StylePair = {
  from: string;
  to: string;
  grammarEnhanced?: string;
  translated?: string;
};

export type GrammarNote = {
  original: string;
  correction: string;
  explanation: string;
};

export type GrammarResult = {
  from_lang: string;
  to_lang: string;
  to_locale?: string;
  wants_translation: boolean;
  intended_meaning?: string;
  best_version?: string;
  canonical_meaning?: string;
  subject_reading?: string;
  grammar_notes?: string;
  grammarNotes?: GrammarNote[];
  provider?: string;
  grammarFix?: StylePair;
  native?: StylePair;
  friendly?: StylePair;
  professional?: StylePair;
  literal?: StylePair;
  friendly_casual?: StylePair;
  professional_formal?: StylePair;
  everyday_neutral?: StylePair;
};

export type GermanTense =
  | "praesens"
  | "praeteritum"
  | "perfekt"
  | "plusquamperfekt"
  | "futur_i"
  | "futur_ii";

export type TenseItem = {
  tense: string;
  text: string;
  persian: string;
  english?: string;
  key?: GermanTense;
};

export type TenseLanguage = "English" | "German";

export const DEFAULT_TENSE_COUNTS: Record<TenseLanguage, number> = {
  English: 12,
  German: 6,
};

export type LanguagesPayload = {
  languages: string[];
  rtl: string[];
  default_from: string;
  default_to: string;
  styles: { label: string; key: string }[];
  tense_languages?: string[];
  default_tense_language?: string;
  tense_counts?: Partial<Record<TenseLanguage, number>>;
  german_tenses?: { key: GermanTense; label: string }[];
  max_input_chars?: number;
  locales?: Record<string, string[]>;
  default_locales?: Record<string, string>;
};

export const MAX_INPUT_CHARS = 1000;

export type ProviderInfo = {
  id: ProviderId;
  label: string;
  available: boolean;
  enabled?: boolean;
  model: string;
  models?: GroqFreeModel[];
};

export type ProviderLimit = {
  limit: number;
  used: number;
  remaining: number;
  using_default_key: boolean;
  period?: "day" | "hour";
  resets_at?: string;
  model?: string;
  rpm_limit?: number;
  rpm_used?: number;
  rpm_remaining?: number;
  rpm_resets_at?: string;
  tpm?: number | null;
  tpd?: number | null;
};

export type LimitsPayload = {
  resets_at: string;
  redis: boolean;
  huggingface: ProviderLimit;
  groq: ProviderLimit;
};

export type HealthPayload = {
  ok: boolean;
  version?: string;
  hf_configured: boolean;
  groq_configured: boolean;
  hf_model: string;
  deepseek_model?: string;
  groq_model: string;
  groq_models?: GroqFreeModel[];
  providers: ProviderInfo[];
  default_provider: ProviderId;
  hf_default_daily_limit?: number;
  groq_default_daily_limit?: number;
  redis?: boolean;
};

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      const first = data.detail[0];
      if (typeof first?.msg === "string") return first.msg;
    }
    return JSON.stringify(data);
  } catch {
    return res.statusText;
  }
}

export const DEFAULT_PROVIDER: ProviderId = "huggingface";

export function readStoredProvider(): ProviderId {
  if (typeof window === "undefined") return DEFAULT_PROVIDER;
  const value = window.localStorage.getItem(PROVIDER_STORAGE_KEY);
  if (value === "ollama") {
    window.localStorage.setItem(PROVIDER_STORAGE_KEY, DEFAULT_PROVIDER);
    return DEFAULT_PROVIDER;
  }
  if (value === "huggingface" || value === "deepseek" || value === "groq") {
    return value;
  }
  return DEFAULT_PROVIDER;
}

export function writeStoredProvider(provider: ProviderId) {
  window.localStorage.setItem(PROVIDER_STORAGE_KEY, provider);
}

export function readStoredGroqKey(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(GROQ_KEY_STORAGE_KEY) || "";
}

export function writeStoredGroqKey(key: string) {
  const trimmed = key.trim();
  if (trimmed) {
    window.localStorage.setItem(GROQ_KEY_STORAGE_KEY, trimmed);
  } else {
    window.localStorage.removeItem(GROQ_KEY_STORAGE_KEY);
  }
}

export function readStoredGroqModel(
  allowed?: string[] | null
): string {
  if (typeof window === "undefined") return DEFAULT_GROQ_MODEL;
  const value = window.localStorage.getItem(GROQ_MODEL_STORAGE_KEY) || "";
  if (allowed?.length) {
    if (value && allowed.includes(value)) return value;
    return allowed.includes(DEFAULT_GROQ_MODEL)
      ? DEFAULT_GROQ_MODEL
      : allowed[0];
  }
  return value || DEFAULT_GROQ_MODEL;
}

export function writeStoredGroqModel(model: string) {
  const trimmed = model.trim();
  if (trimmed) {
    window.localStorage.setItem(GROQ_MODEL_STORAGE_KEY, trimmed);
  } else {
    window.localStorage.removeItem(GROQ_MODEL_STORAGE_KEY);
  }
}

export function readStoredHfKey(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(HF_KEY_STORAGE_KEY) || "";
}

export function writeStoredHfKey(key: string) {
  const trimmed = key.trim();
  if (trimmed) {
    window.localStorage.setItem(HF_KEY_STORAGE_KEY, trimmed);
  } else {
    window.localStorage.removeItem(HF_KEY_STORAGE_KEY);
  }
}

export function getClientId(): string {
  if (typeof window === "undefined") return "";
  const existing = window.localStorage.getItem(CLIENT_ID_STORAGE_KEY);
  if (existing) return existing;
  const id =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `cid-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  window.localStorage.setItem(CLIENT_ID_STORAGE_KEY, id);
  return id;
}

function apiHeaders(json = false): HeadersInit {
  const headers: Record<string, string> = {};
  if (json) headers["Content-Type"] = "application/json";
  const clientId = getClientId();
  if (clientId) headers["X-Client-Id"] = clientId;
  return headers;
}

/** Share in-flight/session GET promises so Strict Mode remounts and tabs do not double-fetch. */
const getPromises = new Map<string, Promise<unknown>>();

function sharedGet<T>(
  key: string,
  run: () => Promise<T>,
  ttlMs?: number
): Promise<T> {
  const hit = getPromises.get(key);
  if (hit) return hit as Promise<T>;
  const promise = run()
    .catch((err) => {
      getPromises.delete(key);
      throw err;
    })
    .then((value) => {
      if (ttlMs != null && ttlMs >= 0) {
        window.setTimeout(() => getPromises.delete(key), ttlMs);
      }
      return value;
    });
  getPromises.set(key, promise);
  return promise as Promise<T>;
}

export async function fetchLimits(
  ownHfKey: boolean,
  ownGroqKey: boolean,
  groqModel?: string
): Promise<LimitsPayload> {
  const params = new URLSearchParams({
    own_hf_key: ownHfKey ? "true" : "false",
    own_groq_key: ownGroqKey ? "true" : "false",
  });
  if (groqModel?.trim()) {
    params.set("groq_model", groqModel.trim());
  }
  const key = `limits:${params.toString()}`;
  return sharedGet(
    key,
    async () => {
      const res = await fetch(`${API_BASE}/api/limits?${params}`, {
        cache: "no-store",
        headers: apiHeaders(),
      });
      if (!res.ok) throw new Error(await parseError(res));
      return res.json();
    },
    1500
  );
}

export function readStoredTenseLanguage(): TenseLanguage {
  if (typeof window === "undefined") return "English";
  const value = window.localStorage.getItem(TENSE_LANG_STORAGE_KEY);
  if (value === "German" || value === "English") return value;
  return "English";
}

export function writeStoredTenseLanguage(language: TenseLanguage) {
  window.localStorage.setItem(TENSE_LANG_STORAGE_KEY, language);
}

export async function fetchLanguages(): Promise<LanguagesPayload> {
  return sharedGet("languages", async () => {
    const res = await fetch(`${API_BASE}/api/languages`);
    if (!res.ok) throw new Error(await parseError(res));
    return res.json();
  });
}

export async function fetchHealth(): Promise<HealthPayload> {
  return sharedGet("health", async () => {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(await parseError(res));
    return res.json();
  });
}

export type ChangelogChange = {
  title: string;
  type: string;
  summary: string;
  why: string;
  files: string;
};

export type ChangelogRelease = {
  version: string;
  date: string;
  kind: string;
  notes: string;
  changes: ChangelogChange[];
};

export async function fetchChangelog(): Promise<{
  current: string;
  releases: ChangelogRelease[];
}> {
  return sharedGet("changelog", async () => {
    const res = await fetch(`${API_BASE}/api/changelog`);
    if (!res.ok) throw new Error(await parseError(res));
    return res.json();
  });
}

export async function postGrammar(body: {
  text: string;
  from_lang: string;
  to_lang: string;
  to_locale?: string;
  provider: ProviderId;
  groq_api_key?: string;
  hf_api_key?: string;
  groq_model?: string;
}): Promise<GrammarResult> {
  const res = await fetch(`${API_BASE}/api/grammar`, {
    method: "POST",
    headers: apiHeaders(true),
    body: JSON.stringify({
      text: body.text.trim().toLowerCase(),
      from_lang: body.from_lang,
      to_lang: body.to_lang,
      ...(body.to_locale?.trim()
        ? { to_locale: body.to_locale.trim() }
        : {}),
      provider: body.provider,
      groq_api_key: body.groq_api_key?.trim() || undefined,
      hf_api_key: body.hf_api_key?.trim() || undefined,
      groq_model: body.groq_model?.trim() || undefined,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function postTenses(
  text: string,
  provider: ProviderId,
  groqApiKey?: string,
  language: TenseLanguage = "English",
  hfApiKey?: string,
  groqModel?: string
): Promise<{
  items: TenseItem[];
  provider?: string;
  language?: string;
}> {
  const res = await fetch(`${API_BASE}/api/tenses`, {
    method: "POST",
    headers: apiHeaders(true),
    body: JSON.stringify({
      text: text.trim().toLowerCase(),
      language,
      provider,
      groq_api_key: groqApiKey?.trim() || undefined,
      hf_api_key: hfApiKey?.trim() || undefined,
      groq_model: groqModel?.trim() || undefined,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export type TenseExample = {
  text?: string;
  en?: string;
  english?: string;
  fa: string;
};

export async function postTenseExplain(
  tense: string,
  provider: ProviderId,
  groqApiKey?: string,
  language: TenseLanguage = "English",
  hfApiKey?: string,
  text?: string,
  example?: string,
  groqModel?: string
): Promise<{
  explanation?: string;
  examples?: TenseExample[];
  provider?: string;
}> {
  const res = await fetch(`${API_BASE}/api/tenses/explain`, {
    method: "POST",
    headers: apiHeaders(true),
    body: JSON.stringify({
      tense,
      language,
      text: text?.trim() || undefined,
      example: example?.trim() || undefined,
      provider,
      groq_api_key: groqApiKey?.trim() || undefined,
      hf_api_key: hfApiKey?.trim() || undefined,
      groq_model: groqModel?.trim() || undefined,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
