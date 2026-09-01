import asyncio
from playwright.async_api import async_playwright

URL = "https://www.google.com/maps/place/Dentista+Dra.+Francine+Goulart/@-22.4125632,-47.5594921,17z/data=!4m6!3m5!1s0x94c7da5a58a30833:0x1f93843856f80228!8m2!3d-22.4125632!4d-47.5594921!16s%2Fg%2F11kn6x5g20"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        # Title and H1
        title = await page.title()
        h1 = await page.locator("h1").first.inner_text()
        print("Page Title:", title)
        print("H1 Profile:", h1)

        # Aria labels on buttons/links
        aria_labels = await page.locator("[aria-label]").evaluate_all(
            """els => els.map(e => e.getAttribute('aria-label')).filter(Boolean)"""
        )
        # Check phone button
        phone_locator = page.locator("button[data-item-id*='phone'], [data-tooltip*='telefone'], [aria-label*='telefone'], [aria-label*='Telefone']")
        phone_count = await phone_locator.count()
        print("Phone locator count:", phone_count)
        if phone_count > 0:
            for i in range(phone_count):
                el = phone_locator.nth(i)
                txt = await el.inner_text()
                al = await el.get_attribute("aria-label")
                print("Phone element:", repr(txt), "aria-label:", repr(al))
        else:
            # Check all elements with text containing (19) or 98849
            els = await page.locator("*:has-text('98849')").all_inner_texts()
            print("Elements with 98849:", els)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
