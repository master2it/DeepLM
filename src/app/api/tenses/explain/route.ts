import { NextResponse } from "next/server";
import { explainTense } from "@/lib/server/tenses";
import { apiError } from "@/lib/server/route";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    if (typeof body.tense !== "string" || !body.tense.trim()) throw new Error("Tense is required.");
    return NextResponse.json(await explainTense({
      tense: body.tense.trim(),
      language: body.language,
      text: typeof body.text === "string" ? body.text.slice(0, 1000) : "",
      example: typeof body.example === "string" ? body.example.slice(0, 1000) : "",
    }));
  } catch (error) {
    return apiError(error);
  }
}
