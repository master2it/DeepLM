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
    hint: "Cloud chat. Paste your HF token below, or leave empty to use the server HF_TOKEN (30 generations per UTC day).",
  },
  {
    id: "groq",
    title: "Groq",
    hint: "Cloud chat. Paste your Groq API key or leave empty for the server key. Groq is always 30 generations per UTC day (your token or the server key).",
  },
];

type Props = {
  provider: ProviderId;
  onChange: (provider: ProviderId) => void;
  groqApiKey: string;
  onGroqApiKeyChange: (key: string) => void;
  hfApiKey: string;
  onHfApiKeyChange: (key: string) => void;
  health: HealthPayload | null;
};

export function SettingsPanel({
  provider,
  onChange,
  groqApiKey,
  onGroqApiKeyChange,
  hfApiKey,
  onHfApiKeyChange,
  health,
}: Props) {
  const byId = Object.fromEntries(
    (health?.providers ?? []).map((p) => [p.id, p])
  );
  const groqReady = Boolean(groqApiKey.trim()) || Boolean(health?.groq_configured);
  const hfReady = Boolean(hfApiKey.trim()) || Boolean(health?.hf_configured);

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        Grammar, tenses, and explanations all use this provider only. They
        will not fall back to Hugging Face or another backend if you pick Groq.
      </p>
      <fieldset className="space-y-3">
        <legend className="sr-only">LLM provider</legend>
        {OPTIONS.map((opt) => {
          const info = byId[opt.id];
          const selected = provider === opt.id;
          const available =
            opt.id === "groq"
              ? groqReady
              : opt.id === "huggingface"
                ? hfReady
                : Boolean(info?.available);
          return (
            <label
              key={opt.id}
              className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 sm:p-4 ${
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
      {provider === "huggingface" && (
        <div className="space-y-2 rounded-lg border border-zinc-700 bg-zinc-900 p-4">
          <Label htmlFor="hf-api-key">Hugging Face API key</Label>
          <Input
            className="mt-2"
            id="hf-api-key"
            type="password"
            autoComplete="off"
            placeholder="hf_…"
            value={hfApiKey}
            onChange={(e) => onHfApiKeyChange(e.target.value)}
          />
          <p className="text-xs text-zinc-500">
            Saved in this browser only. Get a token at{" "}
            <a
              className="text-blue-400 underline"
              href="https://huggingface.co/settings/tokens"
              target="_blank"
              rel="noreferrer"
            >
              huggingface.co/settings/tokens
            </a>
            . Leave empty to use the server{" "}
            <code className="text-zinc-300">HF_TOKEN</code> (30 generations per
            UTC day — see the Limits tab).
          </p>
        </div>
      )}
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
            . Leave empty to use the server{" "}
            <code className="text-zinc-300">GROQ_API_KEY</code>. Groq is always
            limited to 30 generations per UTC day (your key or the server key —
            see the Limits tab).
          </p>
        </div>
      )}
    </div>
  );
}
