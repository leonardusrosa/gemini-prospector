import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale='pt-BR', viewport={'width': 1400, 'height': 900})
        url = 'https://www.google.com/maps/search/Instituto+Ferreira+Odontologia+Harmoniza%C3%A7%C3%A3o+Orofacial+Rio+Claro+SP'
        print("Navigating to search URL...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        
        # Click directly on the 5,0 rating stars text to open reviews tab/view if possible
        # Or click on coordinates of '5,0'
        # Let's inspect elements under the left panel
        scrollable_sel = 'div[role="main"], div.m6QErb.DxyBCb, div.m6QErb'
        
        # Let's scroll the panel down 10 times and capture HTML
        for scroll_idx in range(1, 8):
            await page.evaluate('''() => {
                const el = document.querySelector('div[role="main"]') || document.querySelector('div.m6QErb.DxyBCb') || document.querySelector('div.m6QErb');
                if (el) {
                    el.scrollTop += 800;
                }
            }''')
            await page.wait_for_timeout(1500)
            await page.screenshot(path=f"scratch_scroll_{scroll_idx}.png")
            
        # Click all 'Mais' buttons
        more_btns = page.locator('button:has-text("Mais"), button:has-text("mais"), button.w8nwRe, span:has-text("Mais")')
        for i in range(await more_btns.count()):
            try:
                await more_btns.nth(i).click(timeout=1000)
            except Exception:
                pass
        await page.wait_for_timeout(1000)
        await page.screenshot(path="scratch_scroll_final.png")
        
        # Dump all text in left panel
        panel_text = await page.evaluate('''() => {
            const el = document.querySelector('div[role="main"]') || document.querySelector('div.m6QErb.DxyBCb') || document.body;
            return el.innerText;
        }''')
        
        with open("scratch_panel_text.txt", "w", encoding="utf-8") as f:
            f.write(panel_text)
            
        print("Panel text length:", len(panel_text))
        print("--- SNIPPET ---")
        print(panel_text[:1500])
        await browser.close()

asyncio.run(main())
