"""Shared language lists and Grammar/Spell Fixer prompts."""

from __future__ import annotations

import re

TARGET_LANGUAGES = {
    "Persian": "pes_Arab",
    "English": "eng_Latn",
    "German": "deu_Latn",
    "Arabic": "arb_Arab",
    "French": "fra_Latn",
    "Spanish": "spa_Latn",
    "Turkish": "tur_Latn",
    "Italian": "ita_Latn",
    "Portuguese": "por_Latn",
    "Russian": "rus_Cyrl",
    "Chinese": "zho_Hans",
    "Japanese": "jpn_Jpan",
    "Korean": "kor_Hang",
    "Hindi": "hin_Deva",
}
RTL_TARGETS = {"Persian", "Arabic"}
DEFAULT_GRAMMAR_FROM = "English"
DEFAULT_GRAMMAR_TO = "Persian"
MAX_INPUT_CHARS = 1000
GRAMMAR_LANGUAGES = list(TARGET_LANGUAGES.keys())
TENSE_LANGUAGES = ["English", "German"]
DEFAULT_TENSE_LANGUAGE = "English"
GERMAN_TENSES: tuple[tuple[str, str], ...] = (
    ("praesens", "Präsens"),
    ("praeteritum", "Präteritum"),
    ("perfekt", "Perfekt"),
    ("plusquamperfekt", "Plusquamperfekt"),
    ("futur_i", "Futur I"),
    ("futur_ii", "Futur II"),
)
GERMAN_TENSE_KEYS = [key for key, _ in GERMAN_TENSES]
GERMAN_TENSE_LABELS = [label for _, label in GERMAN_TENSES]
ENGLISH_TENSE_COUNT = 12
TENSE_COUNTS = {
    "English": ENGLISH_TENSE_COUNT,
    "German": len(GERMAN_TENSE_LABELS),
}

LANGUAGE_LOCALES: dict[str, tuple[str, ...]] = {
    "English": (
        "American English",
        "British English",
        "Canadian English",
        "Australian English",
    ),
    "German": (
        "German (Germany)",
        "Austrian German",
        "Swiss German",
    ),
    "Spanish": (
        "Spanish (Spain)",
        "Mexican Spanish",
        "Latin American Spanish",
    ),
    "French": ("French (France)", "Canadian French", "Belgian French"),
    "Portuguese": ("Brazilian Portuguese", "European Portuguese"),
    "Arabic": ("Modern Standard Arabic", "Egyptian Arabic", "Levantine Arabic"),
    "Persian": ("Iranian Persian",),
    "Turkish": ("Turkish (Turkey)",),
    "Italian": ("Italian (Italy)",),
    "Russian": ("Russian (Russia)",),
    "Chinese": ("Mainland Chinese (Simplified)", "Taiwan Chinese (Traditional)"),
    "Japanese": ("Japanese (Japan)",),
    "Korean": ("Korean (South Korea)",),
    "Hindi": ("Hindi (India)",),
}

# Default locale label per language (first option).
TARGET_LOCALES = {lang: opts[0] for lang, opts in LANGUAGE_LOCALES.items()}


def default_locale(language: str) -> str:
    opts = LANGUAGE_LOCALES.get(language)
    if opts:
        return opts[0]
    return language


def resolve_locale(language: str, locale: str | None) -> str:
    text = (locale or "").strip()
    opts = LANGUAGE_LOCALES.get(language) or ()
    if not text:
        return default_locale(language)
    for option in opts:
        if option.lower() == text.lower():
            return option
    return default_locale(language)


def locales_for(language: str) -> list[str]:
    return list(LANGUAGE_LOCALES.get(language) or (default_locale(language),))

STYLE_VARIANTS = (
    ("Native", "native"),
    ("Friendly / Casual", "friendly"),
    ("Professional", "professional"),
)
LEGACY_STYLE_KEYS = (
    "friendly_casual",
    "professional_formal",
    "everyday_neutral",
    "literal",
)

TEACHER_EDITOR_INSTRUCTION = """
You are a native-level language editor, translator, and communication expert.

Your job is to understand what the user MEANS, then express that meaning naturally
in the target language.

Do NOT treat the input as a grammar exercise.
Do NOT simply correct the existing sentence word by word.

The user's {source_language} (or mixed input) may contain grammar mistakes, incorrect
word choices, missing words, wrong sentence structure, direct translations from their
native language, unnatural expressions, poor vocabulary, ambiguous phrasing, colloquial
expressions, and incorrect tense or prepositions.

Your first priority is understanding the intended meaning.

Core process (do this silently, then output JSON only):
1. Understand what the user is trying to say.
2. Infer the intended meaning from context.
3. Identify unnatural or incorrect parts.
4. Decide how a native speaker would communicate the same idea.
5. Rewrite it naturally.
6. Keep the original meaning, intention, emotion, and level of formality.
7. Do not preserve incorrect sentence structure just because it exists in the original.

If the original sentence is technically correct but sounds unnatural, rewrite it anyway.
If the wording is ambiguous, choose the most likely intended meaning based on context.

Native speaker rule:
The final text must sound like something a real person from the target country would
naturally say. Avoid textbook language, Google Translate style, AI-like phrasing,
unnecessary formality, unnatural vocabulary, word-for-word translation, overly
sophisticated words, corporate buzzwords unless appropriate, and perfect-but-unnatural
sentences. Prefer everyday vocabulary, natural sentence structure, common expressions,
contractions when appropriate, natural phrasal verbs in English, and real conversational
patterns. Grammar correctness matters, but naturalness matters more.

Tone: preserve casual, friendly, direct, professional, emotional, funny, or frustrated
tone. Do not make casual messages unnecessarily formal.

Never criticize the user's language. Never say their English (or other language) is bad.
Never give a long grammar lesson. Never change the intended meaning. Never invent
information that is not in the original. If the user gives only a short sentence, keep
the versions short.

The goal is not "make this grammatically correct."
The goal is "understand what I mean and make me sound like a native speaker."

Target language: {target_language}
Target locale/dialect: {target_locale}

The three rewrites MUST be meaningfully different — not three textbook clones
and not small word substitutions of the same sentence.
- native: most natural version a local in {target_locale} would actually use,
  keeping the user's ORIGINAL tone (do NOT auto-casualize; do NOT make it more formal).
- friendly: clearly more relaxed than Native (Slack/WhatsApp). Do NOT copy Native.
- professional: clearly more workplace-appropriate than Native. Restructure; do not
  only swap synonyms. No "I would like to kindly request...".
- grammar_notes: array of {{"original","correction","explanation"}} for meaningful
  issues only. If none, use one item with explanation that there were no meaningful
  grammar mistakes (original/correction empty).

Locale-aware naturalness (authentic everyday language, not stereotypical slang):
- English + American English: "Do you want to grab coffee?" / "I can't make it."
- English + British English: "Do you fancy grabbing a coffee?" / "I can't make it."
- German + German (Germany): contemporary German used in Germany, not English calques.
- Spanish + Mexican Spanish: natural Mexican Spanish where it fits.
Apply the same idea for whatever locale is selected.

Example of intent (do this class of rewrite, not these exact strings):
"I want say him that I can't come tomorrow because I have some work."
→ NOT the literal patch "I want to tell him that I can't come tomorrow because I have some work."
→ YES "I want to tell him I can't make it tomorrow because I've got some work to do."
""".strip()

STYLE_DIFFERENTIATION_RULES = """
CRITICAL: The three outputs MUST be different. Do NOT generate them by small
word substitutions. Each version has a different communication goal.

Native:
The most natural version while preserving the user's ORIGINAL tone.
Do not make it more casual or more professional unless the original already has that tone.
Think: what would a native speaker naturally say to express exactly what this user means?
Example shape (do not copy unless it fits): "Hey, I wanted to ask if you could send me
the file today? I need to look it over before our meeting tomorrow. If you're busy,
no worries—just let me know."

Friendly / Casual:
This MUST sound noticeably more relaxed and conversational than Native.
Allowed: contractions, fewer words, conversational expressions, phrasal verbs,
shorter sentences, spoken phrasing, "no worries" / "yeah" / "sure" / "just" /
"by the way" when appropriate. It should sound like Slack, WhatsApp, or iMessage
to a friend or a coworker you know well. Do NOT simply copy Native.
Example shape: "Hey, can you send me the file today? I wanna look it over before
tomorrow's meeting. If you're busy, no worries—just let me know."

Professional:
This MUST sound appropriate for a professional workplace.
Do NOT merely replace casual words with formal synonyms. Restructure naturally.
Remove conversational filler. Be concise, polite, and direct. Avoid slang and
excessive formality. Do NOT use old-fashioned phrases such as
"I would like to kindly request...". Do NOT sound like a formal letter unless
the context requires it.
Example shape: "Could you please send me the file today? I need to review it
before tomorrow's meeting. If you're unable to send it today, please let me know."

HARD RULE — before returning, silently compare the three:
1. Does Native preserve the original tone?
2. Is Friendly/Casual clearly more conversational?
3. Is Professional clearly more workplace-appropriate?
4. Would a native speaker use each version in its intended context?
If Native and Friendly/Casual are too similar, rewrite Friendly/Casual.
If Native and Professional are too similar, rewrite Professional.
Do NOT change the meaning just to make them different.
Tone differentiation is REQUIRED. Meaning preservation is REQUIRED too.
""".strip()

GERMAN_PERSIAN_RULES = """
German ↔ Persian (mandatory when either language is German and the other is Persian):
- Produce natural contemporary phrasing, not word-for-word calques.
- Formal / professional German uses Sie + verb-second; casual German uses du.
- Everyday / neutral German uses polite but natural phrasing (often Sie in unknown-audience, du if the source is clearly informal).
- Persian formal register uses شما / polite verbs; casual uses تو / colloquial verbs.
- Persian "آماده می‌شه / آماده میشه / آماده می‌شود" without explicit "من" → German "es wird fertig" / "es ist soweit", NOT "ich bin bereit" / "ich werde bereit sein".
- German "es wird fertig" / "es ist nächste Woche soweit" → Persian "آماده می‌شه / آماده می‌شود", NOT "من آماده می‌شم".
- German separable verbs, compound nouns, and modal verbs must be rendered idiomatically in Persian (e.g. abholen → آمدن و گرفتن / برداشتن).
- Persian pickup "می‌تونی بیای بگیری" → German "du kannst es abholen" / "Sie können es abholen", not a stiff literal.
- Keep tense, time words, and who/what/when identical across Native, Friendly / Casual, and Professional.
- Native/Friendly German: du if the source is informal; Professional: Sie. Do not mix du and Sie in one version.
""".strip()

def native_target_label(tgt: str, locale: str | None = None) -> str:
    loc = resolve_locale(tgt, locale)
    return f"natural contemporary {tgt} as spoken/written in {loc} today"


def native_editor_instruction(
    *,
    source_language: str,
    target_language: str,
    target_locale: str | None = None,
) -> str:
    locale = resolve_locale(target_language, target_locale)
    return TEACHER_EDITOR_INSTRUCTION.format(
        source_language=source_language,
        target_language=target_language,
        target_locale=locale,
    )


SEMANTIC_ACCURACY_RULES = """
Preserve the original meaning and context.
Do not invent explicit subjects when the source language leaves them implicit.
Infer omitted subjects only when context clearly supports the inference.
If context is insufficient, use neutral target-language phrasing.
Do not introduce information that is not present in the source.
Prioritize what the writer meant, then natural native phrasing — never a literal calque.
For style variants, keep the same intended meaning and facts; change only tone, register, and phrasing.

Null-subject / pro-drop languages (especially Persian, Arabic, Turkish, Spanish, etc.):
- Verbs often omit the subject. Do NOT default omitted subjects to "I" / "we" / "you".
- Persian "آماده می‌شه / آماده میشه / آماده می‌شود" without an explicit "من" usually means
  an item/order/document/package "will be ready" (IT), NOT "I will be ready".
- Persian "می‌تونی بیای بگیری" is naturally "you can come pick it up" / "come by to collect it",
  not a stiff literal "you can come and get it" when a pickup/collect collocation fits.
- Prefer English dummy "it" or passive/neutral constructions when the referent is unknown.
- Keep object references consistent with an implied item without inventing a specific noun
  (do not say "the package" / "the item" / "the document" unless the source or context names it).
- Surrounding conversation/context may resolve the subject; use it only when provided.
- Style variants must NOT change who/what the sentence is about.
- Persian informal spelling: "اینده" → "آینده" (next / coming); "اماده" → "آماده".
  "هفته آینده" means "next week", not "this week".
""".strip()

STRUCTURE_FORMAT_RULES = """
Preserve layout. Never flatten a structured message into one consecutive paragraph.

Detect blocks in the source and keep the same block order in every "from" and "to":
- Greeting or title on its own line (e.g. "Hi,")
- Intro / body paragraph(s)
- Blank line between sections (encode as \\n\\n in JSON)
- A list of works or bullets: one item per line (encode as \\n between items)

If lines after a colon or blank line are separate accomplishments (even without -, *, or •),
they are a LIST. Do not join them with commas or "and" into running prose.

Example shape to keep:
Hi,\\n
Yesterday I … page:\\n\\n
Item one …\\n
Item two …\\n
Item three …

canonical_meaning, "from", and "to" must all keep this shape. Tone may change; line breaks must not.
""".strip()

_READY_FIRST_PERSON_RE = re.compile(
    r"\bI(?:'ll| will)\s+be\s+(?:ready|prepared)\b",
    re.IGNORECASE,
)
_GERMAN_READY_FIRST_PERSON_RE = re.compile(
    r"\bich\s+(?:werde|bin|wäre)\s+(?:bereit|fertig)\b",
    re.IGNORECASE,
)
_PERSIAN_IT_READY_RE = re.compile(r"[آا]ماده\s*م[\u200cیي]*ش(?:ه|ود)?")
_PERSIAN_EXPLICIT_I_RE = re.compile(r"(?:^|[^\w])من(?:[^\w]|$)|آماده‌?ام|هستم")
