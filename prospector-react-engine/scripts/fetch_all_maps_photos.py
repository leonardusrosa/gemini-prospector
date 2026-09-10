import asyncio
import json
import re
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()

        collected_photos = set()
        
        # Listen to all responses
        def on_response(response):
            url = response.url
            if "googleusercontent.com" in url or "ggpht.com" in url:
                # filter out small icons/avatars (like w36-h36)
                if not re.search(r'(=w36-h36|=w48-h48|=s32|=s48|=s64|=w24-h24|br100|ba12)', url):
                    clean = re.sub(r'(=w\d+-h\d+.*|=s\d+.*|=k-no.*)', '', url)
                    collected_photos.add(clean)

        page.on("response", on_response)

        # Direct Google Maps URL with photos pane parameter !3m8!1e2
        # In Google Maps, !1e2 opens the photos pane directly!
        url = "https://www.google.com/maps/place/Dallas+Detailing+And+Buffing/@32.9725357,-96.8424282,17z/data=!4m7!3m6!1s0x864c20bdf8a4cd63:0x9e31a704cb899cc4!8m2!3d32.9725357!4d-96.8424282!10e5!16s%2Fg%2F1pzpjt5dt"
        
        print("Loading Maps URL...")
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(3000)

        # Look for photo buttons or tabs
        # Look for the Photos button
        btns = await page.locator('button').all()
        for b in btns:
            txt = (await b.inner_text()).strip().lower()
            aria = (await b.get_attribute("aria-label") or "").lower()
            if "photo" in txt or "photo" in aria or "all" in txt:
                print(f"Found candidate button: text='{txt}', aria='{aria}'")
                try:
                    await b.click()
                    await page.wait_for_timeout(2000)
                    break
                except:
                    pass

        # Scroll down the pane
        print("Scrolling pane...")
        for i in range(10):
            await page.mouse.wheel(0, 800)
            await page.wait_for_timeout(1000)

        # Also inspect DOM for background-image and img src
        dom_urls = await page.evaluate('''() => {
            const list = [];
            document.querySelectorAll('*').forEach(el => {
                const bg = window.getComputedStyle(el).backgroundImage;
                if (bg && (bg.includes('googleusercontent.com') || bg.includes('ggpht.com'))) {
                    const match = bg.match(/url\\(["']?(.*?)["']?\\)/);
                    if (match) list.push(match[1]);
                }
                if (el.tagName === 'IMG' && el.src) {
                    list.push(el.src);
                }
            });
            return list;
        }''')

        for u in dom_urls:
            if not re.search(r'(=w36-h36|=w48-h48|=s32|=s48|=s64|=w24-h24|br100|ba12)', u):
                clean = re.sub(r'(=w\d+-h\d+.*|=s\d+.*|=k-no.*)', '', u)
                collected_photos.add(clean)

        print(f"Total collected raw photo URLs: {len(collected_photos)}")
        valid_photos = [u for u in collected_photos if "googleusercontent" in u or "ggpht" in u]
        print(f"Valid Google photo URLs: {len(valid_photos)}")
        for i, u in enumerate(valid_photos):
            print(f"[{i+1}] {u}")

        with open("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/all_maps_photos.json", "w", encoding="utf-8") as f:
            json.dump(valid_photos, f, indent=2)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
