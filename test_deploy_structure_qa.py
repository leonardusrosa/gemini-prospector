import os, sys, time, threading, http.server, socketserver
from playwright.sync_api import sync_playwright

DEPLOY_ROOT = r"E:\Antigravity\prospector-sites"
PORT = 8766

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DEPLOY_ROOT, **kwargs)
    def log_message(self, format, *args):
        pass

def run_local_qa():
    print("=== STARTING LOCAL DEPLOY-STRUCTURE QA ===", flush=True)

    # Start HTTP server
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    print(f"Serving {DEPLOY_ROOT} on http://127.0.0.1:{PORT}", flush=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for viewport, mode in [({"width": 1440, "height": 900}, "desktop"), ({"width": 390, "height": 844}, "mobile")]:
                print(f"\n--- Testing mode: {mode} ({viewport['width']}x{viewport['height']}) ---", flush=True)
                context = browser.new_context(viewport=viewport)
                page = context.new_page()

                failed_requests = []
                def on_request_failed(req):
                    failed_requests.append(f"FAILED: {req.url} - {req.failure}")
                page.on("requestfailed", on_request_failed)

                responses_404 = []
                def on_response(res):
                    if res.status >= 400 and not res.url.endswith("favicon.ico"):
                        responses_404.append(f"HTTP {res.status}: {res.url}")
                page.on("response", on_response)

                # 1. Open proposta.html
                prop_url = f"http://127.0.0.1:{PORT}/clientes/instituto-ferreira-odontologia-rio-claro/proposta.html"
                print(f"1. Navigating to {prop_url}...", flush=True)
                page.goto(prop_url, wait_until="networkidle")
                page.wait_for_timeout(500)

                prop_title = page.title()
                print(f"Proposal title: {prop_title}", flush=True)
                assert "Instituto Ferreira" in prop_title or "Proposta" in prop_title

                # Check CTA button in proposta.html
                cta = page.locator('a[href="./"]')
                print(f"Proposal CTA count: {cta.count()}", flush=True)
                assert cta.count() >= 1, "Proposal CTA with href='./' not found!"

                # 2. Click CTA -> should navigate to index.html
                print("2. Clicking proposal CTA...", flush=True)
                cta.first.click()
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(500)

                current_url = page.url
                print(f"Navigated to: {current_url}", flush=True)
                assert current_url.rstrip("/").endswith("/clientes/instituto-ferreira-odontologia-rio-claro"), f"Unexpected URL: {current_url}"

                # 3. Check public site content & structure
                site_title = page.title()
                print(f"Site title: {site_title}", flush=True)
                assert "Instituto Ferreira" in site_title

                # Check hero visibility
                hero = page.locator("section, header, .hero, h1").first
                assert hero.is_visible(), "Hero is not visible!"
                print("Hero visibility: PASS", flush=True)

                # Check key sections
                sections_text = page.locator("body").text_content()
                assert "Cassio Ferreira" in sections_text or "Dr." in sections_text, "Doctor info not found!"
                assert "Rio Claro" in sections_text, "City reference not found!"
                print("Full site content checks: PASS", flush=True)

                # Check no editor artifacts
                editor_elements = page.locator("[data-pe-author-style], #prospector-editor, .editor-toolbar, #editor-panel")
                assert editor_elements.count() == 0, f"Editor elements detected in public site! Count: {editor_elements.count()}"
                print("No editor exposed: PASS", flush=True)

                # 4. Test browser back
                print("3. Testing browser back...", flush=True)
                page.go_back(wait_until="networkidle")
                page.wait_for_timeout(500)
                back_url = page.url
                print(f"Back URL: {back_url}", flush=True)
                assert "proposta.html" in back_url, f"Browser back failed to return to proposta.html: {back_url}"
                print("Browser back: PASS", flush=True)

                # Take screenshots
                screenshot_path = f"qa_deploy_{mode}.png"
                page.screenshot(path=screenshot_path)
                print(f"Saved screenshot: {screenshot_path}", flush=True)

                # Check 404s / failures
                print(f"Failed requests: {failed_requests}", flush=True)
                print(f"404 responses: {responses_404}", flush=True)
                assert len(failed_requests) == 0, f"Encountered failed requests: {failed_requests}"
                assert len(responses_404) == 0, f"Encountered 404 responses: {responses_404}"

                context.close()

            browser.close()

        print("\n=== LOCAL DEPLOY-STRUCTURE QA: ALL CHECKS PASSED ===", flush=True)
        return True
    finally:
        httpd.shutdown()
        httpd.server_close()

if __name__ == "__main__":
    success = run_local_qa()
    if not success:
        sys.exit(1)
