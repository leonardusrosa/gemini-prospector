import type { Lead, LeadUpdate, OutreachHistory } from "./types";

export interface CRMRepository {
  listLeads(): Promise<Lead[]>;
  getLead(slug: string): Promise<Lead | null>;
  updateLead(slug: string, update: LeadUpdate): Promise<Lead>;
  getOutreachHistory(slug: string): Promise<OutreachHistory[]>;
}
