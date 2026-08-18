"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  fetchLimits,
  type LimitsPayload,
  type ProviderLimit,
} from "@/lib/api";

function QuotaCard({
  title,
  tag,
  tagClass,
  uncapped,
  ownKey,
  ownKeyLabel = "Your key (30/day)",
  usedLabel = "Used today",
  serverConfigured,
  row,
  barClass,
  fallbackLimit = 30,
}: {
  title: string;
  tag?: string;
  tagClass?: string;
  uncapped: boolean;
  ownKey: boolean;
  ownKeyLabel?: string;
  usedLabel?: string;
  serverConfigured: boolean;
  row: ProviderLimit | undefined;
  barClass: string;
  fallbackLimit?: number;
}) {
  const limit = row?.limit ?? fallbackLimit;
  const used = row?.used ?? 0;
  const remaining = row?.remaining ?? Math.max(0, limit - used);
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const resets = row?.resets_at
    ? new Date(row.resets_at).toUTCString()
    : null;
  return (
    <Card>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 space-y-0">
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-base">{title}</CardTitle>
          {tag && <Badge className={tagClass}>{tag}</Badge>}
        </div>
        <Badge>
          {uncapped
            ? "Using your key (uncapped)"
            : ownKey
              ? ownKeyLabel
              : serverConfigured
                ? "Using server key"
                : "Server key not set"}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
          <div
            className={`h-full ${barClass}`}
            style={{ width: `${uncapped ? 0 : pct}%` }}
          />
        </div>
        <p>
          {usedLabel}:{" "}
          <span className="font-medium text-zinc-100">
            {uncapped ? "—" : used}
          </span>{" "}
          / {limit}
        </p>
        <p>
          Remaining:{" "}
          <span className="font-medium text-zinc-100">
            {uncapped ? "unlimited" : remaining}
          </span>
        </p>
        {resets && <p className="text-zinc-500">Resets: {resets}</p>}
      </CardContent>
    </Card>
  );
}

export function LimitsPanel({
  hfApiKey,
  hfConfigured,
  groqApiKey,
  groqConfigured,
}: {
  hfApiKey: string;
  hfConfigured: boolean;
  groqApiKey: string;
  groqConfigured: boolean;
}) {
  const ownHf = Boolean(hfApiKey.trim());
  const ownGroq = Boolean(groqApiKey.trim());
  const [data, setData] = useState<LimitsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    function load() {
      fetchLimits(ownHf, ownGroq)
        .then((payload) => {
          if (!cancelled) {
            setData(payload);
            setError(null);
          }
        })
        .catch((e) => {
          if (!cancelled) {
            setError(e instanceof Error ? e.message : "Failed to load limits");
          }
        });
    }
    load();
    window.addEventListener("focus", load);
    return () => {
      cancelled = true;
      window.removeEventListener("focus", load);
    };
  }, [ownHf, ownGroq]);

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        Groq is limited to 30 successful Grammar, Tenses, and Explain generations
        per UTC hour (this browser and your IP), whether you paste your own Groq
        key or use the server key. Hugging Face is capped at 50/day on the shared
        server token only — your own HF key is uncapped. Cache hits do not count.
      </p>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <QuotaCard
        title="Hugging Face"
        tag="Slower · better text"
        tagClass="border-violet-700 bg-violet-950 text-violet-200"
        uncapped={ownHf}
        ownKey={ownHf}
        serverConfigured={hfConfigured}
        row={data?.huggingface}
        barClass="bg-blue-500"
        fallbackLimit={50}
      />
      <QuotaCard
        title="Groq"
        tag="Suggested · fast"
        tagClass="border-emerald-700 bg-emerald-950 text-emerald-200"
        uncapped={false}
        ownKey={ownGroq}
        ownKeyLabel="Your key (30/hour)"
        usedLabel="Used this hour"
        serverConfigured={groqConfigured}
        row={data?.groq}
        barClass="bg-emerald-500"
      />
      {data && !data.redis && (
        <p className="text-sm text-amber-400">
          Redis is offline. Groq generations and default-key Hugging Face
          generations are blocked until Redis is reachable.
        </p>
      )}
    </div>
  );
}
