const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

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

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return res.statusText;
  }
}

export async function fetchLanguages(): Promise<LanguagesPayload> {
  const res = await fetch(`${API_BASE}/api/languages`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<{
    ok: boolean;
    ollama: boolean;
    hf_configured: boolean;
    ollama_model: string;
  }>;
}

export async function postGrammar(body: {
  text: string;
  from_lang: string;
  to_lang: string;
}): Promise<GrammarResult> {
  const res = await fetch(`${API_BASE}/api/grammar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function postTenses(text: string): Promise<{
  items: TenseItem[];
  provider?: string;
}> {
  const res = await fetch(`${API_BASE}/api/tenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function postTenseExplain(tense: string): Promise<{
  explanation?: string;
  examples?: { en: string; fa: string }[];
  provider?: string;
}> {
  const res = await fetch(`${API_BASE}/api/tenses/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tense }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
