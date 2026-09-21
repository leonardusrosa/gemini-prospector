import { NextRequest, NextResponse } from "next/server";
import { clearAuthCookies, getAccessToken } from "@/lib/auth";
import { NO_STORE_HEADERS } from "@/lib/http";
import { validateSameOriginRequest } from "@/lib/request-security";

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing server environment variable: ${name}`);
  return value;
}

export async function POST(request: NextRequest) {
  if (!validateSameOriginRequest(request)) {
    return new NextResponse("Forbidden", { status: 403, headers: NO_STORE_HEADERS });
  }

  try {
    const accessToken = await getAccessToken();
    if (accessToken) {
      await fetch(`${required("SUPABASE_URL")}/auth/v1/logout`, {
        method: "POST",
        headers: {
          apikey: required("SUPABASE_ANON_KEY"),
          Authorization: `Bearer ${accessToken}`,
        },
        cache: "no-store",
      });
    }
  } finally {
    await clearAuthCookies();
  }

  return NextResponse.redirect(new URL("/login", request.url), { headers: NO_STORE_HEADERS });
}
