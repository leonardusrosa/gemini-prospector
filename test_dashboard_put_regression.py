import sqlite3
import json
import os
import sys
import tempfile
import urllib.request
import threading
from http.server import ThreadingHTTPServer

# Import core
sys.path.insert(0, os.path.abspath('prospector-de-sites/dashboard'))
import importlib.util

spec = importlib.util.spec_from_file_location('dashboard_server', 'prospector-de-sites/dashboard/dashboard-server.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def run_test():
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, 'prospector.db')
    config_file = os.path.join(temp_dir, 'prospector-config.json')

    core.PASTA = temp_dir
    core.DB = db_file
    core.CONFIG = config_file
    core.PORTA = 9876

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump({'deploy': {'domain': 'example.com'}}, f)

    # Initialize DB
    conn = core.conexao()
    conn.execute('''INSERT INTO leads (slug, nome, status, telefone, whatsapp)
                    VALUES ('existing-lead-test', 'Existing Lead', 'novo', '(11) 99999-9999', '5511999999999')''')
    conn.commit()
    conn.close()

    server = ThreadingHTTPServer(('127.0.0.1', 9876), core.App)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = 'http://127.0.0.1:9876'

    try:
        # Test 1: PUT nonexistent slug -> 404
        req = urllib.request.Request(
            f'{base_url}/api/leads/nonexistent-lead-slug',
            data=json.dumps({'status': 'published', 'telefone': '(19) 99999-0000'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='PUT'
        )
        try:
            with urllib.request.urlopen(req) as resp:
                assert False, f"Expected 404, got {resp.status}"
        except urllib.error.HTTPError as e:
            assert e.code == 404, f"Expected 404, got {e.code}"
            err_data = json.loads(e.read().decode('utf-8'))
            assert err_data.get('ok') is False, f"Expected ok: false, got {err_data}"
            assert err_data.get('error') == 'lead_not_found', f"Expected error: lead_not_found, got {err_data}"
            print("PASS: PUT nonexistent lead returned 404 lead_not_found")

        # Test 2: PUT existing slug -> 200, value updated
        req2 = urllib.request.Request(
            f'{base_url}/api/leads/existing-lead-test',
            data=json.dumps({'status': 'published', 'telefone': '(11) 88888-8888'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='PUT'
        )
        with urllib.request.urlopen(req2) as resp:
            assert resp.status == 200, f"Expected 200, got {resp.status}"
            data = json.loads(resp.read().decode('utf-8'))
            assert data.get('ok') is True, f"Expected ok: true, got {data}"
            print("PASS: PUT existing lead returned 200 ok")

        # Verify DB value updated
        conn = sqlite3.connect(db_file)
        row = conn.execute("SELECT status, telefone FROM leads WHERE slug='existing-lead-test'").fetchone()
        conn.close()
        assert row == ('published', '(11) 88888-8888'), f"Expected updated values, got {row}"
        print("PASS: Existing lead values updated in database")

        # Test 3: POST synthetic lead -> created
        req3 = urllib.request.Request(
            f'{base_url}/api/leads',
            data=json.dumps({
                'slug': 'synthetic-new-lead',
                'nome': 'Synthetic New Lead',
                'status': 'published',
                'telefone': '(19) 99999-1111'
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req3) as resp:
            assert resp.status == 200
            print("PASS: POST new synthetic lead returned 200")

        # Verify lead exists in GET /api/leads
        with urllib.request.urlopen(f'{base_url}/api/leads') as resp:
            leads = json.loads(resp.read().decode('utf-8'))
            found = [l for l in leads if l.get('slug') == 'synthetic-new-lead']
            assert len(found) == 1, f"Expected 1 synthetic lead, got {found}"
            print("PASS: GET /api/leads returned created synthetic lead")

        # Test 4: DELETE synthetic lead -> removed
        req4 = urllib.request.Request(
            f'{base_url}/api/leads/synthetic-new-lead',
            method='DELETE'
        )
        with urllib.request.urlopen(req4) as resp:
            assert resp.status == 200
            print("PASS: DELETE synthetic lead returned 200")

        # Verify DB pristine (only existing-lead-test remains)
        with urllib.request.urlopen(f'{base_url}/api/leads') as resp:
            leads = json.loads(resp.read().decode('utf-8'))
            slugs = [l['slug'] for l in leads]
            assert slugs == ['existing-lead-test'], f"Expected only existing-lead-test, got {slugs}"
            print("PASS: Database is pristine after cleanup")

        print("\nALL REGRESSION TESTS PASSED SUCCESSFULLY!")

    finally:
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    run_test()
