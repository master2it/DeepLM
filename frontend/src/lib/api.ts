const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "production"
    ? "https://deeplm.up.railway.app"
    : "http://localhost:8000")
).replace(/\/$/, "");

export type ProviderId = "ollama" | "huggingface" | "groq";

export const PROVIDER_STORAGE_KEY = "deeplm.provider";
export const TENSE_LANG_STORAGE_KEY = "deeplm.tense_language";

export type StylePair = { from: string; to: string };

export type GrammarResult = {
  from_lang: string;
  to_lang: string;
  wants_translation: boolean;
  canonical_meaning?: string;
  subject_reading?: string;
  grammar_notes?: string;
  provider?: string;
  friendly_casual: StylePair;
  professional_formal: StylePair;
  everyday_neutral: StylePair;
};

export type TenseItem = { tense: string; text: string; persian: string };

export type TenseLanguage = "English" | "German";

export type LanguagesPayload = {
  languages: string[];
  rtl: string[];
  default_from: string;
  default_to: string;
  styles: { label: string; key: string }[];
  tense_languages?: string[];
  default_tense_language?: string;
};

export type ProviderInfo = {
  id: ProviderId;
  label: string;
  available: boolean;
  model: string;
};

export type HealthPayload = {
  ok: boolean;
  version?: string;
  ollama: boolean;
  hf_configured: boolean;
  groq_configured: boolean;
  ollama_model: string;
  hf_model: string;
  groq_model: string;
  providers: ProviderInfo[];
  default_provider: ProviderId;
};

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return res.statusText;
  }
}

export function readStoredProvider(): ProviderId {
  if (typeof window === "undefined") return "ollama";
  const value = window.localStorage.getItem(PROVIDER_STORAGE_KEY);
  if (value === "huggingface" || value === "groq" || value === "ollama") {
    return value;
  }
  return "ollama";
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
  const res = await fetch(`${API_BASE}/api/languages`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchHealth(): Promise<HealthPayload> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function postGrammar(body: {
  text: string;
  from_lang: string;
  to_lang: string;
  provider: ProviderId;
  groq_api_key?: string;
}): Promise<GrammarResult> {
  const res = await fetch(`${API_BASE}/api/grammar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...body,
      groq_api_key: body.groq_api_key?.trim() || undefined,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function postTenses(
  text: string,
  provider: ProviderId,
  groqApiKey?: string,
  language: TenseLanguage = "English"
): Promise<{
  items: TenseItem[];
  provider?: string;
  language?: string;
}> {
  const res = await fetch(`${API_BASE}/api/tenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      language,
      provider,
      groq_api_key: groqApiKey?.trim() || undefined,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function postTenseExplain(
  tense: string,
  provider: ProviderId,
  groqApiKey?: string,
  language: TenseLanguage = "English"
): Promise<{
  explanation?: string;
  examples?: { text?: string; en?: string; fa: string }[];
  provider?: string;
}> {
  const res = await fetch(`${API_BASE}/api/tenses/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tense,
      language,
      provider,
      groq_api_key: groqApiKey?.trim() || undefined,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
