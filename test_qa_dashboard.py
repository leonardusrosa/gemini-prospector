import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).parent

async def test_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        dash_url = f"file:///{ (ROOT / 'dashboard.html').as_posix() }"
        await page.goto(dash_url, wait_until="load")
        await page.wait_for_timeout(1500)
        
        # Lead cards are rendered in the Clientes view; overview intentionally shows metrics.
        await page.locator("#nav button").filter(has_text="Clientes").click()
        await page.wait_for_timeout(100)
        iost_card = await page.get_by_text("IOST Ortodontia", exact=False).count()
        print("IOST card present on dashboard:", "PASS" if iost_card else "FAIL")

        await page.screenshot(path="qa_dashboard_iost_updated.png", full_page=True)
        print("Captured qa_dashboard_iost_updated.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_dashboard())
