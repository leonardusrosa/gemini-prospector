import asyncio
import json
import re
from playwright.async_api import async_playwright

URL_VIEWER = "https://www.google.com/maps/place/Dallas+Detailing+And+Buffing/@32.9725357,-96.8424282,3a,75y,90t/data=!3m7!1e2!3m5!1sCIABIhADycKz4iNVhWgQXYQAAakD!2e10!3e12!7i3024!8i4032!4m9!3m8!1s0x864c20bdf8a4cd63:0x9e31a704cb899cc4!8m2!3d32.9725357!4d-96.8424282!10e5!16s%2Fg%2F1pzpjt5dt"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()

        collected = []
        seen_urls = set()

        def handle_response(response):
            u = response.url
            if ("googleusercontent.com" in u or "ggpht.com" in u) and not re.search(r'(=w36-h36|=w48-h48|=s32|=s48|=s64|ba12|br100)', u):
                # Clean base url
                base = re.sub(r'(=w\d+-h\d+.*|=s\d+.*|=k-no.*)', '', u)
                if base not in seen_urls:
                    seen_urls.add(base)

        page.on("response", handle_response)

        print("Opening photo viewer on Maps...")
        await page.goto(URL_VIEWER, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)

        for step in range(15):
            print(f"Step {step+1}: inspecting active photo...")
            
            # Extract metadata from current viewer screen
            info = await page.evaluate('''() => {
                // Find main image element
                let mainImg = document.querySelector('div[role="main"] img[src*="googleusercontent"], div.widget-scene img, img[class*="viewer"]');
                if (!mainImg) {
                    const allImgs = Array.from(document.querySelectorAll('img[src*="googleusercontent.com"]'));
                    allImgs.sort((a,b) => (b.naturalWidth * b.naturalHeight) - (a.naturalWidth * a.naturalHeight));
                    mainImg = allImgs[0];
                }

                // Look for uploader and caption
                const uploaderEl = document.querySelector('div[aria-label*="Foto"], button[aria-label*="Foto"], a[href*="contrib"], span.gm2-body-2, h1');
                const uploader = uploaderEl ? (uploaderEl.innerText || uploaderEl.getAttribute('aria-label') || '') : '';

                return {
                    src: mainImg ? mainImg.src : null,
                    width: mainImg ? mainImg.naturalWidth : 0,
                    height: mainImg ? mainImg.naturalHeight : 0,
                    uploader: uploader
                };
            }''')

            if info and info.get('src'):
                clean = re.sub(r'(=w\d+-h\d+.*|=s\d+.*|=k-no.*)', '', info['src'])
                if clean not in [x['baseUrl'] for x in collected]:
                    collected.append({
                        "step": step,
                        "baseUrl": clean,
                        "fullSrc": info['src'],
                        "width": info['width'],
                        "height": info['height'],
                        "uploader": info['uploader']
                    })
                    print(f"  -> Captured photo: {clean[:70]}... ({info['width']}x{info['height']})")

            # Press ArrowRight to move to next photo in viewer
            await page.keyboard.press("ArrowRight")
            await page.wait_for_timeout(1500)

        print(f"\nTotal unique high-res gallery photos collected: {len(collected)}")
        with open("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/dallas_maps_gallery_photos.json", "w", encoding="utf-8") as f:
            json.dump(collected, f, indent=2)

        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
