import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont

async def test_and_capture():
    site_dir = Path("sites/iost-ortodontia-aline-iost-rio-claro").resolve()
    html_url = (site_dir / "index.html").as_uri()

    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # 1. Viewport 390x844 (Mobile)
        context_390 = await browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
        page_390 = await context_390.new_page()
        await page_390.goto(html_url, wait_until="networkidle")
        await page_390.wait_for_timeout(800)

        metrics_390 = await page_390.evaluate("""() => {
            const h = document.querySelector('header');
            const hero = document.querySelector('[data-role="hero"]');
            const drawer = document.getElementById('mobile-drawer');
            const assistant = document.getElementById('iost-assistant-root');
            const body = document.body;
            const main = document.querySelector('main') || body;

            const hr = h ? h.getBoundingClientRect() : null;
            const heror = hero ? hero.getBoundingClientRect() : null;
            const ds = drawer ? window.getComputedStyle(drawer) : null;
            const bs = window.getComputedStyle(body);
            const ms = window.getComputedStyle(main);

            const scrollW = document.documentElement.scrollWidth;
            const clientW = document.documentElement.clientWidth;

            // Hero image bounding
            const heroImg = document.querySelector('img[data-role="hero-image"]');
            const imgr = heroImg ? heroImg.getBoundingClientRect() : null;
            const heroTitle = document.querySelector('.hero-title');
            const titler = heroTitle ? heroTitle.getBoundingClientRect() : null;

            // Check face area collision (upper 35% of mobile image)
            let faceObstruction = false;
            if (imgr && titler) {
                const faceBottom = imgr.y + (imgr.height * 0.40);
                if (titler.y < faceBottom) {
                    faceObstruction = true;
                }
            }

            return {
                headerHeight: hr ? hr.height : 0,
                headerY: hr ? hr.y : 0,
                heroY: heror ? heror.y : 0,
                gap: (heror && hr) ? (heror.y - (hr.y + hr.height)) : 0,
                bodyPaddingTop: bs.paddingTop,
                mainPaddingTop: ms.paddingTop,
                drawerDisplay: ds ? ds.display : null,
                drawerHeight: drawer ? drawer.offsetHeight : 0,
                scrollWidth: scrollW,
                clientWidth: clientW,
                horizontalOverflow: scrollW > clientW,
                assistantPresent: !!assistant,
                faceObstruction: faceObstruction,
                heroImgWidth: imgr ? imgr.width : 0
            };
        }""")
        results["390x844"] = metrics_390
        path_390 = site_dir / "mobile_390x844.png"
        await page_390.screenshot(path=str(path_390))
        print(f"Captured 390x844 to {path_390}: {metrics_390}")
        await context_390.close()

        # 2. Viewport 430x932 (Large Mobile)
        context_430 = await browser.new_context(viewport={"width": 430, "height": 932}, is_mobile=True)
        page_430 = await context_430.new_page()
        await page_430.goto(html_url, wait_until="networkidle")
        await page_430.wait_for_timeout(800)

        metrics_430 = await page_430.evaluate("""() => {
            const h = document.querySelector('header');
            const hero = document.querySelector('[data-role="hero"]');
            const hr = h ? h.getBoundingClientRect() : null;
            const heror = hero ? hero.getBoundingClientRect() : null;
            const scrollW = document.documentElement.scrollWidth;
            const clientW = document.documentElement.clientWidth;
            return {
                headerHeight: hr ? hr.height : 0,
                gap: (heror && hr) ? (heror.y - (hr.y + hr.height)) : 0,
                scrollWidth: scrollW,
                clientWidth: clientW,
                horizontalOverflow: scrollW > clientW
            };
        }""")
        results["430x932"] = metrics_430
        path_430 = site_dir / "mobile_430x932.png"
        await page_430.screenshot(path=str(path_430))
        print(f"Captured 430x932 to {path_430}: {metrics_430}")
        await context_430.close()

        # 3. Viewport 800x1024 (Tablet)
        context_800 = await browser.new_context(viewport={"width": 800, "height": 1024})
        page_800 = await context_800.new_page()
        await page_800.goto(html_url, wait_until="networkidle")
        await page_800.wait_for_timeout(800)

        metrics_800 = await page_800.evaluate("""() => {
            const scrollW = document.documentElement.scrollWidth;
            const clientW = document.documentElement.clientWidth;
            return {
                scrollWidth: scrollW,
                clientWidth: clientW,
                horizontalOverflow: scrollW > clientW
            };
        }""")
        results["800x1024"] = metrics_800
        path_800 = site_dir / "tablet_800x1024.png"
        await page_800.screenshot(path=str(path_800))
        print(f"Captured 800x1024 to {path_800}: {metrics_800}")
        await context_800.close()

        # 4. Viewport 1440x900 (Desktop)
        context_1440 = await browser.new_context(viewport={"width": 1440, "height": 900})
        page_1440 = await context_1440.new_page()
        await page_1440.goto(html_url, wait_until="networkidle")
        await page_1440.wait_for_timeout(800)

        metrics_1440 = await page_1440.evaluate("""() => {
            const heroImg = document.querySelector('img[data-role="hero-image"]');
            const imgr = heroImg ? heroImg.getBoundingClientRect() : null;
            const scrollW = document.documentElement.scrollWidth;
            const clientW = document.documentElement.clientWidth;
            return {
                scrollWidth: scrollW,
                clientWidth: clientW,
                horizontalOverflow: scrollW > clientW,
                heroImgWidth: imgr ? imgr.width : 0
            };
        }""")
        results["1440x900"] = metrics_1440
        path_1440 = site_dir / "desktop_1440x900.png"
        await page_1440.screenshot(path=str(path_1440))
        print(f"Captured 1440x900 to {path_1440}: {metrics_1440}")
        await context_1440.close()

        await browser.close()

    # Create Before / After Composite
    before_path = site_dir / "mobile_before_390x844.png"
    after_path = site_dir / "mobile_390x844.png"
    composite_path = site_dir / "iost-mobile-before-after.png"

    if before_path.exists() and after_path.exists():
        img_before = Image.open(before_path).convert("RGB")
        img_after = Image.open(after_path).convert("RGB")

        # Target size for each: width=390, height=844
        w, h = img_before.size
        header_banner_h = 50
        gap = 20

        comp_w = w * 2 + gap + 40
        comp_h = h + header_banner_h + 40

        comp = Image.new("RGB", (comp_w, comp_h), (15, 23, 42))
        draw = ImageDraw.Draw(comp)

        # Labels
        # Before image on left
        comp.paste(img_before, (20, header_banner_h + 20))
        # After image on right
        comp.paste(img_after, (20 + w + gap, header_banner_h + 20))

        # Text banner
        draw.rectangle([(20, 15), (20 + w, header_banner_h + 10)], fill=(220, 38, 38))
        draw.text((40, 24), "BEFORE (Bug: 135px top-bar + 78px header = 213px)", fill=(255, 255, 255))

        draw.rectangle([(20 + w + gap, 15), (comp_w - 20, header_banner_h + 10)], fill=(15, 118, 110))
        draw.text((20 + w + gap + 20, 24), "AFTER (Compact 58px header, 0px gap to hero)", fill=(255, 255, 255))

        comp.save(str(composite_path))
        print(f"Generated before/after comparison at {composite_path}")

    # Output json metrics
    metrics_file = site_dir / "responsive_metrics.json"
    metrics_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("Responsive metrics saved successfully.")

if __name__ == "__main__":
    asyncio.run(test_and_capture())
