import { NextRequest, NextResponse } from "next/server";
import { getOperatorSession } from "@/lib/auth";
import { getCRMRepository } from "@/lib/crm";
import { NO_STORE_HEADERS } from "@/lib/http";
import { proposalUrl } from "@/lib/presentation";

export async function GET(_: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  if (!(await getOperatorSession())) return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers: NO_STORE_HEADERS });
  const { slug } = await params;
  const lead = await getCRMRepository().getLead(slug);
  if (!lead) return NextResponse.json({ error: "Not found" }, { status: 404, headers: NO_STORE_HEADERS });
  const publicUrl = proposalUrl(lead);
  return NextResponse.json({ exists: Boolean(publicUrl), localUrl: null, publicUrl, preferredUrl: publicUrl }, { headers: NO_STORE_HEADERS });
}
