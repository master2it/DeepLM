export type ProviderId = "openai";
export const MAX_INPUT_CHARS = 1000;
export const TENSE_LANG_STORAGE_KEY = "deeplm.tense_language";

export type StylePair = { from: string; to: string; grammarEnhanced?: string; translated?: string };
export type GrammarNote = { original: string; correction: string; explanation: string };
export type GrammarResult = {
  from_lang: string; to_lang: string; to_locale?: string; wants_translation: boolean;
  intended_meaning?: string; best_version?: string; canonical_meaning?: string; subject_reading?: string;
  grammar_notes?: string; grammarNotes?: GrammarNote[]; provider?: string;
  grammarFix?: StylePair; native?: StylePair; friendly?: StylePair; professional?: StylePair;
  everyday_neutral?: StylePair; friendly_casual?: StylePair; professional_formal?: StylePair;
};
export type GermanTense = "praesens" | "praeteritum" | "perfekt" | "plusquamperfekt" | "futur_i" | "futur_ii";
export type TenseLanguage = "English" | "German";
export type TenseItem = { tense: string; text: string; persian: string; english?: string; key?: GermanTense };
export type TenseExample = { text?: string; en?: string; english?: string; fa: string };
export const DEFAULT_TENSE_COUNTS: Record<TenseLanguage, number> = { English: 12, German: 6 };
export type LanguagesPayload = {
  languages: string[]; rtl: string[]; default_from: string; default_to: string;
  styles: { label: string; key: string }[]; tense_languages?: string[];
  default_tense_language?: string; tense_counts?: Partial<Record<TenseLanguage, number>>;
  german_tenses?: { key: GermanTense; label: string }[]; max_input_chars?: number;
  locales?: Record<string, string[]>; default_locales?: Record<string, string>;
};
export type HealthPayload = { ok: boolean; version?: string; openai_configured: boolean; openai_model: string };
export type ChangelogChange = { title: string; type: string; summary: string; why: string; files: string };
export type ChangelogRelease = { version: string; date: string; kind: string; notes: string; changes: ChangelogChange[] };

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
export function readStoredTenseLanguage(): TenseLanguage {
  if (typeof window === "undefined") return "English";
  return window.localStorage.getItem(TENSE_LANG_STORAGE_KEY) === "German" ? "German" : "English";
}
export function writeStoredTenseLanguage(language: TenseLanguage) {
  window.localStorage.setItem(TENSE_LANG_STORAGE_KEY, language);
}
export const fetchLanguages = () => cachedGet<LanguagesPayload>("/api/languages");
export const fetchHealth = () => cachedGet<HealthPayload>("/api/health");
export const fetchChangelog = () => cachedGet<{ current: string; releases: ChangelogRelease[] }>("/api/changelog");

export function postGrammar(body: { text: string; from_lang: string; to_lang: string; to_locale?: string; context?: string }) {
  return request<GrammarResult>("/api/grammar", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, text: body.text.trim(), to_locale: body.to_locale?.trim() || undefined }),
  });
}
export function postTenses(text: string, language: TenseLanguage = "English") {
  return request<{ items: TenseItem[]; provider?: string; language?: string }>("/api/tenses", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text.trim(), language }),
  });
}
export function postTenseExplain(tense: string, language: TenseLanguage = "English", text?: string, example?: string) {
  return request<{ explanation?: string; examples?: TenseExample[]; provider?: string }>("/api/tenses/explain", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tense, language, text: text?.trim(), example: example?.trim() }),
  });
}
