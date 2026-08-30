import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            locale="pt-BR",
            viewport={"width": 1400, "height": 900}
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        page = await context.new_page()
        url = 'https://www.google.com/maps/place/Instituto+Ferreira+Odontologia+e+Harmoniza%C3%A7%C3%A3o+Facial+%7C+Dr.+Cassio+Ferreira+%7C+Dentista+em+Rio+Claro/@-22.3906109,-47.5691163,17z/data=!4m8!3m7!1s0x94c7db099ccb002d:0xc7bc67d9b0f9c6b3!8m2!3d-22.3906109!4d-47.5691163!9m1!1b1!16s%2Fg%2F11c60crpk9'
        print("Navigating with stealth settings...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(6000)
        await page.screenshot(path="scratch_stealth.png")
        
        # Check text
        text = await page.evaluate('''() => {
            const el = document.querySelector('div[role="main"]') || document.body;
            return el.innerText;
        }''')
        print("Text len:", len(text))
        print("Has avaliações:", "avalia" in text.lower())
        
        # Check if reviews tab or cards exist
        cards = page.locator('div.jftiEf, div[data-review-id]')
        print("Review cards count:", await cards.count())
        
        with open("scratch_stealth_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        await browser.close()

asyncio.run(main())
