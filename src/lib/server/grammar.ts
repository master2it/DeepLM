import { DEFAULT_GRAMMAR_FROM, DEFAULT_GRAMMAR_TO, GRAMMAR_LANGUAGES, resolveLocale } from "@/lib/server/constants";
import { chat, parseModelJson } from "@/lib/server/openai";

type Pair = {
  from?: string;
  to?: string;
  grammarEnhanced?: string;
  translated?: string;
  translation?: string;
  source?: string;
  corrected?: string;
  target?: string;
  roman?: string;
  romanWriting?: string;
  roman_writing?: string;
  transliteration?: string;
};

function firstText(raw: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

const ABBREVIATIONS = ["ASAP", "ETA", "FYI", "BTW", "LGTM", "WIP", "TBD", "IMO", "TBH", "API", "PR", "UI", "UX", "DB", "config", "repo", "env", "auth", "prod", "dev", "info"];

function missingAbbreviations(from: string, to: string) {
  return ABBREVIATIONS.filter((token) => {
    const pattern = new RegExp(`\\b${token}\\b`, "i");
    return pattern.test(from) && !pattern.test(to);
  });
}

function pair(value: Pair | string | undefined) {
  const raw = (typeof value === "string" ? { from: value } : value ?? {}) as Record<string, unknown>;
  const from = firstText(raw, ["from", "grammarEnhanced", "source", "corrected"]);
  const to = firstText(raw, ["to", "translated", "translation", "target"]);
  const roman = firstText(raw, ["roman", "romanWriting", "roman_writing", "transliteration"]);
  return { from, to, grammarEnhanced: from, translated: to, roman };
}

function applyRoman(
  value: { from: string; to: string; grammarEnhanced: string; translated: string; roman: string },
  language: string,
  translated: boolean
) {
  const source = translated ? value.to : value.from;
  const roman = value.roman || (language === "English" ? source : "");
  return { ...value, roman };
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
    ? `grammarFix.from is only a minimal correction of the original in ${from}. grammarFix.to is required and must be the ${to} (${locale}) translation of grammarFix.from, not of a rewrite and not of the uncorrected original. native.to, friendly.to, professional.to, and programmer.to translate their own "from" fields. Never leave a "to" field empty. Never copy source-language text into "to".`
    : `Keep every "to" field empty.`;
  const system = `You are an expert editor and translator. Return JSON only.
The source language is ${from}; the target language is ${to} (${locale}).
First make a minimal spelling/grammar correction of the original. Then create four independent source-language rewrites: natural native, friendly/casual, professional, and programmer. Preserve the user's meaning, subject, tense, and factual details. Do not invent a speaker or change pronouns.
programmer is how a software engineer would say the same thing in a Slack message to teammates: short, direct, concrete, and chatty. Use the abbreviations engineers actually type whenever a normal short form exists: information → info, configuration → config, repository → repo, environment → env, database → DB, application programming interface → API, pull request → PR, user interface → UI, user experience → UX, authentication → auth, production → prod, development → dev, as soon as possible → ASAP, estimated time of arrival → ETA, for your information → FYI, by the way → BTW, right now → RN, in my opinion → IMO, to be honest → TBH, looks good to me → LGTM, work in progress → WIP, to be determined → TBD. Keep names, numbers, and facts exact. Do not invent a technical detail just to add an abbreviation. programmer.to must keep every abbreviation token from programmer.from exactly (PR, UI, DB, API, config, repo, env, auth, prod, ASAP, FYI, and the rest). Translate only the surrounding words. Never expand an abbreviation into a full word in either language. No corporate filler, no emoji, and no hashtags.
Each style needs "roman": Roman writing of that style's ${to} (${locale}) sentence, using English letters only.
When ${to} is English, "roman" is exactly the same English sentence as "to"${wantsTranslation ? "" : `, or as "from" when "to" is empty`}.
When ${to} is not English, "roman" is the Latin transliteration of "to" for the ${locale} pronunciation. Write how that sentence sounds. Do not rewrite it as a new English translation. Keep abbreviations unchanged. Never use ${to} script inside "roman".
${targetInstruction}
Grammar notes must discuss the original input only.
Return exactly this JSON object:
{"detected_lang":"${from}","grammarFix":{"from":"","to":"","roman":""},"native":{"from":"","to":"","roman":""},"friendly":{"from":"","to":"","roman":""},"professional":{"from":"","to":"","roman":""},"programmer":{"from":"","to":"","roman":""},"grammar_notes":[{"original":"","correction":"","explanation":""}]}`;
  const content = await chat(
    [{ role: "system", content: system }, { role: "user", content: `${input.context ? `Context: ${input.context}\n\n` : ""}Text:\n${input.text}` }],
    { maxTokens: 4096 }
  );
  const raw = parseModelJson(content);
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new Error("OpenAI returned an unexpected grammar response.");
  }
  const data = raw as Record<string, unknown>;
  let grammarFix = pair(data.grammarFix as Pair);
  if (wantsTranslation && !grammarFix.to) {
    const retry = await chat(
      [
        { role: "system", content: system },
        { role: "user", content: `${input.context ? `Context: ${input.context}\n\n` : ""}Text:\n${input.text}` },
        { role: "user", content: "The previous grammarFix.to was empty. Return the full JSON again. grammarFix.from must stay in the source language. grammarFix.to must be the target-language translation of that corrected sentence." },
      ],
      { maxTokens: 4096 }
    );
    const retried = parseModelJson(retry);
    if (retried && typeof retried === "object" && !Array.isArray(retried)) {
      grammarFix = pair((retried as Record<string, unknown>).grammarFix as Pair);
    }
  }
  const native = pair((data.native ?? data.everyday_neutral) as Pair);
  const friendly = pair((data.friendly ?? data.friendly_casual) as Pair);
  const professional = pair((data.professional ?? data.professional_formal) as Pair);
  let programmer = pair(data.programmer as Pair);
  const dropped = wantsTranslation ? missingAbbreviations(programmer.from, programmer.to) : [];
  if (dropped.length) {
    const retry = await chat(
      [
        { role: "system", content: system },
        { role: "user", content: `${input.context ? `Context: ${input.context}\n\n` : ""}Text:\n${input.text}` },
        { role: "user", content: `programmer.to dropped these abbreviations: ${dropped.join(", ")}. Return the full JSON again. programmer.to must contain each of those tokens exactly and must not expand them.` },
      ],
      { maxTokens: 4096 }
    );
    const retried = parseModelJson(retry);
    if (retried && typeof retried === "object" && !Array.isArray(retried)) {
      const next = pair((retried as Record<string, unknown>).programmer as Pair);
      if (next.to && missingAbbreviations(programmer.from, next.to).length < dropped.length) programmer = next;
    }
  }
  const notes = Array.isArray(data.grammar_notes)
    ? data.grammar_notes
        .filter((note): note is Record<string, unknown> => Boolean(note && typeof note === "object"))
        .map((note) => ({
          original: String(note.original ?? "").trim(),
          correction: String(note.correction ?? note.fixed ?? "").trim(),
          explanation: String(note.explanation ?? note.why ?? "").trim(),
        }))
    : [];
  const grammarFixOut = applyRoman(grammarFix, to, wantsTranslation);
  const nativeOut = applyRoman(native, to, wantsTranslation);
  const friendlyOut = applyRoman(friendly, to, wantsTranslation);
  const professionalOut = applyRoman(professional, to, wantsTranslation);
  const programmerOut = applyRoman(programmer, to, wantsTranslation);
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
    grammarFix: grammarFixOut,
    native: nativeOut,
    friendly: friendlyOut,
    professional: professionalOut,
    programmer: programmerOut,
    everyday_neutral: nativeOut,
    friendly_casual: friendlyOut,
    professional_formal: professionalOut,
    provider: "openai",
  };
}
