import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

HTML_PATH = Path("e:/Antigravity/prospector-sites/clientes/iost-ortodontia-aline-iost-rio-claro/index.html").resolve()
FILE_URL = f"file:///{str(HTML_PATH).replace('\\', '/')}"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Desktop 1440x900
        page_desktop = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page_desktop.goto(FILE_URL)
        await page_desktop.wait_for_load_state("networkidle")
        
        # Check hero full-bleed dimensions
        hero_box = await page_desktop.locator("section[data-role='hero']").bounding_box()
        img_box = await page_desktop.locator("img[data-role='hero-image']").bounding_box()
        
        assert hero_box is not None, "Hero section not found"
        assert img_box is not None, "Hero image not found"
        
        width_ratio = img_box["width"] / hero_box["width"]
        height_ratio = img_box["height"] / hero_box["height"]
        
        print(f"[Desktop 1440x900] Hero Box: {hero_box['width']}x{hero_box['height']}, Img Box: {img_box['width']}x{img_box['height']}")
        print(f"[Desktop 1440x900] Width ratio: {width_ratio:.3f} (>=0.97 required), Height ratio: {height_ratio:.3f} (>=0.95 required)")
        
        assert width_ratio >= 0.97, f"Hero image width ratio {width_ratio:.3f} < 0.97"
        assert height_ratio >= 0.95, f"Hero image height ratio {height_ratio:.3f} < 0.95"
        
        # Check currentSrc on desktop
        current_src_desktop = await page_desktop.locator("img[data-role='hero-image']").evaluate("el => el.currentSrc")
        print(f"[Desktop 1440x900] currentSrc: {current_src_desktop}")
        assert "desktop" in current_src_desktop.lower() or "hero-expert-placeholder-desktop" in current_src_desktop.lower(), "Desktop asset not selected on 1440px"
        
        # Check H1 typography and legibility
        h1_text = await page_desktop.locator("h1.hero-title").inner_text()
        print(f"[Desktop 1440x900] H1 Text: {h1_text}")
        assert "Ortodontia e atendimento odontológico em Rio Claro" in h1_text
        
        # Check Reviews section
        reviews_rating = await page_desktop.locator("section[data-role='reviews']").get_attribute("data-review-rating")
        reviews_count = await page_desktop.locator("section[data-role='reviews']").get_attribute("data-review-count")
        reviews_mode = await page_desktop.locator("section[data-role='reviews']").get_attribute("data-review-mode")
        
        print(f"[Desktop 1440x900] Reviews mode={reviews_mode}, rating={reviews_rating}, count={reviews_count}")
        assert reviews_mode == "verified-text"
        assert reviews_rating == "5.0"
        assert reviews_count == "12"
        
        # Verified text reviews must be evidence-bound carousel items.
        carousel_items = await page_desktop.locator("section[data-role='reviews'] [data-role='review-carousel-item']").count()
        assert carousel_items >= 3, f"Expected at least 3 verified review items, found {carousel_items}"
        
        # The public subtitle must stay source-neutral; quoted source text may contain native wording.
        reviews_subtitle = await page_desktop.locator("section[data-role='reviews'] .reviews-subtitle").inner_text()
        assert reviews_subtitle == "Avaliações públicas sobre o atendimento."
        
        await page_desktop.screenshot(path="e:/Antigravity/prospector/desktop_hero_qa.png")
        print("[Desktop 1440x900] Screenshot saved: desktop_hero_qa.png")
        
        # 2. Mobile 390x844
        page_mobile = await browser.new_page(viewport={"width": 390, "height": 844})
        await page_mobile.goto(FILE_URL)
        await page_mobile.wait_for_load_state("networkidle")
        
        current_src_mobile = await page_mobile.locator("img[data-role='hero-image']").evaluate("el => el.currentSrc")
        print(f"[Mobile 390x844] currentSrc: {current_src_mobile}")
        assert "mobile" in current_src_mobile.lower(), f"Mobile asset not selected on 390px viewport; got {current_src_mobile}"
        
        # Check floating WhatsApp and Assistant geometry
        wa_floating_locator = page_mobile.locator("[data-role='floating-whatsapp']")
        wa_floating = await wa_floating_locator.bounding_box() if await wa_floating_locator.count() else None
        assistant = await page_mobile.locator("button[data-role='assistant-launcher'], #btn-launcher").bounding_box()
        
        print(f"[Mobile 390x844] Floating WA Box: {wa_floating}, Assistant Box: {assistant}")
        assert wa_floating is None, "Assistant-present site must not expose a floating WhatsApp launcher"
        assert assistant is not None, "Assistant-present site must expose the fixed assistant launcher"
        
        await page_mobile.screenshot(path="e:/Antigravity/prospector/mobile_hero_qa.png")
        print("[Mobile 390x844] Screenshot saved: mobile_hero_qa.png")
        
        await browser.close()
        print("\n[ALL VISUAL & DOM QA CHECKS PASSED]")

if __name__ == "__main__":
    asyncio.run(main())
