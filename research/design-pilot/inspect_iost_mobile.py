import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    site_dir = Path("sites/iost-ortodontia-aline-iost-rio-claro").resolve()
    html_file = site_dir / "index.html"
    url = html_file.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)

        # Take before screenshot
        screenshot_path = site_dir / "mobile_before_390x844.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"Captured BEFORE screenshot to {screenshot_path}")

        # Measure elements
        header = page.locator('header, [data-role="site-header"], .site-header, .header').first
        header_box = await header.bounding_box() if await header.count() > 0 else None
        print("Header bounding box:", header_box)

        hero = page.locator('[data-role="hero"], section#inicio, .hero-section, #hero').first
        hero_box = await hero.bounding_box() if await hero.count() > 0 else None
        print("Hero bounding box:", hero_box)

        if header_box and hero_box:
            gap = hero_box['y'] - (header_box['y'] + header_box['height'])
            print(f"Distance header bottom ({header_box['y'] + header_box['height']}) -> hero top ({hero_box['y']}): {gap}px")

        # Check body/main padding
        body_padding = await page.evaluate("""() => {
            const b = document.body;
            const m = document.querySelector('main') || b;
            const bs = window.getComputedStyle(b);
            const ms = window.getComputedStyle(m);
            return {
                bodyPaddingTop: bs.paddingTop,
                bodyMarginTop: bs.marginTop,
                mainPaddingTop: ms.paddingTop,
                mainMarginTop: ms.marginTop,
            };
        }""")
        print("Body/Main offsets:", body_padding)

        # Inspect header children bounding boxes and computed styles
        header_info = await page.evaluate("""() => {
            const h = document.querySelector('header, [data-role="site-header"], .site-header, .header');
            if (!h) return { error: "no header found" };
            const hs = window.getComputedStyle(h);
            const children = Array.from(h.children).map(c => {
                const cs = window.getComputedStyle(c);
                const rect = c.getBoundingClientRect();
                return {
                    tag: c.tagName,
                    class: c.className,
                    id: c.id,
                    display: cs.display,
                    visibility: cs.visibility,
                    height: rect.height,
                    width: rect.width,
                    y: rect.y
                };
            });
            return {
                tagName: h.tagName,
                className: h.className,
                computedHeight: hs.height,
                minHeight: hs.minHeight,
                padding: hs.padding,
                paddingTop: hs.paddingTop,
                paddingBottom: hs.paddingBottom,
                position: hs.position,
                top: hs.top,
                rect: h.getBoundingClientRect(),
                children: children
            };
        }""")
        print("Header detailed info:", header_info)

        # Check for spacers or siblings between header and hero
        between_info = await page.evaluate("""() => {
            const h = document.querySelector('header, [data-role="site-header"], .site-header, .header');
            const hero = document.querySelector('[data-role="hero"], section#inicio, .hero-section, #hero');
            if (!h || !hero) return { error: "elements not found" };
            const siblings = [];
            let curr = h.nextElementSibling;
            while (curr && curr !== hero) {
                const cs = window.getComputedStyle(curr);
                const rect = curr.getBoundingClientRect();
                siblings.push({
                    tag: curr.tagName,
                    class: curr.className,
                    id: curr.id,
                    height: rect.height,
                    display: cs.display
                });
                curr = curr.nextElementSibling;
            }
            return { siblingsBetween: siblings };
        }""")
        print("Between header and hero:", between_info)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
