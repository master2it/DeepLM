"""Shared language lists and Grammar/Spell Fixer prompts."""

from __future__ import annotations

import re

TARGET_LANGUAGES = {
    "Persian": "pes_Arab",
    "English": "eng_Latn",
    "Arabic": "arb_Arab",
    "French": "fra_Latn",
    "German": "deu_Latn",
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
DEFAULT_GRAMMAR_FROM = "Persian"
DEFAULT_GRAMMAR_TO = "English"
GRAMMAR_LANGUAGES = list(TARGET_LANGUAGES.keys())

STYLE_VARIANTS = (
    ("Friendly / Casual", "friendly_casual"),
    ("Professional / Formal", "professional_formal"),
    ("Everyday / Neutral", "everyday_neutral"),
)

TEACHER_EDITOR_INSTRUCTION = """
Whenever I send you a text in Persian, act as an American English language teacher and correct its grammar and natural usage.

First, translate and fix the text into natural American English (B2 level).
Then provide 3 versions of the corrected sentence:
1. Friendly / casual
2. Professional / formal
3. Everyday / neutral conversational

Rules:

- Do not reuse or rely on previous sentences. Each message is independent.
- Only correct and improve the sentence I send in that turn.
- If there are grammar mistakes, explain them briefly and fix them naturally.
- Keep the output clean, native-like, and natural as spoken in the US.
- Avoid overly complex vocabulary; stay around B2 level unless necessary.
- Keep the meaning and intent of the original text unchanged.
- Do not add information that is not present in the original text.
""".strip()

SEMANTIC_ACCURACY_RULES = """
Preserve the original meaning and context.
Do not invent explicit subjects when the source language leaves them implicit.
Infer omitted subjects only when context clearly supports the inference.
If context is insufficient, use neutral target-language phrasing.
Do not introduce information that is not present in the source.
Prioritize natural native-level phrasing over literal word-for-word translation.
For style variants, preserve semantic meaning exactly and change only tone, register, and phrasing.

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

_READY_FIRST_PERSON_RE = re.compile(
    r"\bI(?:'ll| will)\s+be\s+(?:ready|prepared)\b",
    re.IGNORECASE,
)
_PERSIAN_IT_READY_RE = re.compile(r"[آا]ماده\s*م[\u200cیي]*ش(?:ه|ود)?")
_PERSIAN_EXPLICIT_I_RE = re.compile(r"(?:^|[^\w])من(?:[^\w]|$)|آماده‌?ام|هستم")
