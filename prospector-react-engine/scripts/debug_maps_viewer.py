import asyncio
from playwright.async_api import async_playwright

URL_VIEWER = "https://www.google.com/maps/place/Dallas+Detailing+And+Buffing/@32.9725357,-96.8424282,3a,75y,90t/data=!3m7!1e2!3m5!1sCIABIhADycKz4iNVhWgQXYQAAakD!2e10!3e12!7i3024!8i4032!4m9!3m8!1s0x864c20bdf8a4cd63:0x9e31a704cb899cc4!8m2!3d32.9725357!4d-96.8424282!10e5!16s%2Fg%2F1pzpjt5dt"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        print("Navigating...")
        await page.goto(URL_VIEWER, wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)

        await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/maps_viewer_debug.png")
        print("Screenshot saved to maps_viewer_debug.png")

        # Print all img tags
        imgs = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('img')).map(i => ({ src: i.src, w: i.width, h: i.height, alt: i.alt }));
        }''')
        print(f"Total img tags: {len(imgs)}")
        for im in imgs:
            print("IMG:", im['src'][:100], f"({im['w']}x{im['h']})", im['alt'])

        await browser.close()

asyncio.run(main())
