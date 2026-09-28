import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { NextResponse } from "next/server";
import { APP_VERSION } from "@/lib/version";

export const runtime = "nodejs";

export async function GET() {
  const content = await readFile(join(process.cwd(), "CHANGELOG.md"), "utf8").catch(() => "");
  const releases = [...content.matchAll(/^## \[([^\]]+)\](?:\s+—\s+([^-]+?))?(?:\s+—\s+(\w+))?$/gm)].map((match) => ({
    version: match[1],
    date: match[2]?.trim() ?? "",
    kind: match[3]?.trim() ?? "",
    notes: "",
    changes: [],
  })).filter((release) => release.version !== "Unreleased");
  return NextResponse.json({ current: APP_VERSION, releases });
}
