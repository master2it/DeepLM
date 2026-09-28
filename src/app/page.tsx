"use client";

import { useEffect, useState } from "react";
import { BookOpen, History, SpellCheck } from "lucide-react";
import { ChangelogPanel } from "@/components/changelog-panel";
import { GrammarFixer } from "@/components/grammar-fixer";
import { InstallButton } from "@/components/install-button";
import { TensesGenerator } from "@/components/tenses-generator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { fetchHealth, fetchLanguages, type HealthPayload, type LanguagesPayload } from "@/lib/api";
import { APP_VERSION } from "@/lib/version";

export default function HomePage() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [languages, setLanguages] = useState<LanguagesPayload | null>(null);

  useEffect(() => {
    Promise.all([fetchHealth(), fetchLanguages()])
      .then(([nextHealth, nextLanguages]) => {
        setHealth(nextHealth);
        setLanguages(nextLanguages);
      })
      .catch(() => undefined);
  }, []);

  return (
    <main className="mx-auto w-full max-w-6xl space-y-4 px-3 py-4 pb-[calc(5.5rem+env(safe-area-inset-bottom))] sm:space-y-6 sm:px-4 sm:py-8 sm:pb-8">
      <header>
        <h1 className="flex flex-wrap items-baseline gap-2 text-xl font-bold sm:text-2xl">
          DeepLM <span className="text-xs font-normal text-zinc-500">v{APP_VERSION}</span>
        </h1>
        <p className="text-sm text-zinc-400">Grammar fixer, translator, and tense practice powered by OpenAI</p>
        <div className="mt-2"><InstallButton /></div>
      </header>
      <Tabs defaultValue="grammar">
        <TabsList className="h-fit fixed inset-x-0 bottom-0 z-50 border-t border-zinc-800 bg-zinc-900/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md sm:static sm:z-auto sm:border-0 sm:bg-zinc-800 sm:pb-1 sm:backdrop-blur-none">
          <TabsTrigger value="grammar"><SpellCheck className="size-5 sm:hidden" aria-hidden /><span className="sm:hidden">Translate</span><span className="hidden sm:inline">Translate / Grammar / Spell Fixer</span></TabsTrigger>
          <TabsTrigger value="tenses"><BookOpen className="size-5 sm:hidden" aria-hidden />Tenses</TabsTrigger>
          <TabsTrigger value="changelog"><History className="size-5 sm:hidden" aria-hidden /><span className="sm:hidden">Versions</span><span className="hidden sm:inline">Changelog</span></TabsTrigger>
        </TabsList>
        <TabsContent value="grammar"><GrammarFixer languages={languages} /></TabsContent>
        <TabsContent value="tenses"><TensesGenerator languages={languages} /></TabsContent>
        <TabsContent value="changelog"><ChangelogPanel apiVersion={health?.version} /></TabsContent>
      </Tabs>
    </main>
  );
}
