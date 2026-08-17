"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { HealthPayload, ProviderId } from "@/lib/api";

const OPTIONS: { id: ProviderId; title: string; hint: string }[] = [
  {
    id: "ollama",
    title: "Ollama",
    hint: "Local model on this machine (default).",
  },
  {
    id: "huggingface",
    title: "Hugging Face",
    hint: "Cloud chat. Requires HF_TOKEN in the server .env.",
  },
  {
    id: "groq",
    title: "Groq",
    hint: "Cloud chat. Paste your Groq API key below (or set GROQ_API_KEY on the server).",
  },
];

type Props = {
  provider: ProviderId;
  onChange: (provider: ProviderId) => void;
  groqApiKey: string;
  onGroqApiKeyChange: (key: string) => void;
  health: HealthPayload | null;
};

export function SettingsPanel({
  provider,
  onChange,
  groqApiKey,
  onGroqApiKeyChange,
  health,
}: Props) {
  const byId = Object.fromEntries(
    (health?.providers ?? []).map((p) => [p.id, p])
  );
  const groqReady = Boolean(groqApiKey.trim()) || Boolean(health?.groq_configured);

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        Prefer this provider first. If it fails, the API tries the others in
        order: Ollama, then Hugging Face, then Groq.
      </p>
      <fieldset className="space-y-3">
        <legend className="sr-only">LLM provider</legend>
        {OPTIONS.map((opt) => {
          const info = byId[opt.id];
          const selected = provider === opt.id;
          const available =
            opt.id === "groq" ? groqReady : Boolean(info?.available);
          return (
            <label
              key={opt.id}
              className={`flex cursor-pointer items-start gap-3 rounded-lg border p-4 ${
                selected
                  ? "border-blue-500 bg-zinc-800"
                  : "border-zinc-700 bg-zinc-900"
              }`}
            >
              <input
                type="radio"
                name="provider"
                value={opt.id}
                checked={selected}
                onChange={() => onChange(opt.id)}
                className="mt-1"
              />
              <span className="space-y-1">
                <span className="block font-medium">{opt.title}</span>
                <span className="block text-sm text-zinc-400">{opt.hint}</span>
                {info && (
                  <span className="block text-xs text-zinc-500">
                    Model: {info.model} —{" "}
                    {available ? "ready" : "not configured / offline"}
                  </span>
                )}
              </span>
            </label>
          );
        })}
      </fieldset>
      {provider === "groq" && (
        <div className="space-y-2 rounded-lg border border-zinc-700 bg-zinc-900 p-4">
          <Label htmlFor="groq-api-key">Groq API key</Label>
          <Input
            className="mt-2"
            id="groq-api-key"
            type="password"
            autoComplete="off"
            placeholder="gsk_…"
            value={groqApiKey}
            onChange={(e) => onGroqApiKeyChange(e.target.value)}
          />
          <p className="text-xs text-zinc-500">
            Saved in this browser only. Get a key at{" "}
            <a
              className="text-blue-400 underline"
              href="https://console.groq.com/keys"
              target="_blank"
              rel="noreferrer"
            >
              console.groq.com/keys
            </a>
            . Server <code className="text-zinc-300">GROQ_API_KEY</code> is used
            if this field is empty.
          </p>
        </div>
      )}
    </div>
  );
}
