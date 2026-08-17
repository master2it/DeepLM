const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "production"
    ? "https://deeplm.up.railway.app"
    : "http://localhost:8000")
).replace(/\/$/, "");

export type ProviderId = "ollama" | "huggingface" | "groq";

export const PROVIDER_STORAGE_KEY = "deeplm.provider";
export const GROQ_KEY_STORAGE_KEY = "deeplm.groq_api_key";

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

export type TenseItem = { tense: string; english: string; persian: string };

export type LanguagesPayload = {
  languages: string[];
  rtl: string[];
  default_from: string;
  default_to: string;
  styles: { label: string; key: string }[];
};

export type ProviderInfo = {
  id: ProviderId;
  label: string;
  available: boolean;
  model: string;
};

export type HealthPayload = {
  ok: boolean;
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
  groqApiKey?: string
): Promise<{
  items: TenseItem[];
  provider?: string;
}> {
  const res = await fetch(`${API_BASE}/api/tenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
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
  groqApiKey?: string
): Promise<{
  explanation?: string;
  examples?: { en: string; fa: string }[];
  provider?: string;
}> {
  const res = await fetch(`${API_BASE}/api/tenses/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tense,
      provider,
      groq_api_key: groqApiKey?.trim() || undefined,
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
