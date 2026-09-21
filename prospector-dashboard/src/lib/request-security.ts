import { NextRequest } from "next/server";

export function validateSameOriginRequest(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");

  if (!origin || !host) return false;

  let parsedOrigin: URL;
  try {
    parsedOrigin = new URL(origin);
  } catch {
    return false;
  }

  const forwardedProto = request.headers.get("x-forwarded-proto");
  const scheme = forwardedProto?.split(",")[0]?.trim() || request.nextUrl.protocol.replace(":", "");
  const expectedOrigin = `${scheme}://${host}`;

  return parsedOrigin.origin === expectedOrigin;
}
