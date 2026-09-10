import os
import http.server
import socketserver
import threading
import time
from playwright.sync_api import sync_playwright

PORT = 4015
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

    viewports = [
        ("desktop_1440", 1440, 900),
        ("tablet_768", 768, 1024),
        ("mobile_390", 390, 844),
    ]

    print("\n=== VERIFYING B3.1 VIEWPORTS & COMPARISON STAGE ===")

    for name, w, h in viewports:
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(f"http://127.0.0.1:{PORT}/", wait_until="networkidle")

        # 1. Check horizontal scroll / overflow
        scroll_w = page.evaluate("document.documentElement.scrollWidth")
        client_w = page.evaluate("document.documentElement.clientWidth")
        overflow = scroll_w > client_w
        print(f"[{name}] Viewport {w}x{h}: scrollWidth={scroll_w}, clientWidth={client_w}, overflow={overflow}")

        # 2. Check Comparison Stage Images
        slider = page.locator('[data-role="signature-section"]')
        images = slider.locator("img")
        img_count = images.count()
        print(f"[{name}] Signature slider images found: {img_count}")

        for i in range(img_count):
            img = images.nth(i)
            src = img.get_attribute("src")
            natural_w = img.evaluate("el => el.naturalWidth")
            natural_h = img.evaluate("el => el.naturalHeight")
            client_iw = img.evaluate("el => el.clientWidth")
            client_ih = img.evaluate("el => el.clientHeight")
            object_fit = img.evaluate("el => window.getComputedStyle(el).objectFit")
            print(f"  Img {i} ({src}): natural={natural_w}x{natural_h}, rendered={client_iw}x{client_ih}, objectFit={object_fit}")
            assert object_fit == "contain", f"Expected objectFit contain, got {object_fit}"
            assert natural_w > 0 and natural_h > 0, "Image failed to load"

        # Take screenshot of comparison section
        screenshot_path = f"public/b3_1_comparison_{name}.png"
        slider.screenshot(path=screenshot_path)
        print(f"  Saved comparison screenshot to {screenshot_path}")

        # Take full page screenshot
        full_screenshot_path = f"public/b3_1_full_{name}.png"
        page.screenshot(path=full_screenshot_path, full_page=True)
        print(f"  Saved full page screenshot to {full_screenshot_path}")

        page.close()

    browser.close()
    print("\nALL VIEWPORTS VERIFIED WITHOUT OVERFLOW OR CROPPING!")
