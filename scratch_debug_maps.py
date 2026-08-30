import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale='pt-BR')
        url = 'https://www.google.com/maps/place/Instituto+Ferreira+Odontologia+e+Harmoniza%C3%A7%C3%A3o+Facial+%7C+Dr.+Cassio+Ferreira+%7C+Dentista+em+Rio+Claro/@-22.3906109,-47.5691163,17z/data=!4m8!3m7!1s0x94c7db099ccb002d:0xc7bc67d9b0f9c6b3!8m2!3d-22.3906109!4d-47.5691163!16s%2Fg%2F11c60crpk9?entry=ttu'
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(4000)
        
        # Look for the rating container or reviews button/tab
        # Find elements containing '5,0' or 'avaliaç'
        elements = await page.locator('span:has-text("5,0"), div:has-text("5,0"), button:has-text("5,0")').all()
        print(f"Found {len(elements)} elements with '5,0'")
        for el in elements:
            try:
                txt = await el.inner_text()
                print("Element text:", txt.replace('\n', ' '))
                # Try clicking it
                await el.click(timeout=1000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                pass
                
        # Scroll side panel down multiple times
        await page.evaluate("""() => {
            const panels = document.querySelectorAll('div.m6QErb, div[role="main"]');
            panels.forEach(p => p.scrollTop += 2000);
        }""")
        await page.wait_for_timeout(3000)
        
        text = await page.inner_text('body')
        with open("scratch_body_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        print("Body text written to scratch_body_text.txt. Length:", len(text))
        await browser.close()

asyncio.run(main())
