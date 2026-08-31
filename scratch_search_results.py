import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_search_results():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        url = "https://www.google.com/maps/search/IOST+Ortodontia+Rio+Claro"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(4000)

        # Check results
        results = []
        links = await page.query_selector_all('a[href*="/maps/place/"]')
        for l in links:
            href = await l.get_attribute("href")
            aria = await l.get_attribute("aria-label")
            txt = await l.inner_text()
            results.append({"aria": aria, "txt": txt, "href": href})
        
        with open("search_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("Saved search_results.json, count:", len(results))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_search_results())
