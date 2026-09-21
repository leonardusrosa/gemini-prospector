import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const ACCESS_COOKIE = "prospector_access_token";
const EXPIRES_COOKIE = "prospector_expires_at";

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing server environment variable: ${name}`);
  return value;
}

export type OperatorSession = { id: string; email: string };

export async function getOperatorSession(): Promise<OperatorSession | null> {
  const jar = await cookies();
  const accessToken = jar.get(ACCESS_COOKIE)?.value;
  const expiresAt = Number(jar.get(EXPIRES_COOKIE)?.value ?? 0);
  if (!accessToken || !expiresAt || Math.floor(Date.now() / 1000) >= expiresAt) return null;

  const response = await fetch(`${required("SUPABASE_URL")}/auth/v1/user`, {
    headers: {
      apikey: required("SUPABASE_ANON_KEY"),
      Authorization: `Bearer ${accessToken}`,
    },
    cache: "no-store",
  });
  if (!response.ok) return null;
  const user = (await response.json()) as { id?: string; email?: string };
  const allowedEmail = required("OPERATOR_EMAIL").trim().toLowerCase();
  if (!user.id || !user.email || user.email.toLowerCase() !== allowedEmail) return null;
  return { id: user.id, email: user.email };
}

export async function requireOperator(): Promise<OperatorSession> {
  const session = await getOperatorSession();
  if (!session) redirect("/login");
  return session;
}

export async function setAuthCookies(payload: {
  access_token: string;
  expires_in: number;
}) {
  const jar = await cookies();
  const secure = process.env.NODE_ENV === "production";
  const base = { httpOnly: true, secure, sameSite: "lax" as const, path: "/" };
  const expiresAt = Math.floor(Date.now() / 1000) + payload.expires_in;
  jar.set(ACCESS_COOKIE, payload.access_token, { ...base, maxAge: payload.expires_in });
  jar.set(EXPIRES_COOKIE, String(expiresAt), { ...base, maxAge: payload.expires_in });
}

export async function getAccessToken() {
  const jar = await cookies();
  return jar.get(ACCESS_COOKIE)?.value ?? null;
}

export async function clearAuthCookies() {
  const jar = await cookies();
  jar.delete(ACCESS_COOKIE);
  jar.delete(EXPIRES_COOKIE);
}
