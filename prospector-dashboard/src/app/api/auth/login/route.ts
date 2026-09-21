import { NextRequest, NextResponse } from "next/server";
import { setAuthCookies } from "@/lib/auth";
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
  const form = await request.formData();
  const email = String(form.get("email") ?? "").trim().toLowerCase();
  const password = String(form.get("password") ?? "");
  if (!email || !password || email !== required("OPERATOR_EMAIL").trim().toLowerCase()) {
    return NextResponse.redirect(new URL("/login?error=1", request.url), { headers: NO_STORE_HEADERS });
  }
  const response = await fetch(`${required("SUPABASE_URL")}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { apikey: required("SUPABASE_ANON_KEY"), "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    cache: "no-store",
  });
  if (!response.ok) return NextResponse.redirect(new URL("/login?error=1", request.url), { headers: NO_STORE_HEADERS });
  const auth = await response.json() as { access_token: string; refresh_token: string; expires_in: number };
  await setAuthCookies(auth);
  return NextResponse.redirect(new URL("/", request.url), { headers: NO_STORE_HEADERS });
}
