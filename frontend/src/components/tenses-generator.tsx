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
  type ProviderId,
  type TenseItem,
  type TenseLanguage,
} from "@/lib/api";

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
  const [infoLoading, setInfoLoading] = useState(false);

  useEffect(() => {
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
      setItems(data.items || []);
      setUsedProvider(data.provider || null);
    } catch (err) {
      setItems([]);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function openInfo(tense: string) {
    setInfoTitle(tense);
    setInfoOpen(true);
    setInfoLoading(true);
    setInfoBody("");
    try {
      const data = await postTenseExplain(
        tense,
        provider,
        groqApiKey,
        language,
        hfApiKey
      );
      const examples = (data.examples || [])
        .map((ex, i) => {
          const de = ex.text || ex.en || "";
          const en = ex.english ? `\n${ex.english}` : "";
          return `${i + 1}. ${de}${en}\n${ex.fa}`;
        })
        .join("\n\n");
      setInfoBody(`${data.explanation || ""}\n\n${examples}`.trim());
    } catch (err) {
      setInfoBody(err instanceof Error ? err.message : "Failed to load explanation");
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
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
        />
        <Button type="submit" disabled={loading} className="w-full sm:w-auto">
          {loading
            ? "Generating…"
            : `Generate ${tenseCount} Tenses`}
        </Button>
      </form>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {usedProvider && (
        <Badge>
          via {usedProvider} · {language} · {tenseCount} tenses
        </Badge>
      )}
      <div
        className={
          language === "German"
            ? "grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
            : "grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5"
        }
      >
        {items.map((item) => (
          <Card key={item.key || item.tense}>
            <CardHeader className="flex-row items-start justify-between space-y-0 gap-2">
              <CardTitle className="min-w-0 flex-1 break-words pr-2 text-sm sm:text-base">
                {item.tense}
              </CardTitle>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-blue-400"
                onClick={() => openInfo(item.tense)}
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
          <p className="whitespace-pre-wrap text-sm text-zinc-300" dir="auto">
            {infoLoading ? "Getting details…" : infoBody}
          </p>
        </DialogContent>
      </Dialog>
    </div>
  );
}
