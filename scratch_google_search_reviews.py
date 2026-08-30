import asyncio
import json
import re
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(locale='pt-BR')
        url = 'https://www.google.com/search?q=Instituto+Ferreira+Odontologia+Harmoniza%C3%A7%C3%A3o+Orofacial+Rio+Claro+SP'
        print("Navigating to Google Search...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(4000)
        
        # Click on reviews link in knowledge panel
        # Common selectors: a[data-fid*="reviews"], a:has-text("avaliações do Google"), a:has-text("comentários do Google")
        rev_links = page.locator('a:has-text("avaliações"), a:has-text("avaliação"), a[data-async-trigger*="review"]')
        print(f"Found {await rev_links.count()} potential review links")
        for i in range(await rev_links.count()):
            try:
                t = await rev_links.nth(i).inner_text()
                print(f"Link {i}: {t}")
                if "google" in t.lower() or "avaliaç" in t.lower():
                    await rev_links.nth(i).click()
                    print(f"Clicked link {i}")
                    await page.wait_for_timeout(4000)
                    break
            except Exception as e:
                print("Click error:", e)
                
        await page.screenshot(path="scratch_google_search.png")
        
        # Look for review blocks
        # Google Search review popup has class .gws-localreviews__google-review or div[data-review-id]
        cards = page.locator('div.gws-localreviews__google-review, div[data-review-id], div.WMbnJf, div.jftiEf')
        count = await cards.count()
        print(f"Found {count} review cards")
        
        reviews = []
        for i in range(count):
            card = cards.nth(i)
            try:
                author = await card.locator('.TSUbDb, .d4r55, .WNx5W, h3, a.Y0A0hc').first.inner_text()
            except Exception:
                author = ""
            try:
                stars_el = card.locator('span.kvMYJc, span[aria-label*="estrela"], span[aria-label*="star"], span.lTi8oc').first
                stars_aria = await stars_el.get_attribute('aria-label') if await stars_el.count() > 0 else '5'
            except Exception:
                stars_aria = '5'
            try:
                date_el = card.locator('span.rsqaWe, span.dehAhe, .xRkGif, span.dehAhe').first
                date_text = await date_el.inner_text() if await date_el.count() > 0 else ''
            except Exception:
                date_text = ""
            try:
                # Click 'Mais' inside card if present
                more = card.locator('a.review-more-link, button:has-text("Mais"), span:has-text("Mais")').first
                if await more.count() > 0:
                    await more.click(timeout=1000)
                    await page.wait_for_timeout(300)
            except Exception:
                pass
            try:
                text_el = card.locator('.review-full-text, .Jtu6Td, span.wiI7Bm, div.MyEned').first
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
                reviews.append(rev_obj)
                print(f"\n--- Review {len(reviews)} ---")
                print(json.dumps(rev_obj, ensure_ascii=False, indent=2))
                
        with open("scratch_reviews.json", "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
            
        print(f"\nTotal extracted textual reviews: {len(reviews)}")
        await browser.close()

asyncio.run(main())
