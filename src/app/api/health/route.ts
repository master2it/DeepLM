import { NextResponse } from "next/server";
import { APP_VERSION } from "@/lib/version";

export const runtime = "nodejs";

export function GET() {
  const model = process.env.OPENAI_MODEL?.trim() || "gpt-4o-mini";
  return NextResponse.json({
    ok: true,
    version: APP_VERSION,
    openai_configured: Boolean(process.env.OPENAI_API_KEY?.trim()),
    openai_model: model,
  });
}
