import { NextResponse } from "next/server";
import { getOperatorSession } from "@/lib/auth";
import { NO_STORE_HEADERS } from "@/lib/http";

export async function GET() {
  if (!(await getOperatorSession())) return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers: NO_STORE_HEADERS });
  return NextResponse.json({
    crmMode: process.env.CRM_MODE ?? "canonical",
    canonicalCrm: process.env.CRM_BACKEND === "postgres" && process.env.CRM_MODE === "canonical" ? "SUPABASE_POSTGRES" : "LOCAL_SQLITE",
    remoteDbStatus: process.env.CRM_BACKEND === "postgres" && process.env.CRM_MODE === "canonical" ? "CANONICAL" : "PREVIEW_COPY",
    writeEnabled: process.env.CRM_WRITE_ENABLED === "true",
    outreachMode: "review",
    outreachSendingEnabled: false,
  }, { headers: NO_STORE_HEADERS });
}
