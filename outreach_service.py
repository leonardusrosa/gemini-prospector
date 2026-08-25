#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector — Serviço de Outreach Multicanal (WhatsApp + Gmail).
Gera mensagens factuais, seleciona canais por prioridade e registra histórico no CRM.
"""

import datetime
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

try:
    from evolution_client import EvolutionClient
except ImportError:
    EvolutionClient = None


def resolve_proposal_url(lead: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Monta a URL pública definitiva ou fallback local da proposta."""
    slug = lead.get("slug", "")
    deploy = config.get("deploy", {})
    domain = deploy.get("domain", "").strip()
    base_path = deploy.get("basePath", "clientes").strip().strip("/")

    if domain:
        if not domain.startswith("http://") and not domain.startswith("https://"):
            domain = "https://" + domain
        return f"{domain}/{base_path}/{slug}/proposta.html"

    # Fallback para urlNova ou caminho local relativo
    url_nova = lead.get("urlNova", "").strip()
    if url_nova and url_nova.startswith("http"):
        if not url_nova.endswith("proposta.html"):
            url_nova = url_nova.rstrip("/") + "/proposta.html"
        return url_nova

    return f"sites/{slug}/proposta.html"


def resolve_channels(lead: Dict[str, Any], config: Dict[str, Any], evo_status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Identifica os canais reais disponíveis e escolhe o recomendado com base na prioridade."""
    outreach_cfg = config.get("outreach", {})
    priority = outreach_cfg.get("channelPriority", ["whatsapp", "email"])

    # Verificação do WhatsApp
    raw_phone = lead.get("whatsapp") or lead.get("telefone") or ""
    clean_wpp, wpp_err = (None, "Cliente Evolution não carregado")
    if EvolutionClient:
        clean_wpp, wpp_err = EvolutionClient.validate_phone_number(raw_phone)

    evo_online = False
    if evo_status and evo_status.get("reachable") and evo_status.get("authenticated") and evo_status.get("instanceFound"):
        state = evo_status.get("connectionState")
        evo_online = (state == "open") or (not evo_status.get("connectionStateSupported"))

    wpp_available = bool(clean_wpp and evo_online)

    # Verificação de E-mail
    raw_email = (lead.get("email") or "").strip()
    email_available = bool(raw_email and "@" in raw_email and "." in raw_email)

    # Seleção de canal com base nas prioridades configuradas
    selected = None
    reason = "Nenhum canal de contato válido encontrado."

    for ch in priority:
        if ch == "whatsapp" and wpp_available:
            selected = "whatsapp"
            reason = "WhatsApp selecionado (número validado com DDI e Evolution API online)."
            break
        elif ch == "email" and email_available:
            selected = "email"
            reason = "E-mail selecionado (e-mail confirmado no cadastro do lead)."
            break

    # Fallback se a primeira prioridade não estiver disponível
    if not selected:
        if wpp_available:
            selected = "whatsapp"
            reason = "WhatsApp disponível como alternativa."
        elif email_available:
            selected = "email"
            reason = "E-mail disponível como alternativa."

    masked_wpp = EvolutionClient.mask_phone_number(clean_wpp) if (EvolutionClient and clean_wpp) else raw_phone

    return {
        "selectedChannel": selected,
        "channelReason": reason,
        "whatsappAvailable": wpp_available,
        "whatsappNumber": clean_wpp,
        "whatsappMasked": masked_wpp,
        "whatsappError": wpp_err if not clean_wpp else (None if evo_online else "Evolution API desconectada"),
        "emailAvailable": email_available,
        "email": raw_email if email_available else None,
        "priority": priority,
    }


SOCIAL_OR_DIRECTORY_DOMAINS = [
    "instagram.com", "facebook.com", "fb.com", "linktr.ee", "linktree.com",
    "wa.me", "api.whatsapp.com", "whatsapp.com", "google.com/maps", "maps.google.com",
    "doctoralia.com.br", "localtreino.com.br", "ifood.com.br", "tripadvisor.com"
]


def classify_website(raw_url: Optional[str]) -> Tuple[str, str]:
    """
    Classifica o status do site e o modo de geração do lead.
    Retorna (website_status, site_mode).
    Valores possíveis:
      website_status: 'existing_weak' | 'none' | 'healthy' | 'unknown'
      site_mode: 'redesign' | 'new_site_concept' | 'none'
    """
    if not raw_url or not isinstance(raw_url, str) or not raw_url.strip():
        return "none", "new_site_concept"

    clean_url = raw_url.strip().lower()
    if any(domain in clean_url for domain in SOCIAL_OR_DIRECTORY_DOMAINS):
        return "none", "new_site_concept"

    if clean_url.startswith("http://") or clean_url.startswith("https://") or "." in clean_url:
        return "existing_weak", "redesign"

    return "unknown", "none"


def generate_messages(lead: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Gera mensagens hiperpersonalizadas estritamente baseadas em dados factuais do lead."""
    nome_lead = (lead.get("nome") or "Profissional").strip()
    nicho = (lead.get("nicho") or "").strip()
    cidade = (lead.get("cidade") or "").strip()
    nota = lead.get("nota")
    avaliacoes = lead.get("avaliacoes")
    site_antigo = (lead.get("siteAntigo") or "").strip()
    motivo = (lead.get("motivo") or "").strip()

    site_mode = lead.get("siteMode")
    website_status = lead.get("websiteStatus")
    if not site_mode or not website_status:
        st, md = classify_website(site_antigo)
        website_status = website_status or st
        site_mode = site_mode or md

    is_new_site = (site_mode == "new_site_concept") or (website_status == "none") or not site_antigo

    assinatura = config.get("assinatura", {})
    autor = assinatura.get("nome", "").strip() or "Especialista em Web"
    apresentacao = assinatura.get("apresentacao", "").strip() or "Criação e Redesign de Páginas"
    wpp_autor = assinatura.get("whatsapp", "").strip()

    proposal_url = resolve_proposal_url(lead, config)

    # 1. Mensagem de WhatsApp (~60-100 palavras, natural, 1 link, sem marketing)
    saudacao = f"Olá, {nome_lead}! Tudo bem?"
    
    contexto_prova = ""
    if nota and avaliacoes:
        contexto_prova = f"Vi o trabalho excelente de vocês em {cidade or 'sua região'} (nota {nota} no Google com {avaliacoes} avaliações)."
    elif nicho:
        contexto_prova = f"Acompanho o trabalho de referência de vocês na área de {nicho}."

    if is_new_site:
        wpp_text = (
            f"{saudacao}\n\n"
            f"{contexto_prova} Como notei que vocês ainda não possuem um site próprio oficial para facilitar o contato e agendamento de clientes, tomei a liberdade de preparar um conceito exclusivo para demonstração:\n"
            f"{proposal_url}\n\n"
            f"Dá uma olhada quando puder (abre muito bem no celular). Me conta o que achou!\n\n"
            f"— {autor}"
        ).strip()
        
        assunto = f"{nome_lead}, uma ideia de site próprio para o seu negócio"
        if len(assunto) > 60:
            assunto = f"Conceito de site para a {nome_lead[:35]}"

        email_body_html = f"""<p>Olá, {nome_lead},</p>

<p>{contexto_prova or 'Encontrei o negócio de vocês enquanto pesquisava referências na sua área.'}</p>

<p>Notei que o negócio ainda não conta com uma página web oficial própria para centralizar informações, localização e facilitar o agendamento direto de novos clientes.</p>

<p>Para ilustrar na prática como uma presença digital profissional pode valorizar o trabalho de vocês, montei uma proposta de site completa e deixei no ar para demonstração:</p>

<p><a href="{proposal_url}">{proposal_url}</a></p>

<p>A página fica disponível para você avaliar com calma no computador ou no celular. Se gostar da ideia, fico à disposição para conversarmos sem qualquer compromisso.</p>

<p>Um abraço,<br>
<b>{autor}</b><br>
{apresentacao}<br>
{wpp_autor and f'WhatsApp: {wpp_autor}' or ''}</p>"""
    else:
        obs_site = "Notei que a página atual tem muito potencial de melhoria na leitura pelo celular e no agendamento direto."
        if motivo:
            obs_site = f"Notei que no site atual {motivo.lower()}."

        wpp_text = (
            f"{saudacao}\n\n"
            f"{contexto_prova} {obs_site}\n\n"
            f"Por conta disso, tomei a liberdade de preparar um conceito novo e mais moderno para vocês, que já deixei publicado para demonstração:\n"
            f"{proposal_url}\n\n"
            f"Dá uma olhada quando puder (abre muito bem no celular). Me conta o que achou!\n\n"
            f"— {autor}"
        ).strip()

        assunto = f"{nome_lead}, posso te mostrar uma ideia para o site?"
        if len(assunto) > 60:
            assunto = f"Uma nova ideia para a {nome_lead[:35]}"

        email_body_html = f"""<p>Olá, {nome_lead},</p>

<p>{contexto_prova or 'Encontrei o negócio de vocês enquanto pesquisava referências na sua área.'}</p>

<p>Ao analisar a página atual ({site_antigo or 'do consultório'}), notei alguns pontos objetivos que podem estar dificultando a conversão de novos clientes, especialmente na navegação via celular e na rapidez de agendamento.</p>

<p>Para ilustrar na prática, montei uma nova versão completa do site e coloquei no ar para você comparar o antes e depois:</p>

<p><a href="{proposal_url}">{proposal_url}</a></p>

<p>A página fica disponível para você avaliar com calma no computador ou no celular. Se gostar do conceito, fico à disposição para conversarmos sem qualquer compromisso.</p>

<p>Um abraço,<br>
<b>{autor}</b><br>
{apresentacao}<br>
{wpp_autor and f'WhatsApp: {wpp_autor}' or ''}</p>"""

    gmail_compose_url = ""
    if lead.get("email"):
        params = {
            "view": "cm",
            "fs": "1",
            "to": lead.get("email", ""),
            "su": assunto,
            "body": re.sub(r"<[^>]+>", "", email_body_html),
        }
        gmail_compose_url = "https://mail.google.com/mail/?" + urllib.parse.urlencode(params)

    return {
        "proposalUrl": proposal_url,
        "whatsapp": {
            "text": wpp_text,
            "wordCount": len(wpp_text.split()),
        },
        "email": {
            "subject": assunto,
            "bodyHtml": email_body_html,
            "bodyPlain": re.sub(r"<[^>]+>", "", email_body_html),
            "composeUrl": gmail_compose_url,
            "wordCount": len(re.sub(r"<[^>]+>", "", email_body_html).split()),
        },
    }


def record_outreach_history(
    conn,
    slug: str,
    canal: str,
    destino: str,
    mensagem: str,
    url_proposta: str,
    mensagem_id: Optional[str] = None,
    status: str = "enviado",
    tipo: str = "proposta",
) -> int:
    """Registra uma interação de outreach no histórico append-only do banco SQLite."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS outreach_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL,
            canal TEXT NOT NULL,
            destino TEXT,
            tipo TEXT DEFAULT 'proposta',
            mensagem TEXT,
            urlProposta TEXT,
            mensagemId TEXT,
            status TEXT DEFAULT 'enviado',
            criadoEm TEXT DEFAULT (datetime('now','localtime'))
        )"""
    )
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO outreach_history (slug, canal, destino, tipo, mensagem, urlProposta, mensagemId, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (slug, canal, destino, tipo, mensagem, url_proposta, mensagem_id or "", status),
    )
    # Atualiza o lead para status 'proposta' e registra a data
    today_iso = datetime.date.today().isoformat()
    cur.execute(
        """UPDATE leads SET status='proposta', dataProposta=COALESCE(dataProposta, ?), atualizado=datetime('now','localtime')
           WHERE slug=?""",
        (today_iso, slug),
    )
    conn.commit()
    return cur.lastrowid


def get_outreach_history(conn, slug: str) -> List[Dict[str, Any]]:
    """Recupera o histórico completo de comunicações de um lead."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS outreach_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL,
            canal TEXT NOT NULL,
            destino TEXT,
            tipo TEXT DEFAULT 'proposta',
            mensagem TEXT,
            urlProposta TEXT,
            mensagemId TEXT,
            status TEXT DEFAULT 'enviado',
            criadoEm TEXT DEFAULT (datetime('now','localtime'))
        )"""
    )
    cur = conn.cursor()
    cur.execute(
        """SELECT id, slug, canal, destino, tipo, mensagem, urlProposta, mensagemId, status, criadoEm
           FROM outreach_history WHERE slug=? ORDER BY id DESC""",
        (slug,),
    )
    cols = ["id", "slug", "canal", "destino", "tipo", "mensagem", "urlProposta", "mensagemId", "status", "criadoEm"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
