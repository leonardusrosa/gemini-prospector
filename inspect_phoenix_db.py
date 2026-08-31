import subprocess

remote_code = """
import sqlite3, json, urllib.request, base64

conn = sqlite3.connect('/var/lib/prospector-dashboard/prospector.db')
conn.row_factory = sqlite3.Row
rows = [dict(r) for r in conn.execute("SELECT slug,nome,status,urlNova,telefone,whatsapp FROM leads WHERE slug='iost-ortodontia-aline-iost-rio-claro'").fetchall()]
print('DB Rows count:', len(rows))
print('DB Rows:', rows)

# Check all slugs in DB
all_slugs = [r['slug'] for r in conn.execute("SELECT slug FROM leads").fetchall()]
print('All DB Slugs:', all_slugs)

# Check local API
req = urllib.request.Request('http://127.0.0.1:8765/api/leads', headers={'Authorization': 'Basic ' + base64.b64encode(b'admin:REDACTED').decode('ascii')})
try:
    with urllib.request.urlopen(req) as resp:
        api_data = json.loads(resp.read().decode('utf-8'))
        print('API Total leads:', len(api_data))
        api_slugs = [l['slug'] for l in api_data]
        print('API Slugs:', api_slugs)
        iost_in_api = [l for l in api_data if l.get('slug') == 'iost-ortodontia-aline-iost-rio-claro']
        print('IOST in API:', iost_in_api)
except Exception as e:
    print('API Error:', e)
"""

p = subprocess.run(['ssh', 'phoenix', 'python3'], input=remote_code, text=True, capture_output=True)
print('STDOUT:\n', p.stdout)
if p.stderr:
    print('STDERR:\n', p.stderr)
