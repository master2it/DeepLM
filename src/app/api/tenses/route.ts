import { NextResponse } from "next/server";
import { generateTenses } from "@/lib/server/tenses";
import { apiError, validText } from "@/lib/server/route";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    return NextResponse.json(await generateTenses(validText(body.text), body.language));
  } catch (error) {
    return apiError(error);
  }
}
