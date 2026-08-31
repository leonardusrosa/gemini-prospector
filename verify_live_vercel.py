import asyncio
import time
from playwright.async_api import async_playwright

LIVE_URL = "https://prospector-sites-beta.vercel.app/clientes/iost-ortodontia-aline-iost-rio-claro/"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        print("Waiting for Vercel deployment...")
        for attempt in range(12):
            resp = await page.goto(LIVE_URL, wait_until="networkidle")
            hero_layout = await page.locator("section[data-role='hero']").get_attribute("data-hero-layout")
            reviews_mode = await page.locator("section[data-role='reviews']").get_attribute("data-review-mode")
            if hero_layout == "full-bleed-background" and reviews_mode == "aggregate-only":
                print(f"[Attempt {attempt+1}] Vercel build live and verified!")
                break
            print(f"[Attempt {attempt+1}] Waiting for Vercel build to propagate (hero-layout={hero_layout}, reviews-mode={reviews_mode})...")
            await asyncio.sleep(5)
        
        # Verify Desktop 1440x900
        hero_box = await page.locator("section[data-role='hero']").bounding_box()
        img_box = await page.locator("img[data-role='hero-image']").bounding_box()
        reviews_rating = await page.locator("section[data-role='reviews']").get_attribute("data-review-rating")
        reviews_count = await page.locator("section[data-role='reviews']").get_attribute("data-review-count")
        
        print(f"HTTP Status: {resp.status}")
        print(f"Desktop Hero: {hero_box['width']}x{hero_box['height']}, Img: {img_box['width']}x{img_box['height']}")
        print(f"Width coverage: {img_box['width'] / hero_box['width']:.3f}, Height coverage: {img_box['height'] / hero_box['height']:.3f}")
        print(f"Reviews Mode: {reviews_mode}, Rating: {reviews_rating}, Count: {reviews_count}")
        
        assert hero_layout == "full-bleed-background"
        assert reviews_mode == "aggregate-only"
        assert reviews_rating == "5.0"
        assert reviews_count == "1"
        assert img_box["width"] / hero_box["width"] >= 0.97
        assert img_box["height"] / hero_box["height"] >= 0.95
        
        # Verify Mobile 390x844
        page_mobile = await browser.new_page(viewport={"width": 390, "height": 844})
        await page_mobile.goto(LIVE_URL, wait_until="networkidle")
        current_src_mobile = await page_mobile.locator("img[data-role='hero-image']").evaluate("el => el.currentSrc")
        print(f"Mobile currentSrc: {current_src_mobile}")
        assert "mobile" in current_src_mobile.lower()
        
        await browser.close()
        print("\n[VERCEL LIVE DEPLOYMENT 100% VERIFIED]")

if __name__ == "__main__":
    asyncio.run(main())
