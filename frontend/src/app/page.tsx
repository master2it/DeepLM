"use client";

import { useEffect, useState } from "react";
import { GrammarFixer } from "@/components/grammar-fixer";
import { TensesGenerator } from "@/components/tenses-generator";
import { SettingsPanel } from "@/components/settings-panel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  fetchHealth,
  readStoredGroqKey,
  readStoredProvider,
  writeStoredGroqKey,
  writeStoredProvider,
  type HealthPayload,
  type ProviderId,
} from "@/lib/api";

export default function HomePage() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [provider, setProvider] = useState<ProviderId>("ollama");
  const [groqApiKey, setGroqApiKey] = useState("");

  useEffect(() => {
    setProvider(readStoredProvider());
    setGroqApiKey(readStoredGroqKey());
    fetchHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  function onProviderChange(next: ProviderId) {
    setProvider(next);
    writeStoredProvider(next);
  }

  function onGroqApiKeyChange(next: string) {
    setGroqApiKey(next);
    writeStoredGroqKey(next);
  }

  const groqReady = Boolean(groqApiKey.trim()) || Boolean(health?.groq_configured);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">DeepLM</h1>
          <p className="text-sm text-zinc-400">
            Grammar fixer and 12 tenses — pick a provider in Settings
          </p>
        </div>
        {health && (
          <div className="flex flex-wrap gap-2">
            <Badge>
              {health.ollama
                ? `Ollama: ${health.ollama_model}`
                : "Ollama: offline"}
            </Badge>
            <Badge>
              {health.hf_configured ? "HF: ready" : "HF: not set"}
            </Badge>
            <Badge>{groqReady ? "Groq: ready" : "Groq: not set"}</Badge>
          </div>
        )}
      </header>
      <Tabs defaultValue="grammar">
        <TabsList>
          <TabsTrigger value="grammar">Grammar/Spell Fixer</TabsTrigger>
          <TabsTrigger value="tenses">12 Tenses Generator</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        <TabsContent value="grammar">
          <GrammarFixer provider={provider} groqApiKey={groqApiKey} />
        </TabsContent>
        <TabsContent value="tenses">
          <TensesGenerator provider={provider} groqApiKey={groqApiKey} />
        </TabsContent>
        <TabsContent value="settings">
          <SettingsPanel
            provider={provider}
            onChange={onProviderChange}
            groqApiKey={groqApiKey}
            onGroqApiKeyChange={onGroqApiKeyChange}
            health={health}
          />
        </TabsContent>
      </Tabs>
    </main>
  );
}
