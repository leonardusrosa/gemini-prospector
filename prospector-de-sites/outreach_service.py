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

try:
    from market_service import detect_country, normalize_phone_by_country, resolve_market
except ImportError:
    detect_country = lambda *a, **k: ("BR", "pt-BR", "pt", "55")
    normalize_phone_by_country = lambda r, c=None: (r, None)
    resolve_market = lambda c="BR": {"country": "BR", "locale": "pt-BR", "language": "pt", "phoneCountryCode": "55"}


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

    market_cfg = config.get("market", {})
    def_country = market_cfg.get("defaultCountry", "BR")

    lead_country = lead.get("country")
    if not lead_country:
        lead_country, _, _, _ = detect_country(lead.get("cidade"), lead.get("endCliente"), def_country)

    # Verificação do WhatsApp com validação por país
    raw_phone = lead.get("whatsapp") or lead.get("telefone") or ""
    clean_wpp, wpp_err = (None, "Cliente Evolution não carregado")
    if EvolutionClient:
        clean_wpp, wpp_err = EvolutionClient.validate_phone_number(raw_phone, country=lead_country)
    else:
        clean_wpp, wpp_err = normalize_phone_by_country(raw_phone, country=lead_country)

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
            reason = f"WhatsApp selecionado (número validado com DDI e Evolution API online - {lead_country})."
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
        "country": lead_country,
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
    """Gera mensagens factuais deixando claro que o preview é a primeira proposta funcional, não o site final."""
    nome_lead = (lead.get("nome") or "Profissional").strip()
    nicho = (lead.get("nicho") or "").strip()
    cidade = (lead.get("cidade") or "").strip()
    nota = lead.get("nota")
    avaliacoes = lead.get("avaliacoes")
    site_antigo = (lead.get("siteAntigo") or "").strip()
    motivo = (lead.get("motivo") or "").strip()

    market_cfg = config.get("market", {})
    def_country = market_cfg.get("defaultCountry", "BR")

    lead_country = lead.get("country")
    if not lead_country:
        lead_country, locale, _, _ = detect_country(cidade, lead.get("endCliente"), def_country)
    else:
        locale = lead.get("locale") or ("pt-PT" if lead_country == "PT" else "pt-BR")

    is_pt = (lead_country == "PT") or (locale == "pt-PT")

    site_mode = lead.get("siteMode")
    website_status = lead.get("websiteStatus")
    if not site_mode or not website_status:
        st, md = classify_website(site_antigo)
        website_status = website_status or st
        site_mode = site_mode or md

    is_new_site = (site_mode == "new_site_concept") or (website_status == "none") or not site_antigo

    assinatura = config.get("assinatura", {})
    autor = assinatura.get("nome", "").strip() or "Especialista em Web"
    apresentacao = assinatura.get("apresentacao", "").strip() or ("Criação e Redesign de Páginas" if not is_pt else "Design e Criação de Páginas Web")
    wpp_autor = assinatura.get("whatsapp", "").strip()

    proposal_url = resolve_proposal_url(lead, config)

    saudacao = f"Olá, {nome_lead}! Tudo bem?"

    if is_pt:
        # European Portuguese (pt-PT)
        contexto_prova = ""
        if nota and avaliacoes:
            contexto_prova = f"Acompanho o vosso trabalho de referência em {cidade or 'sua região'} (classificação {nota} no Google com {avaliacoes} avaliações)."
        elif nicho:
            contexto_prova = f"Acompanho o vosso trabalho de referência na área de {nicho}."

        if is_new_site:
            wpp_text = (
                f"{saudacao}\n\n"
                f"{contexto_prova} Como reparei que ainda não dispõem de um site oficial próprio para centralizar contactos e marcações diretas, tomei a liberdade de preparar uma primeira proposta funcional de site e deixei-a online para demonstração:\n"
                f"{proposal_url}\n\n"
                f"É um ponto de partida; se a direção fizer sentido, a versão final é refinada em conjunto antes da publicação definitiva. Veja quando tiver oportunidade e diga-me o que achou.\n\n"
                f"— {autor}"
            ).strip()

            assunto = f"{nome_lead}, uma proposta de site próprio para o vosso espaço"
            if len(assunto) > 60:
                assunto = f"Proposta de site para {nome_lead[:35]}"

            email_body_html = f"""<p>Olá, {nome_lead},</p>

<p>{contexto_prova or 'Encontrei o vosso negócio enquanto pesquisava referências na vossa área.'}</p>

<p>Reparei que o negócio ainda não conta com uma página web oficial própria para centralizar informações, localização e facilitar marcações diretas de novos clientes.</p>

<p>Para mostrar na prática uma possível direção, preparei uma primeira proposta funcional de site e deixei-a online para demonstração:</p>

<p><a href="{proposal_url}">{proposal_url}</a></p>

<p>Esta é uma primeira versão para demonstração e serve como ponto de partida. Se a direção fizer sentido, a versão final é refinada em conjunto — textos, imagens, prioridades e restantes ajustes — antes da publicação definitiva.</p>

<p>A página fica disponível para avaliar com calma no computador ou no telemóvel. Se gostar da proposta, fico ao dispor para conversarmos sem qualquer compromisso.</p>

<p>Com os melhores cumprimentos,<br>
<b>{autor}</b><br>
{apresentacao}<br>
{wpp_autor and f'WhatsApp: {wpp_autor}' or ''}</p>"""
        else:
            obs_site = "Notei que a página atual tem potencial de melhoria na leitura no telemóvel e na rapidez de marcação."
            if motivo:
                obs_site = f"Notei que no site atual {motivo.lower()}."

            wpp_text = (
                f"{saudacao}\n\n"
                f"{contexto_prova} {obs_site}\n\n"
                f"Por esse motivo, preparei uma primeira proposta de nova versão do site, já funcional, para mostrar a direção na prática:\n"
                f"{proposal_url}\n\n"
                f"É uma primeira versão; se fizer sentido, refinamos em conjunto antes da entrega final. Veja quando tiver oportunidade e diga-me o que achou.\n\n"
                f"— {autor}"
            ).strip()

            assunto = f"{nome_lead}, posso mostrar-lhe uma ideia para o vosso site?"
            if len(assunto) > 60:
                assunto = f"Uma nova ideia para {nome_lead[:35]}"

            email_body_html = f"""<p>Olá, {nome_lead},</p>

<p>{contexto_prova or 'Encontrei o vosso negócio enquanto pesquisava referências na vossa área.'}</p>

<p>Ao analisar a página atual ({site_antigo or 'do espaço'}), notei alguns pontos objetivos que podem estar a dificultar a conversão de novos clientes, especialmente na navegação via telemóvel e na rapidez de contacto.</p>

<p>Para mostrar uma possível direção na prática, montei uma primeira proposta de nova versão do site, já funcional, e coloquei-a online para poder comparar o antes e depois:</p>

<p><a href="{proposal_url}">{proposal_url}</a></p>

<p>Esta é uma primeira versão para demonstração. Se a direção fizer sentido, a versão final é refinada em conjunto — textos, imagens, prioridades e restantes ajustes — antes da publicação definitiva.</p>

<p>A página fica disponível para avaliar com calma no computador ou no telemóvel. Se gostar do conceito, fico ao dispor para conversarmos sem qualquer compromisso.</p>

<p>Com os melhores cumprimentos,<br>
<b>{autor}</b><br>
{apresentacao}<br>
{wpp_autor and f'WhatsApp: {wpp_autor}' or ''}</p>"""

    else:
        # Brazilian Portuguese (pt-BR)
        contexto_prova = ""
        if nota and avaliacoes:
            contexto_prova = f"Vi o trabalho excelente de vocês em {cidade or 'sua região'} (nota {nota} no Google com {avaliacoes} avaliações)."
        elif nicho:
            contexto_prova = f"Acompanho o trabalho de referência de vocês na área de {nicho}."

        if is_new_site:
            wpp_text = (
                f"{saudacao}\n\n"
                f"{contexto_prova} Como notei que vocês ainda não possuem um site próprio oficial para facilitar o contato e agendamento de clientes, tomei a liberdade de preparar uma primeira proposta funcional de site e deixei online para demonstração:\n"
                f"{proposal_url}\n\n"
                f"Ela serve como ponto de partida; se a direção fizer sentido, a versão final é refinada em conjunto antes da publicação definitiva. Dá uma olhada quando puder e me conta o que achou.\n\n"
                f"— {autor}"
            ).strip()

            assunto = f"{nome_lead}, uma ideia de site próprio para o seu negócio"
            if len(assunto) > 60:
                assunto = f"Conceito de site para a {nome_lead[:35]}"

            email_body_html = f"""<p>Olá, {nome_lead},</p>

<p>{contexto_prova or 'Encontrei o negócio de vocês enquanto pesquisava referências na sua área.'}</p>

<p>Notei que o negócio ainda não conta com uma página web oficial própria para centralizar informações, localização e facilitar o agendamento direto de novos clientes.</p>

<p>Para mostrar na prática uma possível direção, montei uma primeira proposta funcional de site e deixei no ar para demonstração:</p>

<p><a href="{proposal_url}">{proposal_url}</a></p>

<p>Esta é uma primeira versão para demonstração e serve como ponto de partida. Se a direção fizer sentido, a versão final é refinada em conjunto — textos, imagens, prioridades e demais ajustes — antes da publicação definitiva.</p>

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
                f"Por conta disso, preparei uma primeira proposta de nova versão do site, já funcional, para mostrar na prática a direção que imaginei:\n"
                f"{proposal_url}\n\n"
                f"É uma primeira versão; se fizer sentido, refinamos juntos antes da entrega final. Dá uma olhada quando puder e me conta o que achou.\n\n"
                f"— {autor}"
            ).strip()

            assunto = f"{nome_lead}, posso te mostrar uma ideia para o site?"
            if len(assunto) > 60:
                assunto = f"Uma nova ideia para a {nome_lead[:35]}"

            email_body_html = f"""<p>Olá, {nome_lead},</p>

<p>{contexto_prova or 'Encontrei o negócio de vocês enquanto pesquisava referências na sua área.'}</p>

<p>Ao analisar a página atual ({site_antigo or 'do consultório'}), notei alguns pontos objetivos que podem estar dificultando a conversão de novos clientes, especialmente na navegação via celular e na rapidez de agendamento.</p>

<p>Para mostrar uma possível direção na prática, montei uma primeira proposta de nova versão do site, já funcional, e coloquei no ar para você comparar o antes e depois:</p>

<p><a href="{proposal_url}">{proposal_url}</a></p>

<p>Esta é uma primeira versão para demonstração. Se a direção fizer sentido, a versão final é refinada em conjunto — textos, imagens, prioridades e demais ajustes — antes da publicação definitiva.</p>

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
        "proposalStage": "first_functional_version",
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