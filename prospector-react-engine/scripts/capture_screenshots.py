import asyncio
from playwright.async_api import async_playwright

async def capture_views():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Desktop View (1440x900)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        await page.goto("http://localhost:4040/", wait_until="networkidle")
        await page.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/b3_3_desktop_full.png", full_page=True)
        print("Desktop screenshot captured")
        await context.close()

        # 2. Mobile View (390x844)
        context_mobile = await browser.new_context(viewport={"width": 390, "height": 844})
        page_mobile = await context_mobile.new_page()
        await page_mobile.goto("http://localhost:4040/", wait_until="networkidle")
        await page_mobile.screenshot(path="e:/Antigravity/prospector/prospector-react-engine/b3_3_mobile_full.png", full_page=True)
        print("Mobile screenshot captured")
        await context_mobile.close()

        await browser.close()

asyncio.run(capture_views())
