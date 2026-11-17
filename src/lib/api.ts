export type ProviderId = "openai";
export const MAX_INPUT_CHARS = 1000;

export type StylePair = { from: string; to: string; grammarEnhanced?: string; translated?: string; roman?: string };
export type GrammarNote = { original: string; correction: string; explanation: string };
export type GrammarResult = {
  from_lang: string; to_lang: string; to_locale?: string; wants_translation: boolean;
  intended_meaning?: string; best_version?: string; canonical_meaning?: string; subject_reading?: string;
  grammar_notes?: string; grammarNotes?: GrammarNote[]; provider?: string;
  grammarFix?: StylePair; native?: StylePair; friendly?: StylePair; professional?: StylePair; programmer?: StylePair;
  everyday_neutral?: StylePair; friendly_casual?: StylePair; professional_formal?: StylePair;
};
export type LanguagesPayload = {
  languages: string[]; rtl: string[]; default_from: string; default_to: string;
  styles: { label: string; key: string }[]; max_input_chars?: number;
  locales?: Record<string, string[]>; default_locales?: Record<string, string>;
};
export type HealthPayload = { ok: boolean; version?: string; openai_configured: boolean; openai_model: string };

async function parseError(res: Response) {
  const data = await res.json().catch(() => null);
  return typeof data?.detail === "string" ? data.detail : res.statusText;
}
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}
const gets = new Map<string, Promise<unknown>>();
function cachedGet<T>(path: string) {
  const existing = gets.get(path);
  if (existing) return existing as Promise<T>;
  const promise = request<T>(path).catch((error) => { gets.delete(path); throw error; });
  gets.set(path, promise);
  return promise;
}

export function providerModelLabel(_provider?: string | null) { return "OpenAI"; }
export const fetchLanguages = () => cachedGet<LanguagesPayload>("/api/languages");
export const fetchHealth = () => cachedGet<HealthPayload>("/api/health");

export function postGrammar(body: { text: string; from_lang: string; to_lang: string; to_locale?: string; context?: string }) {
  return request<GrammarResult>("/api/grammar", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, text: body.text.trim(), to_locale: body.to_locale?.trim() || undefined }),
  });
}
