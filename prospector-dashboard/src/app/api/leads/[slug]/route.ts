import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getOperatorSession } from "@/lib/auth";
import { getCRMRepository } from "@/lib/crm";
import { NO_STORE_HEADERS, validateMutationRequest } from "@/lib/http";

const updateSchema = z.object({
  status: z.string().max(80).nullable().optional(),
  obs: z.string().max(20000).nullable().optional(),
  contratoStatus: z.string().max(80).nullable().optional(),
  contratoEm: z.string().max(100).nullable().optional(),
  manutencao: z.number().nullable().optional(),
  pago: z.number().int().min(0).max(1).nullable().optional(),
  docCliente: z.string().max(500).nullable().optional(),
  endCliente: z.string().max(1000).nullable().optional(),
  valor: z.number().nullable().optional(),
  dataProposta: z.string().max(100).nullable().optional(),
  candidateUrl: z.string().url().nullable().optional(),
  liveUrl: z.string().url().nullable().optional(),
  proposalUrl: z.string().url().nullable().optional(),
}).strict();

export const dynamic = "force-dynamic";

export async function GET(_: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  if (!(await getOperatorSession())) return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers: NO_STORE_HEADERS });
  const { slug } = await params;
  const lead = await getCRMRepository().getLead(slug);
  if (!lead) return NextResponse.json({ error: "Not found" }, { status: 404, headers: NO_STORE_HEADERS });
  return NextResponse.json(lead, { headers: NO_STORE_HEADERS });
}

export async function PUT(request: NextRequest, { params }: { params: Promise<{ slug: string }> }) {
  if (!(await getOperatorSession())) return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers: NO_STORE_HEADERS });
  if (process.env.CRM_WRITE_ENABLED !== "true") {
    return NextResponse.json({ error: "Preview writes are disabled" }, { status: 423, headers: NO_STORE_HEADERS });
  }
  const invalid = validateMutationRequest(request);
  if (invalid) return NextResponse.json({ error: invalid }, { status: 403, headers: NO_STORE_HEADERS });
  const body = updateSchema.safeParse(await request.json());
  if (!body.success) return NextResponse.json({ error: "Invalid payload" }, { status: 400, headers: NO_STORE_HEADERS });
  const { slug } = await params;
  const lead = await getCRMRepository().updateLead(slug, body.data);
  return NextResponse.json(lead, { headers: NO_STORE_HEADERS });
}
