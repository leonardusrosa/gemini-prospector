import { NextRequest, NextResponse } from "next/server";
import { NO_STORE_HEADERS } from "./lib/http";

const ACCESS_COOKIE = "prospector_access_token";
const EXPIRES_COOKIE = "prospector_expires_at";

type SupabaseUser = {
  email?: string | null;
};

function isApiRequest(request: NextRequest) {
  return request.nextUrl.pathname.startsWith("/api/");
}

function unauthorized(request: NextRequest) {
  if (isApiRequest(request)) {
    return NextResponse.json(
      { error: "Unauthorized" },
      { status: 401, headers: NO_STORE_HEADERS },
    );
  }

  const loginUrl = request.nextUrl.clone();
  loginUrl.pathname = "/login";
  loginUrl.search = "";
  return NextResponse.redirect(loginUrl, { headers: NO_STORE_HEADERS });
}

function forbidden(request: NextRequest) {
  if (isApiRequest(request)) {
    return NextResponse.json(
      { error: "Forbidden" },
      { status: 403, headers: NO_STORE_HEADERS },
    );
  }

  return new NextResponse("Forbidden", {
    status: 403,
    headers: NO_STORE_HEADERS,
  });
}

function sessionIsExpired(request: NextRequest) {
  const raw = request.cookies.get(EXPIRES_COOKIE)?.value;
  if (!raw) return false;

  const expiresAt = Number(raw);
  if (!Number.isFinite(expiresAt)) return true;

  // Supabase expires_at values are Unix seconds.
  return expiresAt <= Math.floor(Date.now() / 1000);
}

export async function middleware(request: NextRequest) {
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  if (!accessToken || sessionIsExpired(request)) {
    return unauthorized(request);
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseAnonKey = process.env.SUPABASE_ANON_KEY;
  const operatorEmail = process.env.OPERATOR_EMAIL?.trim().toLowerCase();

  if (!supabaseUrl || !supabaseAnonKey || !operatorEmail) {
    return new NextResponse("Authentication is not configured", {
      status: 503,
      headers: NO_STORE_HEADERS,
    });
  }

  let authResponse: Response;
  try {
    authResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
      method: "GET",
      headers: {
        apikey: supabaseAnonKey,
        Authorization: `Bearer ${accessToken}`,
      },
      cache: "no-store",
    });
  } catch {
    return new NextResponse("Authentication service unavailable", {
      status: 503,
      headers: NO_STORE_HEADERS,
    });
  }

  if (!authResponse.ok) {
    return unauthorized(request);
  }

  const user = (await authResponse.json()) as SupabaseUser;
  if (user.email?.trim().toLowerCase() !== operatorEmail) {
    return forbidden(request);
  }

  const response = NextResponse.next();
  for (const [name, value] of Object.entries(NO_STORE_HEADERS)) {
    response.headers.set(name, value);
  }
  return response;
}

export const config = {
  matcher: [
    "/((?!login$|api/auth/login$|api/auth/logout$|_next/static|_next/image|favicon.ico).*)",
  ],
};
