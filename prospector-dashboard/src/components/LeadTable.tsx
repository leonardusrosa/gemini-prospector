"use client";

import { useMemo, useState } from "react";
import type { Lead } from "@/lib/crm/types";
import { proposalUrl } from "@/lib/presentation";

export function LeadTable({ leads }: { leads: Lead[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const statuses = useMemo(
    () => Array.from(new Set(leads.map((lead) => lead.status).filter(Boolean))).sort() as string[],
    [leads],
  );
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return leads.filter((lead) => {
      if (status && lead.status !== status) return false;
      if (!needle) return true;
      return [lead.nome, lead.slug, lead.cidade, lead.country, lead.nicho]
        .some((value) => value?.toLowerCase().includes(needle));
    });
  }, [leads, query, status]);

  return (
    <div className="card">
      <div className="toolbar">
        <input aria-label="Buscar leads" placeholder="Buscar leads" value={query} onChange={(event) => setQuery(event.target.value)} />
        <select aria-label="Filtrar por status" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">Todos os status</option>
          {statuses.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <span className="subtle">{filtered.length} de {leads.length}</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Lead</th><th>Status</th><th>Mercado</th><th>Contrato / pagamento</th><th>Ações</th></tr></thead>
          <tbody>
            {filtered.map((lead) => {
              const proposal = proposalUrl(lead);
              return (
                <tr key={lead.slug}>
                  <td><strong>{lead.nome ?? lead.slug}</strong><br /><span className="subtle">{lead.cidade ?? "—"}</span></td>
                  <td>{lead.status ?? "—"}</td>
                  <td>{[lead.country, lead.locale, lead.currency, lead.marketTier].filter(Boolean).join(" · ") || "—"}</td>
                  <td>{lead.contratoStatus ?? "—"} · {lead.pago ? "pago" : "não pago"}</td>
                  <td><div className="actions">
                    <a className="button" href={`/leads/${encodeURIComponent(lead.slug)}`}>abrir</a>
                    {proposal && <a className="button" href={proposal} target="_blank" rel="noreferrer">ver proposta ↗</a>}
                    {lead.urlNova && <a className="button" href={lead.urlNova} target="_blank" rel="noreferrer">site ↗</a>}
                  </div></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
