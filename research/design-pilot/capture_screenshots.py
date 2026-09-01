import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

def capture(html_path, out_desktop, out_mobile):
    html_uri = Path(html_path).resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # Desktop 1440x900
        page_desktop = browser.new_page(viewport={"width": 1440, "height": 900})
        page_desktop.goto(html_uri, wait_until="networkidle")
        page_desktop.wait_for_timeout(1000)
        page_desktop.screenshot(path=out_desktop, full_page=True)
        print(f"Captured desktop: {out_desktop}")
        
        # Mobile 390x844
        page_mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
        page_mobile.goto(html_uri, wait_until="networkidle")
        page_mobile.wait_for_timeout(1000)
        page_mobile.screenshot(path=out_mobile, full_page=True)
        print(f"Captured mobile: {out_mobile}")
        
        browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python capture_screenshots.py <html_path> <out_desktop> <out_mobile>")
        sys.exit(1)
    capture(sys.argv[1], sys.argv[2], sys.argv[3])
