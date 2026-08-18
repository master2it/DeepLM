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
  ownKey,
  serverConfigured,
  row,
  barClass,
}: {
  title: string;
  ownKey: boolean;
  serverConfigured: boolean;
  row: ProviderLimit | undefined;
  barClass: string;
}) {
  const limit = row?.limit ?? 30;
  const used = row?.used ?? 0;
  const remaining = row?.remaining ?? Math.max(0, limit - used);
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base">{title}</CardTitle>
        <Badge>
          {ownKey
            ? "Using your key (uncapped)"
            : serverConfigured
              ? "Using server key"
              : "Server key not set"}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
          <div
            className={`h-full ${barClass}`}
            style={{ width: `${ownKey ? 0 : pct}%` }}
          />
        </div>
        <p>
          Used today:{" "}
          <span className="font-medium text-zinc-100">{ownKey ? "—" : used}</span>{" "}
          / {limit}
        </p>
        <p>
          Remaining:{" "}
          <span className="font-medium text-zinc-100">
            {ownKey ? "unlimited" : remaining}
          </span>
        </p>
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

  const resets = data?.resets_at
    ? new Date(data.resets_at).toUTCString()
    : "next UTC midnight";

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        Shared server Hugging Face and Groq keys are each limited to 30 successful
        Grammar, Tenses, and Explain generations per UTC day (this browser and
        your IP). Your own keys in Settings are not capped. Cache hits do not
        count.
      </p>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <QuotaCard
        title="Default HF key"
        ownKey={ownHf}
        serverConfigured={hfConfigured}
        row={data?.huggingface}
        barClass="bg-blue-500"
      />
      <QuotaCard
        title="Default Groq key"
        ownKey={ownGroq}
        serverConfigured={groqConfigured}
        row={data?.groq}
        barClass="bg-emerald-500"
      />
      <p className="text-sm text-zinc-500">Resets: {resets}</p>
      {data && !data.redis && (
        <p className="text-sm text-amber-400">
          Redis is offline. Default-key generations are blocked until Redis is
          reachable.
        </p>
      )}
    </div>
  );
}
