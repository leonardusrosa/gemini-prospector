import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

VIEWPORTS = [
    {"name": "desktop_1440x900", "width": 1440, "height": 900},
    {"name": "ultrawide_1920x1080", "width": 1920, "height": 1080},
    {"name": "tablet_800x1024", "width": 800, "height": 1024},
    {"name": "mobile_390x844", "width": 390, "height": 844, "is_mobile": True},
]

async def main():
    site_dir = Path("sites/clinica-dra-francine-goulart-rio-claro").resolve()
    html_file = site_dir / "index.html"
    screenshots_dir = site_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    url = html_file.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for vp in VIEWPORTS:
            context = await browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                is_mobile=vp.get("is_mobile", False),
                device_scale_factor=1,
            )
            page = await context.new_page()
            await page.goto(url, wait_until="load")
            await page.wait_for_timeout(500)
            
            # Check horizontal overflow
            overflow = await page.evaluate(
                "document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )
            scroll_w = await page.evaluate("document.documentElement.scrollWidth")
            client_w = await page.evaluate("document.documentElement.clientWidth")
            
            out_file = screenshots_dir / f"{vp['name']}.png"
            await page.screenshot(path=str(out_file), full_page=True)
            print(f"[{vp['name']}] scrollWidth: {scroll_w}, clientWidth: {client_w}, overflow: {overflow} -> Saved {out_file.name}")
            
            await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
