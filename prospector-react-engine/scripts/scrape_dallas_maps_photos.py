import asyncio
import json
import re
from playwright.async_api import async_playwright

MAPS_URL = "https://www.google.com/maps/place/Dallas+Detailing+And+Buffing/@32.9725357,-96.8424282,17z/data=!4m7!3m6!1s0x864c20bdf8a4cd63:0x9e31a704cb899cc4!8m2!3d32.9725357!4d-96.8424282!10e5!16s%2Fg%2F1pzpjt5dt?entry=ttu"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()

        print("Navigating to Google Maps Place Profile...")
        await page.goto(MAPS_URL, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(4000)

        # Look for Photos button / tab
        # Click on Photos button
        try:
            # Look for button with text "Photos" or containing photo thumbnails
            photos_btn = page.locator('button[aria-label*="Photos"], button:has-text("Photos"), div[role="tab"]:has-text("Photos")')
            if await photos_btn.count() > 0:
                print("Clicking Photos button...")
                await photos_btn.first.click()
                await page.wait_for_timeout(3000)
            else:
                # Try clicking the lead photo to open media gallery
                lead_photo = page.locator('button[aria-label*="Photo"], img[src*="googleusercontent"]').first
                if await lead_photo.count() > 0:
                    print("Clicking lead photo...")
                    await lead_photo.click()
                    await page.wait_for_timeout(3000)
        except Exception as e:
            print("Error clicking photo tab:", e)

        # Scroll photo gallery container to load more images
        print("Scrolling gallery...")
        for _ in range(5):
            await page.keyboard.press("PageDown")
            await page.wait_for_timeout(1000)

        # Extract all image elements with googleusercontent URLs
        images_data = await page.evaluate('''() => {
            const items = [];
            const imgEls = document.querySelectorAll('img[src*="googleusercontent.com"]');
            imgEls.forEach((img, idx) => {
                const src = img.getAttribute('src');
                const alt = img.getAttribute('alt') || '';
                // Check closest parent or container for uploader
                let container = img.closest('div[aria-label], button, a');
                let aria = container ? (container.getAttribute('aria-label') || '') : '';
                items.push({
                    index: idx,
                    src: src,
                    alt: alt,
                    ariaLabel: aria
                });
            });
            return items;
        }''')

        print(f"Discovered {len(images_data)} image elements on Maps profile.")
        
        # Deduplicate by core URL (stripping size parameters =w...-h... or =s...)
        seen = set()
        deduped = []
        for item in images_data:
            base_url = re.sub(r'=w\d+-h\d+.*|=s\d+.*', '', item['src'])
            if base_url not in seen and 'googleusercontent.com' in base_url:
                seen.add(base_url)
                deduped.append({
                    "baseUrl": base_url,
                    "originalSrc": item['src'],
                    "alt": item['alt'],
                    "ariaLabel": item['ariaLabel']
                })

        print(f"Total unique photo sources: {len(deduped)}")
        with open("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/maps_photos.json", "w", encoding="utf-8") as f:
            json.dump(deduped, f, indent=2)

        await browser.close()
        print("Saved maps_photos.json successfully.")

if __name__ == "__main__":
    asyncio.run(main())
