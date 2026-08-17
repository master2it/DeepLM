"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchChangelog,
  type ChangelogRelease,
} from "@/lib/api";
import { APP_VERSION } from "@/lib/version";

function typeClass(type: string) {
  const t = type.toLowerCase();
  if (t.includes("major")) return "border-red-500/50 text-red-300";
  if (t.includes("minor")) return "border-blue-500/50 text-blue-300";
  if (t.includes("release")) return "border-emerald-500/50 text-emerald-300";
  return "border-zinc-500 text-zinc-300";
}

export function ChangelogPanel({ apiVersion }: { apiVersion?: string }) {
  const [releases, setReleases] = useState<ChangelogRelease[]>([]);
  const [current, setCurrent] = useState(APP_VERSION);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchChangelog()
      .then((data) => {
        setCurrent(data.current || APP_VERSION);
        setReleases(data.releases || []);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load changelog"));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Badge>App v{APP_VERSION}</Badge>
        <Badge>API v{apiVersion || current}</Badge>
      </div>
      <p className="text-sm text-zinc-400">
        Versions and what changed (major / minor / patch / release).
      </p>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {releases.map((rel) => (
        <Card key={`${rel.version}-${rel.date}`}>
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-2">
              <span>v{rel.version}</span>
              {rel.kind && (
                <Badge className={typeClass(rel.kind)}>{rel.kind}</Badge>
              )}
              {rel.date && (
                <span className="text-xs font-normal text-zinc-500">{rel.date}</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {rel.notes && <p className="text-zinc-300">{rel.notes}</p>}
            {rel.changes.map((change) => (
              <div
                key={change.title}
                className="space-y-1 border-t border-zinc-700 pt-3 first:border-t-0 first:pt-0"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{change.title}</span>
                  {change.type && (
                    <Badge className={typeClass(change.type)}>{change.type}</Badge>
                  )}
                </div>
                {change.summary && (
                  <p className="text-zinc-300">{change.summary}</p>
                )}
                {change.why && (
                  <p className="text-xs text-zinc-500">Why: {change.why}</p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
