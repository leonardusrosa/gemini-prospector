import asyncio
import functools
import http.server
import os
import socketserver
import threading
import time
from pathlib import Path
from playwright.async_api import async_playwright, expect

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "out"

EXPECTED_SERVICES = [
    "Interior and exterior auto detailing.",
    "Paint correction and buffing services.",
    "Color sanding services for automotive paint surfaces.",
    "Headlight restoration services.",
    "Engine bay detailing.",
    "Wheel and brake caliper cleaning and detailing.",
]

FORBIDDEN_VISIBLE_COPY = [
    "professional tools",
    "vehicle-safe formulas",
    "carpet extraction",
    "leather conditioning",
    "surface decontamination",
    "eliminate deep swirl marks",
    "eliminates deep swirl marks",
    "swirl elimination",
    "deep scratch removal",
    "show-car clear coats",
    "nighttime projection",
    "road visibility",
    "iron particle decontamination",
    "serviced on-site at our addison facility",
    "private website concept",
    "website concept",
    "private preview",
    "demo site",
    "mockup",
    "prototype",
    "prepared for",
    "google rating",
    "google reviews",
    "google maps reviews",
]


class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def start_server(port=3456):
    handler = functools.partial(SilentHandler, directory=str(OUT_DIR))
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


async def assert_no_horizontal_overflow(page, label):
    overflow = await page.evaluate(
        """
        () => Math.max(
            document.documentElement.scrollWidth,
            document.body.scrollWidth
        ) - window.innerWidth
        """
    )
    assert overflow <= 1, f"{label}: horizontal overflow = {overflow}px"


async def assert_full_width_hero(page, label):
    result = await page.evaluate(
        """
        () => {
            const hero = document.querySelector('[data-role="hero"]');
            const media = document.querySelector('[data-role="hero-media-plane"]');
            if (!hero || !media) return null;
            const h = hero.getBoundingClientRect();
            const m = media.getBoundingClientRect();
            return {
                heroWidth: h.width,
                mediaWidth: m.width,
                ratio: m.width / window.innerWidth
            };
        }
        """
    )
    assert result is not None, f"{label}: hero/media plane missing"
    assert result["ratio"] >= 0.98, (
        f"{label}: hero media is only {result['ratio'] * 100:.1f}% of viewport"
    )


async def verify_content(page):
    hero_desc = page.locator(".hero-desc")
    await expect(hero_desc).to_have_text(
        "Paint correction, buffing, and full auto detailing by Wilson "
        "in Addison, Texas. Backed by a 4.9 rating across 268 reviews."
    )

    await expect(page.locator("#services .section-eyebrow")).to_have_text("Services")
    await expect(page.locator("#services .section-title")).to_have_text("Detailing Services")

    cards = page.locator(".service-card .service-desc")
    assert await cards.count() == len(EXPECTED_SERVICES), (
        f"Expected {len(EXPECTED_SERVICES)} service descriptions, found {await cards.count()}"
    )

    actual_services = [
        (await cards.nth(i).inner_text()).strip()
        for i in range(await cards.count())
    ]
    assert actual_services == EXPECTED_SERVICES, (
        f"Service descriptions mismatch:\n{actual_services}"
    )

    signature = page.locator("#paint-correction-compare")
    await expect(signature).to_be_visible()
    await expect(signature.locator(".section-title")).to_have_text("Before & After Comparison")

    sig_desc = (await signature.locator(".section-desc").inner_text()).strip().lower()
    for forbidden in ["deep extraction", "restoration"]:
        assert forbidden not in sig_desc, f"Signature contains unsupported phrase: {forbidden}"

    await expect(signature.locator(".after-badge")).to_have_text(
        "Corrected Surface: Illustrative"
    )

    await expect(page.locator("#reviews .section-eyebrow")).to_have_text("REVIEWS")
    await expect(page.locator("#reviews .section-title")).to_have_text("WHAT PEOPLE ARE SAYING")

    visible_text = (await page.locator("body").inner_text()).lower()
    for phrase in FORBIDDEN_VISIBLE_COPY:
        assert phrase not in visible_text, f"Forbidden visible phrase found: {phrase!r}"


def measure_js_bundle():
    chunks_dir = OUT_DIR / "_next" / "static" / "chunks"
    total_bytes = 0
    file_count = 0
    if chunks_dir.exists():
        for file in chunks_dir.rglob("*.js"):
            total_bytes += file.stat().st_size
            file_count += 1
    return total_bytes, file_count


async def measure_cls_and_render_time(page, url):
    t0 = time.time()
    await page.goto(url, wait_until="load")
    render_time_ms = (time.time() - t0) * 1000

    cls = await page.evaluate(
        """
        () => new Promise((resolve) => {
            let clsValue = 0;
            const observer = new PerformanceObserver((entryList) => {
                for (const entry of entryList.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                }
            });
            observer.observe({ type: 'layout-shift', buffered: true });
            setTimeout(() => {
                observer.disconnect();
                resolve(clsValue);
            }, 300);
        })
        """
    )
    return render_time_ms, cls


async def main():
    port = 3456
    server = start_server(port)
    url = f"http://127.0.0.1:{port}/"
    print(f"Engine B static export server running at {url}")

    total_js_bytes, js_files = measure_js_bundle()
    print(f"Total JS bundle: {total_js_bytes / 1024:.1f} KB across {js_files} chunks")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # 1. Desktop 1440
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        render_time_ms, cls = await measure_cls_and_render_time(page, url)
        print(f"Desktop 1440 render time: {render_time_ms:.1f}ms, CLS: {cls:.4f}")
        await verify_content(page)
        await assert_no_horizontal_overflow(page, "Desktop 1440")
        await assert_full_width_hero(page, "Desktop 1440")
        print("[PASS] Desktop 1440")
        await page.close()

        # 2. Tablet 768
        page = await browser.new_page(viewport={"width": 768, "height": 1024})
        await page.goto(url, wait_until="load")
        await verify_content(page)
        await assert_no_horizontal_overflow(page, "Tablet 768")
        await assert_full_width_hero(page, "Tablet 768")
        print("[PASS] Tablet 768")
        await page.close()

        # 3. Mobile 390
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        await page.goto(url, wait_until="load")
        await verify_content(page)
        await assert_no_horizontal_overflow(page, "Mobile 390")
        await assert_full_width_hero(page, "Mobile 390")
        print("[PASS] Mobile 390")
        await page.close()

        # 4. Reduced Motion
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            reduced_motion="reduce",
        )
        page = await context.new_page()
        await page.goto(url, wait_until="load")
        video = page.locator(".hero-video-bg")
        poster = page.locator(".hero-poster-fallback")
        assert await video.evaluate("el => getComputedStyle(el).display") == "none"
        assert await poster.evaluate("el => getComputedStyle(el).display") != "none"
        await assert_full_width_hero(page, "Reduced Motion")
        await assert_no_horizontal_overflow(page, "Reduced Motion")
        print("[PASS] Reduced Motion")
        await context.close()

        # 5. No-JS
        context = await browser.new_context(
            java_script_enabled=False,
            viewport={"width": 390, "height": 844},
        )
        page = await context.new_page()
        await page.goto(url, wait_until="load")
        await verify_content(page)
        await expect(page.locator(".hero-poster-fallback")).to_be_visible()
        await assert_full_width_hero(page, "No-JS")
        await assert_no_horizontal_overflow(page, "No-JS")
        print("[PASS] No-JS")
        await context.close()

        await browser.close()

    server.shutdown()
    print("\nALL ENGINE B PLAYWRIGHT TESTS PASSED (5/5)")


if __name__ == "__main__":
    asyncio.run(main())
