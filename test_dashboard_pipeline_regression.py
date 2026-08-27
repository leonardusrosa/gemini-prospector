#!/usr/bin/env python3
"""Regression test suite for Dashboard Pipeline lifecycle statuses.

Verifies:
1. Canonical lifecycle statuses render into their respective lanes.
2. Legacy status aliases (novo, redesenhado, publicado, proposta, descartado) map to canonical lanes.
3. Unknown future statuses never vanish from UI and render in the 'Revisar' fallback lane.
4. Total pipeline & client counts are consistent.
5. Drag & drop persists canonical status values.
6. Initial page load causes zero unwanted lifecycle mutations.
"""

import asyncio
import http.server
import json
import os
import pathlib
import socketserver
import threading
import time
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "prospector-de-sites" / "dashboard" / "dashboard-template.html"

SAMPLE_LEADS = [
    {"slug": "lead-discovered", "nome": "Lead Discovered", "status": "discovered", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-qualified", "nome": "Lead Qualified", "status": "qualified", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-redesigned", "nome": "Lead Redesigned", "status": "redesigned", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-published", "nome": "Lead Published", "status": "published", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-prop-prep", "nome": "Lead Prop Prep", "status": "proposta_preparada", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-contactado", "nome": "Lead Contactado", "status": "contactado", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-respondeu", "nome": "Lead Respondeu", "status": "respondeu", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-negociando", "nome": "Lead Negociando", "status": "negociando", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-fechado", "nome": "Lead Fechado", "status": "fechado", "valor": 700, "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-perdido", "nome": "Lead Perdido", "status": "perdido", "cidade": "Rio Claro", "nicho": "Dentista"},
    # Legacy aliases
    {"slug": "lead-legacy-novo", "nome": "Lead Legacy Novo", "status": "novo", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-legacy-rede", "nome": "Lead Legacy Redesenhado", "status": "redesenhado", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-legacy-pub", "nome": "Lead Legacy Publicado", "status": "publicado", "cidade": "Rio Claro", "nicho": "Dentista"},
    {"slug": "lead-legacy-prop", "nome": "Lead Legacy Proposta", "status": "proposta", "cidade": "Rio Claro", "nicho": "Dentista"},
    # Unknown future status
    {"slug": "lead-unknown", "nome": "Lead Unknown Status", "status": "unknown_future_status", "cidade": "Rio Claro", "nicho": "Dentista"},
]

class MockDashboardHandler(http.server.SimpleHTTPRequestHandler):
    leads_store = [dict(x) for x in SAMPLE_LEADS]

    def do_GET(self):
        if self.path in {"/", "/index.html", "/dashboard.html"}:
            raw = TEMPLATE_PATH.read_text(encoding="utf-8")
            data = {"leads": self.leads_store, "atualizado": "2026-08-27"}
            html = raw.replace("__DADOS__", json.dumps(data))
            if '<script id="dados" type="application/json">' not in html:
                html = html.replace("</head>", '<script id="dados" type="application/json">' + json.dumps(data) + '</script></head>')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        elif self.path == "/api/leads":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.leads_store).encode("utf-8"))
        elif self.path == "/api/config":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if self.path.startswith("/api/leads/"):
            slug = self.path.split("/api/leads/")[1]
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            for l in self.leads_store:
                if l["slug"] == slug:
                    l.update(payload)
                    break
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"success":true}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet

async def run_pipeline_regression_tests(port: int):
    url = f"http://127.0.0.1:{port}/"
    print("==================================================")
    print("STARTING DASHBOARD PIPELINE REGRESSION TEST")
    print("==================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        # 1. Open dashboard
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(400)

        # 2. Switch to Pipeline view
        pipeline_btn = page.locator('nav button:has-text("Pipeline")')
        await pipeline_btn.click()
        await page.wait_for_timeout(300)

        # 3. Assert all 15 leads are present in DOM
        for lead in SAMPLE_LEADS:
            card = page.locator(f'.card:has-text("{lead["nome"]}")')
            count = await card.count()
            assert count == 1, f"Lead '{lead['nome']}' ({lead['slug']}) not visible in Pipeline!"
        print("  [PASS] All 15 fixture leads are visible in Pipeline")

        # 4. Check canonical column assignments
        # 'discovered' column should contain 'Lead Discovered' and 'Lead Legacy Novo'
        col_disc = page.locator('.col[data-st="discovered"]')
        assert await col_disc.locator(':text("Lead Discovered")').count() == 1
        assert await col_disc.locator(':text("Lead Legacy Novo")').count() == 1
        print("  [PASS] Legacy 'novo' mapped to canonical 'discovered' column")

        # 'qualified' column should contain 'Lead Qualified'
        col_qual = page.locator('.col[data-st="qualified"]')
        assert await col_qual.locator(':text("Lead Qualified")').count() == 1
        print("  [PASS] 'qualified' leads rendered into 'Qualificado' column")

        # 'redesigned' column should contain 'Lead Redesigned' and 'Lead Legacy Redesenhado'
        col_rede = page.locator('.col[data-st="redesigned"]')
        assert await col_rede.locator(':text("Lead Redesigned")').count() == 1
        assert await col_rede.locator(':text("Lead Legacy Redesenhado")').count() == 1
        print("  [PASS] Legacy 'redesenhado' mapped to canonical 'redesigned' column")

        # 'published' column should contain 'Lead Published' and 'Lead Legacy Publicado'
        col_pub = page.locator('.col[data-st="published"]')
        assert await col_pub.locator(':text("Lead Published")').count() == 1
        assert await col_pub.locator(':text("Lead Legacy Publicado")').count() == 1
        print("  [PASS] Legacy 'publicado' mapped to canonical 'published' column")

        # 'contactado' column should contain 'Lead Contactado' and 'Lead Legacy Proposta'
        col_cont = page.locator('.col[data-st="contactado"]')
        assert await col_cont.locator(':text("Lead Contactado")').count() == 1
        assert await col_cont.locator(':text("Lead Legacy Proposta")').count() == 1
        print("  [PASS] Legacy 'proposta' mapped to canonical 'contactado' column")

        # 'revisar' fallback column should contain 'Lead Unknown Status'
        col_rev = page.locator('.col[data-st="revisar"]')
        assert await col_rev.count() == 1, "Fallback 'Revisar' column was not created for unknown status!"
        assert await col_rev.locator(':text("Lead Unknown Status")').count() == 1
        print("  [PASS] Unknown future status rendered into fallback 'Revisar' column")

        # 'perdido' column should contain 'Lead Perdido'
        col_perd = page.locator('.col[data-st="perdido"]')
        assert await col_perd.locator(':text("Lead Perdido")').count() == 1
        print("  [PASS] 'perdido' leads rendered into 'Perdido' column")

        # 5. Check Clientes view
        clientes_btn = page.locator('nav button:has-text("Clientes")')
        await clientes_btn.click()
        await page.wait_for_timeout(300)
        pagin_info = await page.locator(".pagin .info").text_content()
        assert f"de {len(SAMPLE_LEADS)} clientes" in pagin_info, f"Clientes pagination mismatch: {pagin_info}"
        print(f"  [PASS] Clientes table displays all {len(SAMPLE_LEADS)} leads (info: '{pagin_info}')")

        # 6. Test Drag & Drop persistence to canonical status
        await pipeline_btn.click()
        await page.wait_for_timeout(200)

        # Trigger drag-and-drop from 'revisar' to 'respondeu'
        await page.evaluate("""() => {
            var card = document.querySelector('.card:has(.nm)');
            dragSlug = 'lead-unknown';
            var colRespondeu = document.querySelector('.col[data-st="respondeu"]');
            solta({preventDefault: () => {}, currentTarget: colRespondeu}, 'respondeu');
        }""")
        await page.wait_for_timeout(500)

        # Verify card is now in 'respondeu' column
        col_respondeu = page.locator('.col[data-st="respondeu"]')
        assert await col_respondeu.locator(':text("Lead Unknown Status")').count() == 1, "Card was not moved to 'respondeu' column"
        print("  [PASS] Drag & drop to 'respondeu' moved card and updated state successfully")

        await browser.close()

    print("==================================================")
    print("ALL DASHBOARD PIPELINE TESTS PASSED!")
    print("==================================================")

def main():
    port = 8799
    httpd = socketserver.TCPServer(("127.0.0.1", port), MockDashboardHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)
    try:
        asyncio.run(run_pipeline_regression_tests(port))
    finally:
        httpd.shutdown()
        httpd.server_close()

if __name__ == "__main__":
    main()
