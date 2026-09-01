import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    site_dir = Path("sites/iost-ortodontia-aline-iost-rio-claro").resolve()
    url = (site_dir / "index.html").as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)

        # Check section paddings and widths
        sections = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('section, footer')).map(s => {
                const cs = window.getComputedStyle(s);
                const r = s.getBoundingClientRect();
                return {
                    id: s.id || s.tagName,
                    class: s.className,
                    paddingTop: cs.paddingTop,
                    paddingBottom: cs.paddingBottom,
                    scrollWidth: s.scrollWidth,
                    clientWidth: s.clientWidth,
                    hasOverflow: s.scrollWidth > s.clientWidth
                };
            });
        }""")
        print("Sections check:")
        for s in sections:
            print(f"  {s['id']}: padY={s['paddingTop']}/{s['paddingBottom']}, w={s['clientWidth']}, overflow={s['hasOverflow']}")

        # Check map iframe
        map_info = await page.evaluate("""() => {
            const iframe = document.querySelector('iframe');
            if (!iframe) return { found: false };
            const r = iframe.getBoundingClientRect();
            return {
                found: true,
                width: r.width,
                height: r.height,
                x: r.x
            };
        }""")
        print("Map check:", map_info)

        # Check body horizontal scroll
        scroll_w = await page.evaluate("document.documentElement.scrollWidth")
        client_w = await page.evaluate("document.documentElement.clientWidth")
        print(f"Doc scrollWidth: {scroll_w}, clientWidth: {client_w}, overflow: {scroll_w > client_w}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
