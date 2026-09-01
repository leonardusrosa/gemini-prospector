import asyncio
from playwright.async_api import async_playwright

VERCEL_URL = "https://prospector-sites-beta.vercel.app/clientes/iost-ortodontia-aline-iost-rio-claro/"

async def verify_live():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page()
        
        print(f"Navigating to live production: {VERCEL_URL}")
        await page.goto(VERCEL_URL, wait_until="networkidle")
        
        # Check review section attributes
        rev_section = page.locator("#avaliacoes")
        mode = await rev_section.get_attribute("data-review-mode")
        rating = await rev_section.get_attribute("data-review-rating")
        count = await rev_section.get_attribute("data-review-count")
        print(f"Reviews Section: mode={mode}, rating={rating}, count={count}")
        
        # Check review card
        card = page.locator("article[data-role='review-card']")
        card_count = await card.count()
        print(f"Review Cards found: {card_count}")
        if card_count > 0:
            ev_id = await card.first.get_attribute("data-review-evidence-id")
            card_text = await card.first.inner_text()
            print(f"Card 0 evidence-id={ev_id}")
            print(f"Card 0 text:\n{card_text}")
            
        # Check Google summary badge
        badge = page.locator("[data-role='reviews-summary']")
        badge_text = await badge.inner_text() if await badge.count() > 0 else "None"
        print(f"Reviews Summary Badge text:\n{badge_text}")
        
        # Desktop 1440
        await page.set_viewport_size({"width": 1440, "height": 900})
        await rev_section.scroll_into_view_if_needed()
        await page.wait_for_timeout(1000)
        await page.screenshot(path="e:/Antigravity/prospector/live_prod_1440.png")
        
        # Reviews section screenshot
        await rev_section.screenshot(path="e:/Antigravity/prospector/live_reviews_section.png")
        
        # Hero section screenshot
        hero = page.locator("section[data-role='hero']")
        await hero.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await hero.screenshot(path="e:/Antigravity/prospector/live_hero_section.png")
        
        # Mobile 390
        await page.set_viewport_size({"width": 390, "height": 844})
        await rev_section.scroll_into_view_if_needed()
        await page.wait_for_timeout(1000)
        await rev_section.screenshot(path="e:/Antigravity/prospector/live_reviews_mobile.png")
        
        print("All live screenshots captured successfully.")
        await b.close()

if __name__ == "__main__":
    asyncio.run(verify_live())
