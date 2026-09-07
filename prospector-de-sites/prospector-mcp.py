#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector de Sites — servidor MCP do CRM (STDIO)
Funciona no ChatGPT (Work/Codex) e no Claude (Desktop/Cowork) ao mesmo tempo,
por cima do MESMO prospector.db do dashboard.

Instalação:  pip install "mcp[cli]"
Execução:    python prospector-mcp.py            (usa a pasta atual)
             python prospector-mcp.py --pasta "C:\\Users\\voce\\Desktop\\Clientes"
Teste local: python prospector-mcp.py --teste
"""
import argparse, json, os, sqlite3, sys, datetime

parser = argparse.ArgumentParser()
parser.add_argument('--pasta', default=os.environ.get('PROSPECTOR_DIR', '.'),
                    help='Pasta do projeto (onde ficam prospector.db e dashboard.html)')
parser.add_argument('--teste', action='store_true', help='Roda o autoteste e sai')
ARGS, _ = parser.parse_known_args()
PASTA = os.path.abspath(ARGS.pasta)
DB = os.path.join(PASTA, 'prospector.db')

CAMPOS = ['slug','nome','nicho','cidade','nota','avaliacoes','email','telefone','whatsapp',
          'siteAntigo','motivo','status','urlNova','dataProposta','valor','obs',
          'contratoStatus','contratoEm','manutencao','pago','docCliente','endCliente',
          'websiteStatus','siteMode','country','locale','language','phoneCountryCode','currency',
          'marketTier']
STATUS_VALIDOS = ['novo','redesenhado','publicado','proposta','respondeu','fechado','descartado']

TIER_A = {'US','CA','GB','IE','NL','CH','DE','AT','DK','SE','NO'}
TIER_B = {'ES','CL','MX','PA','CR','UY','PT'}
MARKET_DEFAULTS = {
    'US': {'currency': 'USD', 'phoneCountryCode': '1'},
    'CA': {'currency': 'CAD', 'phoneCountryCode': '1'},
    'GB': {'currency': 'GBP', 'phoneCountryCode': '44'},
    'IE': {'currency': 'EUR', 'phoneCountryCode': '353'},
    'NL': {'currency': 'EUR', 'phoneCountryCode': '31'},
    'CH': {'currency': 'CHF', 'phoneCountryCode': '41'},
    'DE': {'currency': 'EUR', 'phoneCountryCode': '49'},
    'AT': {'currency': 'EUR', 'phoneCountryCode': '43'},
    'DK': {'currency': 'DKK', 'phoneCountryCode': '45'},
    'SE': {'currency': 'SEK', 'phoneCountryCode': '46'},
    'NO': {'currency': 'NOK', 'phoneCountryCode': '47'},
    'ES': {'currency': 'EUR', 'phoneCountryCode': '34'},
    'CL': {'currency': 'CLP', 'phoneCountryCode': '56'},
    'MX': {'currency': 'MXN', 'phoneCountryCode': '52'},
    'PA': {'currency': 'USD', 'phoneCountryCode': '507'},
    'CR': {'currency': 'CRC', 'phoneCountryCode': '506'},
    'UY': {'currency': 'UYU', 'phoneCountryCode': '598'},
    'PT': {'currency': 'EUR', 'phoneCountryCode': '351'},
    'BR': {'currency': 'BRL', 'phoneCountryCode': '55'},
}

def _compute_market_tier(country_code):
    cc = str(country_code or '').strip().upper()
    if cc in TIER_A: return 'TIER_A'
    if cc in TIER_B: return 'TIER_B'
    if cc: return 'OTHER'
    return None

def conexao():
    c = sqlite3.connect(DB)
    c.execute('''CREATE TABLE IF NOT EXISTS leads(
        slug TEXT PRIMARY KEY, nome TEXT, nicho TEXT, cidade TEXT, nota REAL,
        avaliacoes INTEGER, email TEXT, telefone TEXT, whatsapp TEXT, siteAntigo TEXT,
        motivo TEXT, status TEXT DEFAULT 'novo', urlNova TEXT, dataProposta TEXT,
        valor REAL, obs TEXT, contratoStatus TEXT DEFAULT 'pendente', contratoEm TEXT,
        manutencao REAL, pago INTEGER DEFAULT 0, docCliente TEXT, endCliente TEXT,
        websiteStatus TEXT DEFAULT 'existing_weak', siteMode TEXT DEFAULT 'redesign',
        country TEXT, locale TEXT, language TEXT, phoneCountryCode TEXT, currency TEXT,
        marketTier TEXT, atualizado TEXT)''')
    for col, tipo in [('contratoStatus',"TEXT DEFAULT 'pendente'"),('contratoEm','TEXT'),('manutencao','REAL'),('pago','INTEGER DEFAULT 0'),('docCliente','TEXT'),('endCliente','TEXT'),('websiteStatus',"TEXT DEFAULT 'existing_weak'"),('siteMode',"TEXT DEFAULT 'redesign'"),('country','TEXT'),('locale','TEXT'),('language','TEXT'),('phoneCountryCode','TEXT'),('currency','TEXT'),('marketTier','TEXT')]:
        try: c.execute('ALTER TABLE leads ADD COLUMN %s %s' % (col, tipo))
        except sqlite3.OperationalError: pass
    # Legacy migration: backfill country for leads with no explicit country.
    # Only uses phone code prefix +351/+55 and explicit "portugal"/"brasil"/"brazil" in city.
    # Does NOT use 2-letter state abbreviation substring checks.
    try:
        rows = c.execute("SELECT slug, cidade, endCliente, whatsapp, telefone FROM leads WHERE country IS NULL OR country = ''").fetchall()
        for r in rows:
            sl, cid, end, wpp, tel = r
            if (wpp and str(wpp).startswith('+351')) or (tel and str(tel).startswith('+351')) or (cid and 'portugal' in str(cid).lower()):
                c.execute("UPDATE leads SET country='PT', locale='pt-PT', language='pt', phoneCountryCode='351', currency='EUR', marketTier='TIER_B' WHERE slug=?", (sl,))
            elif (wpp and str(wpp).startswith('+55')) or (tel and str(tel).startswith('+55')) or (cid and any(k in str(cid).lower() for k in ['brasil','brazil'])):
                c.execute("UPDATE leads SET country='BR', locale='pt-BR', language='pt', phoneCountryCode='55', currency='BRL', marketTier='OTHER' WHERE slug=?", (sl,))
    except Exception:
        pass
    c.execute('''CREATE TABLE IF NOT EXISTS outreach_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT NOT NULL, canal TEXT NOT NULL,
        destino TEXT, tipo TEXT DEFAULT 'proposta', mensagem TEXT, urlProposta TEXT,
        mensagemId TEXT, status TEXT DEFAULT 'enviado', criadoEm TEXT DEFAULT (datetime('now','localtime')))''')
    c.commit()
    return c

def _linhas(rows, cols):
    return [dict(zip(cols, r)) for r in rows]

def _agora():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

def _is_brazilian_lead(dados):
    """Detect Brazilian leads for NEW_DISCOVERY_BR gating.

    Rule:
    - Explicit country exists → trust it (country == BR means BR, anything else means not BR)
    - Country missing → conservative inference:
      - phoneCountryCode == '55' → BR
      - Verified E.164 number starts with '+55' → BR
      - City explicitly contains 'brasil' or 'brazil' → BR
    - Raw number merely starting '55' (without +) does NOT imply BR
    - No 2-letter state abbreviation substring checks
    """
    country = str(dados.get('country') or '').strip().upper()
    if country:
        return country == 'BR'
    # Country missing — conservative inference only
    phone_code = str(dados.get('phoneCountryCode') or '').strip()
    if phone_code == '55':
        return True
    for field in ('whatsapp', 'telefone'):
        val = str(dados.get(field) or '').strip()
        if val.startswith('+55'):
            return True
    cidade = str(dados.get('cidade') or '').lower()
    if 'brasil' in cidade or 'brazil' in cidade:
        return True
    return False

# ---------- Lógica (compartilhada entre MCP e autoteste) ----------

def f_listar(status=None):
    c = conexao(); cur = c.cursor()
    if status:
        cur.execute('SELECT %s FROM leads WHERE status=? ORDER BY nome' % ','.join(CAMPOS), (status,))
    else:
        cur.execute('SELECT %s FROM leads ORDER BY status, nome' % ','.join(CAMPOS))
    r = _linhas(cur.fetchall(), CAMPOS); c.close(); return r

def f_obter(slug):
    c = conexao(); cur = c.cursor()
    cur.execute('SELECT %s FROM leads WHERE slug=?' % ','.join(CAMPOS), (slug,))
    row = cur.fetchone(); c.close()
    return dict(zip(CAMPOS, row)) if row else None

def f_salvar(dados):
    if not dados.get('slug'):
        return {'erro': 'slug é obrigatório (ex.: maria-silva)'}
    if dados.get('status') and dados['status'] not in STATUS_VALIDOS:
        return {'erro': 'status inválido. Use: %s' % ', '.join(STATUS_VALIDOS)}
    existente = f_obter(dados['slug'])
    # Market Policy V3: NEW_DISCOVERY_BR = DISABLED.
    # New Brazilian leads cannot be created. Existing Brazilian leads remain valid and can be updated.
    if existente is None and _is_brazilian_lead(dados):
        return {'erro': 'NEW_DISCOVERY_BR is DISABLED under Market Policy V3. New Brazilian prospects cannot be created in CRM.'}
    atual = existente or {}
    atual.update({k: v for k, v in dados.items() if k in CAMPOS and v is not None})
    atual.setdefault('status', 'novo'); atual.setdefault('contratoStatus', 'pendente'); atual.setdefault('pago', 0)
    # Auto-populate marketTier and safe market defaults when country is known
    cc = str(atual.get('country') or '').strip().upper()
    if cc and not atual.get('marketTier'):
        atual['marketTier'] = _compute_market_tier(cc)
    if cc and cc in MARKET_DEFAULTS:
        defaults = MARKET_DEFAULTS[cc]
        for safe_field in ('currency', 'phoneCountryCode'):
            if not atual.get(safe_field):
                atual[safe_field] = defaults.get(safe_field)
    c = conexao()
    c.execute('INSERT OR REPLACE INTO leads (%s,atualizado) VALUES (%s,?)' % (','.join(CAMPOS), ','.join('?'*len(CAMPOS))),
              [atual.get(k) for k in CAMPOS] + [_agora()])
    c.commit(); c.close()
    res = {'ok': True, 'lead': atual['slug'], 'status': atual['status']}
    if atual.get('status') == 'publicado':
        # Local SQLite is the canonical CRM. Phoenix remote sync is legacy/optional
        # and is never part of the normal publication workflow (see prospector_remote.py).
        res['status_result'] = 'PUBLISHED_LOCAL_ONLY'
    return res

def f_status(slug, status, obs_extra=None):
    if status not in STATUS_VALIDOS:
        return {'erro': 'status inválido. Use: %s' % ', '.join(STATUS_VALIDOS)}
    lead = f_obter(slug)
    if not lead: return {'erro': 'lead não encontrado: %s' % slug}
    c = conexao()
    if status == 'proposta' and not lead.get('dataProposta'):
        c.execute('UPDATE leads SET dataProposta=? WHERE slug=?', (datetime.date.today().isoformat(), slug))
    if obs_extra:
        novo_obs = ((lead.get('obs') or '') + ' | ' + obs_extra).strip(' |')
        c.execute('UPDATE leads SET obs=? WHERE slug=?', (novo_obs, slug))
    c.execute('UPDATE leads SET status=?, atualizado=? WHERE slug=?', (status, _agora(), slug))
    c.commit(); c.close()

    res = {'ok': True, 'lead': slug, 'novo_status': status}
    if status == 'publicado':
        # Local SQLite is the canonical CRM. Phoenix remote sync is legacy/optional
        # and is never part of the normal publication workflow (see prospector_remote.py).
        res['status_result'] = 'PUBLISHED_LOCAL_ONLY'

    return res

def f_fechar(slug, valor, manutencao=None):
    lead = f_obter(slug)
    if not lead: return {'erro': 'lead não encontrado: %s' % slug}
    c = conexao()
    c.execute('UPDATE leads SET status=?, valor=?, manutencao=?, atualizado=? WHERE slug=?',
              ('fechado', valor, manutencao, _agora(), slug))
    c.commit(); c.close()
    return {'ok': True, 'lead': slug, 'valor': valor, 'manutencao': manutencao}

def f_followups(dias=3):
    c = conexao(); cur = c.cursor()
    cur.execute('''SELECT %s FROM leads
        WHERE status='proposta'
          AND date(dataProposta) <= date('now', '-%d day')
          AND (obs IS NULL OR obs NOT LIKE '%%%%Follow-up enviado em%%%%')
        ORDER BY dataProposta ASC''' % (','.join(CAMPOS), dias))
    r = _linhas(cur.fetchall(), CAMPOS); c.close(); return r

def f_financeiro():
    c = conexao(); cur = c.cursor()
    cur.execute("SELECT COUNT(*), SUM(valor), SUM(manutencao) FROM leads WHERE status='fechado'")
    fechados, val_fechado, mrr = cur.fetchone()
    cur.execute("SELECT SUM(valor) FROM leads WHERE status='fechado' AND pago=1")
    recebido = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*), SUM(valor) FROM leads WHERE status='proposta'")
    prop_qtd, prop_val = cur.fetchone()
    c.close()
    val_fechado = val_fechado or 0; mrr = mrr or 0
    return {
        'clientesFechados': fechados or 0,
        'receitaProjetos': round(val_fechado, 2),
        'recebido': round(recebido, 2),
        'aReceber': round(val_fechado - recebido, 2),
        'mrrManutencao': round(mrr, 2),
        'arrManutencao': round(mrr * 12, 2),
        'projecao12Meses': round(val_fechado + (mrr * 12), 2),
        'propostasEmAberto': prop_qtd or 0,
        'pipelineAberto': round(prop_val or 0, 2)
    }

def f_dashboard():
    tpl_path = None
    for cand in ['dashboard.html', 'prospector-de-sites/dashboard.html', 'prospector-de-sites/dashboard/dashboard-template.html']:
        p = os.path.join(PASTA, cand)
        if os.path.exists(p): tpl_path = p; break
    if not tpl_path: return {'erro': 'dashboard.html/template não encontrado na pasta %s' % PASTA}
    import re
    t = open(tpl_path, encoding='utf-8').read()
    dados = json.dumps({'atualizado': _agora(), 'leads': f_listar()}, ensure_ascii=False)
    if '__DADOS__' in t:
        novo = t.replace('__DADOS__', dados)
    else:
        novo = re.sub(r'(<script id="dados"[^>]*>).*?(</script>)', lambda m: m.group(1)+dados+m.group(2), t, flags=re.S)
    open(os.path.join(PASTA, 'dashboard.html'), 'w', encoding='utf-8').write(novo)
    return {'ok': True, 'leads': len(f_listar())}

# ---------- Autoteste ----------
if ARGS.teste:
    import tempfile
    PASTA = tempfile.mkdtemp(); DB = os.path.join(PASTA, 'prospector.db')
    print('1 salvar:', f_salvar({'slug':'teste-mcp','nome':'Teste MCP','email':'t@t.com','nicho':'nutricionista','cidade':'Lisboa','country':'PT','currency':'EUR'}))
    lead_pt = f_obter('teste-mcp')
    assert lead_pt['marketTier'] == 'TIER_B', f"PT should be TIER_B, got {lead_pt['marketTier']}"
    print('  marketTier PT:', lead_pt['marketTier'])
    print('2 listar:', len(f_listar()), 'lead(s)')
    print('3 status:', f_status('teste-mcp','proposta'))
    import sqlite3 as s3
    c=s3.connect(DB); c.execute("UPDATE leads SET dataProposta=date('now','-5 day') WHERE slug='teste-mcp'"); c.commit(); c.close()
    print('4 followups pendentes:', f_followups())
    print('5 fechar:', f_fechar('teste-mcp', 700, 100))
    print('6 financeiro:', f_financeiro())
    print('7 status inválido (deve dar erro):', f_status('teste-mcp','banana'))
    print('8 novo lead BR bloqueado:', f_salvar({'slug':'novo-br','cidade':'Rio Claro SP','country':'BR'}))
    # V3.1.1: US cities must NOT be flagged as BR
    res_us = f_salvar({'slug':'springfield-il','nome':'Springfield Dental','cidade':'Springfield, IL','country':'US','phoneCountryCode':'1'})
    assert res_us.get('ok'), f"Springfield IL US must not be blocked: {res_us}"
    lead_us = f_obter('springfield-il')
    assert lead_us['marketTier'] == 'TIER_A', f"US should be TIER_A, got {lead_us['marketTier']}"
    assert lead_us['currency'] == 'USD', f"US currency should be USD, got {lead_us['currency']}"
    print('9 US lead (Springfield IL):', res_us, '| tier:', lead_us['marketTier'])
    # V3.1.1: raw phone starting 55 without + must NOT imply BR when no country
    res_raw = f_salvar({'slug':'raw-55-test','nome':'Test Raw','cidade':'Dallas, TX','whatsapp':'5512345678'})
    assert res_raw.get('ok'), f"Raw 55 phone without + must not block: {res_raw}"
    print('10 raw 55 phone (no +, no country):', res_raw)
    print('AUTOTESTE OK')
    sys.exit(0)

# ---------- Servidor MCP ----------
from mcp.server.fastmcp import FastMCP
mcp = FastMCP('prospector-crm')

@mcp.tool()
def listar_leads(status: str = '') -> str:
    """Lista os leads do CRM. Opcional: filtrar por status (novo, redesenhado, publicado, proposta, respondeu, fechado, descartado)."""
    return json.dumps(f_listar(status or None), ensure_ascii=False)

@mcp.tool()
def obter_lead(slug: str) -> str:
    """Retorna todos os dados de um lead pelo slug (ex.: maria-silva)."""
    return json.dumps(f_obter(slug) or {'erro': 'não encontrado'}, ensure_ascii=False)

@mcp.tool()
def salvar_lead(slug: str, nome: str = '', nicho: str = '', cidade: str = '', nota: float = 0,
                avaliacoes: int = 0, email: str = '', telefone: str = '', whatsapp: str = '',
                siteAntigo: str = '', motivo: str = '', urlNova: str = '', obs: str = '',
                country: str = '', locale: str = '', currency: str = '', phoneCountryCode: str = '',
                marketTier: str = '') -> str:
    """Cria ou atualiza um lead no CRM (usar após prospectar ou ao corrigir dados). Slug no formato nome-sobrenome."""
    d = {k: v for k, v in locals().items() if v not in ('', 0)}
    return json.dumps(f_salvar(d), ensure_ascii=False)

@mcp.tool()
def atualizar_status(slug: str, status: str, observacao: str = '') -> str:
    """Move o lead no funil: novo → redesenhado → publicado → proposta → respondeu → fechado/descartado. NUNCA use 'fechado' sem confirmação explícita do usuário (para fechar com valor, use registrar_fechamento)."""
    return json.dumps(f_status(slug, status, observacao or None), ensure_ascii=False)

@mcp.tool()
def registrar_fechamento(slug: str, valor: float, manutencao_mensal: float = 0) -> str:
    """Registra um cliente FECHADO com o valor acordado (e manutenção mensal, se houver). Use somente quando o usuário confirmar o fechamento e o valor."""
    return json.dumps(f_fechar(slug, valor, manutencao_mensal or None), ensure_ascii=False)

@mcp.tool()
def followups_pendentes(dias: int = 3) -> str:
    """Lista leads com proposta enviada há N+ dias, sem resposta e sem follow-up registrado — os que precisam de follow-up agora."""
    return json.dumps(f_followups(dias), ensure_ascii=False)

@mcp.tool()
def registrar_followup(slug: str) -> str:
    """Registra que o follow-up foi enviado hoje para o lead (1 por lead, nunca repetir)."""
    return json.dumps(f_status(slug, 'proposta', 'Follow-up enviado em %s' % datetime.date.today().isoformat()), ensure_ascii=False)

@mcp.tool()
def resumo_financeiro() -> str:
    """Painel financeiro: total fechado, recebido, a receber, MRR de manutenções e projeção 12 meses."""
    return json.dumps(f_financeiro(), ensure_ascii=False)

@mcp.tool()
def regenerar_dashboard() -> str:
    """Regenera o dashboard.html (painel visual) com os dados atuais do banco. Use ao final de qualquer sequência de alterações."""
    return json.dumps(f_dashboard(), ensure_ascii=False)

if __name__ == '__main__':
    mcp.run()
