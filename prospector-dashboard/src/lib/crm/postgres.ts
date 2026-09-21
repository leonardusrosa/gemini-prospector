import type { CRMRepository } from "./repository";
import type { Lead, LeadUpdate, OutreachHistory } from "./types";

type PostgresLead = Omit<Lead, "candidateUrl" | "liveUrl" | "proposalUrl"> & {
  candidate_url?: string | null;
  live_url?: string | null;
  proposal_url?: string | null;
};

function mapLead(row: PostgresLead): Lead {
  return {
    ...row,
    candidateUrl: row.candidate_url ?? null,
    liveUrl: row.live_url ?? null,
    proposalUrl: row.proposal_url ?? null,
  };
}

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing server environment variable: ${name}`);
  return value;
}

function headers(): HeadersInit {
  const key = required("SUPABASE_SERVICE_ROLE_KEY");
  return {
    apikey: key,
    Authorization: `Bearer ${key}`,
    "Content-Type": "application/json",
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${required("SUPABASE_URL")}/rest/v1/${path}`;
  const response = await fetch(url, {
    ...init,
    headers: { ...headers(), ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`CRM request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export class PostgresCRMRepository implements CRMRepository {
  async listLeads(): Promise<Lead[]> {
    const rows = await request<PostgresLead[]>("leads?select=*&order=nome.asc.nullslast,slug.asc");
    return rows.map(mapLead);
  }

  async getLead(slug: string): Promise<Lead | null> {
    const rows = await request<Lead[]>(`leads?slug=eq.${encodeURIComponent(slug)}&select=*&limit=1`);
    return rows[0] ? mapLead(rows[0]) : null;
  }

  async updateLead(slug: string, update: LeadUpdate): Promise<Lead> {
    if (process.env.CRM_WRITE_ENABLED !== "true") {
      throw new Error("Preview database is read-only");
    }
    const rows = await request<PostgresLead[]>(`leads?slug=eq.${encodeURIComponent(slug)}&select=*`, {
      method: "PATCH",
      headers: { Prefer: "return=representation" },
      body: JSON.stringify({
        ...update,
        ...(update.candidateUrl !== undefined ? { candidate_url: update.candidateUrl } : {}),
        ...(update.liveUrl !== undefined ? { live_url: update.liveUrl } : {}),
        ...(update.proposalUrl !== undefined ? { proposal_url: update.proposalUrl } : {}),
        candidateUrl: undefined,
        liveUrl: undefined,
        proposalUrl: undefined,
      }),
    });
    if (!rows[0]) throw new Error("Lead not found");
    return mapLead(rows[0]);
  }

  async getOutreachHistory(slug: string): Promise<OutreachHistory[]> {
    return request<OutreachHistory[]>(
      `outreach_history?slug=eq.${encodeURIComponent(slug)}&select=*&order=id.desc`,
    );
  }
}
