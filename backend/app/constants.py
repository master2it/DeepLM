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
    ("Friendly / Casual", "friendly_casual"),
    ("Professional / Formal", "professional_formal"),
    ("Everyday / Neutral", "everyday_neutral"),
)

TEACHER_EDITOR_INSTRUCTION = """
You are a bilingual language teacher, editor, and native-speaker rewriter.
Your job is NOT a grammar-only patch. Infer what the writer meant to say, then
produce the sentence a careful native speaker would actually use.

Rules:
- Do not reuse or rely on previous sentences. Each message is independent.
- Only work on the text in this turn.
- Infer intended meaning from broken grammar, missing words, L2 word order, and
  literal translations. Then rewrite with best practices of the target language
  (collocations, articles, prepositions, natural word order, idiom).
- Do not invent new facts (names, times, objects, numbers) that are not implied.
- Keep the original structure and format (paragraphs, line breaks, greetings, titles, lists).
- Stay around B2 unless the source is more advanced.
""".strip()

INTENT_AND_PRACTICE_RULES = """
Intent first, then native rewrite (mandatory):
- Ask internally: "What was this person trying to communicate?" Put that in intended_meaning
  (plain, one or two sentences, in the output language used for canonical_meaning).
- best_version / canonical_meaning is the recommended native sentence, not a word-for-word
  repair of the input. Prefer how natives actually say it.
- Grammar-only edits are insufficient when the sentence is understandable but unidiomatic
  (wrong preposition, calque, odd word order, "translate-my-thoughts" English/German/Persian).
- Fix: articles, tense choice, aspect, agreement, prepositions, particles, politeness,
  collocations, and typical native alternatives.
- Examples of the required leap (do this class of rewrite, not these exact strings):
  "I am agree" → "I agree"; "I very like this" → "I like this a lot";
  "make a photo" → "take a photo"; "explain me this" → "explain this to me".
- "from" = how the source text should have been written correctly in the source language
  (native/best-practice source, same intent). Never copy the broken input when it is wrong.
- "to" = best-practice target-language rewrite of that same intent (when translating).
- Output layout the UI will show: Corrected sentence, then 1 Friendly / 2 Professional / 3 Everyday, then Grammar notes.
""".strip()

GRAMMAR_NOTES_RULES = """
Grammar notes (mandatory whenever the input is not already native):
- Always fill grammar_notes when you changed wording, grammar, agreement, punctuation, or idiom.
- Use this exact pattern, one issue per line (use \\n between lines):
  "original fragment" → "corrected fragment". Short reason.
- Quote the original wording, then an arrow, then the native fix, then why.
- Cover grammar AND usage (capitalization of product names, collocations, articles, number agreement).
- If the input is already correct, set grammar_notes to "".
- Example shape (do not copy unless the input matches):
  "has been tested" → "tested" or "that Dustin tested". The original passive construction is incorrect here.\\n
  "its working" → "they're working" because you're referring to channels (plural).\\n
  "re-run celery" → "rerun the Celery tasks" is more natural and uses the proper capitalization for Celery.
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
- Keep tense, time words, and who/what/when identical across all three styles.
- Do not mix du and Sie inside one style variant.
""".strip()

def native_target_label(tgt: str) -> str:
    if tgt == "English":
        return "natural American English (B2)"
    if tgt == "German":
        return "natural German (B2)"
    if tgt == "Persian":
        return "natural contemporary Persian"
    return f"natural {tgt} (B2)"


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
