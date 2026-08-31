import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_photos():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        url = "https://www.google.com/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138409,-47.5600884,17z/data=!4m7!3m6!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(4000)

        # Check photos button
        photo_btn = await page.query_selector('button[aria-label*="Fotos"], button[aria-label*="fotos"], button:has-text("Fotos")')
        photos = []
        if photo_btn:
            await photo_btn.click()
            await page.wait_for_timeout(3000)
            img_els = await page.query_selector_all('div[role="main"] img, div[role="region"] img, button img')
            for img in img_els:
                src = await img.get_attribute("src")
                alt = await img.get_attribute("alt")
                if src and "googleusercontent" in src:
                    photos.append({"src": src, "alt": alt})
        
        with open("maps_photos.json", "w", encoding="utf-8") as f:
            json.dump(photos, f, ensure_ascii=False, indent=2)
        print("Found photos count:", len(photos))
        await page.screenshot(path="maps_photos_view.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_photos())
