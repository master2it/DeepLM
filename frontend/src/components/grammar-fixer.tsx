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
  { key: "friendly_casual" as const, label: "Friendly / Casual" },
  { key: "professional_formal" as const, label: "Professional / Formal" },
  { key: "everyday_neutral" as const, label: "Everyday / Neutral" },
];

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
      })
      .catch((e) => setError(e.message));
  }, []);

  const rtl = new Set(meta?.rtl ?? ["Persian", "Arabic"]);

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
        {fromLang} → {toLang}: Friendly / Formal / Neutral styles
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
            setFromLang(toLang);
            setToLang(fromLang);
          }}
        >
          <ArrowLeftRight className="h-4 w-4 rotate-90 sm:rotate-0" />
        </Button>
        <div className="w-full space-y-1 sm:min-w-40 sm:flex-1">
          <Label>To</Label>
          <Select value={toLang} onValueChange={setToLang}>
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
            item.provider ? ` · ${item.provider}` : ""
          } · ${formatHistoryTime(item.at)}`,
        }))}
        onSelect={(id) => {
          const item = history.find((row) => row.id === id);
          if (!item) return;
          setText(item.text);
          setFromLang(item.from_lang);
          setToLang(item.to_lang);
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
          {result.grammar_notes && (
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-400">Grammar notes</CardTitle>
              </CardHeader>
              <CardContent className="whitespace-pre-wrap break-words text-sm text-zinc-300">
                {result.grammar_notes}
              </CardContent>
            </Card>
          )}
          {STYLE_KEYS.map(({ key, label }) => {
            const pair = result[key];
            return (
              <Card key={key}>
                <CardHeader>
                  <CardTitle className="text-blue-400">{label}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 overflow-hidden text-sm">
                  <p className="break-words">
                    <span className="text-zinc-400">[From]: </span>
                    <span dir={rtl.has(result.from_lang) ? "rtl" : "ltr"} className="inline">
                      {pair.from || "(empty)"}
                    </span>
                  </p>
                  {result.wants_translation && (
                    <p className="break-words">
                      <span className="text-zinc-400">[To]: </span>
                      <span dir={rtl.has(result.to_lang) ? "rtl" : "ltr"} className="inline">
                        {pair.to || "(empty)"}
                      </span>
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </form>
  );
}
