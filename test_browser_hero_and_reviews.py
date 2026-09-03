import asyncio
import pathlib
from playwright.async_api import async_playwright

HTML_PATH = pathlib.Path("e:/Antigravity/prospector-sites/clientes/iost-ortodontia-aline-iost-rio-claro/index.html").resolve()
FILE_URL = HTML_PATH.as_uri()

VIEWPORTS = [
    ("Desktop_1280x800", 1280, 800),
    ("Desktop_1440x900", 1440, 900),
    ("Desktop_1920x1080", 1920, 1080),
    ("Desktop_2560x1440", 2560, 1440),
    ("Tablet_800x1024", 800, 1024),
    ("Mobile_390x844", 390, 844),
]

async def run_browser_suite():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        results = []
        
        for name, w, h in VIEWPORTS:
            page = await browser.new_page(viewport={"width": w, "height": h})
            await page.goto(FILE_URL, wait_until="networkidle")
            
            # 1. Hero Checks
            hero_box = await page.locator("section[data-role='hero']").bounding_box()
            img_el = page.locator("img[data-role='hero-image']")
            img_box = await img_el.bounding_box()
            
            # Geometry & CSS
            img_eval = await img_el.evaluate("""img => ({
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                renderedWidth: img.clientWidth,
                renderedHeight: img.clientHeight,
                objectFit: window.getComputedStyle(img).objectFit,
                currentSrc: img.currentSrc
            })""")
            
            natural_ratio = img_eval["naturalWidth"] / img_eval["naturalHeight"]
            rendered_ratio = img_eval["renderedWidth"] / img_eval["renderedHeight"]
            ratio_diff = abs(rendered_ratio - natural_ratio) / natural_ratio
            
            assert img_eval["objectFit"] != "cover", f"[{name}] object-fit cannot be cover, got {img_eval['objectFit']}"
            assert ratio_diff <= 0.02, f"[{name}] Aspect ratio mismatch: natural={natural_ratio:.4f}, rendered={rendered_ratio:.4f}, diff={ratio_diff:.4f}"
            
            # 2. Reviews Checks
            reviews_sec = page.locator("section[data-role='reviews']")
            await reviews_sec.scroll_into_view_if_needed()
            await page.wait_for_timeout(200)
            
            sec_box = await reviews_sec.bounding_box()
            summary_el = reviews_sec.locator("[data-role='reviews-summary']")
            summary_box = await summary_el.bounding_box()
            
            mode = await reviews_sec.get_attribute("data-review-mode")
            presentation = await reviews_sec.get_attribute("data-review-presentation")
            assert mode == "verified-text", f"[{name}] Expected verified-text reviews, got {mode}"
            assert presentation is None, f"[{name}] Verified-text reviews must not use aggregate-only presentation, got {presentation}"
            
            # Desktop summary remains compact; verified text carousel may occupy more vertical space.
            if w >= 1024:
                assert summary_box["height"] <= 180, f"[{name}] reviews-summary height ({summary_box['height']}px) exceeds 180px ceiling"
            assert sec_box["height"] > 0, f"[{name}] reviews section must be visible"
            
            # Check old card not present
            old_card_count = await page.locator(".reviews-aggregate-card").count()
            assert old_card_count == 0, f"[{name}] Old .reviews-aggregate-card must be removed"

            carousel_count = await reviews_sec.locator("[data-role='review-carousel-item']").count()
            assert carousel_count >= 3, f"[{name}] Expected at least 3 evidence-bound review items, found {carousel_count}"
            
            # Verify score and count
            score_text = await summary_el.locator(".reviews-score-num").inner_text()
            count_text = await summary_el.locator(".reviews-count-text").inner_text()
            assert score_text == "5,0"
            assert "12 avaliações" in count_text
            
            screenshot_path = f"e:/Antigravity/prospector/qa_{name}.png"
            await page.screenshot(path=screenshot_path)
            
            results.append({
                "viewport": name,
                "dims": f"{w}x{h}",
                "hero": f"{hero_box['width']:.0f}x{hero_box['height']:.0f}",
                "img": f"{img_box['width']:.0f}x{img_box['height']:.0f}",
                "objectFit": img_eval["objectFit"],
                "ratioDiff": f"{ratio_diff*100:.2f}%",
                "summaryHeight": f"{summary_box['height']:.0f}px",
                "sectionHeight": f"{sec_box['height']:.0f}px",
                "screenshot": screenshot_path
            })
            
            await page.close()
            
        await browser.close()
        
        print("\n=== BROWSER QA RESULTS ===")
        for r in results:
            print(f"[{r['viewport']}] Hero: {r['hero']} | Img: {r['img']} (fit={r['objectFit']}, diff={r['ratioDiff']}) | ReviewsSummary: {r['summaryHeight']} | ReviewsSec: {r['sectionHeight']}")
        print("\nALL BROWSER QA CHECKS PASSED!")

if __name__ == "__main__":
    asyncio.run(run_browser_suite())
