"use client";

import { useEffect, useState } from "react";
import { BookOpen, Gauge, History, Settings, SpellCheck } from "lucide-react";
import { InstallButton } from "@/components/install-button";
import { ChangelogPanel } from "@/components/changelog-panel";
import { GrammarFixer } from "@/components/grammar-fixer";
import { LimitsPanel } from "@/components/limits-panel";
import { TensesGenerator } from "@/components/tenses-generator";
import { SettingsPanel } from "@/components/settings-panel";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  DEFAULT_GROQ_MODEL,
  fetchHealth,
  fetchLanguages,
  getClientId,
  readStoredGroqKey,
  readStoredGroqModel,
  readStoredHfKey,
  readStoredProvider,
  shortModelName,
  writeStoredGroqKey,
  writeStoredGroqModel,
  writeStoredHfKey,
  writeStoredProvider,
  type HealthPayload,
  type LanguagesPayload,
  type ProviderId,
} from "@/lib/api";
import { APP_VERSION } from "@/lib/version";

export default function HomePage() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [languages, setLanguages] = useState<LanguagesPayload | null>(null);
  const [provider, setProvider] = useState<ProviderId>("huggingface");
  const [groqApiKey, setGroqApiKey] = useState("");
  const [groqModel, setGroqModel] = useState(DEFAULT_GROQ_MODEL);
  const [hfApiKey, setHfApiKey] = useState("");

  useEffect(() => {
    let cancelled = false;
    getClientId();
    setProvider(readStoredProvider());
    setGroqApiKey(readStoredGroqKey());
    setHfApiKey(readStoredHfKey());
    Promise.all([fetchHealth(), fetchLanguages()])
      .then(([healthPayload, languagesPayload]) => {
        if (cancelled) return;
        setHealth(healthPayload);
        setLanguages(languagesPayload);
        const allowed = (healthPayload.groq_models || []).map((m) => m.id);
        setGroqModel(readStoredGroqModel(allowed.length ? allowed : null));
      })
      .catch(() => {
        if (cancelled) return;
        setHealth(null);
        setLanguages(null);
        setGroqModel(readStoredGroqModel());
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function onProviderChange(next: ProviderId) {
    setProvider(next);
    writeStoredProvider(next);
  }

  function onGroqApiKeyChange(next: string) {
    setGroqApiKey(next);
    writeStoredGroqKey(next);
  }

  function onGroqModelChange(next: string) {
    setGroqModel(next);
    writeStoredGroqModel(next);
  }

  function onHfApiKeyChange(next: string) {
    setHfApiKey(next);
    writeStoredHfKey(next);
  }

  const groqReady = Boolean(groqApiKey.trim()) || Boolean(health?.groq_configured);
  const hfReady = Boolean(hfApiKey.trim()) || Boolean(health?.hf_configured);
  const activeGroqLabel = shortModelName(groqModel, "gpt-oss-120b");

  return (
    <main className="mx-auto w-full max-w-6xl space-y-4 px-3 py-4 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:space-y-6 sm:px-4 sm:py-8 sm:pb-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <div>
          <h1 className="flex flex-wrap items-baseline gap-2 text-xl font-bold sm:text-2xl">
            DeepLM
            <span className="text-xs font-normal text-zinc-500">v{APP_VERSION}</span>
          </h1>
          <p className="text-sm text-zinc-400">
            Grammar fixer and 12 tenses — pick a model in Settings
          </p>
          <div className="mt-2">
            <InstallButton />
          </div>
        </div>
        {health && (
          <div className="flex flex-wrap gap-2">
            <Badge
              className={
                hfReady
                  ? "border-emerald-700 bg-emerald-950 text-emerald-300"
                  : "border-red-700 bg-red-950 text-red-300"
              }
            >
              {hfReady
                ? `${shortModelName(health.hf_model, "Qwen2.5-72B-Instruct")}: ready · slower`
                : `${shortModelName(health.hf_model, "Qwen2.5-72B-Instruct")}: not set`}
            </Badge>
            <Badge
              className={
                hfReady
                  ? "border-emerald-700 bg-emerald-950 text-emerald-300"
                  : "border-red-700 bg-red-950 text-red-300"
              }
            >
              {hfReady
                ? `${shortModelName(health.deepseek_model, "DeepSeek-V4-Flash")}: ready · HF`
                : `${shortModelName(health.deepseek_model, "DeepSeek-V4-Flash")}: not set`}
            </Badge>
            <Badge
              className={
                groqReady
                  ? "border-emerald-700 bg-emerald-950 text-emerald-300"
                  : "border-red-700 bg-red-950 text-red-300"
              }
            >
              {groqReady
                ? `${activeGroqLabel}: ready · Groq Free`
                : `${activeGroqLabel}: not set`}
            </Badge>
          </div>
        )}
      </header>
      <Tabs defaultValue="grammar">
        <TabsList className="h-fit fixed inset-x-0 bottom-0 z-50 border-t border-zinc-800 bg-zinc-900/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md sm:static sm:z-auto sm:border-0 sm:bg-zinc-800 sm:pb-1 sm:backdrop-blur-none">
          <TabsTrigger value="grammar">
            <SpellCheck className="size-5 sm:hidden" aria-hidden />
            <span className="sm:hidden">Translate</span>
            <span className="hidden sm:inline">Translate / Grammar / Spell Fixer</span>
          </TabsTrigger>
          <TabsTrigger value="tenses">
            <BookOpen className="size-5 sm:hidden" aria-hidden />
            Tenses
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="size-5 sm:hidden" aria-hidden />
            Settings
          </TabsTrigger>
          <TabsTrigger value="limits">
            <Gauge className="size-5 sm:hidden" aria-hidden />
            Limits
          </TabsTrigger>
          <TabsTrigger value="changelog">
            <History className="size-5 sm:hidden" aria-hidden />
            <span className="sm:hidden">Versions</span>
            <span className="hidden sm:inline">Changelog</span>
          </TabsTrigger>
        </TabsList>
        <TabsContent value="grammar">
          <GrammarFixer
            provider={provider}
            groqApiKey={groqApiKey}
            hfApiKey={hfApiKey}
            hfModel={health?.hf_model}
            deepseekModel={health?.deepseek_model}
            groqModel={groqModel}
            languages={languages}
          />
        </TabsContent>
        <TabsContent value="tenses">
          <TensesGenerator
            provider={provider}
            groqApiKey={groqApiKey}
            hfApiKey={hfApiKey}
            hfModel={health?.hf_model}
            deepseekModel={health?.deepseek_model}
            groqModel={groqModel}
            languages={languages}
          />
        </TabsContent>
        <TabsContent value="settings">
          <SettingsPanel
            provider={provider}
            onChange={onProviderChange}
            groqApiKey={groqApiKey}
            onGroqApiKeyChange={onGroqApiKeyChange}
            groqModel={groqModel}
            onGroqModelChange={onGroqModelChange}
            hfApiKey={hfApiKey}
            onHfApiKeyChange={onHfApiKeyChange}
            health={health}
          />
        </TabsContent>
        <TabsContent value="limits">
          <LimitsPanel
            hfApiKey={hfApiKey}
            hfConfigured={Boolean(health?.hf_configured)}
            hfModel={health?.hf_model}
            groqApiKey={groqApiKey}
            groqConfigured={Boolean(health?.groq_configured)}
            groqModel={groqModel}
          />
        </TabsContent>
        <TabsContent value="changelog">
          <ChangelogPanel apiVersion={health?.version} />
        </TabsContent>
      </Tabs>
    </main>
  );
}
