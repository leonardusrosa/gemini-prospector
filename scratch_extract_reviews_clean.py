import asyncio
import json
import re
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
        print("Navigating...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(6000)
        
        cards = page.locator('div.jftiEf')
        count = await cards.count()
        print(f"Cards count: {count}")
        
        reviews = []
        for i in range(count):
            card = cards.nth(i)
            # Try to click 'Mais' inside this card
            more_btn = card.locator('button.w8nwRe, button:has-text("Mais"), span:has-text("Mais")').first
            if await more_btn.count() > 0:
                try:
                    await more_btn.click(timeout=1000)
                    await page.wait_for_timeout(200)
                except Exception:
                    pass
            
            author = ""
            for a_sel in ['.d4r55', '.WNx5W', '.TSUbDb', 'div[class*="header"]']:
                el = card.locator(a_sel).first
                if await el.count() > 0:
                    author = await el.inner_text()
                    if author:
                        break
                        
            stars_aria = "5"
            stars_el = card.locator('span.kvMYJc, span[aria-label*="estrela"]').first
            if await stars_el.count() > 0:
                stars_aria = await stars_el.get_attribute('aria-label') or "5"
                
            date_text = ""
            date_el = card.locator('span.rsqaWe, span.dehAhe').first
            if await date_el.count() > 0:
                date_text = await date_el.inner_text()
                
            text = ""
            text_el = card.locator('span.wiI7Bm, div.MyEned').first
            if await text_el.count() > 0:
                text = await text_el.inner_text()
                
            if author and text:
                m = re.search(r'(\d+)', stars_aria)
                rating = int(m.group(1)) if m else 5
                rev = {
                    "author": author.strip(),
                    "rating": rating,
                    "text": text.strip().replace('\n', ' '),
                    "dateLabel": date_text.strip()
                }
                reviews.append(rev)
                
        print(f"Extracted {len(reviews)} reviews")
        with open("scratch_all_extracted_reviews.json", "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
            
        await browser.close()

asyncio.run(main())
