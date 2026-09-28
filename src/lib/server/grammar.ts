import { DEFAULT_GRAMMAR_FROM, DEFAULT_GRAMMAR_TO, GRAMMAR_LANGUAGES, resolveLocale } from "@/lib/server/constants";
import { chat, parseModelJson } from "@/lib/server/openai";

type Pair = { from?: string; to?: string; grammarEnhanced?: string; translated?: string };

function pair(value: Pair | string | undefined) {
  const raw = typeof value === "string" ? { from: value } : value ?? {};
  const from = (raw.from ?? raw.grammarEnhanced ?? "").trim();
  const to = (raw.to ?? raw.translated ?? "").trim();
  return { from, to, grammarEnhanced: from, translated: to };
}

export async function generateGrammar(input: {
  text: string;
  from_lang?: string;
  to_lang?: string;
  to_locale?: string;
  context?: string;
}) {
  const from = GRAMMAR_LANGUAGES.includes(input.from_lang ?? "")
    ? input.from_lang!
    : DEFAULT_GRAMMAR_FROM;
  const to = GRAMMAR_LANGUAGES.includes(input.to_lang ?? "")
    ? input.to_lang!
    : DEFAULT_GRAMMAR_TO;
  const locale = resolveLocale(to, input.to_locale);
  const wantsTranslation = from !== to;
  const targetInstruction = wantsTranslation
    ? `Translate every result to ${to} (${locale}).`
    : `Keep every "to" field empty.`;
  const system = `You are an expert editor and translator. Return JSON only.
The source language is ${from}; the target language is ${to} (${locale}).
First make a minimal spelling/grammar correction. Then create three independent source-language rewrites: natural native, friendly/casual, and professional. Preserve the user's meaning, subject, tense, and factual details. Do not invent a speaker or change pronouns.
${targetInstruction}
For every style, translate that style's own "from" value, never one shared translation.
Grammar notes must discuss the original input only.
Return exactly this JSON object:
{"detected_lang":"${from}","grammarFix":{"from":"","to":""},"native":{"from":"","to":""},"friendly":{"from":"","to":""},"professional":{"from":"","to":""},"grammar_notes":[{"original":"","correction":"","explanation":""}]}`;
  const content = await chat(
    [{ role: "system", content: system }, { role: "user", content: `${input.context ? `Context: ${input.context}\n\n` : ""}Text:\n${input.text}` }],
    { temperature: 0.15, maxTokens: 4096 }
  );
  const raw = parseModelJson(content);
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new Error("OpenAI returned an unexpected grammar response.");
  }
  const data = raw as Record<string, unknown>;
  const grammarFix = pair(data.grammarFix as Pair);
  const native = pair((data.native ?? data.everyday_neutral) as Pair);
  const friendly = pair((data.friendly ?? data.friendly_casual) as Pair);
  const professional = pair((data.professional ?? data.professional_formal) as Pair);
  const notes = Array.isArray(data.grammar_notes)
    ? data.grammar_notes
        .filter((note): note is Record<string, unknown> => Boolean(note && typeof note === "object"))
        .map((note) => ({
          original: String(note.original ?? "").trim(),
          correction: String(note.correction ?? note.fixed ?? "").trim(),
          explanation: String(note.explanation ?? note.why ?? "").trim(),
        }))
    : [];
  return {
    from_lang: String(data.detected_lang ?? from),
    to_lang: to,
    to_locale: locale,
    wants_translation: wantsTranslation,
    intended_meaning: String(data.intended_meaning ?? "").trim(),
    best_version: String(data.best_version ?? data.canonical_meaning ?? grammarFix.from).trim(),
    canonical_meaning: String(data.canonical_meaning ?? grammarFix.from).trim(),
    subject_reading: String(data.subject_reading ?? "").trim(),
    grammar_notes: notes.map((note) => `${note.original} → ${note.correction}${note.explanation ? `: ${note.explanation}` : ""}`).join("\n"),
    grammarNotes: notes,
    grammarFix,
    native,
    friendly,
    professional,
    everyday_neutral: native,
    friendly_casual: friendly,
    professional_formal: professional,
    provider: "openai",
  };
}
