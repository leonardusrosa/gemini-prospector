import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    site_dir = Path("sites/iost-ortodontia-aline-iost-rio-claro").resolve()
    url = (site_dir / "index.html").as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(500)

        toggle = page.locator("#mobile-toggle")
        drawer = page.locator("#mobile-drawer")

        # Initial state (closed)
        aria_closed = await toggle.get_attribute("aria-expanded")
        drawer_visible = await drawer.is_visible()
        drawer_box = await drawer.bounding_box()
        print(f"Closed: aria-expanded={aria_closed}, is_visible={drawer_visible}, box={drawer_box}")

        # Click to open
        await toggle.click()
        await page.wait_for_timeout(300)
        aria_open = await toggle.get_attribute("aria-expanded")
        open_visible = await drawer.is_visible()
        open_box = await drawer.bounding_box()
        print(f"Open: aria-expanded={aria_open}, is_visible={open_visible}, height={open_box['height'] if open_box else 0}")

        # Click to close
        await toggle.click()
        await page.wait_for_timeout(300)
        aria_closed_again = await toggle.get_attribute("aria-expanded")
        closed_again_visible = await drawer.is_visible()
        hero = page.locator('[data-role="hero"]')
        hero_box = await hero.bounding_box()
        print(f"Closed again: aria-expanded={aria_closed_again}, is_visible={closed_again_visible}, hero_y={hero_box['y'] if hero_box else 0}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
