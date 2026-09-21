import type { Lead } from "./crm/types";

export function proposalUrl(lead: Lead): string | null {
  if (lead.proposalUrl) return lead.proposalUrl;
  if (!lead.urlNova) return null;
  return lead.urlNova.endsWith("proposta.html") ? lead.urlNova : `${lead.urlNova.replace(/\/$/, "")}/proposta.html`;
}

export function candidateUrl(lead: Lead): string | null {
  return lead.candidateUrl;
}

export function liveUrl(lead: Lead): string | null {
  return lead.liveUrl;
}

export function maskDestination(value: string | null): string | null {
  if (!value) return null;
  if (value.includes("@")) {
    const [local, domain] = value.split("@");
    return `${local.slice(0, 2)}***@${domain}`;
  }
  const digits = value.replace(/\D/g, "");
  if (digits.length < 5) return "***";
  return `${digits.slice(0, 2)}***${digits.slice(-4)}`;
}
