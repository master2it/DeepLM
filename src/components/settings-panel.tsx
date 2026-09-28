"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  resolveGroqModels,
  shortModelName,
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

type ModelOption =
  | {
      kind: "provider";
      id: "huggingface" | "deepseek";
      title: string;
      hint: string;
    }
  | {
      kind: "groq";
      id: string;
      title: string;
      hint: string;
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
  const groqModels = resolveGroqModels(health?.groq_models);
  const selectedGroq =
    groqModels.find((m) => m.id === groqModel) || groqModels[0];
  const groqTitle = shortModelName(selectedGroq?.id, "gpt-oss-120b");

  const options: ModelOption[] = [
    {
      kind: "provider",
      id: "huggingface",
      title: hfModel,
      hint: "Default. Stronger, more careful wording — usually slower. Uses your Hugging Face token (or the server token: 50 generations per UTC day).",
    },
    {
      kind: "provider",
      id: "deepseek",
      title: deepseekModel,
      hint: "DeepSeek-V4-Flash via Hugging Face Inference Providers. Same HF token as above (50/day on the shared server token).",
    },
    ...groqModels.map((m) => ({
      kind: "groq" as const,
      id: m.id,
      title: m.label,
      hint: `${m.rpm} RPM · ${m.rpd} RPD${
        m.tpm != null ? ` · ${m.tpm.toLocaleString()} TPM` : ""
      }${m.tpd != null ? ` · ${m.tpd.toLocaleString()} TPD` : ""}.`,
    })),
  ];

  const showHfKey = provider === "huggingface" || provider === "deepseek";
  const showGroqKey = provider === "groq";
  const hfKeyLabel = provider === "deepseek" ? deepseekModel : hfModel;

  function isSelected(opt: ModelOption): boolean {
    if (opt.kind === "provider") return provider === opt.id;
    return provider === "groq" && groqModel === opt.id;
  }

  function selectOption(opt: ModelOption) {
    if (opt.kind === "provider") {
      onChange(opt.id);
      return;
    }
    onChange("groq");
    onGroqModelChange(opt.id);
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-zinc-400">
        Grammar, tenses, and explanations use the selected model only. They
        will not fall back to another model if the chosen one fails.
      </p>
      <fieldset className="space-y-3">
        <legend className="text-sm font-medium text-zinc-200">Models</legend>
        {options.map((opt) => {
          const selected = isSelected(opt);
          const available = opt.kind === "groq" ? groqReady : hfReady;
          const radioValue =
            opt.kind === "provider" ? opt.id : `groq:${opt.id}`;
          return (
            <label
              key={radioValue}
              className={`flex items-start gap-3 rounded-lg border p-3 sm:p-4 ${
                selected
                  ? "cursor-pointer border-blue-500 bg-zinc-800"
                  : "cursor-pointer border-zinc-700 bg-zinc-900"
              }`}
            >
              <input
                type="radio"
                name="model"
                value={radioValue}
                checked={selected}
                onChange={() => selectOption(opt)}
                className="mt-1"
              />
              <span className="space-y-1">
                <span className="font-medium">{opt.title}</span>
                <span className="block text-sm text-zinc-400">{opt.hint}</span>
                <span className="block text-xs text-zinc-500">
                  {available ? "ready" : "not configured / offline"}
                </span>
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
      {showGroqKey && (
        <div className="space-y-2 rounded-lg border border-zinc-700 bg-zinc-900 p-4">
          <Label htmlFor="groq-api-key">Groq API key ({groqTitle})</Label>
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
            Saved in this browser only. Shared by all Groq models above. Get a
            key at{" "}
            <a
              className="text-blue-400 underline"
              href="https://console.groq.com/keys"
              target="_blank"
              rel="noreferrer"
            >
              console.groq.com/keys
            </a>
            . Leave empty to use the server key. Free RPM/RPD for{" "}
            {selectedGroq.label}: {selectedGroq.rpm}/{selectedGroq.rpd} (
            <a
              className="text-blue-400 underline"
              href="https://console.groq.com/docs/rate-limits"
              target="_blank"
              rel="noreferrer"
            >
              docs
            </a>
            ).
          </p>
        </div>
      )}
    </div>
  );
}
