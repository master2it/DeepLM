"use client";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DEFAULT_GROQ_MODEL,
  shortModelName,
  type GroqFreeModel,
  type HealthPayload,
  type ProviderId,
} from "@/lib/api";

type Props = {
  provider: ProviderId;
  onChange: (provider: ProviderId) => void;
  groqApiKey: string;
  onGroqApiKeyChange: (key: string) => void;
  groqModel: string;
  onGroqModelChange: (model: string) => void;
  hfApiKey: string;
  onHfApiKeyChange: (key: string) => void;
  health: HealthPayload | null;
};

export function SettingsPanel({
  provider,
  onChange,
  groqApiKey,
  onGroqApiKeyChange,
  groqModel,
  onGroqModelChange,
  hfApiKey,
  onHfApiKeyChange,
  health,
}: Props) {
  const byId = Object.fromEntries(
    (health?.providers ?? []).map((p) => [p.id, p])
  );
  const groqReady = Boolean(groqApiKey.trim()) || Boolean(health?.groq_configured);
  const hfReady = Boolean(hfApiKey.trim()) || Boolean(health?.hf_configured);
  const hfModel = shortModelName(
    byId.huggingface?.model || health?.hf_model,
    "Qwen2.5-72B-Instruct"
  );
  const deepseekModel = shortModelName(
    byId.deepseek?.model || health?.deepseek_model,
    "DeepSeek-V4-Flash"
  );
  const groqModels: GroqFreeModel[] =
    health?.groq_models?.length
      ? health.groq_models
      : [
          {
            id: DEFAULT_GROQ_MODEL,
            label: "gpt-oss-120b",
            rpm: 30,
            rpd: 1000,
            tpm: 8000,
            tpd: 200000,
            tag: "Default",
          },
        ];
  const selectedGroq =
    groqModels.find((m) => m.id === groqModel) || groqModels[0];
  const groqTitle = shortModelName(selectedGroq?.id, "gpt-oss-120b");

  const options: {
    id: ProviderId;
    title: string;
    tag?: string;
    tagClass?: string;
    hint: string;
  }[] = [
    {
      id: "huggingface",
      title: hfModel,
      tag: "Slower · better text",
      tagClass: "border-violet-700 bg-violet-950 text-violet-200",
      hint: "Default. Stronger, more careful wording — usually slower. Uses your Hugging Face token (or the server token: 50 generations per UTC day).",
    },
    {
      id: "deepseek",
      title: deepseekModel,
      tag: "HF · fast MoE",
      tagClass: "border-sky-700 bg-sky-950 text-sky-200",
      hint: "DeepSeek-V4-Flash via Hugging Face Inference Providers. Same HF token as above (50/day on the shared server token).",
    },
    {
      id: "groq",
      title: groqTitle,
      tag: "Groq Free",
      tagClass: "border-emerald-700 bg-emerald-950 text-emerald-200",
      hint: "Pick any Free-plan chat model below. Limits follow Groq Free RPM/RPD for that model (your key or the server key).",
    },
  ];

  const showHfKey = provider === "huggingface" || provider === "deepseek";
  const hfKeyLabel = provider === "deepseek" ? deepseekModel : hfModel;

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        Grammar, tenses, and explanations use the selected model only. They
        will not fall back to another model if the chosen one fails.
      </p>
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium text-zinc-200">Models</legend>
        {options.map((opt) => {
          const info = byId[opt.id];
          const selected = provider === opt.id;
          const available =
            opt.id === "groq" ? groqReady : hfReady;
          return (
            <label
              key={opt.id}
              className={`flex items-start gap-3 rounded-lg border p-3 sm:p-4 ${
                selected
                  ? "cursor-pointer border-blue-500 bg-zinc-800"
                  : "cursor-pointer border-zinc-700 bg-zinc-900"
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
                <span className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{opt.title}</span>
                  {opt.tag && (
                    <Badge className={opt.tagClass}>{opt.tag}</Badge>
                  )}
                </span>
                <span className="block text-sm text-zinc-400">{opt.hint}</span>
                {info && (
                  <span className="block text-xs text-zinc-500">
                    {available ? "ready" : "not configured / offline"}
                  </span>
                )}
              </span>
            </label>
          );
        })}
      </fieldset>
      {showHfKey && (
        <div className="space-y-2 rounded-lg border border-zinc-700 bg-zinc-900 p-4">
          <Label htmlFor="hf-api-key">Hugging Face API key ({hfKeyLabel})</Label>
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
            . Shared by Qwen and DeepSeek. Leave empty to use the server token
            (50 generations per UTC day — see the Limits tab).
          </p>
        </div>
      )}
      {provider === "groq" && (
        <div className="space-y-4 rounded-lg border border-zinc-700 bg-zinc-900 p-4">
          <div className="space-y-2">
            <Label htmlFor="groq-model">Groq Free model</Label>
            <Select value={selectedGroq.id} onValueChange={onGroqModelChange}>
              <SelectTrigger id="groq-model" className="mt-2">
                <SelectValue placeholder="Choose a Groq model" />
              </SelectTrigger>
              <SelectContent>
                {groqModels.map((m) => (
                  <SelectItem key={m.id} value={m.id}>
                    {m.label}
                    {m.tag ? ` · ${m.tag}` : ""} · {m.rpm} RPM / {m.rpd} RPD
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-zinc-500">
              Free-plan limits for {selectedGroq.label}:{" "}
              <span className="text-zinc-300">
                {selectedGroq.rpm} RPM · {selectedGroq.rpd} RPD
                {selectedGroq.tpm != null
                  ? ` · ${selectedGroq.tpm.toLocaleString()} TPM`
                  : ""}
                {selectedGroq.tpd != null
                  ? ` · ${selectedGroq.tpd.toLocaleString()} TPD`
                  : ""}
              </span>
              . Source:{" "}
              <a
                className="text-blue-400 underline"
                href="https://console.groq.com/docs/rate-limits"
                target="_blank"
                rel="noreferrer"
              >
                console.groq.com/docs/rate-limits
              </a>
              .
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="groq-api-key">API key ({groqTitle})</Label>
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
              . Leave empty to use the server key. DeepLM still enforces this
              model&apos;s Free RPM/RPD for every user.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
