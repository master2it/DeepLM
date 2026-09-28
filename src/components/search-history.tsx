"use client";

import { History, X } from "lucide-react";
import { Button } from "@/components/ui/button";

export type HistoryRow = {
  id: string;
  at: number;
  title: string;
  subtitle: string;
};

export function SearchHistory({
  items,
  onSelect,
  onRemove,
  onClear,
}: {
  items: HistoryRow[];
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
  onClear: () => void;
}) {
  if (items.length === 0) return null;
  return (
    <section className="space-y-2 rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-medium text-zinc-200">
          <History className="size-4 text-zinc-400" aria-hidden />
          Recent searches
        </h2>
        <Button type="button" variant="ghost" size="sm" onClick={onClear}>
          Clear
        </Button>
      </div>
      <ul className="max-h-56 space-y-1 overflow-y-auto">
        {items.map((item) => (
          <li key={item.id} className="flex items-stretch gap-1">
            <button
              type="button"
              className="min-w-0 flex-1 rounded-md px-2 py-2 text-left hover:bg-zinc-800"
              onClick={() => onSelect(item.id)}
            >
              <span className="block truncate text-sm text-zinc-100">
                {item.title}
              </span>
              <span className="block truncate text-xs text-zinc-500">
                {item.subtitle}
              </span>
            </button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-9 w-9 shrink-0 text-zinc-500"
              title="Remove"
              onClick={() => onRemove(item.id)}
            >
              <X className="size-4" />
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function formatHistoryTime(at: number) {
  try {
    return new Date(at).toLocaleString();
  } catch {
    return "";
  }
}
