import asyncio
from playwright.async_api import async_playwright
import shutil
import re

async def main():
    print("=== STARTING HARD RULE REVIEW CAROUSEL QA ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Desktop Test (1440x900)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        await page.goto("http://localhost:4040/", wait_until="networkidle")
        await page.evaluate('window.scrollTo(0, document.getElementById("reviews").offsetTop - 40)')
        await page.wait_for_timeout(1000)

        # Check visible reviews at once
        quotes = await page.locator('#reviews blockquote').all()
        visible_quotes = [q for q in quotes if await q.is_visible()]
        visible_count = len(visible_quotes)
        print(f"VISIBLE_REVIEWS_AT_ONCE: {visible_count}")
        assert visible_count == 1, f"Expected 1 visible review at once, found {visible_count}"

        # Check for selector boxes / cards
        selector_buttons = await page.locator('#reviews button[aria-label^="View review"]').all()
        print(f"REVIEW_SELECTOR_CARD_COUNT: {len(selector_buttons)}")
        assert len(selector_buttons) == 0, f"Found {len(selector_buttons)} selector cards"

        # Check for text PREV / NEXT
        reviews_html = await page.locator('#reviews').inner_html()
        has_prev_text = bool(re.search(r'\b(PREV|PREVIOUS)\b', reviews_html, re.IGNORECASE))
        has_next_text = bool(re.search(r'\b(NEXT)\b', reviews_html, re.IGNORECASE))
        # Wait: make sure aria-labels are fine, but visible text is 0
        visible_text = await page.locator('#reviews').inner_text()
        has_visible_prev = bool(re.search(r'\b(PREV|PREVIOUS)\b', visible_text, re.IGNORECASE))
        has_visible_next = bool(re.search(r'\b(NEXT)\b', visible_text, re.IGNORECASE))
        print(f"TEXT_PREV_NEXT_COUNT: {1 if (has_visible_prev or has_visible_next) else 0}")
        assert not has_visible_prev and not has_visible_next, "Found visible PREV or NEXT text!"

        # Check Icon buttons
        btn_prev = page.locator('#reviews button[aria-label="Previous review"]')
        btn_next = page.locator('#reviews button[aria-label="Next review"]')
        assert await btn_prev.is_visible(), "Previous review button not visible"
        assert await btn_next.is_visible(), "Next review button not visible"
        assert await btn_prev.locator('svg').count() == 1, "Previous button missing svg icon"
        assert await btn_next.locator('svg').count() == 1, "Next button missing svg icon"
        print("ICON_PREVIOUS: PASS")
        print("ICON_NEXT: PASS")

        # Initial review position indicator
        pos_text = await page.locator('#reviews').inner_text()
        assert re.search(r'01\s*/\s*12', pos_text), f"Expected 01 / 12 indicator, got: {pos_text}"
        print("POSITION_INDICATOR_INITIAL: 01 / 12")

        # Screenshot Desktop initial
        await page.locator('#reviews').screenshot(path="e:/Antigravity/prospector/prospector-react-engine/carousel_desktop_initial.png")

        # 2. Test Manual Click Navigation (Next)
        await btn_next.click()
        await page.wait_for_timeout(700)
        pos_text_2 = await page.locator('#reviews').inner_text()
        assert re.search(r'02\s*/\s*12', pos_text_2), f"Expected 02 / 12 after click next, got: {pos_text_2}"
        print("MANUAL_NEXT_CLICK: PASS (advanced to 02 / 12)")

        # 3. Test Manual Click Navigation (Prev from 02 -> 01 -> 12)
        await btn_prev.click()
        await page.wait_for_timeout(700)
        pos_text_1 = await page.locator('#reviews').inner_text()
        assert re.search(r'01\s*/\s*12', pos_text_1), f"Expected 01 / 12 after click prev, got: {pos_text_1}"
        await btn_prev.click()
        await page.wait_for_timeout(700)
        pos_text_12 = await page.locator('#reviews').inner_text()
        assert re.search(r'12\s*/\s*12', pos_text_12), f"Expected 12 / 12 after wrapping prev, got: {pos_text_12}"
        print("MANUAL_PREV_CLICK & WRAP: PASS (wrapped to 12 / 12)")

        # 4. Test Keyboard Navigation
        # Focus the carousel region
        carousel_region = page.locator('#reviews div[role="region"]')
        await carousel_region.focus()
        await page.keyboard.press("ArrowRight")
        await page.wait_for_timeout(700)
        pos_text_kb = await page.locator('#reviews').inner_text()
        assert re.search(r'01\s*/\s*12', pos_text_kb), f"Expected 01 / 12 after keyboard ArrowRight, got: {pos_text_kb}"
        print("KEYBOARD_NAV: PASS (ArrowRight wrapped from 12 back to 01)")

        # Screenshot Desktop after interaction
        await page.locator('#reviews').screenshot(path="e:/Antigravity/prospector/prospector-react-engine/carousel_desktop_interacted.png")
        await context.close()

        # 5. Test Auto-Advance on fresh context (wait 8.5s without touching)
        print("Testing Auto-Carousel Advance (interval 7.5s)...")
        context_auto = await browser.new_context(viewport={"width": 1440, "height": 900})
        page_auto = await context_auto.new_page()
        await page_auto.goto("http://localhost:4040/", wait_until="networkidle")
        await page_auto.evaluate('window.scrollTo(0, document.getElementById("reviews").offsetTop - 40)')
        pos_auto_0 = await page_auto.locator('#reviews').inner_text()
        assert re.search(r'01\s*/\s*12', pos_auto_0)
        
        # Wait 8.2 seconds for auto advance
        await page_auto.wait_for_timeout(8200)
        pos_auto_1 = await page_auto.locator('#reviews').inner_text()
        assert re.search(r'02\s*/\s*12', pos_auto_1), f"Expected auto-advance to 02 / 12, got: {pos_auto_1}"
        print("AUTO_CAROUSEL: PASS (successfully auto-advanced from 01 to 02)")
        await context_auto.close()

        # 6. Test prefers-reduced-motion
        print("Testing prefers-reduced-motion...")
        context_rm = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce"
        )
        page_rm = await context_rm.new_page()
        await page_rm.goto("http://localhost:4040/", wait_until="networkidle")
        await page_rm.evaluate('window.scrollTo(0, document.getElementById("reviews").offsetTop - 40)')
        await page_rm.wait_for_timeout(500)
        pos_rm_0 = await page_rm.locator('#reviews').inner_text()
        assert re.search(r'01\s*/\s*12', pos_rm_0)
        
        # Wait 8.5 seconds - with reduced motion, it should NOT auto-advance
        await page_rm.wait_for_timeout(8500)
        pos_rm_1 = await page_rm.locator('#reviews').inner_text()
        assert re.search(r'01\s*/\s*12', pos_rm_1), f"Expected auto-advance to be disabled under reduced-motion, but got {pos_rm_1}"
        print("REDUCED_MOTION_AUTOPLAY_DISABLED: PASS (remained 01 / 12)")
        await context_rm.close()

        # 7. Mobile View (390x844)
        print("Testing Mobile View (390x844)...")
        context_m = await browser.new_context(viewport={"width": 390, "height": 844})
        page_m = await context_m.new_page()
        await page_m.goto("http://localhost:4040/", wait_until="networkidle")
        await page_m.evaluate('window.scrollTo(0, document.getElementById("reviews").offsetTop - 40)')
        await page_m.wait_for_timeout(1000)

        # Check overflow
        overflow = await page_m.evaluate('document.body.scrollWidth > window.innerWidth')
        assert not overflow, "Mobile has horizontal overflow!"

        quotes_m = await page_m.locator('#reviews blockquote').all()
        visible_quotes_m = [q for q in quotes_m if await q.is_visible()]
        assert len(visible_quotes_m) == 1, "Mobile must show exactly 1 review"

        btn_prev_m = page_m.locator('#reviews button[aria-label="Previous review"]')
        btn_next_m = page_m.locator('#reviews button[aria-label="Next review"]')
        assert await btn_prev_m.is_visible()
        assert await btn_next_m.is_visible()

        await page_m.locator('#reviews').screenshot(path="e:/Antigravity/prospector/prospector-react-engine/carousel_mobile.png")
        print("MOBILE: PASS")
        await context_m.close()

        await browser.close()

    # Copy screenshots to brain artifacts directory
    artifact_dir = "C:/Users/leo_b/.gemini/antigravity-ide/brain/e9e77699-be15-4e73-a267-218d256e1de1"
    shutil.copyfile("e:/Antigravity/prospector/prospector-react-engine/carousel_desktop_initial.png", f"{artifact_dir}/carousel_desktop_initial.png")
    shutil.copyfile("e:/Antigravity/prospector/prospector-react-engine/carousel_desktop_interacted.png", f"{artifact_dir}/carousel_desktop_interacted.png")
    shutil.copyfile("e:/Antigravity/prospector/prospector-react-engine/carousel_mobile.png", f"{artifact_dir}/carousel_mobile.png")
    print("All screenshots copied to artifacts directory successfully!")

asyncio.run(main())
