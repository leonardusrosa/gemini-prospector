import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

async def check_query(query: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/maps/search/{encoded}"
        print(f"Searching: {query}")
        print(f"URL: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(5000)
            print("Final URL:", page.url)
            print("Page Title:", await page.title())
            
            # Check for consent or modal
            try:
                reject_btn = await page.query_selector('button[aria-label="Rejeitar tudo"], button:has-text("Rejeitar tudo"), button:has-text("Reject all")')
                if reject_btn:
                    await reject_btn.click()
                    await page.wait_for_timeout(2000)
            except Exception as e:
                pass

            # Extract main heading / place details
            heading_el = await page.query_selector('h1')
            heading = await heading_el.inner_text() if heading_el else "None"
            print(f"H1: {heading}")

            # Check for stars / reviews
            rating_el = await page.query_selector('div[aria-label*="estrelas"], span[aria-label*="estrelas"], div[aria-label*="stars"]')
            if rating_el:
                print("Rating aria:", await rating_el.get_attribute("aria-label"))

            # Take screenshot
            slug_q = query.replace(" ", "_").replace("/", "_")
            await page.screenshot(path=f"maps_{slug_q}.png")

            # Check if there are search result items
            items = await page.query_selector_all('div[role="feed"] > div > div[jsaction]')
            print(f"Search results count: {len(items)}")

            # Let's inspect text on page
            body_text = await page.inner_text("body")
            print("Body snippet (first 500 chars):", body_text[:500])

        except Exception as e:
            print("Error:", e)
        finally:
            await browser.close()

async def main():
    queries = [
        "IOST Ortodontia Rio Claro",
        "Aline Iost Ortodontia Rio Claro",
        "Dra. Aline Iost Rio Claro",
        "Avenida 9, 411, Rio Claro"
    ]
    for q in queries:
        await check_query(q)
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
