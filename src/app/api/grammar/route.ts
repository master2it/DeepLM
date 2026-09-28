import { NextResponse } from "next/server";
import { generateGrammar } from "@/lib/server/grammar";
import { apiError, validText } from "@/lib/server/route";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    return NextResponse.json(await generateGrammar({
      text: validText(body.text),
      from_lang: body.from_lang,
      to_lang: body.to_lang,
      to_locale: body.to_locale,
      context: body.context,
    }));
  } catch (error) {
    return apiError(error);
  }
}
