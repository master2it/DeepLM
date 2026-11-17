import type { GrammarResult } from "@/lib/api";

export const GRAMMAR_HISTORY_KEY = "deeplm.history.grammar";

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

export function clearGrammarHistory() {
  window.localStorage.removeItem(GRAMMAR_HISTORY_KEY);
}

export function removeGrammarHistory(id: string): GrammarHistoryItem[] {
  const list = readGrammarHistory().filter((row) => row.id !== id);
  writeList(GRAMMAR_HISTORY_KEY, list);
  return list;
}
