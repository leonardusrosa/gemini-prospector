"use client";

import { useMemo, useState } from "react";
import type { Lead, LeadUpdate } from "@/lib/crm/types";
import { candidateUrl, liveUrl, proposalUrl } from "@/lib/presentation";

type View = "geral" | "pipeline" | "clientes" | "sites" | "comparador" | "followup" | "contratos" | "financeiro" | "config";
type RuntimeState = { mode: string; backend: string; writeEnabled: boolean; canonical: string; remoteStatus: string };

const STATUS_ORDER = ["discovered", "qualified", "redesigned", "published", "proposta_preparada", "contactado", "respondeu", "negociando", "fechado", "perdido"];
const STATUS_LABELS: Record<string, string> = {
  discovered: "Descoberto", qualified: "Qualificado", redesigned: "Redesenhado", published: "Publicado",
  proposta_preparada: "Proposta preparada", contactado: "Contactado", respondeu: "Respondeu",
  negociando: "Negociando", fechado: "Fechado", perdido: "Perdido", revisar: "Revisar",
};

function canonicalStatus(status: string | null) {
  const value = (status ?? "discovered").trim().toLowerCase();
  return ({ novo: "discovered", redesenhado: "redesigned", publicado: "published", proposta: "contactado", descartado: "perdido" } as Record<string, string>)[value] ?? value;
}

function label(status: string | null) {
  const key = canonicalStatus(status);
  return STATUS_LABELS[key] ?? (status || "Revisar");
}

function ageInDays(date: string | null) {
  if (!date) return 0;
  return Math.max(0, Math.floor((Date.now() - new Date(`${date}T12:00:00`).getTime()) / 86400000));
}

function isFollowup(lead: Lead) {
  const status = canonicalStatus(lead.status);
  return (status === "contactado" || status === "proposta_preparada") && ageInDays(lead.dataProposta) >= 4;
}

function hasSite(lead: Lead) {
  return Boolean(candidateUrl(lead) || liveUrl(lead) || proposalUrl(lead));
}

function money(value: number | null) {
  return value == null ? "—" : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

function LinkSet({ lead }: { lead: Lead }) {
  const candidate = candidateUrl(lead);
  const live = liveUrl(lead);
  const proposal = proposalUrl(lead);
  return (
    <div className="link-set">
      {candidate && <a href={candidate} target="_blank" rel="noreferrer">candidato ↗</a>}
      {live && <a href={live} target="_blank" rel="noreferrer">ao vivo ↗</a>}
      {proposal && <a href={proposal} target="_blank" rel="noreferrer">proposta ↗</a>}
      {lead.siteAntigo && <a href={lead.siteAntigo} target="_blank" rel="noreferrer">site anterior ↗</a>}
      {!candidate && !live && !proposal && <span className="muted">sem links verificados</span>}
    </div>
  );
}

function StatusPill({ status }: { status: string | null }) {
  return <span className={`status-pill status-${canonicalStatus(status)}`}>{label(status)}</span>;
}

export function DashboardShell({ initialLeads, operatorEmail, runtime }: { initialLeads: Lead[]; operatorEmail: string; runtime: RuntimeState }) {
  const [leads, setLeads] = useState(initialLeads);
  const [view, setView] = useState<View>("geral");
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"todos" | "redesign" | "new_site_concept">("todos");
  const [selected, setSelected] = useState<Lead | null>(null);
  const [theme, setTheme] = useState<"light" | "paper" | "dark">("light");
  const [saving, setSaving] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return leads.filter((lead) => {
      const searchable = [lead.nome, lead.nicho, lead.cidade, lead.status, lead.obs, lead.motivo, lead.country, lead.locale].filter(Boolean).join(" ").toLowerCase();
      if (needle && !searchable.includes(needle)) return false;
      if (mode === "redesign" && (!lead.siteAntigo || lead.siteMode === "new_site_concept")) return false;
      if (mode === "new_site_concept" && (lead.siteAntigo && lead.siteMode !== "new_site_concept")) return false;
      return true;
    });
  }, [leads, mode, query]);

  async function updateLead(slug: string, update: LeadUpdate) {
    setSaving(slug);
    setNotice(null);
    try {
      const response = await fetch(`/api/leads/${encodeURIComponent(slug)}`, {
        method: "PUT", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify(update),
      });
      if (!response.ok) throw new Error(`Falha ao salvar (${response.status})`);
      const updated = await response.json() as Lead;
      setLeads((current) => current.map((lead) => lead.slug === slug ? updated : lead));
      setSelected((current) => current?.slug === slug ? updated : current);
      setNotice("Alteração salva no CRM canônico.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Falha ao salvar alteração.");
    } finally {
      setSaving(null);
    }
  }

  function applyTheme(next: "light" | "paper" | "dark") {
    setTheme(next);
    document.documentElement.dataset.theme = next;
  }

  const active = filtered.filter((lead) => canonicalStatus(lead.status) !== "perdido");
  const proposals = filtered.filter((lead) => ["contactado", "proposta_preparada"].includes(canonicalStatus(lead.status)));
  const closed = filtered.filter((lead) => canonicalStatus(lead.status) === "fechado");
  const followups = filtered.filter(isFollowup);
  const revenue = closed.reduce((sum, lead) => sum + (lead.valor ?? 0), 0);
  const views: Array<[View, string, number | null]> = [
    ["geral", "Visão geral", null], ["pipeline", "Pipeline", active.length], ["clientes", "Clientes", filtered.length],
    ["sites", "Sites", filtered.filter(hasSite).length], ["comparador", "Comparador", filtered.filter((lead) => Boolean(lead.siteAntigo && (candidateUrl(lead) || liveUrl(lead)))).length],
    ["followup", "Follow-ups", followups.length], ["contratos", "Contratos", closed.length], ["financeiro", "Financeiro", null], ["config", "Configurações", null],
  ];

  function leadCard(lead: Lead) {
    return (
      <article className="lead-card" key={lead.slug} draggable onDragStart={(event) => event.dataTransfer.setData("text/plain", lead.slug)}>
        <div className="lead-card-title"><strong>{lead.nome ?? lead.slug}</strong><span className="market-badge">{lead.country ?? "—"}</span></div>
        <div className="lead-meta">{lead.cidade ?? "—"}{lead.nota != null ? ` · ★ ${lead.nota} (${lead.avaliacoes ?? "—"})` : ""}</div>
        {lead.motivo && <p className="lead-reason">{lead.motivo}</p>}
        {lead.obs && <p className="lead-note">{lead.obs}</p>}
        <LinkSet lead={lead} />
        <div className="card-actions"><button className="text-button" onClick={() => setSelected(lead)}>✎ dados</button>{saving === lead.slug && <span className="muted">salvando…</span>}</div>
      </article>
    );
  }

  function renderGeneral() {
    const funnel = STATUS_ORDER.filter((status) => status !== "perdido").map((status) => [status, filtered.filter((lead) => canonicalStatus(lead.status) === status).length] as const);
    const max = Math.max(1, ...funnel.map(([, count]) => count));
    return <div className="view-stack">
      <section className="stats-grid">
        <div className="metric"><strong>{active.length}</strong><span>Leads ativos</span></div>
        <div className="metric"><strong>{proposals.length}</strong><span>Propostas na rua</span></div>
        <div className="metric warning-metric"><strong>{followups.length}</strong><span>Follow-ups pendentes</span></div>
        <div className="metric success-metric"><strong>{closed.length}</strong><span>Fechados</span></div>
        <div className="metric success-metric"><strong>{money(revenue)}</strong><span>Receita fechada</span></div>
        <div className="metric"><strong>{money(active.length * 700)}</strong><span>Potencial de referência</span></div>
      </section>
      <section className="panel"><div className="section-heading"><div><span className="eyebrow">Operação</span><h2>Funil do pipeline</h2></div><span className="muted">CRM canônico</span></div><div className="funnel">{funnel.map(([status, count]) => <div className="funnel-row" key={status}><span>{STATUS_LABELS[status]}</span><div className="funnel-track"><i style={{ width: `${(count / max) * 100}%` }} /></div><b>{count}</b></div>)}</div></section>
      <section className="panel"><div className="section-heading"><div><span className="eyebrow">Atenção</span><h2>Follow-ups pendentes</h2></div><span className="muted">somente leitura</span></div>{followups.length ? <div className="follow-list">{followups.map((lead) => <div className="follow-row" key={lead.slug}><strong>{lead.nome}</strong><span>{ageInDays(lead.dataProposta)} dias · proposta em {lead.dataProposta}</span><button className="text-button" onClick={() => setSelected(lead)}>abrir dados</button></div>)}</div> : <p className="empty">Nenhum follow-up pendente.</p>}</section>
    </div>;
  }

  function renderPipeline() {
    return <div className="view-stack"><p className="hint">Arraste um card para mudar o status. O envio de outreach permanece desabilitado.</p><div className="board">{[...STATUS_ORDER].map((status) => <section className="board-column" key={status} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { const slug = event.dataTransfer.getData("text/plain"); if (slug) void updateLead(slug, { status }); }}><h3>{STATUS_LABELS[status]} <span>{filtered.filter((lead) => canonicalStatus(lead.status) === status).length}</span></h3><div className="board-cards">{filtered.filter((lead) => canonicalStatus(lead.status) === status).map(leadCard)}</div></section>)}</div></div>;
  }

  function renderClients() {
    return <section className="panel table-panel"><div className="section-heading"><div><span className="eyebrow">Base de leads</span><h2>Clientes</h2></div><div className="filter-row"><button className={mode === "todos" ? "filter-button active" : "filter-button"} onClick={() => setMode("todos")}>Todos</button><button className={mode === "redesign" ? "filter-button active" : "filter-button"} onClick={() => setMode("redesign")}>Site fraco</button><button className={mode === "new_site_concept" ? "filter-button active" : "filter-button"} onClick={() => setMode("new_site_concept")}>Sem site</button></div></div><div className="table-scroll"><table><thead><tr><th>Cliente</th><th>Mercado</th><th>Status</th><th>Valor</th><th>Links</th></tr></thead><tbody>{filtered.map((lead) => <tr key={lead.slug}><td><strong>{lead.nome ?? lead.slug}</strong><small>{lead.email ?? "sem e-mail"}</small></td><td>{[lead.country, lead.locale, lead.cidade].filter(Boolean).join(" · ") || "—"}</td><td><StatusPill status={lead.status} /></td><td>{money(lead.valor)}</td><td><LinkSet lead={lead} /><button className="text-button" onClick={() => setSelected(lead)}>editar</button></td></tr>)}</tbody></table></div></section>;
  }

  function renderSites() {
    const sites = filtered.filter(hasSite);
    return <div className="sites-grid">{sites.length ? sites.map((lead) => { const preview = candidateUrl(lead) || liveUrl(lead); return <article className="site-card" key={lead.slug}><div className="site-preview">{preview ? <iframe src={preview} title={`Prévia de ${lead.nome ?? lead.slug}`} loading="lazy" /> : <div className="empty">Sem prévia</div>}</div><div className="site-card-body"><div className="section-heading"><div><strong>{lead.nome ?? lead.slug}</strong><span className="lead-meta">{lead.cidade ?? "—"}</span></div><StatusPill status={lead.status} /></div><LinkSet lead={lead} /><button className="button secondary" onClick={() => setSelected(lead)}>abrir dados</button></div></article>; }) : <section className="panel"><p className="empty">Nenhum site com URL verificada.</p></section>}</div>;
  }

  function renderComparator() {
    const comparable = filtered.filter((lead) => lead.siteAntigo && (candidateUrl(lead) || liveUrl(lead)));
    return <section className="panel"><div className="section-heading"><div><span className="eyebrow">Antes / atual</span><h2>Comparador</h2></div><span className="muted">somente quando as duas URLs existem</span></div>{comparable.length ? <div className="compare-grid">{comparable.map((lead) => <article key={lead.slug} className="compare-card"><h3>{lead.nome ?? lead.slug}</h3><div className="compare-columns"><div><span>Presença anterior</span><a href={lead.siteAntigo!} target="_blank" rel="noreferrer">abrir site anterior ↗</a></div><div><span>Candidate / live</span><LinkSet lead={lead} /></div></div></article>)}</div> : <p className="empty">Nenhum lead tem URLs suficientes para comparação.</p>}</section>;
  }

  function renderFollowup() { return <section className="panel"><div className="section-heading"><div><span className="eyebrow">Ritmo comercial</span><h2>Follow-ups</h2></div><span className="muted">outreach desabilitado</span></div>{followups.length ? <div className="follow-list">{followups.map((lead) => <div className="follow-row" key={lead.slug}><strong>{lead.nome}</strong><span>{lead.dataProposta ?? "sem data"} · {ageInDays(lead.dataProposta)} dias</span><button className="text-button" onClick={() => setSelected(lead)}>ver lead</button></div>)}</div> : <p className="empty">Nenhum follow-up pendente.</p>}</section>; }

  function renderContracts() { return <section className="panel table-panel"><div className="section-heading"><div><span className="eyebrow">Documentos</span><h2>Contratos</h2></div><span className="muted">status e pagamento, sem envio</span></div>{closed.length ? <div className="table-scroll"><table><thead><tr><th>Cliente</th><th>Valor</th><th>Contrato</th><th>Data</th><th>Pago</th></tr></thead><tbody>{closed.map((lead) => <tr key={lead.slug}><td><strong>{lead.nome}</strong></td><td>{money(lead.valor)}</td><td><select value={lead.contratoStatus ?? "pendente"} onChange={(event) => void updateLead(lead.slug, { contratoStatus: event.target.value })}><option value="pendente">pendente</option><option value="enviado">enviado</option><option value="assinado">assinado</option></select></td><td>{lead.contratoEm ?? "—"}</td><td><input type="checkbox" checked={Boolean(lead.pago)} onChange={(event) => void updateLead(lead.slug, { pago: event.target.checked ? 1 : 0 })} /></td></tr>)}</tbody></table></div> : <p className="empty">Nenhum cliente fechado.</p>}</section>; }

  function renderFinance() { const received = closed.filter((lead) => lead.pago).reduce((sum, lead) => sum + (lead.valor ?? 0), 0); const due = closed.filter((lead) => !lead.pago).reduce((sum, lead) => sum + (lead.valor ?? 0), 0); const mrr = closed.reduce((sum, lead) => sum + (lead.manutencao ?? 0), 0); return <div className="view-stack"><section className="stats-grid"><div className="metric success-metric"><strong>{money(received)}</strong><span>Recebido</span></div><div className="metric warning-metric"><strong>{money(due)}</strong><span>A receber</span></div><div className="metric"><strong>{money(mrr)}</strong><span>Manutenções / mês</span></div><div className="metric success-metric"><strong>{money(received + due + mrr * 12)}</strong><span>Projeção 12 meses</span></div></section><section className="panel"><h2>Como o financeiro se alimenta</h2><p className="muted">Valor, manutenção, contrato e pagamento vêm dos campos persistidos do CRM. Esta tela não envia contratos nem dispara cobrança.</p></section></div>; }

  function renderConfig() { return <div className="view-stack"><section className="panel"><div className="section-heading"><div><span className="eyebrow">Estado operacional</span><h2>Configurações seguras</h2></div><span className="status-pill status-published">canônico</span></div><dl className="config-list"><div><dt>CRM</dt><dd>{runtime.canonical}</dd></div><div><dt>Backend</dt><dd>{runtime.backend}</dd></div><div><dt>Persistência</dt><dd>{runtime.writeEnabled ? "habilitada para operador" : "somente leitura"}</dd></div><div><dt>Banco remoto</dt><dd>{runtime.remoteStatus}</dd></div><div><dt>Outreach</dt><dd>desabilitado</dd></div><div><dt>SQLite local</dt><dd>backup somente leitura, não usado pelo hosted app</dd></div></dl></section><section className="panel"><h2>Limites do painel</h2><p className="muted">Contratos, outreach, credenciais e integrações externas não são disparados por esta interface. Alterações estruturais permanecem fora do painel.</p></section></div>; }

  const content = { geral: renderGeneral(), pipeline: renderPipeline(), clientes: renderClients(), sites: renderSites(), comparador: renderComparator(), followup: renderFollowup(), contratos: renderContracts(), financeiro: renderFinance(), config: renderConfig() }[view];
  return <div className={`dashboard-app theme-${theme}`}>
    <aside className="sidebar"><div className="brand"><span className="brand-mark">✦</span><span>Prospector</span></div><nav className="sidebar-nav">{views.map(([key, title, count]) => <button key={key} className={view === key ? "nav-item active" : "nav-item"} onClick={() => setView(key)}>{title}{count != null && <span>{count}</span>}</button>)}</nav><div className="sidebar-footer"><span className="muted">operador</span><strong>{operatorEmail}</strong><form action="/api/auth/logout" method="post"><button className="logout-button" type="submit">Sair</button></form></div></aside>
    <main className="dashboard-main"><header className="dashboard-topbar"><div><span className="eyebrow">Prospector / CRM</span><h1>{views.find(([key]) => key === view)?.[1]}</h1><span className="muted">atualizado em tempo real · {runtime.canonical}</span></div><div className="topbar-actions"><input aria-label="Buscar cliente, nicho ou cidade" placeholder="Buscar cliente, nicho ou cidade…" value={query} onChange={(event) => setQuery(event.target.value)} /><button className="theme-button" onClick={() => applyTheme(theme === "light" ? "paper" : theme === "paper" ? "dark" : "light")}>{theme === "light" ? "Claro" : theme === "paper" ? "Papel" : "Escuro"}</button></div></header>{notice && <div className="notice" role="status">{notice}</div>}{content}</main>
    {selected && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}><section className="edit-modal" role="dialog" aria-modal="true"><div className="section-heading"><div><span className="eyebrow">Lead</span><h2>{selected.nome ?? selected.slug}</h2><span className="muted">{selected.slug}</span></div><button className="close-button" onClick={() => setSelected(null)} aria-label="Fechar">×</button></div><div className="edit-grid"><label>Status<select value={selected.status ?? "discovered"} onChange={(event) => setSelected({ ...selected, status: event.target.value })}>{STATUS_ORDER.map((status) => <option key={status} value={status}>{STATUS_LABELS[status]}</option>)}</select></label><label>Valor<input type="number" value={selected.valor ?? ""} onChange={(event) => setSelected({ ...selected, valor: event.target.value === "" ? null : Number(event.target.value) })} /></label><label className="wide">Observações<textarea value={selected.obs ?? ""} onChange={(event) => setSelected({ ...selected, obs: event.target.value })} /></label><label>Contrato<select value={selected.contratoStatus ?? "pendente"} onChange={(event) => setSelected({ ...selected, contratoStatus: event.target.value })}><option value="pendente">pendente</option><option value="enviado">enviado</option><option value="assinado">assinado</option></select></label><label>Pago<select value={selected.pago ? "1" : "0"} onChange={(event) => setSelected({ ...selected, pago: Number(event.target.value) })}><option value="0">não pago</option><option value="1">pago</option></select></label></div><div className="edit-links"><span className="eyebrow">Links independentes</span><LinkSet lead={selected} /></div><div className="modal-actions"><button className="button secondary" onClick={() => setSelected(null)}>Cancelar</button><button className="button primary" onClick={() => { const { slug, status, valor, obs, contratoStatus, pago } = selected; void updateLead(slug, { status, valor, obs, contratoStatus, pago }); }}>Salvar alterações</button></div></section></div>}
  </div>;
}
