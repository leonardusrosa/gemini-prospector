import asyncio
from playwright.async_api import async_playwright
import re

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

        photos = []
        page.on("response", lambda r: photos.append(r.url) if ("googleusercontent.com" in r.url or "ggpht.com" in r.url) else None)

        print("Navigating to search...")
        await page.goto(URL_SEARCH, wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)

        await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/maps_search_result.png")
        print("Saved screenshot to maps_search_result.png")

        # Check if photos tab or photo button exists
        btn_photos = page.locator('button[aria-label*="Foto"], button[aria-label*="Photo"], button:has-text("Photos"), div[role="tab"]:has-text("Photos")')
        print(f"Candidate photo buttons: {await btn_photos.count()}")
        if await btn_photos.count() > 0:
            await btn_photos.first.click()
            await page.wait_for_timeout(4000)
            await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/maps_photos_tab.png")
            print("Saved photos tab screenshot")

        print("Total googleusercontent responses intercepted:", len(photos))
        unique_photos = set()
        for u in photos:
            if not re.search(r'(=w36-h36|=w48-h48|=s32|=s48|=s64|ba12|br100)', u):
                base = re.sub(r'(=w\d+-h\d+.*|=s\d+.*|=k-no.*)', '', u)
                unique_photos.add(base)

        print(f"Unique photo base URLs: {len(unique_photos)}")
        for i, u in enumerate(unique_photos):
            print(f"[{i+1}] {u}")

        await browser.close()

asyncio.run(main())
