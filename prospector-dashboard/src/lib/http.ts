import type { NextRequest } from "next/server";

export const NO_STORE_HEADERS = {
  "Cache-Control": "no-store, private, max-age=0",
  Pragma: "no-cache",
  "X-Robots-Tag": "noindex, nofollow, noarchive",
};

export function validateMutationRequest(request: NextRequest): string | null {
  const contentType = request.headers.get("content-type") ?? "";
  if (!contentType.toLowerCase().startsWith("application/json")) return "Content-Type must be application/json";

  const origin = request.headers.get("origin");
  if (!origin) return "Origin header required";
  const host = request.headers.get("host");
  if (!host) return "Host header required";
  const expected = `${request.nextUrl.protocol}//${host}`;
  if (origin !== expected) return "Origin rejected";
  return null;
}
