"use client";

import { useEffect, useState } from "react";
import { GrammarFixer } from "@/components/grammar-fixer";
import { TensesGenerator } from "@/components/tenses-generator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { fetchHealth } from "@/lib/api";

export default function HomePage() {
  const [health, setHealth] = useState<{
    ollama: boolean;
    hf_configured: boolean;
    ollama_model: string;
  } | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">DeepLM</h1>
          <p className="text-sm text-zinc-400">
            Grammar fixer and 12 tenses — Ollama first, Hugging Face fallback
          </p>
        </div>
        {health && (
          <div className="flex gap-2">
            <Badge>{health.ollama ? `Ollama: ${health.ollama_model}` : "Ollama: offline"}</Badge>
            <Badge>{health.hf_configured ? "HF: ready" : "HF: not set"}</Badge>
          </div>
        )}
      </header>
      <Tabs defaultValue="grammar">
        <TabsList>
          <TabsTrigger value="grammar">Grammar/Spell Fixer</TabsTrigger>
          <TabsTrigger value="tenses">12 Tenses Generator</TabsTrigger>
        </TabsList>
        <TabsContent value="grammar">
          <GrammarFixer />
        </TabsContent>
        <TabsContent value="tenses">
          <TensesGenerator />
        </TabsContent>
      </Tabs>
    </main>
  );
}
