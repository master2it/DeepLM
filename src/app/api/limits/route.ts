import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({
    enabled: false,
    message: "Usage limits are managed by the configured OpenAI account.",
  });
}
