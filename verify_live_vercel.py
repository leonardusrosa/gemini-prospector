import asyncio
import sys
import time
from playwright.async_api import async_playwright

PROD_URL = "https://prospector-sites-beta.vercel.app/clientes/iost-ortodontia-aline-iost-rio-claro/"

async def verify_live():
    print(f"Verifying live Vercel deployment at {PROD_URL} ...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Poll until Vercel updates with patch 3 markers
        for attempt in range(1, 15):
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            try:
                resp = await page.goto(f"{PROD_URL}?_t={int(time.time())}", wait_until="networkidle")
                status = resp.status if resp else 0
                
                hero_frame_policy = await page.locator("section[data-role='hero']").get_attribute("data-hero-frame-policy")
                review_presentation = await page.locator("section[data-role='reviews']").get_attribute("data-review-presentation")
                
                if hero_frame_policy == "preserve-complete-frame" and review_presentation == "compact-summary":
                    print(f"[Attempt {attempt}] Vercel build Patch 3 live and verified!")
                    print(f"HTTP Status: {status}")
                    
                    # 1. Desktop 1440x900 Verification
                    hero_box_1440 = await page.locator("section[data-role='hero']").bounding_box()
                    img_el_1440 = page.locator("img[data-role='hero-image']")
                    img_box_1440 = await img_el_1440.bounding_box()
                    img_eval_1440 = await img_el_1440.evaluate("""img => ({
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                        width: img.clientWidth,
                        height: img.clientHeight,
                        objectFit: window.getComputedStyle(img).objectFit,
                        attrWidth: img.getAttribute('width'),
                        attrHeight: img.getAttribute('height')
                    })""")
                    
                    print(f"Desktop 1440 Hero: {hero_box_1440['width']:.0f}x{hero_box_1440['height']:.0f} | Img: {img_box_1440['width']:.0f}x{img_box_1440['height']:.0f}")
                    print(f"Declared dims: {img_eval_1440['attrWidth']}x{img_eval_1440['attrHeight']} | Natural dims: {img_eval_1440['naturalWidth']}x{img_eval_1440['naturalHeight']}")
                    print(f"object-fit: {img_eval_1440['objectFit']}")
                    
                    assert img_eval_1440["objectFit"] != "cover"
                    assert img_eval_1440["attrWidth"] == "1983"
                    assert img_eval_1440["attrHeight"] == "793"
                    
                    await page.screenshot(path="e:/Antigravity/prospector/prod_1440.png")
                    
                    # 2. Desktop 1920x1080 Verification
                    page_1920 = await browser.new_page(viewport={"width": 1920, "height": 1080})
                    await page_1920.goto(f"{PROD_URL}?_t={int(time.time())}", wait_until="networkidle")
                    hero_box_1920 = await page_1920.locator("section[data-role='hero']").bounding_box()
                    img_box_1920 = await page_1920.locator("img[data-role='hero-image']").bounding_box()
                    print(f"Desktop 1920 Hero: {hero_box_1920['width']:.0f}x{hero_box_1920['height']:.0f} | Img: {img_box_1920['width']:.0f}x{img_box_1920['height']:.0f}")
                    await page_1920.screenshot(path="e:/Antigravity/prospector/prod_1920.png")
                    await page_1920.close()
                    
                    # 3. Reviews Verification
                    rev_sec = page.locator("section[data-role='reviews']")
                    await rev_sec.scroll_into_view_if_needed()
                    await page.wait_for_timeout(200)
                    
                    sec_box = await rev_sec.bounding_box()
                    summary_box = await page.locator("[data-role='reviews-summary']").bounding_box()
                    print(f"Reviews Section Height: {sec_box['height']:.0f}px | Summary Height: {summary_box['height']:.0f}px")
                    
                    assert sec_box["height"] <= 380
                    assert summary_box["height"] <= 180
                    
                    await page.close()
                    await browser.close()
                    print("\n[VERCEL LIVE PRODUCTION 100% VERIFIED]")
                    return
                else:
                    print(f"[Attempt {attempt}] Waiting for new deployment (found hero_policy={hero_frame_policy}, review_pres={review_presentation})...")
            except Exception as e:
                print(f"[Attempt {attempt}] Error: {e}")
            finally:
                await page.close()
            await asyncio.sleep(5)
            
        await browser.close()
        print("Timeout waiting for Vercel deployment.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_live())
