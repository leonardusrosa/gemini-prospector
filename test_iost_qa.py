import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent
HTML_FILE = ROOT / "sites" / "iost-ortodontia-aline-iost-rio-claro" / "iost-ortodontia-aline-iost-rio-claro.html"
PROPOSTA_FILE = ROOT / "sites" / "iost-ortodontia-aline-iost-rio-claro" / "proposta.html"

async def test_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Desktop 1440x900
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))

        file_url = f"file:///{HTML_FILE.as_posix()}"
        await page.goto(file_url, wait_until="load")
        await page.wait_for_timeout(1000)
        
        # Check horizontal overflow
        has_h_scroll = await page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        print(f"[Desktop 1440x900] Horizontal overflow: {'FAIL' if has_h_scroll else 'PASS'}")

        # Check Hero CTA count
        hero_ctas = await page.query_selector_all(".hero-cta-wrap .btn, .hero-section .btn")
        print(f"[Desktop] Hero CTA count: {len(hero_ctas)} (Expected: 1) -> {'PASS' if len(hero_ctas) == 1 else 'FAIL'}")

        # Screenshot Desktop
        await page.screenshot(path="qa_iost_desktop_1440x900.png", full_page=True)
        print("Captured qa_iost_desktop_1440x900.png")

        # 2. Tablet 800x1024
        await page.set_viewport_size({"width": 800, "height": 1024})
        await page.wait_for_timeout(500)
        has_h_scroll_tab = await page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        print(f"[Tablet 800x1024] Horizontal overflow: {'FAIL' if has_h_scroll_tab else 'PASS'}")
        await page.screenshot(path="qa_iost_tablet_800.png", full_page=True)
        print("Captured qa_iost_tablet_800.png")

        # 3. Mobile 390x844
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(500)
        has_h_scroll_mob = await page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth")
        print(f"[Mobile 390x844] Horizontal overflow: {'FAIL' if has_h_scroll_mob else 'PASS'}")
        await page.screenshot(path="qa_iost_mobile_390x844.png", full_page=True)
        print("Captured qa_iost_mobile_390x844.png")

        # 4. Proposta Desktop & Mobile
        prop_url = f"file:///{PROPOSTA_FILE.as_posix()}"
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.goto(prop_url, wait_until="load")
        await page.screenshot(path="qa_iost_proposta_desktop.png")
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.screenshot(path="qa_iost_proposta_mobile.png")
        print("Captured proposal screenshots.")

        print(f"Console errors: {len(console_errors)}")
        for err in console_errors:
            print("  ERROR:", err)

        await browser.close()

def audit_text_rules():
    html_content = HTML_FILE.read_text(encoding="utf-8")
    
    # Strip script and style
    no_scripts = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    # Strip HTML tags
    text_only = re.sub(r'<[^>]+>', ' ', no_scripts)
    
    # Check em-dashes and en-dashes
    em_dashes = [m.start() for m in re.finditer(r'—', text_only)]
    en_dashes = [m.start() for m in re.finditer(r'–', text_only)]
    
    # Check emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(text_only)
    
    print("\n--- TEXT RULES AUDIT ---")
    print(f"Em-dashes in visible copy: {len(em_dashes)} -> {'PASS' if len(em_dashes) == 0 else 'FAIL'}")
    print(f"En-dashes in visible copy: {len(en_dashes)} -> {'PASS' if len(en_dashes) == 0 else 'FAIL'}")
    print(f"Emojis in visible copy: {len(emojis)} -> {'PASS' if len(emojis) == 0 else 'FAIL'}")
    if em_dashes:
        print("Em-dash snippets:", [text_only[max(0, p-30):p+30] for p in em_dashes[:5]])
    if en_dashes:
        print("En-dash snippets:", [text_only[max(0, p-30):p+30] for p in en_dashes[:5]])

if __name__ == "__main__":
    audit_text_rules()
    asyncio.run(test_page())
