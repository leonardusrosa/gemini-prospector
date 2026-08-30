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
        
        # Scroll the review panel several times to ensure all reviews are loaded
        scroll_sel = 'div.m6QErb.DxyBCb, div.m6QErb'
        for _ in range(8):
            await page.evaluate("""() => {
                const scrollable = document.querySelector('div.m6QErb.DxyBCb') || document.querySelector('div[role="main"]') || document.querySelector('div.m6QErb');
                if (scrollable) scrollable.scrollTop += 1200;
            }""")
            await page.wait_for_timeout(1000)
            
        # Click all "... Mais" or "Mais" buttons to expand truncated reviews
        more_btns = page.locator('button.w8nwRe, button:has-text("Mais"), button:has-text("mais"), span:has-text("Mais")')
        count_more = await more_btns.count()
        print(f"Clicking {count_more} 'Mais' buttons...")
        for i in range(count_more):
            try:
                await more_btns.nth(i).click(timeout=1000)
                await page.wait_for_timeout(300)
            except Exception:
                pass
                
        await page.wait_for_timeout(1500)
        
        # Extract reviews
        cards = page.locator('div.jftiEf')
        count = await cards.count()
        print(f"Total review cards found: {count}")
        
        all_reviews = []
        for i in range(count):
            card = cards.nth(i)
            try:
                author = await card.locator('.d4r55').first.inner_text()
            except Exception:
                author = ""
            try:
                stars_el = card.locator('span.kvMYJc').first
                stars_aria = await stars_el.get_attribute('aria-label') if await stars_el.count() > 0 else '5'
            except Exception:
                stars_aria = '5'
            try:
                date_el = card.locator('span.rsqaWe').first
                date_text = await date_el.inner_text() if await date_el.count() > 0 else ''
            except Exception:
                date_text = ""
            try:
                text_el = card.locator('span.wiI7Bm').first
                review_text = await text_el.inner_text() if await text_el.count() > 0 else ''
            except Exception:
                review_text = ""
                
            if author and review_text:
                m = re.search(r'(\d+)', stars_aria)
                rating = int(m.group(1)) if m else 5
                
                rev_obj = {
                    "author": author.strip(),
                    "rating": rating,
                    "text": review_text.strip(),
                    "dateLabel": date_text.strip(),
                }
                all_reviews.append(rev_obj)
                
        print(f"Extracted {len(all_reviews)} full textual reviews!")
        with open("scratch_all_extracted_reviews.json", "w", encoding="utf-8") as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)
            
        await browser.close()

asyncio.run(main())
