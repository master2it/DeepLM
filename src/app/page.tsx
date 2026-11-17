"use client";

import { useEffect, useState } from "react";
import { GrammarFixer } from "@/components/grammar-fixer";
import { InstallButton } from "@/components/install-button";
import { fetchLanguages, type LanguagesPayload } from "@/lib/api";
import { APP_VERSION } from "@/lib/version";

export default function HomePage() {
  const [languages, setLanguages] = useState<LanguagesPayload | null>(null);

  useEffect(() => {
    fetchLanguages()
      .then(setLanguages)
      .catch(() => undefined);
  }, []);

  return (
    <main className="mx-auto w-full space-y-4 px-3 py-4 sm:space-y-6 sm:px-4 sm:py-8">
      <header>
        <h1 className="flex flex-wrap items-baseline gap-2 text-xl font-bold sm:text-2xl">
          DeepLM <span className="text-xs font-normal text-zinc-500">v{APP_VERSION}</span>
        </h1>
        <p className="text-sm text-zinc-400">Grammar fixer and translator powered by OpenAI</p>
        <div className="mt-2"><InstallButton /></div>
      </header>
      <GrammarFixer languages={languages} />
    </main>
  );
}
