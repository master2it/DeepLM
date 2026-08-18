"use client";

import { useEffect, useState } from "react";
import { ArrowLeftRight } from "lucide-react";
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
  fetchLanguages,
  postGrammar,
  type GrammarResult,
  type LanguagesPayload,
  type ProviderId,
  type StylePair,
  MAX_INPUT_CHARS,
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
  provider,
  groqApiKey,
  hfApiKey,
}: {
  provider: ProviderId;
  groqApiKey: string;
  hfApiKey: string;
}) {
  const [meta, setMeta] = useState<LanguagesPayload | null>(null);
  const [text, setText] = useState("");
  const [fromLang, setFromLang] = useState("English");
  const [toLang, setToLang] = useState("Persian");
  const [toLocale, setToLocale] = useState("Iranian Persian");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GrammarResult | null>(null);
  const [history, setHistory] = useState<GrammarHistoryItem[]>([]);

  useEffect(() => {
    setHistory(readGrammarHistory());
    fetchLanguages()
      .then((data) => {
        setMeta(data);
        setFromLang(data.default_from);
        setToLang(data.default_to);
        setToLocale(
          data.default_locales?.[data.default_to] ||
            data.locales?.[data.default_to]?.[0] ||
            data.default_to
        );
      })
      .catch((e) => setError(e.message));
  }, []);

  const rtl = new Set(meta?.rtl ?? ["Persian", "Arabic"]);
  const localeOptions = localesFor(meta, toLang);

  function changeToLang(next: string) {
    setToLang(next);
    setToLocale(defaultLocaleFor(meta, next));
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
        to_locale: toLocale,
        provider,
        groq_api_key: groqApiKey,
        hf_api_key: hfApiKey,
      });
      setResult(data);
      setHistory(
        pushGrammarHistory({
          text: text.trim(),
          from_lang: fromLang,
          to_lang: toLang,
          to_locale: toLocale,
          provider: data.provider,
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

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <p className="text-sm text-zinc-400">
        Understands what you mean, then Grammar Fix, Native, Friendly / Casual, and Professional in{" "}
        {toLocale}.
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
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <div className="w-full space-y-1 sm:min-w-40 sm:flex-1">
          <Label>From</Label>
          <Select value={fromLang} onValueChange={setFromLang}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(meta?.languages ?? [fromLang]).map((lang) => (
                <SelectItem key={lang} value={lang}>
                  {lang}
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
          className="mx-auto sm:mx-0"
          onClick={() => {
            const nextTo = fromLang;
            setFromLang(toLang);
            changeToLang(nextTo);
          }}
        >
          <ArrowLeftRight className="h-4 w-4 rotate-90 sm:rotate-0" />
        </Button>
        <div className="w-full space-y-1 sm:min-w-40 sm:flex-1">
          <Label>To</Label>
          <Select value={toLang} onValueChange={changeToLang}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(meta?.languages ?? [toLang]).map((lang) => (
                <SelectItem key={lang} value={lang}>
                  {lang}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-full space-y-1 sm:min-w-44 sm:flex-1">
          <Label>Locale</Label>
          <Select
            value={localeOptions.includes(toLocale) ? toLocale : localeOptions[0]}
            onValueChange={setToLocale}
          >
            <SelectTrigger>
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
        <Button type="submit" variant="success" disabled={loading} className="w-full sm:w-auto">
          {loading ? "Translating…" : "Translate"}
        </Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <SearchHistory
        items={history.map((item) => ({
          id: item.id,
          at: item.at,
          title: item.text,
          subtitle: `${item.from_lang} → ${item.to_lang}${
            item.to_locale ? ` (${item.to_locale})` : ""
          }${item.provider ? ` · ${item.provider}` : ""} · ${formatHistoryTime(item.at)}`,
        }))}
        onSelect={(id) => {
          const item = history.find((row) => row.id === id);
          if (!item) return;
          setText(item.text);
          setFromLang(item.from_lang);
          setToLang(item.to_lang);
          if (item.to_locale) setToLocale(item.to_locale);
          else setToLocale(defaultLocaleFor(meta, item.to_lang));
          setResult(item.result);
          setError(null);
        }}
        onRemove={(id) => setHistory(removeGrammarHistory(id))}
        onClear={() => {
          clearGrammarHistory();
          setHistory([]);
        }}
      />
      {result && (
        <div className="space-y-4">
          {result.provider && <Badge>via {result.provider}</Badge>}
          {STYLE_KEYS.map(({ key, label }) => {
            const pair = stylePair(result, key);
            const enhanced = pair.grammarEnhanced || pair.from || "";
            const translated = pair.translated || pair.to || "";
            const version = result.wants_translation
              ? translated
              : enhanced || translated;
            return (
              <Card key={key}>
                <CardHeader>
                  <CardTitle className="text-blue-400"># {label}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 overflow-hidden text-sm">
                  {result.wants_translation && enhanced && (
                    <div className="break-words whitespace-pre-wrap">
                      <span className="text-zinc-500">Grammar enhanced</span>
                      <span
                        dir={rtl.has(result.from_lang) ? "rtl" : "ltr"}
                        className="mt-1 block whitespace-pre-wrap text-zinc-300"
                      >
                        {enhanced}
                      </span>
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
                </CardContent>
              </Card>
            );
          })}
          {result.grammarNotes && result.grammarNotes.length > 0 ? (
            <Card className="border-amber-800 bg-zinc-950">
              <CardHeader>
                <CardTitle className="text-amber-400">Grammar Notes</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-zinc-300">
                {result.grammarNotes.map((note, i) => (
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
                ))}
              </CardContent>
            </Card>
          ) : result.grammar_notes ? (
            <Card className="border-amber-800 bg-zinc-950">
              <CardHeader>
                <CardTitle className="text-amber-400">Grammar Notes</CardTitle>
              </CardHeader>
              <CardContent className="whitespace-pre-wrap break-words text-sm text-zinc-300">
                {result.grammar_notes}
              </CardContent>
            </Card>
          ) : null}
        </div>
      )}
    </form>
  );
}
