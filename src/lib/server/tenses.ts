import { DEFAULT_TENSE_LANGUAGE, GERMAN_TENSES, TENSE_LANGUAGES } from "@/lib/server/constants";
import { chat, parseModelJson } from "@/lib/server/openai";

type TenseLanguage = "English" | "German";

function languageOf(value?: string): TenseLanguage {
  return value === "German" ? "German" : DEFAULT_TENSE_LANGUAGE;
}

function normalizeItems(value: unknown, language: TenseLanguage) {
  const rows = Array.isArray(value) ? value : (value as { items?: unknown })?.items;
  if (!Array.isArray(rows)) return [];
  const items = rows
    .filter((row): row is Record<string, unknown> => Boolean(row && typeof row === "object"))
    .map((row) => ({
      key: typeof row.key === "string" ? row.key : undefined,
      tense: String(row.tense ?? "").trim(),
      text: String(row.text ?? row.german ?? row.english ?? "").trim(),
      english: String(row.english ?? "").trim() || undefined,
      persian: String(row.persian ?? row.fa ?? "").trim(),
    }));
  if (language !== "German") return items;
  return GERMAN_TENSES.flatMap((tense) => {
    const item = items.find((row) => row.key === tense.key || row.tense === tense.label);
    return item ? [{ ...item, key: tense.key, tense: tense.label }] : [];
  });
}

export async function generateTenses(text: string, languageInput?: string) {
  const language = languageOf(languageInput);
  const German = language === "German";
  const requested = German
    ? GERMAN_TENSES.map(({ key, label }) => `${key} (${label})`).join(", ")
    : "Present Simple, Present Continuous, Present Perfect, Present Perfect Continuous, Past Simple, Past Continuous, Past Perfect, Past Perfect Continuous, Future Simple, Future Continuous, Future Perfect, Future Perfect Continuous";
  const system = `You are an expert ${language} teacher for Persian-speaking students. The user supplies a short phrase. Identify its subject and base verb and conjugate it in exactly these ${German ? "six German tenses" : "twelve English tenses"}: ${requested}.
${German ? "German has exactly six tense categories; never use English continuous categories. Include key values: praesens, praeteritum, perfekt, plusquamperfekt, futur_i, futur_ii." : ""}
Return JSON only as {"items":[{"${German ? 'key":"","' : ""}"tense":"","text":"","english":"","persian":""}]}. Text is the requested-language sentence; English is required for German and optional for English; Persian must be natural.`;
  const data = parseModelJson(await chat([{ role: "system", content: system }, { role: "user", content: text }], { temperature: 0.1, maxTokens: 2500 }));
  return { items: normalizeItems(data, language), provider: "openai", language };
}

export async function explainTense(input: { tense: string; language?: string; text?: string; example?: string }) {
  const language = languageOf(input.language);
  const system = `You are an expert ${language} teacher explaining grammar to a Persian student. Explain "${input.tense}" simply in natural Persian. Give exactly three everyday examples in this same tense. Return JSON only as {"explanation":"","examples":[{"text":"","english":"","fa":""}]}. ${language === "German" ? "German has exactly six tense categories: Präsens, Präteritum, Perfekt, Plusquamperfekt, Futur I, Futur II." : ""}`;
  const user = `Student phrase: ${input.text || "(none)"}\nCurrent example: ${input.example || "(none)"}`;
  const raw = parseModelJson(await chat([{ role: "system", content: system }, { role: "user", content: user }], { temperature: 0.2, maxTokens: 1500 }));
  const data = raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> : {};
  const examples = Array.isArray(data.examples)
    ? data.examples.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object")).map((item) => ({
        text: String(item.text ?? item.en ?? item.de ?? "").trim(),
        english: String(item.english ?? "").trim() || undefined,
        fa: String(item.fa ?? item.persian ?? "").trim(),
      }))
    : [];
  return { explanation: String(data.explanation ?? "").trim(), examples, provider: "openai", language };
}
