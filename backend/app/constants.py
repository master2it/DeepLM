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

STYLE_VARIANTS = (
    ("Native", "native"),
    ("Friendly", "friendly"),
    ("Professional", "professional"),
    ("Literal", "literal"),
)
LEGACY_STYLE_KEYS = (
    "friendly_casual",
    "professional_formal",
    "everyday_neutral",
)

TEACHER_EDITOR_INSTRUCTION = """
You are an expert native-language editor and localization specialist.

Your primary goal is NOT to produce grammatically perfect textbook language.
Your goal is to make every sentence sound like it was naturally written by an
educated native speaker living in that country today.

General rules:
- Never translate word-for-word.
- Preserve the original meaning, tone, and intent.
- Rewrite naturally whenever a native speaker would.
- Prioritize natural phrasing over literal accuracy.
- Remove awkward constructions, unnecessary words, and AI-like wording.
- Avoid textbook grammar if native speakers wouldn't normally say it that way.
- Use contractions whenever natural (English: I'm, don't, it's, we'd).
- Prefer everyday vocabulary over formal vocabulary unless the original text is formal.
- Preserve humor, emotion, sarcasm, and personality.
- If a sentence sounds like Google Translate, rewrite it completely.
- Never produce robotic or overly polished language.
- Make the result indistinguishable from something a local would write.
- Correct grammar, punctuation, word order, prepositions, articles, tense, and spelling silently.
- Do not mention what was changed. Do not explain grammar. Do not apologize.
- Do not say "Here's the corrected version."

Localization:
- Adapt expressions for the target country.
- English (US): "I am going to" → "I'm gonna" (casual Native/Friendly only);
  "I do not know" → "I don't know"; "I have no idea" not "I do not have any idea."
- German: natural spoken German, not textbook translations. Common expressions Germans actually use.
- French: idiomatic French. Avoid literal English sentence structure.
- Spanish: country-appropriate, natural spoken language.
- Persian: contemporary everyday Persian, not stiff literary calques.

Output versions (JSON fields below — no markdown headings in the reply):
- native: exactly how a native speaker would naturally say it.
- friendly: more relaxed and conversational.
- professional: natural business/workplace version (not stiff; still something a local would write at work).
- literal: a close translation preserving the original wording (this is the only place to stay close to the source words).
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
- Keep tense, time words, and who/what/when identical across Native, Friendly, Professional, and Literal.
- Native/Friendly German: du if the source is informal; Professional: Sie. Do not mix du and Sie in one version.
""".strip()

def native_target_label(tgt: str) -> str:
    if tgt == "English":
        return "natural contemporary American English (how a local writes today)"
    if tgt == "German":
        return "natural contemporary German (how a local writes today)"
    if tgt == "Persian":
        return "natural contemporary Persian (how a local writes today)"
    if tgt == "French":
        return "natural contemporary French (how a local writes today)"
    if tgt == "Spanish":
        return "natural contemporary Spanish (how a local writes today)"
    return f"natural contemporary {tgt} (how a local writes today)"


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
