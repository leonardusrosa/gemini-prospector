import asyncio
from playwright.async_api import async_playwright
import re
import json

URL_SEARCH = "https://www.google.com/maps/search/Dallas+Detailing+And+Buffing+Addison+TX"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()

        photos = set()
        def on_response(r):
            u = r.url
            if "googleusercontent.com" in u or "ggpht.com" in u:
                if not re.search(r'(=w36-h36|=w48-h48|=s32|=s48|=s64|=w24-h24|ba12|br100)', u):
                    clean = re.sub(r'(=w\d+-h\d+.*|=s\d+.*|=k-no.*)', '', u)
                    photos.add(clean)

        page.on("response", on_response)

        print("Navigating to search...")
        await page.goto(URL_SEARCH, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        # Click the first result (Dallas Detailing And Buffing 4.9)
        first_result = page.locator('div[role="feed"] a[href*="place"], div[role="article"]').first
        print("Clicking first result...")
        await first_result.click()
        await page.wait_for_timeout(4000)

        await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/maps_place_card.png")
        print("Saved place card screenshot")

        # Check if Photos button or tab exists
        photos_btn = page.locator('button[aria-label*="photo" i], button[aria-label*="foto" i], button:has-text("Photos"), button:has-text("Fotos")')
        print(f"Photos buttons count: {await photos_btn.count()}")
        if await photos_btn.count() > 0:
            print("Clicking Photos tab...")
            await photos_btn.first.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/maps_photos_open.png")

            # Scroll through the photos tab
            for _ in range(8):
                await page.keyboard.press("PageDown")
                await page.wait_for_timeout(800)

        print(f"Total unique photo URLs intercepted: {len(photos)}")
        photos_list = list(photos)
        with open("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/scraped_maps_photos.json", "w") as f:
            json.dump(photos_list, f, indent=2)

        await browser.close()

asyncio.run(main())
