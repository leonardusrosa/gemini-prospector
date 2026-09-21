import { notFound } from "next/navigation";
import { requireOperator } from "@/lib/auth";
import { getCRMRepository } from "@/lib/crm";
import { candidateUrl, liveUrl, maskDestination, proposalUrl } from "@/lib/presentation";

export const dynamic = "force-dynamic";

export default async function LeadPage({ params }: { params: Promise<{ slug: string }> }) {
  await requireOperator();
  const { slug } = await params;
  const repo = getCRMRepository();
  const lead = await repo.getLead(slug);
  if (!lead) notFound();
  const history = await repo.getOutreachHistory(slug);
  const canonical = process.env.CRM_BACKEND === "postgres" && process.env.CRM_MODE === "canonical";
  const proposal = proposalUrl(lead);
  const fields = [
    ["Status", lead.status], ["Nicho", lead.nicho], ["Cidade", lead.cidade], ["País / locale", [lead.country, lead.locale].filter(Boolean).join(" · ")],
    ["Website status", lead.websiteStatus], ["Site mode", lead.siteMode], ["Nota / avaliações", lead.nota == null ? null : `${lead.nota} / ${lead.avaliacoes ?? "—"}`],
    ["Observações", lead.obs], ["Contrato", lead.contratoStatus], ["Contrato em", lead.contratoEm], ["Valor", lead.valor], ["Manutenção", lead.manutencao],
    ["Pagamento", lead.pago ? "pago" : "não pago"], ["Atualizado", lead.atualizado],
  ] as const;

  return (
    <main className="shell stack">
      <div className="topbar"><div><span className="badge">{canonical ? "CANÔNICO" : "PREVIEW"}</span><h1 className="title">{lead.nome ?? lead.slug}</h1><div className="subtle">{lead.slug}</div></div><a className="button" href="/">← Leads</a></div>
      <section className="card"><h2 className="section-title">Lead</h2><dl className="grid">{fields.map(([field, value]) => <div className="field" key={field}><dt>{field}</dt><dd>{value == null || value === "" ? "—" : String(value)}</dd></div>)}</dl></section>
      <section className="card"><h2 className="section-title">Links independentes</h2><div className="actions">{candidateUrl(lead) && <a className="button" href={candidateUrl(lead)!} target="_blank" rel="noreferrer">candidato ↗</a>}{liveUrl(lead) && <a className="button" href={liveUrl(lead)!} target="_blank" rel="noreferrer">ao vivo ↗</a>}{proposal && <a className="button" href={proposal} target="_blank" rel="noreferrer">proposta ↗</a>}{lead.siteAntigo && <a className="button" href={lead.siteAntigo} target="_blank" rel="noreferrer">site anterior ↗</a>}</div></section>
      <section className="card"><h2 className="section-title">Outreach review</h2><p className="subtle">Envio permanece desabilitado.</p><dl className="grid"><div className="field"><dt>Email</dt><dd>{maskDestination(lead.email) ?? "—"}</dd></div><div className="field"><dt>WhatsApp</dt><dd>{maskDestination(lead.whatsapp) ?? "—"}</dd></div><div className="field"><dt>Histórico</dt><dd>{history.length} registros</dd></div><div className="field"><dt>Ação</dt><dd>Somente revisão, sem endpoint de envio</dd></div></dl></section>
    </main>
  );
}
