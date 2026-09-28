import { NextResponse } from "next/server";
import {
  DEFAULT_GRAMMAR_FROM,
  DEFAULT_GRAMMAR_TO,
  DEFAULT_TENSE_LANGUAGE,
  GERMAN_TENSES,
  GRAMMAR_LANGUAGES,
  LANGUAGE_LOCALES,
  MAX_INPUT_CHARS,
  RTL_TARGETS,
  TENSE_COUNTS,
  TENSE_LANGUAGES,
} from "@/lib/server/constants";

export function GET() {
  return NextResponse.json({
    max_input_chars: MAX_INPUT_CHARS,
    languages: GRAMMAR_LANGUAGES,
    rtl: [...RTL_TARGETS].sort(),
    default_from: DEFAULT_GRAMMAR_FROM,
    default_to: DEFAULT_GRAMMAR_TO,
    locales: LANGUAGE_LOCALES,
    default_locales: Object.fromEntries(Object.entries(LANGUAGE_LOCALES).map(([language, locales]) => [language, locales[0]])),
    styles: [
      { label: "Grammar Fix", key: "grammarFix" },
      { label: "Native", key: "native" },
      { label: "Friendly / Casual", key: "friendly" },
      { label: "Professional", key: "professional" },
    ],
    tense_languages: TENSE_LANGUAGES,
    default_tense_language: DEFAULT_TENSE_LANGUAGE,
    tense_counts: TENSE_COUNTS,
    german_tenses: GERMAN_TENSES,
  });
}
