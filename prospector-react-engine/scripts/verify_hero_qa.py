import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACTS_DIR = r"C:\Users\leo_b\.gemini\antigravity-ide\brain\e9e77699-be15-4e73-a267-218d256e1de1"

async def run_hero_qa():
    print("=== Starting Hero Browser QA ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        viewports = [
            ("desktop_1440", 1440, 900),
            ("tablet_768", 768, 1024),
            ("mobile_390", 390, 844),
        ]

        for name, w, h in viewports:
            print(f"\n--- Testing Viewport {name} ({w}x{h}) ---")
            is_mobile = (w <= 600)
            context = await browser.new_context(
                viewport={"width": w, "height": h},
                has_touch=is_mobile,
                is_mobile=is_mobile,
            )
            page = await context.new_page()
            await page.goto("http://localhost:4040/", wait_until="networkidle")

            hero_el = page.locator("[data-role='hero']")
            await hero_el.scroll_into_view_if_needed()
            await page.wait_for_timeout(400)

            # 1. Verify eyebrow
            eyebrow = await page.locator("[data-role='hero-eyebrow']").inner_text()
            print(f"Eyebrow: {repr(eyebrow)}")

            # 2. Verify headline
            headline = await page.locator("[data-role='hero'] h1").inner_text()
            print(f"Headline: {repr(headline)}")

            # 3. Verify supporting copy
            support = await page.locator("[data-role='hero-desc']").inner_text()
            print(f"Support: {repr(support)}")

            # 4. Verify CTA
            cta_count = await page.locator("[data-role='hero'] [data-role='hero-cta']").count()
            cta_text = await page.locator("[data-role='hero'] [data-role='hero-cta']").inner_text()
            print(f"CTA count: {cta_count}, CTA text: {repr(cta_text)}")
            assert cta_count == 1, f"Expected exactly 1 CTA, found {cta_count}"

            # 5. Verify trust line
            trust_count = await page.locator("[data-role='hero'] [data-role='hero-trust']").count()
            trust_text = await page.locator("[data-role='hero'] [data-role='hero-trust']").inner_text()
            print(f"Trust line count: {trust_count}, Trust text: {repr(trust_text)}")
            assert trust_count == 1, f"Expected exactly 1 trust line, found {trust_count}"

            # 6. Verify no cards/pills in hero
            has_cards = await page.locator("[data-role='hero'] .card, [data-role='hero'] .badge-item, [data-role='hero'] .pill").count()
            print(f"Card / pill count in hero: {has_cards}")
            assert has_cards == 0, f"Expected 0 cards/pills in hero, found {has_cards}"

            # 7. Check horizontal overflow
            overflow = await page.evaluate("document.body.scrollWidth > window.innerWidth + 1")
            print(f"Horizontal overflow: {overflow}")
            assert overflow is False, "Horizontal overflow detected!"

            # 8. Screenshot hero
            shot_path = os.path.join(ARTIFACTS_DIR, f"hero_{name}.png")
            await hero_el.screenshot(path=shot_path)
            print(f"Saved screenshot to {shot_path}")

            await context.close()

        await browser.close()

    print("\n=== Hero Browser QA Complete ===")

if __name__ == "__main__":
    asyncio.run(run_hero_qa())
