import { NextResponse } from "next/server";
import { getOperatorSession } from "@/lib/auth";
import { getCRMRepository } from "@/lib/crm";
import { NO_STORE_HEADERS } from "@/lib/http";

export const dynamic = "force-dynamic";

export async function GET() {
  if (!(await getOperatorSession())) return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers: NO_STORE_HEADERS });
  const leads = await getCRMRepository().listLeads();
  return NextResponse.json(leads, { headers: NO_STORE_HEADERS });
}
