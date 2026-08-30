import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale='pt-BR')
        url = 'https://www.google.com/maps/search/Instituto+Ferreira+Odontologia+Harmoniza%C3%A7%C3%A3o+Orofacial+Rio+Claro+SP'
        print("Navigating to search URL...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(6000)
        
        # Click on reviews link or tab
        # Google Maps search places direct card often has "5,0" with "(36)" or "36 avaliações"
        rating_link = page.locator('button[aria-label*="avaliaç"], span[aria-label*="estrelas"], div.F7nice, button:has-text("avaliações")').first
        if await rating_link.count() > 0:
            print("Found rating link, clicking it...")
            await rating_link.click()
            await page.wait_for_timeout(4000)
            
        await page.screenshot(path="scratch_maps_reviews_view.png")
            
        # Scroll the review panel
        scrollable = page.locator('div.m6QErb.DxyBCb.kA9KIf.dS8AEf, div.m6QErb[aria-label*="avaliações"], div.m6QErb').first
        for _ in range(5):
            if await scrollable.count() > 0:
                await scrollable.evaluate('(el) => el.scrollTop += 800')
                await page.wait_for_timeout(1000)
        
        # Click all 'Mais' buttons to expand review texts
        more_btns = page.locator('button:has-text("Mais"), button:has-text("mais"), button.w8nwRe')
        for i in range(await more_btns.count()):
            try:
                await more_btns.nth(i).click(timeout=1000)
            except Exception:
                pass
        await page.wait_for_timeout(1000)
        
        cards = page.locator('div.jftiEf, div[data-review-id]')
        count = await cards.count()
        print(f"Found {count} review cards")
        
        reviews = []
        for i in range(count):
            card = cards.nth(i)
            try:
                author = await card.locator('.d4r55, .WNx5W, .TSUbDb, span.X43Kjb').first.inner_text()
            except Exception:
                author = ""
            try:
                stars_el = card.locator('span.kvMYJc, span[aria-label*="estrela"], span[aria-label*="star"]').first
                stars_aria = await stars_el.get_attribute('aria-label') if await stars_el.count() > 0 else '5'
            except Exception:
                stars_aria = '5'
            try:
                date_el = card.locator('span.rsqaWe, span.dehAhe, .xRkGif').first
                date_text = await date_el.inner_text() if await date_el.count() > 0 else ''
            except Exception:
                date_text = ""
            try:
                text_el = card.locator('span.wiI7Bm, div.MyEned').first
                review_text = await text_el.inner_text() if await text_el.count() > 0 else ''
            except Exception:
                review_text = ""
                
            if author and review_text:
                # Parse numeric rating
                import re
                m = re.search(r'(\d+)', stars_aria)
                rating = int(m.group(1)) if m else 5
                
                rev_obj = {
                    "author": author.strip(),
                    "rating": rating,
                    "text": review_text.strip(),
                    "dateLabel": date_text.strip(),
                }
                reviews.append(rev_obj)
                print(f"\n--- Review {len(reviews)} ---")
                print(json.dumps(rev_obj, ensure_ascii=False, indent=2))
                
        with open("scratch_reviews.json", "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
            
        print(f"\nTotal extracted textual reviews: {len(reviews)}")
        await browser.close()

asyncio.run(main())
