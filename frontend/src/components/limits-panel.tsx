"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  fetchLimits,
  shortModelName,
  type LimitsPayload,
  type ProviderLimit,
} from "@/lib/api";

function QuotaCard({
  title,
  tag,
  tagClass,
  uncapped,
  ownKey,
  ownKeyLabel = "Your key",
  usedLabel = "Used today",
  serverConfigured,
  row,
  barClass,
  fallbackLimit = 30,
  extra,
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
  extra?: React.ReactNode;
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
        {extra}
      </CardContent>
    </Card>
  );
}

export function LimitsPanel({
  hfApiKey,
  hfConfigured,
  hfModel,
  groqApiKey,
  groqConfigured,
  groqModel,
}: {
  hfApiKey: string;
  hfConfigured: boolean;
  hfModel?: string;
  groqApiKey: string;
  groqConfigured: boolean;
  groqModel?: string;
}) {
  const ownHf = Boolean(hfApiKey.trim());
  const ownGroq = Boolean(groqApiKey.trim());
  const [data, setData] = useState<LimitsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const carefulModel = shortModelName(hfModel, "Qwen2.5-72B-Instruct");
  const fastModel = shortModelName(groqModel, "gpt-oss-120b");
  const groq = data?.groq;
  const rpmLimit = groq?.rpm_limit ?? 30;
  const rpmUsed = groq?.rpm_used ?? 0;
  const rpdLimit = groq?.limit ?? 1000;

  useEffect(() => {
    let cancelled = false;
    function load() {
      fetchLimits(ownHf, ownGroq, groqModel)
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
  }, [ownHf, ownGroq, groqModel]);

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        Hugging Face (Qwen / DeepSeek): 50/day on the shared server token; your
        own HF token is uncapped. Groq Free models follow{" "}
        <a
          className="text-blue-400 underline"
          href="https://console.groq.com/docs/rate-limits"
          target="_blank"
          rel="noreferrer"
        >
          Groq Free plan RPM/RPD
        </a>{" "}
        for the selected model (your key or the server key). Cache hits do not
        count.
      </p>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <QuotaCard
        title={carefulModel}
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
        title={fastModel}
        tag="Groq Free"
        tagClass="border-emerald-700 bg-emerald-950 text-emerald-200"
        uncapped={false}
        ownKey={ownGroq}
        ownKeyLabel={`Your key (${rpdLimit} RPD)`}
        usedLabel="Used today (RPD)"
        serverConfigured={groqConfigured}
        row={data?.groq}
        barClass="bg-emerald-500"
        fallbackLimit={1000}
        extra={
          <div className="space-y-1 border-t border-zinc-800 pt-3 text-zinc-400">
            <p>
              This minute (RPM):{" "}
              <span className="font-medium text-zinc-100">
                {rpmUsed}
              </span>{" "}
              / {rpmLimit}
            </p>
            {groq?.tpm != null && (
              <p>Model TPM (org): {groq.tpm.toLocaleString()}</p>
            )}
            {groq?.tpd != null && (
              <p>Model TPD (org): {groq.tpd.toLocaleString()}</p>
            )}
          </div>
        }
      />
      {data && !data.redis && (
        <p className="text-sm text-amber-400">
          Redis is offline. Groq Free limits and default-key HF generations are
          blocked until Redis is reachable.
        </p>
      )}
    </div>
  );
}
