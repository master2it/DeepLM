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
} from "@/lib/api";

const STYLE_KEYS = [
  { key: "friendly_casual" as const, label: "Friendly / Casual" },
  { key: "professional_formal" as const, label: "Professional / Formal" },
  { key: "everyday_neutral" as const, label: "Everyday / Neutral" },
];

export function GrammarFixer({
  provider,
  groqApiKey,
}: {
  provider: ProviderId;
  groqApiKey: string;
}) {
  const [meta, setMeta] = useState<LanguagesPayload | null>(null);
  const [text, setText] = useState("");
  const [fromLang, setFromLang] = useState("Persian");
  const [toLang, setToLang] = useState("English");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GrammarResult | null>(null);

  useEffect(() => {
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
    setLoading(true);
    setError(null);
    try {
      const data = await postGrammar({
        text: text.trim(),
        from_lang: fromLang,
        to_lang: toLang,
        provider,
        groq_api_key: groqApiKey,
      });
      setResult(data);
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
        Persian → American English (B2): Friendly / Formal / Neutral styles
      </p>
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter Persian (or other) text…"
        dir={rtl.has(fromLang) ? "rtl" : "ltr"}
        className="min-h-[100px]"
      />
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[160px] space-y-1">
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
          onClick={() => {
            setFromLang(toLang);
            setToLang(fromLang);
          }}
        >
          <ArrowLeftRight className="h-4 w-4" />
        </Button>
        <div className="min-w-[160px] space-y-1">
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
        <Button type="submit" variant="success" disabled={loading}>
          {loading ? "Translating…" : "Translate with Styles"}
        </Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {result && (
        <div className="space-y-4">
          {result.provider && <Badge>via {result.provider}</Badge>}
          {result.grammar_notes && (
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-400">Grammar notes</CardTitle>
              </CardHeader>
              <CardContent className="whitespace-pre-wrap text-sm text-zinc-300">
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
                <CardContent className="space-y-2 text-sm">
                  <p>
                    <span className="text-zinc-400">[From]: </span>
                    <span dir={rtl.has(result.from_lang) ? "rtl" : "ltr"} className="inline-block">
                      {pair.from || "(empty)"}
                    </span>
                  </p>
                  {result.wants_translation && (
                    <p>
                      <span className="text-zinc-400">[To]: </span>
                      <span dir={rtl.has(result.to_lang) ? "rtl" : "ltr"} className="inline-block">
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
