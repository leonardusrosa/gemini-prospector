import asyncio
import functools
import http.server
import json
import os
import random
import shutil
import socketserver
import threading
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIR_ENGINE_A = PROJECT_ROOT.parent.parent / "prospector-sites" / "clientes" / "dallas-detailing-and-buffing"
DIR_ENGINE_B = PROJECT_ROOT / "out"
ARTIFACTS_DIR = Path(r"C:\Users\leo_b\.gemini\antigravity-ide\brain\e9e77699-be15-4e73-a267-218d256e1de1")

class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_server(directory, port):
    handler = functools.partial(SilentHandler, directory=str(directory))
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

async def capture():
    server_a = start_server(DIR_ENGINE_A, 4001)
    server_b = start_server(DIR_ENGINE_B, 4002)

    # Randomly assign Engine A and Engine B to Specimen 1 and Specimen 2
    is_a_specimen_1 = random.choice([True, False])
    mapping = {
        "specimen_1": "Engine A (Vanilla)" if is_a_specimen_1 else "Engine B2 (Round 2 React)",
        "specimen_2": "Engine B2 (Round 2 React)" if is_a_specimen_1 else "Engine A (Vanilla)",
        "url_1": "http://127.0.0.1:4001/" if is_a_specimen_1 else "http://127.0.0.1:4002/",
        "url_2": "http://127.0.0.1:4002/" if is_a_specimen_1 else "http://127.0.0.1:4001/",
    }

    key_path = PROJECT_ROOT / "scripts" / "blind_key.json"
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"Recorded sealed mapping to {key_path}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for s_id, url in [("specimen_1", mapping["url_1"]), ("specimen_2", mapping["url_2"])]:
            # Desktop 1440x900 full page
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            desktop_path = PROJECT_ROOT / "scripts" / f"{s_id}_desktop_1440.png"
            await page.screenshot(path=str(desktop_path), full_page=True)
            print(f"Captured {desktop_path.name}")
            
            # Copy to artifacts dir
            if ARTIFACTS_DIR.exists():
                shutil.copy(desktop_path, ARTIFACTS_DIR / desktop_path.name)
            await page.close()

            # Mobile 390x844 full page
            page = await browser.new_page(viewport={"width": 390, "height": 844})
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            mobile_path = PROJECT_ROOT / "scripts" / f"{s_id}_mobile_390.png"
            await page.screenshot(path=str(mobile_path), full_page=True)
            print(f"Captured {mobile_path.name}")
            
            if ARTIFACTS_DIR.exists():
                shutil.copy(mobile_path, ARTIFACTS_DIR / mobile_path.name)
            await page.close()

        await browser.close()

    server_a.shutdown()
    server_b.shutdown()
    print("Blind screenshot capture complete!")

if __name__ == "__main__":
    asyncio.run(capture())
