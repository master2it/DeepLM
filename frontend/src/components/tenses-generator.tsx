"use client";

import { useEffect, useState } from "react";
import { Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
  postTenseExplain,
  postTenses,
  readStoredTenseLanguage,
  writeStoredTenseLanguage,
  DEFAULT_TENSE_COUNTS,
  MAX_INPUT_CHARS,
  type ProviderId,
  type TenseItem,
  type TenseLanguage,
  type TenseExample,
} from "@/lib/api";
import {
  formatHistoryTime,
  SearchHistory,
} from "@/components/search-history";
import {
  clearTensesHistory,
  pushTensesHistory,
  readTensesHistory,
  removeTensesHistory,
  type TensesHistoryItem,
} from "@/lib/search-history";

export function TensesGenerator({
  provider,
  groqApiKey,
  hfApiKey,
}: {
  provider: ProviderId;
  groqApiKey: string;
  hfApiKey: string;
}) {
  const [languages, setLanguages] = useState<string[]>(["English", "German"]);
  const [tenseCounts, setTenseCounts] = useState<Record<string, number>>(
    DEFAULT_TENSE_COUNTS
  );
  const [language, setLanguage] = useState<TenseLanguage>("English");
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<TenseItem[]>([]);
  const [usedProvider, setUsedProvider] = useState<string | null>(null);
  const [infoOpen, setInfoOpen] = useState(false);
  const [infoTitle, setInfoTitle] = useState("");
  const [infoBody, setInfoBody] = useState("");
  const [infoExamples, setInfoExamples] = useState<TenseExample[]>([]);
  const [infoLoading, setInfoLoading] = useState(false);
  const [history, setHistory] = useState<TensesHistoryItem[]>([]);

  useEffect(() => {
    setHistory(readTensesHistory());
    setLanguage(readStoredTenseLanguage());
    fetchLanguages()
      .then((data) => {
        if (data.tense_languages?.length) {
          setLanguages(data.tense_languages);
        }
        if (data.tense_counts) {
          setTenseCounts({ ...DEFAULT_TENSE_COUNTS, ...data.tense_counts });
        }
      })
      .catch(() => {});
  }, []);

  function onLanguageChange(next: string) {
    const lang = next === "German" ? "German" : "English";
    setLanguage(lang);
    writeStoredTenseLanguage(lang);
    setItems([]);
    setUsedProvider(null);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) {
      setError("Please enter a text first.");
      return;
    }
    if (text.trim().length > MAX_INPUT_CHARS) {
      setError(`Text must be at most ${MAX_INPUT_CHARS} characters.`);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await postTenses(
        text.trim(),
        provider,
        groqApiKey,
        language,
        hfApiKey
      );
      const itemsOut = data.items || [];
      setItems(itemsOut);
      setUsedProvider(data.provider || null);
      setHistory(
        pushTensesHistory({
          text: text.trim(),
          language,
          provider: data.provider,
          items: itemsOut,
        })
      );
    } catch (err) {
      setItems([]);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function openInfo(item: TenseItem) {
    setInfoTitle(item.tense);
    setInfoOpen(true);
    setInfoLoading(true);
    setInfoBody("");
    setInfoExamples([]);
    try {
      const data = await postTenseExplain(
        item.tense,
        provider,
        groqApiKey,
        language,
        hfApiKey,
        text.trim(),
        item.text
      );
      setInfoBody((data.explanation || "").trim());
      setInfoExamples(data.examples || []);
    } catch (err) {
      setInfoBody(err instanceof Error ? err.message : "Failed to load explanation");
      setInfoExamples([]);
    } finally {
      setInfoLoading(false);
    }
  }

  const placeholder = language === "German" ? "Ich arbeite" : "I did";
  const tenseCount = tenseCounts[language] ?? DEFAULT_TENSE_COUNTS[language];
  function labelFor(lang: string) {
    const n = tenseCounts[lang] ?? (lang === "German" ? 6 : 12);
    return `${lang} (${n} ${n === 1 ? "tense" : "tenses"})`;
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onSubmit} className="space-y-3">
        <div className="w-full max-w-sm space-y-1">
          <Label>Language</Label>
          <Select value={language} onValueChange={onLanguageChange}>
            <SelectTrigger>
              <SelectValue>{labelFor(language)}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang} value={lang}>
                  {labelFor(lang)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <p className="text-sm text-zinc-400">
          {language === "German"
            ? `German has ${tenseCount} tenses: Präsens, Präteritum, Perfekt, Plusquamperfekt, Futur I, Futur II. Enter a short German (or English) phrase.`
            : `English has ${tenseCount} tenses. Enter a short English text. You get Persian on every card.`}
        </p>
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value.slice(0, MAX_INPUT_CHARS))}
          placeholder={placeholder}
          maxLength={MAX_INPUT_CHARS}
        />
        <p className="text-xs text-zinc-500">
          {text.length} / {MAX_INPUT_CHARS} characters
        </p>
        <Button type="submit" disabled={loading} className="w-full sm:w-auto">
          {loading
            ? "Generating…"
            : `Generate ${tenseCount} Tenses`}
        </Button>
      </form>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <SearchHistory
        items={history.map((item) => ({
          id: item.id,
          at: item.at,
          title: item.text,
          subtitle: `${item.language}${
            item.provider ? ` · ${item.provider}` : ""
          } · ${formatHistoryTime(item.at)}`,
        }))}
        onSelect={(id) => {
          const item = history.find((row) => row.id === id);
          if (!item) return;
          setText(item.text);
          setLanguage(item.language);
          writeStoredTenseLanguage(item.language);
          setItems(item.items);
          setUsedProvider(item.provider || null);
          setError(null);
        }}
        onRemove={(id) => setHistory(removeTensesHistory(id))}
        onClear={() => {
          clearTensesHistory();
          setHistory([]);
        }}
      />
      {usedProvider && (
        <Badge>
          via {usedProvider} · {language} · {tenseCount} tenses
        </Badge>
      )}
      {!loading && usedProvider && items.length === 0 && (
        <p className="text-sm text-amber-400">
          No tense cards were returned. Try again with a short phrase.
        </p>
      )}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <Card
            key={item.key || item.tense}
            role="button"
            tabIndex={0}
            className="cursor-pointer transition-colors hover:border-zinc-500"
            onClick={() => openInfo(item)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                openInfo(item);
              }
            }}
          >
            <CardHeader className="flex-row items-start justify-between space-y-0 gap-2">
              <CardTitle className="min-w-0 flex-1 break-words pr-2 text-sm sm:text-base">
                {item.tense}
              </CardTitle>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-blue-400"
                aria-label={`Explain ${item.tense}`}
                onClick={(e) => {
                  e.stopPropagation();
                  openInfo(item);
                }}
              >
                <Info className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-2 overflow-hidden text-sm">
              <p className="break-words" dir="ltr">
                {item.text}
              </p>
              {item.english && (
                <p className="break-words text-zinc-300" dir="ltr">
                  {item.english}
                </p>
              )}
              <p dir="rtl" className="break-words text-zinc-400">
                {item.persian}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Dialog open={infoOpen} onOpenChange={setInfoOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Tense explanation: {infoTitle}</DialogTitle>
          </DialogHeader>
          {infoLoading ? (
            <p className="text-sm text-zinc-300">Getting details…</p>
          ) : (
            <div className="space-y-4 text-sm text-zinc-300">
              {infoBody && (
                <p className="whitespace-pre-wrap" dir="auto">
                  {infoBody}
                </p>
              )}
              {infoExamples.length > 0 && (
                <div className="space-y-3">
                  <p className="font-medium text-zinc-100">Examples</p>
                  <ol className="list-decimal space-y-3 ps-5">
                    {infoExamples.map((ex, i) => (
                      <li key={i} className="space-y-1">
                        <p className="break-words text-zinc-100" dir="ltr">
                          {ex.text || ex.en || ""}
                        </p>
                        {ex.english && (
                          <p className="break-words text-zinc-300" dir="ltr">
                            {ex.english}
                          </p>
                        )}
                        {ex.fa && (
                          <p className="break-words text-zinc-400" dir="rtl">
                            {ex.fa}
                          </p>
                        )}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
