import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

VIEWPORTS = [
    {"name": "desktop_1440x900", "width": 1440, "height": 900},
    {"name": "mobile_390x844", "width": 390, "height": 844, "is_mobile": True},
]

async def main():
    site_dir = Path("sites/clinica-dra-francine-goulart-rio-claro").resolve()
    html_file = site_dir / "index.html"
    url = html_file.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for vp in VIEWPORTS:
            context = await browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                is_mobile=vp.get("is_mobile", False),
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)

            hero = page.locator('[data-role="hero"]')
            hero_box = await hero.bounding_box()
            hero_img = page.locator('[data-role="hero"] img[data-role="hero-image"]')
            img_box = await hero_img.bounding_box()

            vp_w = vp["width"]
            img_w = img_box["width"] if img_box else 0
            ratio = (img_w / vp_w) * 100

            print(f"[{vp['name']}] Viewport Width: {vp_w}px | Hero Width: {hero_box['width']}px | Hero Img Width: {img_w}px | Ratio: {ratio:.2f}% | >=98%: {ratio >= 98.0}")

            await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
