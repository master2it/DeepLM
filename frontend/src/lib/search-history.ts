import type { GrammarResult, TenseItem, TenseLanguage } from "@/lib/api";

export const GRAMMAR_HISTORY_KEY = "deeplm.history.grammar";
export const TENSES_HISTORY_KEY = "deeplm.history.tenses";

const MAX_ITEMS = 20;

export type GrammarHistoryItem = {
  id: string;
  at: number;
  text: string;
  from_lang: string;
  to_lang: string;
  to_locale?: string;
  provider?: string;
  result: GrammarResult;
};

export type TensesHistoryItem = {
  id: string;
  at: number;
  text: string;
  language: TenseLanguage;
  provider?: string;
  items: TenseItem[];
};

function newId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `h-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function readList<T>(key: string): T[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return [];
    const data = JSON.parse(raw);
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function writeList<T>(key: string, items: T[]) {
  window.localStorage.setItem(key, JSON.stringify(items.slice(0, MAX_ITEMS)));
}

export function readGrammarHistory(): GrammarHistoryItem[] {
  return readList<GrammarHistoryItem>(GRAMMAR_HISTORY_KEY);
}

export function readTensesHistory(): TensesHistoryItem[] {
  return readList<TensesHistoryItem>(TENSES_HISTORY_KEY);
}

export function pushGrammarHistory(
  item: Omit<GrammarHistoryItem, "id" | "at">
): GrammarHistoryItem[] {
  const text = item.text.trim();
  const next: GrammarHistoryItem = {
    ...item,
    text,
    id: newId(),
    at: Date.now(),
  };
  const rest = readGrammarHistory().filter(
    (row) =>
      !(
        row.text.trim().toLowerCase() === text.toLowerCase() &&
        row.from_lang === item.from_lang &&
        row.to_lang === item.to_lang &&
        (row.to_locale || "") === (item.to_locale || "")
      )
  );
  const list = [next, ...rest];
  writeList(GRAMMAR_HISTORY_KEY, list);
  return list;
}

export function pushTensesHistory(
  item: Omit<TensesHistoryItem, "id" | "at">
): TensesHistoryItem[] {
  const text = item.text.trim();
  const next: TensesHistoryItem = {
    ...item,
    text,
    id: newId(),
    at: Date.now(),
  };
  const rest = readTensesHistory().filter(
    (row) =>
      !(
        row.text.trim().toLowerCase() === text.toLowerCase() &&
        row.language === item.language
      )
  );
  const list = [next, ...rest];
  writeList(TENSES_HISTORY_KEY, list);
  return list;
}

export function clearGrammarHistory() {
  window.localStorage.removeItem(GRAMMAR_HISTORY_KEY);
}

export function clearTensesHistory() {
  window.localStorage.removeItem(TENSES_HISTORY_KEY);
}

export function removeGrammarHistory(id: string): GrammarHistoryItem[] {
  const list = readGrammarHistory().filter((row) => row.id !== id);
  writeList(GRAMMAR_HISTORY_KEY, list);
  return list;
}

export function removeTensesHistory(id: string): TensesHistoryItem[] {
  const list = readTensesHistory().filter((row) => row.id !== id);
  writeList(TENSES_HISTORY_KEY, list);
  return list;
}
