import "server-only";

type Message = { role: "system" | "user"; content: string };

const OPENAI_URL = "https://api.openai.com/v1/chat/completions";

export class OpenAIError extends Error {}

export async function chat(
  messages: Message[],
  options: { temperature?: number; maxTokens?: number } = {}
) {
  const key = process.env.OPENAI_API_KEY?.trim();
  if (!key) throw new OpenAIError("OPENAI_API_KEY is not configured.");

  const response = await fetch(OPENAI_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: process.env.OPENAI_MODEL?.trim() || "gpt-4o-mini",
      messages,
      max_completion_tokens: options.maxTokens ?? 2048,
      response_format: { type: "json_object" },
    }),
    cache: "no-store",
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new OpenAIError(payload?.error?.message || "OpenAI request failed.");
  }
  const content = payload?.choices?.[0]?.message?.content;
  if (typeof content !== "string" || !content.trim()) {
    throw new OpenAIError("OpenAI returned an empty response.");
  }
  return content.trim();
}

export function parseModelJson(content: string): unknown {
  const cleaned = content
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/, "")
    .trim();
  return JSON.parse(cleaned);
}
