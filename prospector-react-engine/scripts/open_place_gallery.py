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

        # Click the text directly
        print("Clicking text 'Dallas Detailing And Buffing'...")
        await page.locator('text="Dallas Detailing And Buffing"').first.click()
        await page.wait_for_timeout(5000)

        await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/maps_card_opened.png")
        print("Saved maps_card_opened.png")

        # Now check if there is a lead image or photos button
        # Look for buttons in the opened place details pane
        all_buttons = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('button')).map(b => ({
                text: b.innerText,
                aria: b.getAttribute('aria-label') || ''
            }));
        }''')
        print(f"Buttons in place card: {len(all_buttons)}")
        for b in all_buttons:
            if 'foto' in b['text'].lower() or 'foto' in b['aria'].lower() or 'photo' in b['text'].lower() or 'photo' in b['aria'].lower():
                print("FOUND PHOTO BUTTON:", b)

        # Click on the photo gallery / lead image
        lead_img_btn = page.locator('button[aria-label*="Foto" i], button[aria-label*="Photo" i], img[src*="googleusercontent"]').first
        if await lead_img_btn.count() > 0:
            print("Clicking photo button/image...")
            await lead_img_btn.click()
            await page.wait_for_timeout(4000)
            await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/maps_gallery_view.png")

            # Scroll down to load more photos
            for _ in range(10):
                await page.mouse.wheel(0, 600)
                await page.wait_for_timeout(600)

        print(f"Total unique photo URLs intercepted: {len(photos)}")
        photos_list = list(photos)
        for i, p in enumerate(photos_list):
            print(f"[{i+1}] {p}")

        with open("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/dallas_maps_photos_final.json", "w") as f:
            json.dump(photos_list, f, indent=2)

        await browser.close()

asyncio.run(main())
