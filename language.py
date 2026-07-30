"""
Ultimate English AI Assistant.

Auth:
  Development — optional `.env` next to this file (see .env.example).
  Packaged .exe — Windows env var HF_TOKEN only (setx); no .env required.
"""

import json
import re
import sys
import threading

from huggingface_hub import InferenceClient
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QPlainTextEdit,
    QTabWidget,
    QScrollArea,
    QFrame,
    QComboBox,
    QMessageBox,
    QGridLayout,
    QSizePolicy,
)

from config import (
    ConfigError,
    get_hf_chat_model,
    get_hf_token,
    load_development_dotenv,
)

# Load .env in development before any HF client use (no-op when frozen).
load_development_dotenv()

# --- HuggingFace (chat) ---
# Prefer accessors; module-level values are snapshots after dotenv load.
HF_TOKEN = get_hf_token()
HF_CHAT_MODEL = get_hf_chat_model()
_hf_client = None

# UI label -> NLLB-200 language code
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

# Styled translation variants (Grammar/Spell Fixer tab)
#
# Architecture (Grammar/Spell Fixer):
#   Source text
#   → Language detection (LLM)
#   → Context / implicit-subject analysis (LLM)
#   → Canonical meaning (single semantic reading)
#   → Style adaptation from that canonical meaning (tone only)
#   → Optional target-language lines derived from the same meaning
#
# Model: HuggingFace chat LLM (HF_CHAT_MODEL, default Qwen/Qwen2.5-72B-Instruct)
# via InferenceClient.chat_completion.
#
# Context: optional `context=` kwarg on get_styled_translations_from_ai.
# Style variants: derived from one canonical_meaning in a single LLM response.
#
# Tests: tests/test_translation_quality.py
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

DEFAULT_GRAMMAR_FROM = "Persian"
DEFAULT_GRAMMAR_TO = "English"
GRAMMAR_LANGUAGES = list(TARGET_LANGUAGES.keys())

# English patterns that invent a first-person subject for "will be ready"
_READY_FIRST_PERSON_RE = re.compile(
    r"\bI(?:'ll| will)\s+be\s+(?:ready|prepared)\b",
    re.IGNORECASE,
)
# Persian 3rd-person / impersonal "ready" (اماده/آماده + میشه/می‌شه/می‌شود)
_PERSIAN_IT_READY_RE = re.compile(
    r"[آا]ماده\s*م[\u200cیي]*ش(?:ه|ود)?"
)
_PERSIAN_EXPLICIT_I_RE = re.compile(r"(?:^|[^\w])من(?:[^\w]|$)|آماده‌?ام|هستم")



# Dark theme palette
APP_BG = "#1A1B1E"
APP_SURFACE = "#25262B"
APP_SURFACE_RAISED = "#2E3036"
APP_BORDER = "#3C3E45"
APP_TEXT = "#ECEDEF"
APP_MUTED = "#9B9EA6"
APP_ACCENT = "#3B82F6"
APP_ACCENT_HOVER = "#2563EB"
APP_SUCCESS = "#22C55E"
APP_SUCCESS_HOVER = "#16A34A"
APP_DANGER = "#EF4444"
APP_LINK = "#60A5FA"

APP_STYLESHEET = f"""
QWidget {{
    background-color: {APP_BG};
    color: {APP_TEXT};
    font-family: 'Segoe UI', Helvetica, sans-serif;
}}
QMainWindow, QDialog {{
    background-color: {APP_BG};
}}
QTabWidget::pane {{
    border: 1px solid {APP_BORDER};
    border-radius: 6px;
    background: {APP_BG};
    top: -1px;
}}
QTabBar::tab {{
    background: {APP_SURFACE};
    color: {APP_MUTED};
    border: 1px solid {APP_BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 4px;
    font-weight: bold;
    font-size: 11pt;
}}
QTabBar::tab:selected {{
    background: {APP_SURFACE_RAISED};
    color: {APP_TEXT};
}}
QTabBar::tab:hover:!selected {{
    color: {APP_TEXT};
    background: {APP_SURFACE_RAISED};
}}
QLabel {{
    background: transparent;
    color: {APP_TEXT};
}}
QPlainTextEdit, QTextEdit {{
    background: {APP_SURFACE};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    border-radius: 6px;
    padding: 10px;
    selection-background-color: {APP_ACCENT};
    selection-color: white;
}}
QComboBox {{
    background: {APP_SURFACE};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 28px;
}}
QComboBox:hover {{
    border-color: {APP_ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {APP_SURFACE_RAISED};
    color: {APP_TEXT};
    border: 1px solid {APP_BORDER};
    selection-background-color: {APP_ACCENT};
    selection-color: white;
    outline: none;
}}
QScrollArea {{
    background: {APP_BG};
    border: none;
}}
QScrollBar:vertical {{
    background: {APP_BG};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {APP_BORDER};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {APP_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QMessageBox {{
    background-color: {APP_SURFACE};
}}
QMessageBox QLabel {{
    color: {APP_TEXT};
}}
"""


# ==========================================
# Helpers
# ==========================================
def extract_json(response_text):
    """Extract a JSON array or object from model text."""
    try:
        match = re.search(r"(\{.*\}|\[.*\])", response_text, re.DOTALL)
        if match:
            return match.group(0)
        return response_text
    except Exception:
        return response_text


def apply_rtl(widget, enabled=True):
    """Point a widget (and its text) in the correct reading direction."""
    if enabled:
        widget.setLayoutDirection(Qt.RightToLeft)
        if hasattr(widget, "setAlignment"):
            try:
                widget.setAlignment(Qt.AlignRight | Qt.AlignAbsolute)
            except TypeError:
                pass
    else:
        widget.setLayoutDirection(Qt.LeftToRight)
        if hasattr(widget, "setAlignment"):
            try:
                widget.setAlignment(Qt.AlignLeft | Qt.AlignAbsolute)
            except TypeError:
                pass


# ==========================================
# HuggingFace helpers
# ==========================================
def require_hf_client():
    """Return a configured InferenceClient, or raise ConfigError with setup help."""
    global _hf_client, HF_TOKEN
    token = get_hf_token(required=True)
    HF_TOKEN = token  # keep module snapshot in sync (never log this)
    if _hf_client is None:
        _hf_client = InferenceClient(token=token)
    return _hf_client


def _chat_content(response):
    """Normalize InferenceClient.chat_completion response to a string."""
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    try:
        choice = response.choices[0]
        message = choice.message
        content = getattr(message, "content", None)
        if content:
            return content
    except Exception:
        pass
    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            return msg.get("content") or ""
    return str(response)


def hf_chat(messages, temperature=0.2, max_tokens=2048):
    """Chat completion via HuggingFace instruct model."""
    api = require_hf_client()
    response = api.chat_completion(
        messages=messages,
        model=HF_CHAT_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return _chat_content(response)


# ==========================================
# Teaching AI (HuggingFace chat)
# ==========================================
def get_tenses_from_ai(text):
    system_prompt = """
    You are an expert English teacher. The user will give you a short text.
    1. Identify subject and BASE VERB.
    2. Conjugate in ALL 12 English verb tenses.
    3. Provide NATURAL Persian translation (Never translate "do" to "میکنم" standalone. Use "انجام دادن").

    Output ONLY a valid JSON ARRAY like this:
    [
        {"tense": "Present Simple", "english": "...", "persian": "..."},
        ...
    ]
    """
    try:
        content = hf_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=2500,
        )
        return json.loads(extract_json(content))
    except Exception as e:
        return {"error": str(e)}


def persian_implies_impersonal_ready(text):
    """True when Persian likely means 'it will be ready', not 'I will be ready'."""
    if not text:
        return False
    if _PERSIAN_EXPLICIT_I_RE.search(text):
        return False
    return bool(_PERSIAN_IT_READY_RE.search(text))


def english_invents_speaker_ready(text):
    """True when English wrongly makes the speaker the thing that becomes ready."""
    return bool(text and _READY_FIRST_PERSON_RE.search(text))


def collect_style_to_texts(data):
    """Gather all style 'to' strings from a parsed styled-translation payload."""
    texts = []
    for _label, key in STYLE_VARIANTS:
        item = (data or {}).get(key) or {}
        if isinstance(item, dict):
            t = (item.get("to") or "").strip()
            if t:
                texts.append(t)
        elif isinstance(item, str) and item.strip():
            texts.append(item.strip())
    canon = ((data or {}).get("canonical_meaning") or "").strip()
    if canon:
        texts.append(canon)
    return texts


def flagged_invented_ready_subject(source_text, result):
    """
    Heuristic quality flag: Persian impersonal 'آماده میشه' must not become
    English 'I'll be ready'.
    """
    if not persian_implies_impersonal_ready(source_text):
        return False
    return any(english_invents_speaker_ready(t) for t in collect_style_to_texts(result))


def _style_pair(item):
    if isinstance(item, str):
        return {"from": item.strip(), "to": ""}
    if not isinstance(item, dict):
        return {"from": "", "to": ""}
    return {
        "from": (item.get("from") or "").strip(),
        "to": (item.get("to") or "").strip(),
    }


def parse_styled_translation_response(data, *, src_hint, tgt, wants_translation):
    """Normalize LLM JSON into the UI contract dict (no network)."""
    if not isinstance(data, dict):
        return {"error": "Unexpected model response."}

    detected = (data.get("detected_lang") or src_hint or "").strip() or src_hint
    return {
        "from_lang": detected,
        "to_lang": tgt,
        "wants_translation": wants_translation,
        "canonical_meaning": (data.get("canonical_meaning") or "").strip(),
        "subject_reading": (data.get("subject_reading") or "").strip(),
        "grammar_notes": (data.get("grammar_notes") or "").strip(),
        "friendly_casual": _style_pair(data.get("friendly_casual")),
        "professional_formal": _style_pair(data.get("professional_formal")),
        "everyday_neutral": _style_pair(data.get("everyday_neutral")),
    }


def build_styled_translation_prompt(
    *,
    src_hint,
    tgt,
    wants_translation,
    context=None,
    retry_feedback=None,
):
    """Build system + user messages for canonical-then-style translation."""
    translation_block = (
        f'The user asks for American English ({tgt}) output at B2 level.\n'
        f'1) Write canonical_meaning: one accurate neutral American English sentence (B2).\n'
        f'2) For each style, "from" = corrected/cleaned source-language text in that tone;\n'
        f'   "to" = the SAME meaning as canonical_meaning, restyled in natural US English '
        f'(Friendly/casual, Professional/formal, or Everyday/neutral).\n'
        f'All three "to" lines must preserve identical who/what/when facts as canonical_meaning.\n'
        f'Sound natural as spoken in the US — not stiff or word-for-word.'
        if wants_translation
        else (
            "No target-language translation was requested. Keep styled rewrites in the source language.\n"
            "1) Write canonical_meaning in the source language (neutral accurate reading).\n"
            '2) Put each styled corrected version in "from" and set "to" to an empty string.\n'
            "Styles change tone only; meaning must match canonical_meaning."
        )
    )

    context_block = (
        f"Surrounding conversation/context (use only to resolve ambiguous subjects):\n{context}\n"
        if context and str(context).strip()
        else "No extra conversation context was provided.\n"
    )

    retry_block = (
        f"\nPREVIOUS ATTEMPT WAS REJECTED:\n{retry_feedback}\n"
        "Fix the subject/meaning errors. Do not invent a first-person subject.\n"
        if retry_feedback
        else ""
    )

    system_prompt = f"""
{TEACHER_EDITOR_INSTRUCTION}

SEMANTIC ACCURACY (mandatory):
{SEMANTIC_ACCURACY_RULES}

Pipeline you MUST follow (internally, then output JSON only):
1. Treat the input as Persian when it is Persian (UI hint may be {src_hint}).
2. Analyze whether subjects/objects are explicit or implicit.
3. Decide a single canonical_meaning in natural American English (B2) when translating.
4. Derive all style variants FROM that canonical meaning (tone only — no meaning drift).
5. {translation_block}

{context_block}
{retry_block}
Also:
- "from" must be grammar-fixed source text, never the raw broken input if errors exist.
- grammar_notes: briefly explain grammar mistakes (or "").
- subject_reading: short note like "implicit inanimate 'it' (will be ready)" or "explicit speaker".

Output ONLY valid JSON (no markdown, no commentary):
{{
    "detected_lang": "<detected language name>",
    "subject_reading": "<how you read omitted/explicit subjects>",
    "canonical_meaning": "<one accurate neutral American English reading (B2)>",
    "grammar_notes": "<brief notes or empty>",
    "friendly_casual": {{"from": "<corrected casual source>", "to": "<Friendly/casual US English or empty>"}},
    "professional_formal": {{"from": "<corrected formal source>", "to": "<Professional/formal US English or empty>"}},
    "everyday_neutral": {{"from": "<corrected neutral source>", "to": "<Everyday/neutral US English or empty>"}}
}}
""".strip()

    if wants_translation:
        user_msg = (
            "Translate and fix this Persian into natural American English (B2). "
            f"Then give Friendly/casual, Professional/formal, and Everyday/neutral versions in {tgt}. "
            "Explain grammar briefly in grammar_notes if needed.\n\n"
            f"Text:\n{{text}}"
        )
    else:
        user_msg = (
            "Correct and improve this text, then provide 3 style variants "
            "(same language, no translation).\n\n"
            "Text:\n{text}"
        )

    return system_prompt, user_msg


def get_styled_translations_from_ai(
    text,
    from_lang=DEFAULT_GRAMMAR_FROM,
    to_lang=DEFAULT_GRAMMAR_TO,
    context=None,
):
    """
    Teacher/editor with canonical-then-style translation.

    Returns the same UI keys as before, plus optional canonical_meaning /
    subject_reading for debugging (UI ignores unknown keys safely).
    """
    src_hint = from_lang if from_lang in TARGET_LANGUAGES else DEFAULT_GRAMMAR_FROM
    tgt = to_lang if to_lang in TARGET_LANGUAGES else DEFAULT_GRAMMAR_TO
    wants_translation = src_hint != tgt

    def _once(retry_feedback=None):
        system_prompt, user_template = build_styled_translation_prompt(
            src_hint=src_hint,
            tgt=tgt,
            wants_translation=wants_translation,
            context=context,
            retry_feedback=retry_feedback,
        )
        user_msg = user_template.replace("{text}", text)
        content = hf_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.15,
            max_tokens=3000,
        )
        raw = json.loads(extract_json(content))
        return parse_styled_translation_response(
            raw,
            src_hint=src_hint,
            tgt=tgt,
            wants_translation=wants_translation,
        )

    try:
        result = _once()
        if "error" in result:
            return result
        # One corrective retry for the known Persian→English "I'll be ready" failure mode
        if wants_translation and flagged_invented_ready_subject(text, result):
            result = _once(
                retry_feedback=(
                    "You translated impersonal Persian 'آماده میشه/می‌شود' as if the SPEAKER "
                    "will be ready ('I'll be ready'). That is wrong. Use neutral 'it will be ready' "
                    "/ 'it'll be ready', and for pickup use 'come pick it up' / 'come by to collect it'."
                )
            )
        return result
    except Exception as e:
        return {"error": str(e)}


def get_tense_explanation_from_ai(tense_name):
    system_prompt = f"""
    You are an expert English teacher explaining grammar to a Persian student.
    Explain the English tense "{tense_name}".
    1. Explain WHEN and WHY we use it in simple, natural Persian.
    2. Provide exactly 3 everyday conversational English examples with their Persian translations.

    Output ONLY a valid JSON OBJECT:
    {{
        "explanation": "توضیح کامل فارسی در مورد کاربرد این زمان...",
        "examples": [
            {{"en": "English example 1", "fa": "ترجمه فارسی ۱"}},
            {{"en": "English example 2", "fa": "ترجمه فارسی ۲"}},
            {{"en": "English example 3", "fa": "ترجمه فارسی ۳"}}
        ]
    }}
    """
    try:
        content = hf_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Explain {tense_name}"},
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        return json.loads(extract_json(content))
    except Exception as e:
        return {"error": str(e)}


# ==========================================
# Thread → UI bridge
# ==========================================
class UiInvoker(QObject):
    """Marshal callables onto the Qt main thread."""

    invoke = Signal(object)

    def __init__(self):
        super().__init__()
        self.invoke.connect(self._run)

    def _run(self, fn):
        fn()

    def call(self, fn):
        self.invoke.emit(fn)


# ==========================================
# Tense explanation popup
# ==========================================
class TenseInfoDialog(QWidget):
    def __init__(self, tense_name, ui_invoker, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle(f"Tense Explanation: {tense_name}")
        self.resize(600, 500)
        self.setStyleSheet(f"background: {APP_BG};")
        self._ui = ui_invoker

        layout = QVBoxLayout(self)
        self.loading = QLabel(f"⏳ Getting details for {tense_name}...")
        self.loading.setAlignment(Qt.AlignCenter)
        self.loading.setStyleSheet(f"color: {APP_LINK}; font-size: 12pt;")
        layout.addWidget(self.loading)

        self.info = QTextEdit()
        self.info.setReadOnly(True)
        self.info.setFont(QFont("Segoe UI", 12))
        self.info.setStyleSheet(
            f"background: {APP_SURFACE}; color: {APP_TEXT}; padding: 15px; "
            f"border: 1px solid {APP_BORDER}; border-radius: 6px;"
        )
        self.info.hide()
        layout.addWidget(self.info)

        def fetch():
            data = get_tense_explanation_from_ai(tense_name)
            self._ui.call(lambda: self._update(data, tense_name))

        threading.Thread(target=fetch, daemon=True).start()

    def _append(self, text, *, family="Segoe UI", size=12, bold=False, color=None, align=None, rtl=False):
        if color is None:
            color = APP_TEXT
        cursor = self.info.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        font = QFont(family, size)
        font.setBold(bold)
        fmt.setFont(font)
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        block = cursor.blockFormat()
        if align is not None:
            block.setAlignment(align)
        block.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        cursor.setBlockFormat(block)
        cursor.insertText(text)
        self.info.setTextCursor(cursor)

    def _update(self, data, tense_name):
        self.loading.hide()
        self.info.show()
        if "error" in data:
            self._append(f"Error: {data['error']}", color=APP_DANGER, bold=True)
            return

        self._append(f"📚 کاربرد زمان: {tense_name}\n", size=13, bold=True, color=APP_TEXT)
        self._append(
            f"{data.get('explanation', '') or ''}\n",
            family="Tahoma",
            size=11,
            color=APP_MUTED,
            align=Qt.AlignRight,
            rtl=True,
        )
        self._append("💡 ۳ مثال روزمره:\n", size=13, bold=True, color=APP_TEXT, align=Qt.AlignLeft)

        for i, ex in enumerate(data.get("examples", []), 1):
            self._append(f"{i}. {ex.get('en', '')}\n", size=12, bold=True, color=APP_SUCCESS)
            self._append(
                f"{ex.get('fa', '') or ''}\n",
                family="Tahoma",
                size=10,
                color=APP_MUTED,
                align=Qt.AlignRight,
                rtl=True,
            )


# ==========================================
# Main window
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ultimate English AI Assistant")
        self.resize(1280, 760)

        self._ui = UiInvoker()

        self.font_title = QFont("Segoe UI", 11, QFont.Bold)
        self.font_bold = QFont("Segoe UI", 12, QFont.Bold)
        self.font_en = QFont("Segoe UI", 12)
        self.font_fa = QFont("Tahoma", 11)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(10, 10, 10, 10)

        notebook = QTabWidget()
        outer.addWidget(notebook)

        # --- Tab 1: 12 Tenses ---
        tab1 = QWidget()
        notebook.addTab(tab1, "📅 12 Tenses Generator")
        t1 = QVBoxLayout(tab1)
        t1.setContentsMargins(20, 15, 20, 20)

        hint1 = QLabel("Enter a short English text (e.g. I did):")
        hint1.setFont(self.font_title)
        hint1.setStyleSheet(f"color: {APP_MUTED};")
        t1.addWidget(hint1)

        self.input_text1 = QPlainTextEdit()
        self.input_text1.setFont(self.font_en)
        self.input_text1.setFixedHeight(80)
        t1.addWidget(self.input_text1)

        self.submit_btn1 = QPushButton("✨ Generate 12 Tenses")
        self.submit_btn1.setFont(self.font_title)
        self.submit_btn1.setCursor(Qt.PointingHandCursor)
        self.submit_btn1.setStyleSheet(
            f"QPushButton {{ background: {APP_ACCENT}; color: white; border: none; "
            f"padding: 8px 20px; border-radius: 6px; }}"
            f"QPushButton:hover {{ background: {APP_ACCENT_HOVER}; }}"
            f"QPushButton:disabled {{ background: {APP_BORDER}; color: {APP_MUTED}; }}"
        )
        self.submit_btn1.clicked.connect(self.process_tenses)
        btn_row1 = QHBoxLayout()
        btn_row1.addStretch()
        btn_row1.addWidget(self.submit_btn1)
        btn_row1.addStretch()
        t1.addLayout(btn_row1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid_layout = QGridLayout(self.grid_host)
        self.grid_layout.setContentsMargins(10, 0, 10, 0)
        self.grid_layout.setSpacing(10)
        scroll.setWidget(self.grid_host)
        t1.addWidget(scroll, 1)

        # --- Tab 2: Grammar/Spell Fixer ---
        tab2 = QWidget()
        notebook.addTab(tab2, "📝 Grammar/Spell Fixer")
        t2 = QVBoxLayout(tab2)
        t2.setContentsMargins(20, 15, 20, 20)

        hint2 = QLabel(
            "Persian → American English (B2): Friendly / Formal / Neutral styles"
        )
        hint2.setFont(self.font_title)
        hint2.setStyleSheet(f"color: {APP_MUTED};")
        t2.addWidget(hint2)

        self.input_text2 = QPlainTextEdit()
        self.input_text2.setFont(self.font_en)
        self.input_text2.setFixedHeight(80)
        t2.addWidget(self.input_text2)

        lang_row = QHBoxLayout()
        from_lbl = QLabel("From")
        from_lbl.setStyleSheet(f"color: {APP_MUTED}; font-weight: bold;")
        self.grammar_from_combo = QComboBox()
        self.grammar_from_combo.addItems(GRAMMAR_LANGUAGES)
        self.grammar_from_combo.setCurrentText(DEFAULT_GRAMMAR_FROM)
        self.grammar_from_combo.setMinimumWidth(140)
        self.grammar_from_combo.setToolTip("Language of the text you typed")

        swap_btn = QPushButton("⇄")
        swap_btn.setFixedWidth(36)
        swap_btn.setCursor(Qt.PointingHandCursor)
        swap_btn.setToolTip("Swap From / To")
        swap_btn.setStyleSheet(
            f"QPushButton {{ background: {APP_SURFACE}; color: {APP_TEXT}; "
            f"border: 1px solid {APP_BORDER}; border-radius: 6px; padding: 4px; }}"
            f"QPushButton:hover {{ background: {APP_SURFACE_RAISED}; border-color: {APP_ACCENT}; }}"
        )
        swap_btn.clicked.connect(self._swap_grammar_langs)

        to_lbl = QLabel("To")
        to_lbl.setStyleSheet(f"color: {APP_MUTED}; font-weight: bold;")
        self.grammar_to_combo = QComboBox()
        self.grammar_to_combo.addItems(GRAMMAR_LANGUAGES)
        self.grammar_to_combo.setCurrentText(DEFAULT_GRAMMAR_TO)
        self.grammar_to_combo.setMinimumWidth(140)
        self.grammar_to_combo.setToolTip("Language to translate into")

        lang_row.addWidget(from_lbl)
        lang_row.addWidget(self.grammar_from_combo)
        lang_row.addWidget(swap_btn)
        lang_row.addWidget(to_lbl)
        lang_row.addWidget(self.grammar_to_combo)
        lang_row.addStretch()
        t2.addLayout(lang_row)

        self.submit_btn2 = QPushButton("✨ Translate with Styles")
        self.submit_btn2.setFont(self.font_title)
        self.submit_btn2.setCursor(Qt.PointingHandCursor)
        self.submit_btn2.setStyleSheet(
            f"QPushButton {{ background: {APP_SUCCESS}; color: white; border: none; "
            f"padding: 8px 20px; border-radius: 6px; }}"
            f"QPushButton:hover {{ background: {APP_SUCCESS_HOVER}; }}"
            f"QPushButton:disabled {{ background: {APP_BORDER}; color: {APP_MUTED}; }}"
        )
        self.submit_btn2.clicked.connect(self.process_grammar)
        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()
        btn_row2.addWidget(self.submit_btn2)
        btn_row2.addStretch()
        t2.addLayout(btn_row2)

        self.output_text2 = QTextEdit()
        self.output_text2.setReadOnly(True)
        self.output_text2.setFont(self.font_en)
        t2.addWidget(self.output_text2, 1)

        notebook.setCurrentIndex(1)

    # ----- tenses -----
    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def process_tenses(self):
        user_input = self.input_text1.toPlainText().strip()
        if not user_input:
            QMessageBox.warning(self, "Warning", "Please enter a text first!")
            return

        self.submit_btn1.setEnabled(False)
        self.submit_btn1.setText("⏳ Generating...")
        self._clear_grid()
        wait = QLabel("Asking AI... Please wait.")
        wait.setFont(QFont("Segoe UI", 12))
        wait.setStyleSheet(f"color: {APP_MUTED};")
        self.grid_layout.addWidget(wait, 0, 0)

        def fetch():
            result = get_tenses_from_ai(user_input)
            self._ui.call(lambda: self.update_tenses_ui(result))

        threading.Thread(target=fetch, daemon=True).start()

    def update_tenses_ui(self, data):
        self._clear_grid()
        self.submit_btn1.setEnabled(True)
        self.submit_btn1.setText("✨ Generate 12 Tenses")

        if isinstance(data, dict) and "error" in data:
            err = QLabel(f"Error: {data['error']}")
            err.setStyleSheet(f"color: {APP_DANGER};")
            self.grid_layout.addWidget(err, 0, 0)
            return

        col_count = 5
        for i, item in enumerate(data):
            row, col = i // col_count, i % col_count
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: {APP_SURFACE}; border: 1px solid {APP_BORDER}; "
                f"border-radius: 8px; }}"
            )
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 15, 15, 15)

            header = QHBoxLayout()
            lbl_tense = QLabel(item.get("tense", ""))
            lbl_tense.setFont(self.font_bold)
            lbl_tense.setStyleSheet(
                f"color: {APP_TEXT}; border: none; background: transparent;"
            )
            btn_info = QPushButton("ℹ️")
            btn_info.setCursor(Qt.PointingHandCursor)
            btn_info.setFlat(True)
            btn_info.setStyleSheet(
                f"QPushButton {{ color: {APP_LINK}; background: transparent; "
                f"border: none; font-size: 12pt; }}"
            )
            tense_name = item.get("tense", "")
            btn_info.clicked.connect(lambda _=False, t=tense_name: self.open_tense_info(t))
            header.addWidget(lbl_tense)
            header.addStretch()
            header.addWidget(btn_info)
            card_layout.addLayout(header)

            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background: {APP_BORDER}; border: none;")
            card_layout.addWidget(sep)

            en = QLabel(item.get("english", ""))
            en.setFont(self.font_en)
            en.setWordWrap(True)
            en.setStyleSheet(
                f"color: {APP_TEXT}; border: none; background: transparent;"
            )
            en.setAlignment(Qt.AlignLeft)
            card_layout.addWidget(en)

            fa = QLabel(item.get("persian", "") or "")
            fa.setFont(self.font_fa)
            fa.setWordWrap(True)
            fa.setStyleSheet(
                f"color: {APP_MUTED}; border: none; background: transparent;"
            )
            apply_rtl(fa, True)
            card_layout.addWidget(fa)

            self.grid_layout.addWidget(card, row, col)

    def open_tense_info(self, tense_name):
        dlg = TenseInfoDialog(tense_name, self._ui, parent=self)
        dlg.show()

    # ----- styled translate -----
    def _swap_grammar_langs(self):
        fr = self.grammar_from_combo.currentText()
        to = self.grammar_to_combo.currentText()
        self.grammar_from_combo.setCurrentText(to)
        self.grammar_to_combo.setCurrentText(fr)

    def process_grammar(self):
        user_input = self.input_text2.toPlainText().strip()
        if not user_input:
            QMessageBox.warning(self, "Warning", "Please enter text first!")
            return

        from_lang = self.grammar_from_combo.currentText() or DEFAULT_GRAMMAR_FROM
        to_lang = self.grammar_to_combo.currentText() or DEFAULT_GRAMMAR_TO
        self.submit_btn2.setEnabled(False)
        self.submit_btn2.setText("⏳ Translating...")
        self.output_text2.clear()
        self.output_text2.setPlainText(
            f"Translating {from_lang} → {to_lang} in 3 styles... Please wait."
        )

        def fetch():
            result = get_styled_translations_from_ai(
                user_input, from_lang=from_lang, to_lang=to_lang
            )
            self._ui.call(
                lambda: self.update_grammar_ui(
                    result, from_lang=from_lang, to_lang=to_lang
                )
            )

        threading.Thread(target=fetch, daemon=True).start()

    def _grammar_append(self, text, *, family="Segoe UI", size=12, bold=False, color=None, align=None, rtl=False):
        if color is None:
            color = APP_TEXT
        cursor = self.output_text2.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        font = QFont(family, size)
        font.setBold(bold)
        fmt.setFont(font)
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        block = cursor.blockFormat()
        if align is not None:
            block.setAlignment(align)
        block.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        cursor.setBlockFormat(block)
        cursor.insertText(text)
        self.output_text2.setTextCursor(cursor)

    def update_grammar_ui(
        self,
        data,
        from_lang=DEFAULT_GRAMMAR_FROM,
        to_lang=DEFAULT_GRAMMAR_TO,
    ):
        self.submit_btn2.setEnabled(True)
        self.submit_btn2.setText("✨ Translate with Styles")
        self.output_text2.clear()

        if "error" in data:
            self._grammar_append(f"Error: {data['error']}", bold=True, color=APP_DANGER)
            return

        used_from = data.get("from_lang") or from_lang
        used_to = data.get("to_lang") or to_lang
        wants_translation = bool(data.get("wants_translation", used_from != used_to))
        from_is_rtl = used_from in RTL_TARGETS
        to_is_rtl = used_to in RTL_TARGETS
        notes = (data.get("grammar_notes") or "").strip()

        if notes:
            self._grammar_append("Grammar notes:\n", bold=True, color=APP_LINK)
            self._grammar_append(f"{notes}\n\n", color=APP_MUTED)

        for i, (label, key) in enumerate(STYLE_VARIANTS):
            pair = data.get(key) or {}
            if isinstance(pair, str):
                from_text, to_text = pair.strip(), ""
            else:
                from_text = (pair.get("from") or "").strip() or "(empty)"
                to_text = (pair.get("to") or "").strip()

            self._grammar_append(f"{label}:\n", bold=True, color=APP_LINK)
            self._grammar_append("[From]: ", bold=True, color=APP_MUTED)
            self._grammar_append(
                f"{from_text}\n",
                family="Tahoma" if from_is_rtl else "Segoe UI",
                color=APP_TEXT,
                align=Qt.AlignRight if from_is_rtl else Qt.AlignLeft,
                rtl=from_is_rtl,
            )
            if wants_translation:
                self._grammar_append("[To]: ", bold=True, color=APP_MUTED)
                self._grammar_append(
                    f"{(to_text or '(empty)')}\n",
                    family="Tahoma" if to_is_rtl else "Segoe UI",
                    color=APP_TEXT,
                    align=Qt.AlignRight if to_is_rtl else Qt.AlignLeft,
                    rtl=to_is_rtl,
                )
            if i < len(STYLE_VARIANTS) - 1:
                self._grammar_append("\n")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)

    # Fail clearly at startup if auth is missing (no traceback / no token leak).
    try:
        get_hf_token(required=True)
    except ConfigError as exc:
        QMessageBox.critical(None, "HF_TOKEN required", str(exc))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
