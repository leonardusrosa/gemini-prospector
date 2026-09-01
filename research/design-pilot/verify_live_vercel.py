import asyncio
import json
from playwright.async_api import async_playwright

async def verify():
    urls = [
        "https://prospector-sites-beta.vercel.app/clientes/iost-ortodontia-aline-iost-rio-claro/",
        "https://prospector-sites-ode4wqqno-leonardusrosas-projects.vercel.app/clientes/iost-ortodontia-aline-iost-rio-claro/"
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for u in urls:
            context = await browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
            page = await context.new_page()
            response = await page.goto(u, wait_until="networkidle")
            print(f"URL: {u}")
            print(f"HTTP Status: {response.status if response else 'None'}")

            metrics = await page.evaluate("""() => {
                const h = document.querySelector('header');
                const hero = document.querySelector('[data-role="hero"]');
                const topBar = document.querySelector('.top-bar');
                const hr = h ? h.getBoundingClientRect() : null;
                const heror = hero ? hero.getBoundingClientRect() : null;
                const topBarDisplay = topBar ? window.getComputedStyle(topBar).display : null;
                const scrollW = document.documentElement.scrollWidth;
                const clientW = document.documentElement.clientWidth;

                return {
                    topBarDisplay: topBarDisplay,
                    headerHeight: hr ? hr.height : 0,
                    headerY: hr ? hr.y : 0,
                    heroY: heror ? heror.y : 0,
                    gap: (heror && hr) ? (heror.y - (hr.y + hr.height)) : 0,
                    scrollWidth: scrollW,
                    clientWidth: clientW,
                    overflow: scrollW > clientW
                };
            }""")
            print("Live page metrics:", json.dumps(metrics, indent=2))
            await context.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify())
