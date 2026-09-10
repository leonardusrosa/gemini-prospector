import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

ARTIFACTS_DIR = r"C:\Users\leo_b\.gemini\antigravity-ide\brain\e9e77699-be15-4e73-a267-218d256e1de1"

async def run_qa():
    print("=== Starting Gallery Automated Playwright QA ===")
    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # ---------------------------------------------------------
        # TEST 1: Viewport 1440x900 (Desktop)
        # ---------------------------------------------------------
        print("\n--- Testing Desktop (1440x900) ---")
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # CLS observer setup
        await page.add_init_script("""
            window.__cls_entries = [];
            new PerformanceObserver((entryList) => {
                for (const entry of entryList.getEntries()) {
                    if (!entry.hadRecentInput) {
                        window.__cls_entries.push(entry.value);
                    }
                }
            }).observe({type: 'layout-shift', buffered: true});
        """)

        await page.goto("http://localhost:4040/", wait_until="networkidle")
        gallery_el = page.locator("#gallery")
        await gallery_el.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)

        # Verify element exists
        is_visible = await gallery_el.is_visible()
        print(f"Gallery visible on desktop: {is_visible}")

        # Check counter initial
        counter_text = await page.locator("#gallery .font-mono.text-xs").first.inner_text()
        print(f"Initial counter text: {repr(counter_text)}")

        # Check images count & lazy loading
        images = await page.locator("#gallery img").all()
        print(f"Total images rendered: {len(images)}")
        img_loadings = [await img.get_attribute("loading") for img in images]
        print(f"Image loading attributes: {img_loadings}")

        # Check horizontal overflow
        overflow = await page.evaluate("document.body.scrollWidth > window.innerWidth")
        print(f"Horizontal overflow desktop: {overflow}")

        # Click next button
        next_btn = page.locator("#gallery button[aria-label='Next photograph']")
        await next_btn.click()
        await page.wait_for_timeout(300)
        counter_after_click = await page.locator("#gallery .font-mono.text-xs").first.inner_text()
        print(f"Counter after next click: {repr(counter_after_click)}")

        # Keyboard navigation (ArrowRight)
        rail = page.locator("#gallery [tabindex='0']")
        await rail.focus()
        await page.keyboard.press("ArrowRight")
        await page.wait_for_timeout(300)
        counter_after_key = await page.locator("#gallery .font-mono.text-xs").first.inner_text()
        print(f"Counter after ArrowRight key: {repr(counter_after_key)}")

        # Drag interaction
        box = await rail.bounding_box()
        if box:
            start_x = box["x"] + box["width"] * 0.7
            start_y = box["y"] + box["height"] * 0.5
            end_x = start_x - 150
            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            await page.mouse.move(end_x, start_y, steps=10)
            await page.mouse.up()
            await page.wait_for_timeout(400)
            counter_after_drag = await page.locator("#gallery .font-mono.text-xs").first.inner_text()
            print(f"Counter after drag left: {repr(counter_after_drag)}")

        # Measure CLS
        cls_scores = await page.evaluate("window.__cls_entries")
        total_cls = sum(cls_scores) if cls_scores else 0.0
        print(f"Gallery Desktop CLS: {total_cls:.4f}")

        # Capture Desktop screenshot
        desktop_shot_path = os.path.join(ARTIFACTS_DIR, "gallery_desktop_1440.png")
        await gallery_el.screenshot(path=desktop_shot_path)
        print(f"Saved desktop screenshot to {desktop_shot_path}")
        await context.close()

        # ---------------------------------------------------------
        # TEST 2: Viewport 768x1024 (Tablet)
        # ---------------------------------------------------------
        print("\n--- Testing Tablet (768x1024) ---")
        context_tab = await browser.new_context(viewport={"width": 768, "height": 1024})
        page_tab = await context_tab.new_page()
        await page_tab.goto("http://localhost:4040/", wait_until="networkidle")
        gallery_tab = page_tab.locator("#gallery")
        await gallery_tab.scroll_into_view_if_needed()
        await page_tab.wait_for_timeout(500)

        overflow_tab = await page_tab.evaluate("document.body.scrollWidth > window.innerWidth")
        print(f"Horizontal overflow tablet: {overflow_tab}")

        tablet_shot_path = os.path.join(ARTIFACTS_DIR, "gallery_tablet_768.png")
        await gallery_tab.screenshot(path=tablet_shot_path)
        print(f"Saved tablet screenshot to {tablet_shot_path}")
        await context_tab.close()

        # ---------------------------------------------------------
        # TEST 3: Viewport 390x844 (Mobile)
        # ---------------------------------------------------------
        print("\n--- Testing Mobile (390x844) ---")
        context_mob = await browser.new_context(
            viewport={"width": 390, "height": 844},
            has_touch=True,
            is_mobile=True,
        )
        page_mob = await context_mob.new_page()
        await page_mob.goto("http://localhost:4040/", wait_until="networkidle")
        gallery_mob = page_mob.locator("#gallery")
        await gallery_mob.scroll_into_view_if_needed()
        await page_mob.wait_for_timeout(500)

        overflow_mob = await page_mob.evaluate("document.body.scrollWidth > window.innerWidth + 1")
        print(f"Horizontal overflow mobile: {overflow_mob}")

        # Touch swipe emulation
        rail_mob = page_mob.locator("#gallery [tabindex='0']")
        box_mob = await rail_mob.bounding_box()
        if box_mob:
            sx = box_mob["x"] + box_mob["width"] * 0.8
            sy = box_mob["y"] + box_mob["height"] * 0.5
            ex = sx - 160
            # Dispatch touch events
            await page_mob.touchscreen.tap(sx, sy)
            # Mouse drag emulation for touch drag
            await page_mob.mouse.move(sx, sy)
            await page_mob.mouse.down()
            await page_mob.mouse.move(ex, sy, steps=10)
            await page_mob.mouse.up()
            await page_mob.wait_for_timeout(400)
            counter_mob_after_swipe = await page_mob.locator("#gallery .font-mono.text-xs").first.inner_text()
            print(f"Counter mobile after swipe: {repr(counter_mob_after_swipe)}")

        mobile_shot_path = os.path.join(ARTIFACTS_DIR, "gallery_mobile_390.png")
        await gallery_mob.screenshot(path=mobile_shot_path)
        print(f"Saved mobile screenshot to {mobile_shot_path}")
        await context_mob.close()

        # ---------------------------------------------------------
        # TEST 4: Prefers-Reduced-Motion
        # ---------------------------------------------------------
        print("\n--- Testing Reduced Motion ---")
        context_rm = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce",
        )
        page_rm = await context_rm.new_page()
        await page_rm.goto("http://localhost:4040/", wait_until="networkidle")
        gallery_rm = page_rm.locator("#gallery")
        await gallery_rm.scroll_into_view_if_needed()
        c_init = await page_rm.locator("#gallery .font-mono.text-xs").first.inner_text()
        print(f"Reduced motion initial counter: {repr(c_init)}")
        # Wait 7.5 seconds (longer than autoplay interval 6.5s) to verify autoplay does NOT advance
        print("Waiting 7.5s to verify autoplay is disabled under reduced motion...")
        await page_rm.wait_for_timeout(7500)
        c_after = await page_rm.locator("#gallery .font-mono.text-xs").first.inner_text()
        print(f"Reduced motion counter after 7.5s: {repr(c_after)}")
        rm_halted = (c_init == c_after)
        print(f"Autoplay disabled under reduced motion: {rm_halted}")
        await context_rm.close()

        await browser.close()

    print("\n=== Playwright Gallery QA Complete ===")

if __name__ == "__main__":
    asyncio.run(run_qa())
