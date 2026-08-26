#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector — Serviço de Descoberta e Persistência de Leads (CRM).
Gerencia runs de prospecção, deduplicação segura (Place ID / fallback) e ciclo de vida.
"""

import datetime
import json
import re
import sqlite3
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

LIFECYCLE_STATUSES = [
    'discovered', 'qualified', 'redesigned', 'published',
    'proposta_preparada', 'contactado', 'respondeu',
    'negociando', 'fechado', 'perdido',
    # Compatibilidade legada
    'novo', 'redesenhado', 'publicado', 'proposta', 'descartado'
]

CAMPOS_DISCOVERY = [
    'slug', 'placeId', 'nome', 'nicho', 'cidade', 'country', 'locale', 'language',
    'phoneCountryCode', 'nota', 'avaliacoes', 'email', 'telefone', 'whatsapp',
    'siteAntigo', 'motivo', 'status', 'websiteStatus', 'siteMode',
    'opportunityType', 'opportunityScore', 'classificationEvidence',
    'mainRisk', 'factualContent', 'imageryLevel', 'socialUrls', 'mapsUrl',
    'urlNova', 'dataProposta', 'valor', 'obs', 'contratoStatus', 'contratoEm',
    'manutencao', 'pago', 'docCliente', 'endCliente', 'runId', 'criadoEm', 'atualizado'
]


def normalizar_texto(txt: Optional[str]) -> str:
    """Normaliza texto para deduplicação: minúsculas, sem acentos nem símbolos."""
    if not txt:
        return ''
    nfkd = unicodedata.normalize('NFKD', str(txt).strip().lower())
    sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub(r'[^a-z0-9]', '', sem_acento)


def gerar_slug(nome: str, cidade: str = '') -> str:
    """Gera slug estável e limpo a partir do nome e cidade."""
    nfkd = unicodedata.normalize('NFKD', f"{nome} {cidade}".strip().lower())
    sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    slug = re.sub(r'[^a-z0-9]+', '-', sem_acento).strip('-')
    # ponytail: slug simples < 60 chars
    return slug[:60] if slug else 'lead-sem-nome'


def setup_db(conn: sqlite3.Connection):
    """Cria/atualiza tabelas de discovery e leads no banco."""
    conn.execute('''CREATE TABLE IF NOT EXISTS discovery_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        nicho TEXT,
        location TEXT,
        country TEXT,
        locale TEXT,
        totalAnalyzed INTEGER DEFAULT 0,
        countExistingWeak INTEGER DEFAULT 0,
        countNone INTEGER DEFAULT 0,
        countHealthy INTEGER DEFAULT 0,
        countUnknown INTEGER DEFAULT 0,
        countInsufficient INTEGER DEFAULT 0,
        metadata TEXT,
        createdAt TEXT DEFAULT (datetime('now','localtime'))
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS leads(
        slug TEXT PRIMARY KEY,
        placeId TEXT,
        nome TEXT,
        nicho TEXT,
        cidade TEXT,
        country TEXT,
        locale TEXT,
        language TEXT,
        phoneCountryCode TEXT,
        nota REAL,
        avaliacoes INTEGER,
        email TEXT,
        telefone TEXT,
        whatsapp TEXT,
        siteAntigo TEXT,
        motivo TEXT,
        status TEXT DEFAULT 'discovered',
        websiteStatus TEXT DEFAULT 'existing_weak',
        siteMode TEXT DEFAULT 'redesign',
        opportunityType TEXT,
        opportunityScore INTEGER,
        classificationEvidence TEXT,
        mainRisk TEXT,
        factualContent TEXT,
        imageryLevel TEXT,
        socialUrls TEXT,
        mapsUrl TEXT,
        urlNova TEXT,
        dataProposta TEXT,
        valor REAL,
        obs TEXT,
        contratoStatus TEXT DEFAULT 'pendente',
        contratoEm TEXT,
        manutencao REAL,
        pago INTEGER DEFAULT 0,
        docCliente TEXT,
        endCliente TEXT,
        runId INTEGER,
        criadoEm TEXT DEFAULT (datetime('now','localtime')),
        atualizado TEXT DEFAULT (datetime('now','localtime'))
    )''')

    # Garante todas as colunas de CAMPOS_DISCOVERY caso a tabela já existisse
    cur = conn.execute("PRAGMA table_info(leads)")
    cols_existentes = {row[1] for row in cur.fetchall()}
    tipos_padrao = {
        'nota': 'REAL', 'avaliacoes': 'INTEGER', 'opportunityScore': 'INTEGER',
        'valor': 'REAL', 'manutencao': 'REAL', 'pago': 'INTEGER DEFAULT 0',
        'runId': 'INTEGER', 'criadoEm': "TEXT DEFAULT (datetime('now','localtime'))",
        'atualizado': "TEXT DEFAULT (datetime('now','localtime'))",
        'contratoStatus': "TEXT DEFAULT 'pendente'",
        'status': "TEXT DEFAULT 'discovered'",
        'websiteStatus': "TEXT DEFAULT 'existing_weak'",
        'siteMode': "TEXT DEFAULT 'redesign'"
    }
    for col in CAMPOS_DISCOVERY + ['criadoEm', 'atualizado']:
        if col not in cols_existentes:
            tipo = tipos_padrao.get(col, 'TEXT')
            try:
                conn.execute(f'ALTER TABLE leads ADD COLUMN {col} {tipo}')
            except sqlite3.OperationalError:
                pass
    conn.execute('''CREATE TABLE IF NOT EXISTS outreach_history (
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
    )''')
    conn.commit()


def encontrar_lead_duplicado(conn: sqlite3.Connection, dados: Dict[str, Any]) -> Optional[str]:
    """
    Estratégia de deduplicação conservadora:
    1. Place ID exato (se presente)
    2. Slug exato
    3. Nome normalizado + endereço normalizado
    4. WhatsApp / telefone normalizado
    5. Domínio do siteAntigo normalizado
    """
    place_id = dados.get('placeId')
    if place_id:
        row = conn.execute('SELECT slug FROM leads WHERE placeId=?', (place_id,)).fetchone()
        if row:
            return row[0]

    slug = dados.get('slug')
    if slug:
        row = conn.execute('SELECT slug FROM leads WHERE slug=?', (slug,)).fetchone()
        if row:
            return row[0]

    # Busca por nome + endereço/cidade
    nome_norm = normalizar_texto(dados.get('nome'))
    cid_norm = normalizar_texto(dados.get('cidade'))
    end_norm = normalizar_texto(dados.get('endCliente') or dados.get('cidade'))
    if nome_norm and len(nome_norm) >= 4:
        rows = conn.execute('SELECT slug, nome, endCliente, cidade FROM leads').fetchall()
        for r_slug, r_nome, r_end, r_cid in rows:
            if normalizar_texto(r_nome) == nome_norm:
                r_cid_norm = normalizar_texto(r_cid)
                r_end_norm = normalizar_texto(r_end)
                # Se mesma cidade ou sem cidade especificada
                if not cid_norm or not r_cid_norm or cid_norm == r_cid_norm or cid_norm in r_end_norm or r_cid_norm in end_norm:
                    return r_slug
                # Ou sobreposição de endereço
                if end_norm and r_end_norm and (end_norm in r_end_norm or r_end_norm in end_norm):
                    return r_slug

    # Busca por telefone / whatsapp único
    wpp = re.sub(r'\D', '', str(dados.get('whatsapp') or dados.get('telefone') or ''))
    if len(wpp) >= 8:
        for r_slug, r_wpp in conn.execute('SELECT slug, whatsapp FROM leads WHERE whatsapp IS NOT NULL AND whatsapp != ""').fetchall():
            if re.sub(r'\D', '', str(r_wpp)) == wpp:
                return r_slug

    # Busca por domínio exato
    site = (dados.get('siteAntigo') or '').strip().lower()
    if site and site.startswith('http'):
        domain = re.sub(r'^https?://(www\.)?', '', site).split('/')[0]
        if len(domain) >= 4:
            for r_slug, r_site in conn.execute('SELECT slug, siteAntigo FROM leads WHERE siteAntigo IS NOT NULL').fetchall():
                if r_site and domain == re.sub(r'^https?://(www\.)?', '', r_site.strip().lower()).split('/')[0]:
                    return r_slug

    return None


def registrar_run(conn: sqlite3.Connection, info_run: Dict[str, Any]) -> int:
    """Registra uma execução de discovery."""
    cur = conn.cursor()
    cur.execute('''INSERT INTO discovery_runs (
        query, nicho, location, country, locale, totalAnalyzed,
        countExistingWeak, countNone, countHealthy, countUnknown,
        countInsufficient, metadata, createdAt
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))''', (
        info_run.get('query'),
        info_run.get('nicho'),
        info_run.get('location'),
        info_run.get('country', 'BR'),
        info_run.get('locale', 'pt-BR'),
        int(info_run.get('totalAnalyzed', 0)),
        int(info_run.get('countExistingWeak', 0)),
        int(info_run.get('countNone', 0)),
        int(info_run.get('countHealthy', 0)),
        int(info_run.get('countUnknown', 0)),
        int(info_run.get('countInsufficient', 0)),
        json.dumps(info_run.get('metadata', {}), ensure_ascii=False) if isinstance(info_run.get('metadata'), dict) else str(info_run.get('metadata') or '')
    ))
    conn.commit()
    return cur.lastrowid


def upsert_lead_discovery(conn: sqlite3.Connection, lead: Dict[str, Any], run_id: Optional[int] = None) -> Dict[str, Any]:
    """Insere ou atualiza um lead descoberto com proteção de downstream status."""
    existing_slug = encontrar_lead_duplicado(conn, lead)
    slug = existing_slug or lead.get('slug') or gerar_slug(lead.get('nome', 'lead'), lead.get('cidade', ''))
    lead['slug'] = slug
    if run_id:
        lead['runId'] = run_id

    # Determina status inicial de discovery
    ws = lead.get('websiteStatus', 'existing_weak')
    default_status = 'qualified' if ws in ('existing_weak', 'none') else 'discovered'

    # Verifica se já existe no banco
    cur = conn.cursor()
    cur.execute('SELECT * FROM leads WHERE slug=?', (slug,))
    existente_row = cur.fetchone()

    agora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if existente_row:
        # Colunas existentes
        cols = [d[0] for d in cur.description]
        existente = dict(zip(cols, existente_row))
        # Não rebaixa status avançados (redesenhado, publicado, etc.)
        status_atual = existente.get('status') or default_status
        if status_atual not in ('discovered', 'qualified', 'novo'):
            lead['status'] = status_atual
        else:
            lead['status'] = lead.get('status') or default_status

        lead['criadoEm'] = existente.get('criadoEm') or agora
        lead['atualizado'] = agora

        # Mescla dados
        dados_finais = {**existente, **{k: v for k, v in lead.items() if v is not None}}
    else:
        lead.setdefault('status', default_status)
        lead.setdefault('contratoStatus', 'pendente')
        lead.setdefault('pago', 0)
        lead.setdefault('criadoEm', agora)
        lead['atualizado'] = agora
        dados_finais = lead

    # Prepara insert or replace
    chaves = [k for k in CAMPOS_DISCOVERY if k in dados_finais]
    sql = f'''INSERT OR REPLACE INTO leads ({','.join(chaves)})
              VALUES ({','.join(['?'] * len(chaves))})'''
    valores = [dados_finais.get(k) for k in chaves]

    conn.execute(sql, valores)
    conn.commit()
    return {'ok': True, 'slug': slug, 'status': dados_finais.get('status'), 'is_update': bool(existente_row)}
