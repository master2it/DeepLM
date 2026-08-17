"use client";

import { useState } from "react";
import { Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { postTenseExplain, postTenses, type ProviderId, type TenseItem } from "@/lib/api";

export function TensesGenerator({
  provider,
  groqApiKey,
}: {
  provider: ProviderId;
  groqApiKey: string;
}) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<TenseItem[]>([]);
  const [usedProvider, setUsedProvider] = useState<string | null>(null);
  const [infoOpen, setInfoOpen] = useState(false);
  const [infoTitle, setInfoTitle] = useState("");
  const [infoBody, setInfoBody] = useState("");
  const [infoLoading, setInfoLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) {
      setError("Please enter a text first.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await postTenses(text.trim(), provider, groqApiKey);
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
      const data = await postTenseExplain(tense, provider, groqApiKey);
      const examples = (data.examples || [])
        .map((ex, i) => `${i + 1}. ${ex.en}\n${ex.fa}`)
        .join("\n\n");
      setInfoBody(`${data.explanation || ""}\n\n${examples}`.trim());
    } catch (err) {
      setInfoBody(err instanceof Error ? err.message : "Failed to load explanation");
    } finally {
      setInfoLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={onSubmit} className="space-y-3">
        <p className="text-sm text-zinc-400">Enter a short English text (e.g. I did):</p>
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="I did"
        />
        <Button type="submit" disabled={loading}>
          {loading ? "Generating…" : "Generate 12 Tenses"}
        </Button>
      </form>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {usedProvider && <Badge>via {usedProvider}</Badge>}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {items.map((item) => (
          <Card key={item.tense}>
            <CardHeader className="flex-row items-start justify-between space-y-0">
              <CardTitle className="pr-2">{item.tense}</CardTitle>
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
            <CardContent className="space-y-2 text-sm">
              <p>{item.english}</p>
              <p dir="rtl" className="text-zinc-400">
                {item.persian}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Dialog open={infoOpen} onOpenChange={setInfoOpen}>
        <DialogContent className="max-h-[80vh] overflow-y-auto max-w-xl">
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
