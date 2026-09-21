import { DatabaseSync } from "node:sqlite";
import type { CRMRepository } from "./repository";
import type { Lead, LeadUpdate, OutreachHistory } from "./types";

export class SQLiteCRMRepository implements CRMRepository {
  private readonly db: DatabaseSync;
  private readonly readOnly: boolean;

  constructor(path: string, readOnly = true) {
    this.db = new DatabaseSync(path, { readOnly });
    this.readOnly = readOnly;
  }

  async listLeads(): Promise<Lead[]> {
    return (this.db.prepare("select * from leads order by nome collate nocase, slug").all() as Lead[]).map((lead) => ({
      ...lead,
      candidateUrl: lead.candidateUrl ?? null,
      liveUrl: lead.liveUrl ?? null,
      proposalUrl: lead.proposalUrl ?? null,
    }));
  }

  async getLead(slug: string): Promise<Lead | null> {
    const lead = (this.db.prepare("select * from leads where slug = ? limit 1").get(slug) as Lead | undefined) ?? null;
    return lead ? { ...lead, candidateUrl: lead.candidateUrl ?? null, liveUrl: lead.liveUrl ?? null, proposalUrl: lead.proposalUrl ?? null } : null;
  }

  async updateLead(slug: string, update: LeadUpdate): Promise<Lead> {
    if (this.readOnly) throw new Error("SQLite repository is read-only");
    const allowed = Object.entries(update).filter(([, value]) => value !== undefined);
    if (!allowed.length) {
      const current = await this.getLead(slug);
      if (!current) throw new Error("Lead not found");
      return current;
    }
    const set = allowed.map(([key]) => `"${key}" = ?`).join(", ");
    this.db.prepare(`update leads set ${set} where slug = ?`).run(...allowed.map(([, value]) => value), slug);
    const updated = await this.getLead(slug);
    if (!updated) throw new Error("Lead not found");
    return updated;
  }

  async getOutreachHistory(slug: string): Promise<OutreachHistory[]> {
    return this.db.prepare("select * from outreach_history where slug = ? order by id desc").all(slug) as OutreachHistory[];
  }
}
