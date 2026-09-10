import os
import gzip
import http.server
import socketserver
import threading
import time
from playwright.sync_api import sync_playwright

PORT = 4009
DIRECTORY = r"e:\Antigravity\prospector\prospector-react-engine\out"

class GzipHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Handle root
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        
        rel_path = self.path.split("?")[0].lstrip("/")
        file_path = os.path.join(DIRECTORY, rel_path)

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return super().do_GET()

        accept_encoding = self.headers.get("Accept-Encoding", "")
        ext = os.path.splitext(file_path)[1].lower()
        compressible = ext in [".html", ".js", ".css", ".json", ".svg", ".txt"]

        if compressible and "gzip" in accept_encoding:
            with open(file_path, "rb") as f:
                content = f.read()
            compressed = gzip.compress(content)
            
            content_types = {
                ".html": "text/html",
                ".js": "application/javascript",
                ".css": "text/css",
                ".json": "application/json",
                ".svg": "image/svg+xml",
            }
            ctype = content_types.get(ext, "application/octet-stream")
            
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(compressed)))
            self.end_headers()
            self.wfile.write(compressed)
        else:
            return super().do_GET()

def run_server():
    with socketserver.TCPServer(("127.0.0.1", PORT), GzipHandler) as httpd:
        httpd.serve_forever()

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(0.5)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    responses = []

    def on_response(response):
        url = response.url
        status = response.status
        headers = response.headers
        try:
            body = response.body()
            responses.append({
                "url": url,
                "status": status,
                "headers": headers,
                "body_len": len(body),
            })
        except Exception:
            pass

    page.on("response", on_response)
    page.goto(f"http://127.0.0.1:{PORT}/", wait_until="networkidle")

    print("\n=== REAL BROWSER (CHROMIUM) NETWORK AUDIT ===")
    app_js_gzip = 0
    polyfill_js_gzip = 0
    total_js_gzip = 0

    for r in responses:
        url = r["url"]
        if ".js" in url:
            filename = url.split("/")[-1].split("?")[0]
            # Use wire content-length if gzipped, otherwise body length
            cl = r["headers"].get("content-length")
            wire_bytes = int(cl) if cl is not None else r["body_len"]
            size_kb = wire_bytes / 1024
            encoding = r["headers"].get("content-encoding", "identity")
            is_poly = "polyfill" in filename.lower()
            is_origin = f"127.0.0.1:{PORT}" in url
            
            print(f"  [{'ORIGIN' if is_origin else '3RD-PARTY'}] [HTTP {r['status']}] {filename}: {size_kb:.1f} KB wire (encoding: {encoding}, polyfill: {is_poly})")
            
            if is_origin:
                if is_poly:
                    polyfill_js_gzip += wire_bytes
                else:
                    app_js_gzip += wire_bytes
                total_js_gzip += wire_bytes

    app_kb = app_js_gzip / 1024
    poly_kb = polyfill_js_gzip / 1024
    total_kb = total_js_gzip / 1024

    print("\n=== SUMMARY OF REAL ORIGIN JS TRANSFERRED OVER THE WIRE ===")
    print(f"APP_JS_GZIP: {app_kb:.1f} KB")
    print(f"POLYFILL_JS_GZIP: {poly_kb:.1f} KB")
    print(f"TOTAL_JS_GZIP_ACTUALLY_TRANSFERRED: {total_kb:.1f} KB")

    browser.close()
