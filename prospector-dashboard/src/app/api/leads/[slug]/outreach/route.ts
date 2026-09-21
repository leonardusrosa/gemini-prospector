import { NextRequest, NextResponse } from "next/server";
import { getOperatorSession } from "@/lib/auth";
import { getCRMRepository } from "@/lib/crm";
import { NO_STORE_HEADERS } from "@/lib/http";
import { maskDestination, proposalUrl } from "@/lib/presentation";

export async function GET(_: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  if (!(await getOperatorSession())) return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers: NO_STORE_HEADERS });
  const { slug } = await params;
  const repo = getCRMRepository();
  const lead = await repo.getLead(slug);
  if (!lead) return NextResponse.json({ error: "Not found" }, { status: 404, headers: NO_STORE_HEADERS });
  const history = await repo.getOutreachHistory(slug);
  return NextResponse.json({
    mode: "review",
    sendingEnabled: false,
    channels: {
      whatsapp: { available: Boolean(lead.whatsapp), destination: maskDestination(lead.whatsapp) },
      email: { available: Boolean(lead.email), destination: maskDestination(lead.email) },
    },
    proposalUrl: proposalUrl(lead),
    history,
  }, { headers: NO_STORE_HEADERS });
}
