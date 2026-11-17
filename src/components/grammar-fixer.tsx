"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowLeftRight } from "lucide-react";
import { LanguageLabel } from "@/components/language-flag";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  postGrammar,
  type GrammarResult,
  type LanguagesPayload,
  type StylePair,
  MAX_INPUT_CHARS,
  providerModelLabel,
} from "@/lib/api";
import {
  formatHistoryTime,
  SearchHistory,
} from "@/components/search-history";
import {
  clearGrammarHistory,
  pushGrammarHistory,
  readGrammarHistory,
  removeGrammarHistory,
  type GrammarHistoryItem,
} from "@/lib/search-history";

const STYLE_KEYS = [
  { key: "grammarFix" as const, label: "Grammar Fix" },
  { key: "native" as const, label: "Native" },
  { key: "friendly" as const, label: "Friendly / Casual" },
  { key: "professional" as const, label: "Professional" },
  { key: "programmer" as const, label: "Programmer" },
];

function localesFor(meta: LanguagesPayload | null, lang: string): string[] {
  const listed = meta?.locales?.[lang];
  if (listed && listed.length) return listed;
  const fallback = meta?.default_locales?.[lang];
  return fallback ? [fallback] : [lang];
}

function defaultLocaleFor(meta: LanguagesPayload | null, lang: string): string {
  return meta?.default_locales?.[lang] || localesFor(meta, lang)[0] || lang;
}

function stylePair(
  result: GrammarResult,
  key: (typeof STYLE_KEYS)[number]["key"]
): StylePair {
  const direct = result[key];
  if (
    direct?.from ||
    direct?.to ||
    direct?.grammarEnhanced ||
    direct?.translated
  ) {
    return direct;
  }
  if (key === "native") return result.everyday_neutral || { from: "", to: "" };
  if (key === "friendly") return result.friendly_casual || { from: "", to: "" };
  if (key === "professional") {
    return result.professional_formal || { from: "", to: "" };
  }
  return { from: "", to: "" };
}

export function GrammarFixer({
  languages,
}: {
  languages: LanguagesPayload | null;
}) {
  const meta = languages;
  const [text, setText] = useState("");
  const [fromLang, setFromLang] = useState("English");
  const [toLang, setToLang] = useState("Persian");
  const [toLocale, setToLocale] = useState("Iranian Persian");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GrammarResult | null>(null);
  const [history, setHistory] = useState<GrammarHistoryItem[]>([]);
  const [copied, setCopied] = useState(false);
  const copiedTimer = useRef<number | null>(null);
  const swapLock = useRef(0);

  useEffect(() => {
    return () => {
      if (copiedTimer.current) window.clearTimeout(copiedTimer.current);
    };
  }, []);

  async function copyText(value: string) {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      const area = document.createElement("textarea");
      area.value = value;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.left = "-9999px";
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      area.remove();
      if (!ok) return;
    }
    setCopied(true);
    if (copiedTimer.current) window.clearTimeout(copiedTimer.current);
    copiedTimer.current = window.setTimeout(() => setCopied(false), 2000);
  }

  useEffect(() => {
    setHistory(readGrammarHistory());
  }, []);

  useEffect(() => {
    if (!languages) return;
    const from = languages.default_from;
    const to =
      languages.default_to === from
        ? languages.languages.find((lang) => lang !== from) || languages.default_to
        : languages.default_to;
    setFromLang(from);
    setToLang(to);
    setToLocale(defaultLocaleFor(languages, to));
  }, [languages]);

  const rtl = new Set(meta?.rtl ?? ["Persian", "Arabic"]);
  const localeOptions = localesFor(meta, toLang);
  const resolvedToLocale =
    toLocale.trim() && localeOptions.includes(toLocale)
      ? toLocale
      : localeOptions[0] || defaultLocaleFor(meta, toLang);

  useEffect(() => {
    const options = localesFor(meta, toLang);
    if (!options.length) return;
    if (!toLocale.trim() || !options.includes(toLocale)) {
      setToLocale(options[0]);
    }
  }, [meta, toLang, toLocale]);

  const languageOptions = meta?.languages?.length
    ? meta.languages
    : [fromLang, toLang];
  const fromOptions = languageOptions.filter((lang) => lang !== toLang);
  const toOptions = languageOptions.filter((lang) => lang !== fromLang);

  function changeFromLang(next: string) {
    if (swapLock.current || !next || next === toLang) return;
    setFromLang(next);
  }

  function changeToLang(next: string) {
    if (swapLock.current || !next || next === fromLang) return;
    setToLang(next);
    setToLocale(defaultLocaleFor(meta, next));
  }

  function swapLanguages() {
    if (!fromLang || !toLang || fromLang === toLang) return;
    window.clearTimeout(swapLock.current);
    swapLock.current = window.setTimeout(() => {
      swapLock.current = 0;
    }, 100);
    const nextFrom = toLang;
    const nextTo = fromLang;
    setFromLang(nextFrom);
    setToLang(nextTo);
    setToLocale(defaultLocaleFor(meta, nextTo));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) {
      setError("Please enter text first.");
      return;
    }
    if (text.trim().length > MAX_INPUT_CHARS) {
      setError(`Text must be at most ${MAX_INPUT_CHARS} characters.`);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await postGrammar({
        text: text.trim(),
        from_lang: fromLang,
        to_lang: toLang,
        to_locale: resolvedToLocale,
      });
      setResult(data);
      setHistory(
        pushGrammarHistory({
          text: text.trim(),
          from_lang: fromLang,
          to_lang: toLang,
          to_locale: resolvedToLocale,
          provider: "openai",
          result: data,
        })
      );
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  const notes = result?.grammarNotes?.filter(
    (note) => note.original || note.correction || note.explanation
  ) ?? [];

  return (
    <div className="grid items-start gap-4 lg:grid-cols-3">
    <form onSubmit={onSubmit} className="@container min-w-0 space-y-4 lg:col-span-2">
      <p className="text-sm text-zinc-400">
        Understands what you mean, then Grammar Fix, Native, Friendly / Casual, Professional, and Programmer for Slack in{" "}
        {resolvedToLocale}.
        {(fromLang === "German" && toLang === "Persian") ||
        (fromLang === "Persian" && toLang === "German")
          ? " · German ↔ Persian (du/Sie and تو/شما)"
          : ""}
      </p>
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, MAX_INPUT_CHARS))}
        placeholder={`Enter ${fromLang} text…`}
        maxLength={MAX_INPUT_CHARS}
        dir={rtl.has(fromLang) ? "rtl" : "ltr"}
        className="min-h-[100px]"
      />
      <p className="text-xs text-zinc-500">
        {text.length} / {MAX_INPUT_CHARS} characters
      </p>
      <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-end gap-2 @[42rem]:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)_minmax(0,1.1fr)_auto]">
        <div className="min-w-0 space-y-1">
          <Label>From</Label>
          <Select value={fromLang} onValueChange={changeFromLang}>
            <SelectTrigger className="min-w-0 overflow-hidden">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {fromOptions.map((lang) => (
                <SelectItem key={lang} value={lang}>
                  <LanguageLabel language={lang} />
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button
          type="button"
          variant="outline"
          size="icon"
          title="Swap From / To"
          className="shrink-0"
          onClick={swapLanguages}
        >
          <ArrowLeftRight className="h-4 w-4" />
        </Button>
        <div className="min-w-0 space-y-1">
          <Label>To</Label>
          <Select value={toLang} onValueChange={changeToLang}>
            <SelectTrigger className="min-w-0 overflow-hidden">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {toOptions.map((lang) => (
                <SelectItem key={lang} value={lang}>
                  <LanguageLabel language={lang} />
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="col-span-3 min-w-0 space-y-1 @[42rem]:col-span-1">
          <Label>Locale</Label>
          <Select value={resolvedToLocale} onValueChange={setToLocale}>
            <SelectTrigger className="min-w-0 overflow-hidden">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {localeOptions.map((loc) => (
                <SelectItem key={loc} value={loc}>
                  {loc}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button type="submit" variant="success" disabled={loading} className="col-span-3 w-full @[42rem]:col-span-1 @[42rem]:w-auto">
          {loading ? "Translating…" : "Translate"}
        </Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {result && (
        <div className="space-y-4">
          {result.provider && (
            <Badge>
              via {providerModelLabel(result.provider)}
            </Badge>
          )}
          {STYLE_KEYS.map(({ key, label }) => {
            const pair = stylePair(result, key);
            const enhanced = pair.grammarEnhanced || pair.from || "";
            const translated = pair.translated || pair.to || "";
            const version = result.wants_translation
              ? translated
              : enhanced || translated;
            const roman =
              pair.roman ||
              (result.to_lang === "English" ? version : "");
            return (
              <Card key={key}>
                <CardHeader>
                  <CardTitle className="text-blue-400"># {label}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 overflow-hidden text-sm">
                  {result.wants_translation && enhanced && (
                    <div className="break-words whitespace-pre-wrap">
                      <span className="text-zinc-500">Grammar enhanced</span>
                      <button
                        type="button"
                        dir={rtl.has(result.from_lang) ? "rtl" : "ltr"}
                        title="Click to copy"
                        onClick={() => copyText(enhanced)}
                        className="mt-1 block w-full cursor-pointer whitespace-pre-wrap text-start font-bold text-zinc-300 hover:text-white"
                      >
                        {enhanced}
                      </button>
                    </div>
                  )}
                  <div className="break-words whitespace-pre-wrap">
                    {result.wants_translation && (
                      <span className="text-zinc-500">Translated</span>
                    )}
                    <span
                      dir={
                        rtl.has(
                          result.wants_translation ? result.to_lang : result.from_lang
                        )
                          ? "rtl"
                          : "ltr"
                      }
                      className={`block whitespace-pre-wrap text-zinc-100 ${
                        result.wants_translation ? "mt-1" : ""
                      }`}
                    >
                      {version || "(empty)"}
                    </span>
                  </div>
                  <div className="break-words whitespace-pre-wrap">
                    <span className="text-zinc-500">Roman Writing</span>
                    <span dir="ltr" className="mt-1 block whitespace-pre-wrap text-zinc-100">
                      {roman || "(empty)"}
                    </span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
      </form>
      <aside className="min-w-0 space-y-4">
      <SearchHistory
        items={history.map((item) => ({
          id: item.id,
          at: item.at,
          title: item.text,
          subtitle: `${item.from_lang} → ${item.to_lang}${
            item.to_locale ? ` (${item.to_locale})` : ""
          }${
            item.provider
              ? ` · ${providerModelLabel(item.provider)}`
              : ""
          } · ${formatHistoryTime(item.at)}`,
        }))}
        onSelect={(id) => {
          const item = history.find((row) => row.id === id);
          if (!item) return;
          const from = item.from_lang;
          const to =
            item.to_lang === from
              ? (meta?.languages ?? []).find((lang) => lang !== from) || item.to_lang
              : item.to_lang;
          setText(item.text);
          setFromLang(from);
          setToLang(to);
          if (item.to_locale && to === item.to_lang) setToLocale(item.to_locale);
          else setToLocale(defaultLocaleFor(meta, to));
          setResult(item.result);
          setError(null);
        }}
        onRemove={(id) => setHistory(removeGrammarHistory(id))}
        onClear={() => {
          clearGrammarHistory();
          setHistory([]);
        }}
      />
      <Card className="border-amber-800 bg-zinc-950">
        <CardHeader>
          <CardTitle className="text-amber-400">Grammar Notes</CardTitle>
        </CardHeader>
        <CardContent className="max-h-[40vh] space-y-2 overflow-y-auto text-sm text-zinc-300">
          {notes.length > 0 ? (
            notes.map((note, i) => (
              <p key={i} className="whitespace-pre-wrap break-words">
                {note.original && note.correction ? (
                  <>
                    <span className="text-zinc-100">
                      “{note.original}” → “{note.correction}”
                    </span>
                    {note.explanation ? `: ${note.explanation}` : ""}
                  </>
                ) : (
                  note.explanation
                )}
              </p>
            ))
          ) : result?.grammar_notes ? (
            <p className="whitespace-pre-wrap break-words">{result.grammar_notes}</p>
          ) : (
            <p className="text-zinc-500">No grammar notes yet.</p>
          )}
        </CardContent>
      </Card>
      </aside>
      {copied && (
        <div
          role="status"
          className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-900 shadow"
        >
          Copied
        </div>
      )}
    </div>
  );
}
