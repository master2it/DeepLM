import { NextResponse } from "next/server";

export function apiError(error: unknown) {
  const message = error instanceof Error ? error.message : "Request failed.";
  const status = /required|must|invalid|at most/i.test(message) ? 400 : 502;
  return NextResponse.json({ detail: message }, { status });
}

export function validText(value: unknown) {
  if (typeof value !== "string" || !value.trim()) throw new Error("Text is required.");
  if (value.trim().length > 1000) throw new Error("Text must be at most 1000 characters.");
  return value.trim();
}
