import asyncio
import pathlib
from playwright.async_api import async_playwright

HTML_PATH = pathlib.Path("e:/Antigravity/prospector-sites/clientes/iost-ortodontia-aline-iost-rio-claro/index.html").resolve()
FILE_URL = HTML_PATH.as_uri()

async def test_all_zooms():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        viewports = [
            ("Desktop_100pct_1440x900", 1440, 900),
            ("Desktop_125pct_1152x720", 1152, 720),
            ("Desktop_150pct_960x600", 960, 600),
            ("Desktop_175pct_820x600", 820, 600),
            ("Tablet_800x1024", 800, 1024),
            ("Mobile_390x844", 390, 844)
        ]
        
        for name, w, h in viewports:
            page = await browser.new_page(viewport={"width": w, "height": h})
            await page.goto(FILE_URL, wait_until="networkidle")
            
            # Check hero bounds
            hero = await page.locator("section[data-role='hero']").bounding_box()
            img = await page.locator("img[data-role='hero-image']").bounding_box()
            h1 = await page.locator("h1.hero-title").bounding_box()
            
            print(f"[{name}] Viewport: {w}x{h} | Hero: {hero['width']:.0f}x{hero['height']:.0f} | Img: {img['width']:.0f}x{img['height']:.0f} | H1: {h1['width']:.0f}x{h1['height']:.0f}")
            
            # Check reviews section
            reviews = page.locator("section[data-role='reviews']")
            await reviews.scroll_into_view_if_needed()
            await page.wait_for_timeout(300)
            
            title = await reviews.locator(".section-title").inner_text()
            rating = await reviews.get_attribute("data-review-rating")
            count = await reviews.get_attribute("data-review-count")
            mode = await reviews.get_attribute("data-review-mode")
            
            assert "Avaliações de pacientes" in title
            assert rating == "5.0"
            assert count == "1"
            assert mode == "aggregate-only"
            
            await page.screenshot(path=f"e:/Antigravity/prospector/qa_zoom_{name}.png")
            print(f"[{name}] Screenshot saved -> qa_zoom_{name}.png")
            await page.close()
            
        await browser.close()
        print("\n[ALL ZOOM & VIEWPORT RESILIENCE TESTS PASSED]")

if __name__ == "__main__":
    asyncio.run(test_all_zooms())
