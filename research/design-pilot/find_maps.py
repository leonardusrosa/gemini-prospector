import sys
import time
from playwright.sync_api import sync_playwright

def find_maps():
    query = "Clínica Odontológica Dra. Francine Goulart Rio Claro"
    search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        print(f"Navigating to {search_url}...")
        page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(5000)

        print(f"Current URL: {page.url}")
        print(f"Title: {page.title()}")
        page.screenshot(path="research/design-pilot/maps_step1.png")

        # Let's inspect headings or text
        h1s = page.locator("h1").all_text_contents()
        print(f"H1s: {h1s}")

        # Let's see if we see any place link or if it redirected to the place
        links = page.locator("a[href*='/maps/place/']").evaluate_all(
            "elements => elements.map(e => ({href: e.href, text: e.innerText}))"
        )
        print(f"Found {len(links)} place links: {links[:3]}")

        # Let's check ratings and reviews in the DOM
        body_text = page.locator("body").inner_text()
        print(f"Body text preview (first 1000 chars):\n{body_text[:1000]}")

        browser.close()

if __name__ == "__main__":
    find_maps()
