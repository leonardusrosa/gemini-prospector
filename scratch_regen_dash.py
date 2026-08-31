import sqlite3
import json
import pathlib

ROOT = pathlib.Path('.').resolve()
TEMPLATE_PATH = ROOT / 'prospector-de-sites' / 'dashboard' / 'dashboard-template.html'
if not TEMPLATE_PATH.exists():
    TEMPLATE_PATH = ROOT / 'dashboard-template.html'

conn = sqlite3.connect('prospector.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute('SELECT * FROM leads ORDER BY opportunityScore DESC, criadoEm DESC')
leads = [dict(r) for r in c.fetchall()]

raw = TEMPLATE_PATH.read_text(encoding='utf-8')
data = {'leads': leads, 'atualizado': '30/08/2026 23:10'}
data_json = json.dumps(data, ensure_ascii=False)

html = raw.replace('__DADOS__', data_json)
script_tag = f'<script id="dados" type="application/json">{data_json}</script>'
if '<script id="dados"' not in html:
    html = html.replace('</head>', f'{script_tag}\n</head>')

(ROOT / 'dashboard.html').write_text(html, encoding='utf-8')
print(f'Successfully regenerated dashboard.html with {len(leads)} leads.')
