"use client";

import { useEffect, useState } from "react";
import { BookOpen, History, Settings, SpellCheck } from "lucide-react";
import { InstallButton } from "@/components/install-button";
import { ChangelogPanel } from "@/components/changelog-panel";
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
import { APP_VERSION } from "@/lib/version";

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
    <main className="mx-auto w-full max-w-6xl space-y-4 px-3 py-4 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:space-y-6 sm:px-4 sm:py-8 sm:pb-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <div>
          <h1 className="flex flex-wrap items-baseline gap-2 text-xl font-bold sm:text-2xl">
            DeepLM
            <span className="text-xs font-normal text-zinc-500">v{APP_VERSION}</span>
          </h1>
          <p className="text-sm text-zinc-400">
            Grammar fixer and 12 tenses — pick a provider in Settings
          </p>
          <div className="mt-2">
            <InstallButton />
          </div>
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
        <TabsList className="fixed inset-x-0 bottom-0 z-50 border-t border-zinc-800 bg-zinc-900/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md sm:static sm:z-auto sm:border-0 sm:bg-zinc-800 sm:pb-1 sm:backdrop-blur-none">
          <TabsTrigger value="grammar">
            <SpellCheck className="size-5 sm:hidden" aria-hidden />
            <span className="sm:hidden">Grammar</span>
            <span className="hidden sm:inline">Grammar/Spell Fixer</span>
          </TabsTrigger>
          <TabsTrigger value="tenses">
            <BookOpen className="size-5 sm:hidden" aria-hidden />
            <span className="sm:hidden">Tenses</span>
            <span className="hidden sm:inline">12 Tenses Generator</span>
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="size-5 sm:hidden" aria-hidden />
            Settings
          </TabsTrigger>
          <TabsTrigger value="changelog">
            <History className="size-5 sm:hidden" aria-hidden />
            <span className="sm:hidden">Versions</span>
            <span className="hidden sm:inline">Changelog</span>
          </TabsTrigger>
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
        <TabsContent value="changelog">
          <ChangelogPanel apiVersion={health?.version} />
        </TabsContent>
      </Tabs>
    </main>
  );
}
