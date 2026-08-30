import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        iphone = p.devices['iPhone 14']
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**iphone, locale='pt-BR')
        page = await context.new_page()
        url = 'https://www.google.com/maps/place/Instituto+Ferreira+Odontologia+e+Harmoniza%C3%A7%C3%A3o+Facial+%7C+Dr.+Cassio+Ferreira+%7C+Dentista+em+Rio+Claro/@-22.3906109,-47.5691163,17z/data=!4m8!3m7!1s0x94c7db099ccb002d:0xc7bc67d9b0f9c6b3!8m2!3d-22.3906109!4d-47.5691163!16s%2Fg%2F11c60crpk9'
        print("Navigating with mobile emulation...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path="scratch_mobile_maps.png")
        
        # Scroll down to reviews
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 1000)")
            await page.wait_for_timeout(1000)
            
        text = await page.inner_text('body')
        with open("scratch_mobile_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        print("Mobile text len:", len(text))
        await page.screenshot(path="scratch_mobile_maps_scrolled.png")
        await browser.close()

asyncio.run(main())
