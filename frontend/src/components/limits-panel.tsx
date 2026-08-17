"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchLimits, type LimitsPayload } from "@/lib/api";

export function LimitsPanel({
  hfApiKey,
  hfConfigured,
}: {
  hfApiKey: string;
  hfConfigured: boolean;
}) {
  const ownKey = Boolean(hfApiKey.trim());
  const [data, setData] = useState<LimitsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLimits(ownKey)
      .then((payload) => {
        setData(payload);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load limits"));
  }, [ownKey]);

  const limit = data?.limit ?? 30;
  const used = data?.used ?? 0;
  const remaining = data?.remaining ?? Math.max(0, limit - used);
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const resets = data?.resets_at
    ? new Date(data.resets_at).toUTCString()
    : "next UTC midnight";

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        The shared server Hugging Face key is limited to {limit} successful
        Grammar, Tenses, and Explain generations per UTC day (counted by this
        browser and your IP). Your own HF token in Settings is not capped here.
      </p>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">Default HF key</CardTitle>
          <Badge>
            {ownKey
              ? "Using your key (uncapped)"
              : hfConfigured
                ? "Using server key"
                : "Server key not set"}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
            <div
              className="h-full bg-blue-500"
              style={{ width: `${ownKey ? 0 : pct}%` }}
            />
          </div>
          <p>
            Used today:{" "}
            <span className="font-medium text-zinc-100">
              {ownKey ? "—" : used}
            </span>{" "}
            / {limit}
          </p>
          <p>
            Remaining:{" "}
            <span className="font-medium text-zinc-100">
              {ownKey ? "unlimited" : remaining}
            </span>
          </p>
          <p className="text-zinc-500">Resets: {resets}</p>
          {data && !data.redis && (
            <p className="text-amber-400">
              Redis is offline. Default-key generations are blocked until Redis
              is reachable.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
