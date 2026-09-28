export const MAX_INPUT_CHARS = 1000;

export const LANGUAGE_LOCALES: Record<string, string[]> = {
  English: ["American English", "British English"],
  Persian: ["Iranian Persian", "Dari Persian"],
  German: ["German (Germany)", "German (Austria)", "German (Switzerland)"],
  Arabic: ["Modern Standard Arabic"],
  French: ["French (France)", "Canadian French"],
  Spanish: ["Spanish (Spain)", "Latin American Spanish"],
  Italian: ["Italian (Italy)"],
  Turkish: ["Turkish (Turkey)"],
  Russian: ["Russian (Russia)"],
  Japanese: ["Japanese (Japan)"],
  Korean: ["Korean (South Korea)"],
  Chinese: ["Simplified Chinese", "Traditional Chinese"],
};

export const GRAMMAR_LANGUAGES = Object.keys(LANGUAGE_LOCALES);
export const RTL_TARGETS = new Set(["Persian", "Arabic"]);
export const DEFAULT_GRAMMAR_FROM = "English";
export const DEFAULT_GRAMMAR_TO = "Persian";
export const TENSE_LANGUAGES = ["English", "German"] as const;
export const DEFAULT_TENSE_LANGUAGE = "English";
export const TENSE_COUNTS = { English: 12, German: 6 };
export const GERMAN_TENSES = [
  { key: "praesens", label: "Präsens" },
  { key: "praeteritum", label: "Präteritum" },
  { key: "perfekt", label: "Perfekt" },
  { key: "plusquamperfekt", label: "Plusquamperfekt" },
  { key: "futur_i", label: "Futur I" },
  { key: "futur_ii", label: "Futur II" },
] as const;

export function resolveLocale(language: string, locale?: string | null) {
  const options = LANGUAGE_LOCALES[language] ?? [language];
  return locale && options.includes(locale) ? locale : options[0];
}
