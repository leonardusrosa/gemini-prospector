#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prospector — servidor local do dashboard (SQLite). Sem dependências: só Python padrão.
Uso: python dashboard-server.py  (ou duplo clique em iniciar-dashboard.bat)
Abre em http://localhost:8765 — edições, exclusões e drag&drop salvam no prospector.db"""
import json, sqlite3, os, sys, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PASTA = os.path.dirname(os.path.abspath(__file__))
os.chdir(PASTA)
DB = os.path.join(PASTA, 'prospector.db')
CONFIG = os.path.join(PASTA, 'prospector-config.json')

# Importação do cliente Evolution
sys.path.insert(0, PASTA)
sys.path.insert(0, os.path.join(PASTA, 'prospector-de-sites'))
try:
    from evolution_client import EvolutionClient
except ImportError:
    EvolutionClient = None

def ler_config():
    try: return json.load(open(CONFIG, encoding='utf-8'))
    except Exception: return {}
PORTA = 8765
CAMPOS = ['slug','nome','nicho','cidade','nota','avaliacoes','email','telefone','whatsapp',
          'siteAntigo','motivo','status','urlNova','dataProposta','valor','obs',
          'contratoStatus','contratoEm','manutencao','pago','docCliente','endCliente']

def conexao():
    c = sqlite3.connect(DB)
    c.execute('''CREATE TABLE IF NOT EXISTS leads(
        slug TEXT PRIMARY KEY, nome TEXT, nicho TEXT, cidade TEXT, nota REAL, avaliacoes INTEGER,
        email TEXT, telefone TEXT, whatsapp TEXT, siteAntigo TEXT, motivo TEXT,
        status TEXT DEFAULT 'novo', urlNova TEXT, dataProposta TEXT, valor REAL, obs TEXT,
        contratoStatus TEXT DEFAULT 'pendente', contratoEm TEXT, manutencao REAL, pago INTEGER DEFAULT 0,
        atualizado TEXT DEFAULT (datetime('now','localtime')))''')
    for col, tipo in [('contratoStatus',"TEXT DEFAULT 'pendente'"),('contratoEm','TEXT'),('manutencao','REAL'),('pago','INTEGER DEFAULT 0'),('docCliente','TEXT'),('endCliente','TEXT')]:
        try: c.execute('ALTER TABLE leads ADD COLUMN %s %s' % (col, tipo))
        except sqlite3.OperationalError: pass
    return c

def importar_snapshot():
    """Primeira execução sem banco: importa os leads embutidos no dashboard.html."""
    try:
        html = open(os.path.join(PASTA, 'dashboard.html'), encoding='utf-8').read()
        ini = html.index('<script id="dados" type="application/json">') + len('<script id="dados" type="application/json">')
        fim = html.index('</script>', ini)
        dados = json.loads(html[ini:fim])
        c = conexao()
        for l in dados.get('leads', []):
            c.execute('INSERT OR IGNORE INTO leads (%s) VALUES (%s)' % (','.join(CAMPOS), ','.join('?'*len(CAMPOS))),
                      [l.get(k) for k in CAMPOS])
        c.commit(); c.close()
        print('Snapshot importado do dashboard.html para o prospector.db')
    except Exception as e:
        print('(sem snapshot para importar: %s)' % e)

class App(SimpleHTTPRequestHandler):
    def _json(self, code, obj):
        corpo = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(corpo)))
        self.end_headers(); self.wfile.write(corpo)
    def _corpo(self):
        n = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(n).decode('utf-8')) if n else {}
    def do_GET(self):
        rota = self.path.split('?')[0]
        if rota == '/api/config':
            cfg = ler_config()
            deploy = dict(cfg.get('deploy', {}))
            if not deploy and 'hostgator' in cfg:
                hg = cfg.get('hostgator', {})
                deploy = {
                    'provider': 'vercel-github',
                    'repoPath': '',
                    'githubRepo': '',
                    'branch': 'main',
                    'basePath': hg.get('pastaBase', 'clientes'),
                    'domain': hg.get('dominio', '')
                }
            evo = cfg.get('evolution', {})
            evo_client = EvolutionClient(cfg) if EvolutionClient else None
            evo_public = {
                'enabled': evo_client.enabled if evo_client else bool(evo.get('enabled', False)),
                'baseUrl': evo_client.base_url if evo_client else (os.environ.get('EVOLUTION_API_URL') or evo.get('baseUrl', '')),
                'instance': evo_client.instance if evo_client else (os.environ.get('EVOLUTION_INSTANCE') or evo.get('instance', '')),
                'apiKeyEnv': evo_client.api_key_env if evo_client else evo.get('apiKeyEnv', 'EVOLUTION_API_KEY'),
                'timeoutSeconds': evo_client.timeout if evo_client else int(evo.get('timeoutSeconds', 15)),
                'hasApiKey': evo_client.has_api_key() if evo_client else bool(os.environ.get(evo.get('apiKeyEnv', 'EVOLUTION_API_KEY')) or os.environ.get('EVOLUTION_API_KEY')),
            }
            return self._json(200, {
                'contratante': cfg.get('contratante', {}),
                'deploy': deploy,
                'evolution': evo_public
            })
        if rota == '/api/evolution/status':
            cfg = ler_config()
            if EvolutionClient:
                c = EvolutionClient(cfg)
                return self._json(200, {
                    'enabled': c.enabled,
                    'baseUrl': c.base_url,
                    'instance': c.instance,
                    'hasApiKey': c.has_api_key(),
                    'isConfigured': c.is_configured(),
                    'apiKeyEnv': c.api_key_env
                })
            return self._json(200, {'configured': False, 'hasApiKey': False, 'error': 'EvolutionClient indisponível'})
        if rota == '/api/leads':
            c = conexao(); c.row_factory = sqlite3.Row
            rows = [dict(r) for r in c.execute('SELECT * FROM leads').fetchall()]; c.close()
            return self._json(200, rows)
        if self.path in ('/', ''):
            self.path = '/dashboard.html'
        return SimpleHTTPRequestHandler.do_GET(self)
    def do_POST(self):
        rota = self.path.split('?')[0]
        if rota == '/api/leads':
            l = self._corpo(); c = conexao()
            c.execute('INSERT OR REPLACE INTO leads (%s) VALUES (%s)' % (','.join(CAMPOS), ','.join('?'*len(CAMPOS))),
                      [l.get(k) for k in CAMPOS])
            c.commit(); c.close(); return self._json(200, {'ok': True})
        if rota == '/api/evolution/test':
            corpo = self._corpo()
            cfg = ler_config()
            evo_cfg = dict(cfg.get('evolution', {}))
            if isinstance(corpo, dict):
                for k in ['baseUrl', 'instance', 'timeoutSeconds', 'apiKeyEnv']:
                    if k in corpo and corpo[k]:
                        evo_cfg[k] = corpo[k]
            if EvolutionClient:
                c = EvolutionClient({'evolution': evo_cfg})
                res = c.test_connection()
                return self._json(200, res)
            return self._json(500, {'error': 'Módulo EvolutionClient não encontrado.'})
        if rota == '/api/evolution/send-test':
            corpo = self._corpo()
            if not isinstance(corpo, dict):
                return self._json(400, {'success': False, 'error': 'Corpo da requisição inválido.'})
            number = corpo.get('number', '')
            text = corpo.get('text', '')
            confirmed = bool(corpo.get('confirmed', False))
            if not confirmed:
                return self._json(400, {'success': False, 'error': 'Envio não autorizado. Confirme o checkbox antes de prosseguir.'})
            if not number:
                return self._json(400, {'success': False, 'error': 'Número de telefone obrigatório.'})
            cfg = ler_config()
            if EvolutionClient:
                c = EvolutionClient(cfg)
                res = c.send_test_message(number=number, text=text, confirmed=confirmed)
                code = 200 if res.get('success') else 400
                return self._json(code, res)
            return self._json(500, {'success': False, 'error': 'Módulo EvolutionClient não encontrado.'})
        return self._json(404, {'erro': 'rota'})
    def do_PUT(self):
        rota = self.path.split('?')[0]
        if rota == '/api/config':
            cfg = ler_config(); corpo = self._corpo()
            if 'contratante' in corpo or 'deploy' in corpo or 'evolution' in corpo or 'hostgator' in corpo:
                if 'contratante' in corpo:
                    ct = cfg.get('contratante', {})
                    ct.update({k: v for k, v in corpo['contratante'].items() if isinstance(v, str)})
                    cfg['contratante'] = ct
                if 'deploy' in corpo:
                    dep = cfg.get('deploy', {})
                    for k, v in corpo['deploy'].items():
                        if isinstance(v, str):
                            dep[k] = v
                    cfg['deploy'] = dep
                    cfg.pop('hostgator', None)
                elif 'hostgator' in corpo:
                    dep = cfg.get('deploy', {})
                    dep['domain'] = corpo['hostgator'].get('dominio', dep.get('domain', ''))
                    dep['basePath'] = corpo['hostgator'].get('pastaBase', dep.get('basePath', 'clientes'))
                    cfg['deploy'] = dep
                if 'evolution' in corpo and isinstance(corpo['evolution'], dict):
                    evo = cfg.get('evolution', {})
                    for k in ['enabled', 'baseUrl', 'instance', 'apiKeyEnv', 'timeoutSeconds']:
                        if k in corpo['evolution']:
                            evo[k] = corpo['evolution'][k]
                    # Garante que NUNCA salva a chave de API no arquivo
                    evo.pop('apiKey', None)
                    evo.pop('key', None)
                    evo.pop('senha', None)
                    cfg['evolution'] = evo
            else:  # compatibilidade: corpo plano = contratante
                ct = cfg.get('contratante', {})
                ct.update({k: v for k, v in corpo.items() if isinstance(v, str)})
                cfg['contratante'] = ct
            json.dump(cfg, open(CONFIG, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            return self._json(200, {'ok': True})
        partes = rota.split('/')
        if len(partes) == 4 and partes[1] == 'api' and partes[2] == 'leads':
            slug, ch = partes[3], self._corpo()
            sets = [k for k in ch if k in CAMPOS and k != 'slug']
            if sets:
                c = conexao()
                c.execute('UPDATE leads SET %s, atualizado=datetime("now","localtime") WHERE slug=?' %
                          ','.join('%s=?' % k for k in sets), [ch[k] for k in sets] + [slug])
                c.commit(); c.close()
            return self._json(200, {'ok': True})
        return self._json(404, {'erro': 'rota'})
    def do_DELETE(self):
        partes = self.path.split('?')[0].split('/')
        if len(partes) == 4 and partes[1] == 'api' and partes[2] == 'leads':
            c = conexao(); c.execute('DELETE FROM leads WHERE slug=?', (partes[3],)); c.commit(); c.close()
            return self._json(200, {'ok': True})
        return self._json(404, {'erro': 'rota'})
    def log_message(self, *a): pass

if __name__ == '__main__':
    novo = not os.path.exists(DB)
    conexao().close()
    if novo: importar_snapshot()
    print('Prospector rodando em http://localhost:%d  (Ctrl+C para parar)' % PORTA)
    try: webbrowser.open('http://localhost:%d' % PORTA)
    except Exception: pass
    try: ThreadingHTTPServer(('127.0.0.1', PORTA), App).serve_forever()
    except KeyboardInterrupt: print('\nEncerrado.')
