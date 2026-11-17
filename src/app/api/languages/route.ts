import { NextResponse } from "next/server";
import {
  DEFAULT_GRAMMAR_FROM,
  DEFAULT_GRAMMAR_TO,
  GRAMMAR_LANGUAGES,
  LANGUAGE_LOCALES,
  MAX_INPUT_CHARS,
  RTL_TARGETS,
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
      { label: "Programmer", key: "programmer" },
    ],
  });
}
