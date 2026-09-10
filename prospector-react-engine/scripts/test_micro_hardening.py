import os
import http.server
import socketserver
import threading
import time
from playwright.sync_api import sync_playwright

PORT = 4030
DIRECTORY = r"e:\Antigravity\prospector\prospector-react-engine\out"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_server():
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(0.5)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    print("\n=== TEST 1: NORMAL MOTION (VIDEO FORMAT & OPACITY) ===")
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    transfers = []
    def on_response(res):
        url = res.url
        if "video" in url:
            try:
                b = res.body()
                transfers.append((url, len(b)))
            except:
                pass
    page.on("response", on_response)

    page.goto(f"http://127.0.0.1:{PORT}/", wait_until="networkidle")

    # Check video format transferred
    for u, sz in transfers:
        print(f"  Video transferred: {u.split('/')[-1]} ({sz} bytes / {sz/1024:.1f} KB)")

    # Check video opacity
    video = page.locator("video.hero-video-bg")
    time.sleep(1.0) # allow 700ms transition
    opacity = video.evaluate("el => window.getComputedStyle(el).opacity")
    print(f"  Video computed opacity: {opacity}")

    # Check video playback
    is_paused = video.evaluate("el => el.paused")
    print(f"  Video is_paused: {is_paused}")

    page.close()

    print("\n=== TEST 2: REDUCED MOTION (ZERO TRANSFER & ZERO PLAYBACK) ===")
    rm_page = browser.new_page(viewport={"width": 1440, "height": 900})
    rm_page.emulate_media(reduced_motion="reduce")

    rm_transfers = []
    def on_rm_response(res):
        url = res.url
        if "video" in url:
            try:
                b = res.body()
                rm_transfers.append((url, len(b)))
            except:
                pass
    rm_page.on("response", on_rm_response)

    rm_page.goto(f"http://127.0.0.1:{PORT}/", wait_until="networkidle")

    rm_video_count = rm_page.locator("video.hero-video-bg").count()
    rm_video_bytes = sum(sz for _, sz in rm_transfers)

    print(f"  Reduced motion video elements in DOM: {rm_video_count}")
    print(f"  Reduced motion video transfers count: {len(rm_transfers)}")
    print(f"  Reduced motion video bytes transferred: {rm_video_bytes} bytes")

    rm_page.close()
    browser.close()
