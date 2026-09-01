import json
import re
import sys
import time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

PLACE_URL = "https://www.google.com/maps/place/Dentista+Dra.+Francine+Goulart/@-22.4125632,-47.5594921,17z/data=!4m6!3m5!1s0x94c7da5a58a30833:0x1f93843856f80228!8m2!3d-22.4125632!4d-47.5594921!16s%2Fg%2F11kn6x5g20"

def traverse_reviews():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        print(f"Navigating to place profile: {PLACE_URL}")
        page.goto(PLACE_URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)

        # 1. Profile header observation
        profile_name = "Dentista Dra. Francine Goulart"
        
        # Check header rating and count
        # In Google Maps, rating is typically in a div with font-size / role, e.g. "4,8"
        # and count is e.g. "(28)" or "28 avaliações"
        page_info = page.evaluate("""() => {
            const h1 = document.querySelector('h1')?.innerText || '';
            
            // Search for aggregate rating number (e.g. 4.8 or 4,8)
            let ratingText = '';
            let countText = '';
            
            const ratingEl = document.querySelector('div.F7nice span[aria-hidden="true"], span.ceNzKf');
            if (ratingEl) ratingText = ratingEl.innerText.trim();
            
            const countEl = document.querySelector('div.F7nice span:nth-child(2) span, button[aria-label*="avalia"]');
            if (countEl) countText = countEl.innerText.trim() || countEl.getAttribute('aria-label') || '';
            
            return { h1, ratingText, countText };
        }""")
        print("Header info observed:", page_info)

        # Let's take screenshot of header
        page.screenshot(path="research/design-pilot/maps_header.png")

        # 2. Click Reviews tab / button
        print("Opening reviews panel...")
        # Button with aria-label containing "avaliações" or tab "Avaliações"
        reviews_tab = page.locator("button[role='tab'][aria-label*='Avaliações'], button[aria-label*='avaliações'], button:has-text('Avaliações')").first
        if reviews_tab.count() > 0:
            reviews_tab.click()
            page.wait_for_timeout(3000)
            print("Clicked reviews tab/button")
        else:
            print("Reviews tab not found via primary selector, searching buttons...")

        page.screenshot(path="research/design-pilot/maps_reviews_opened.png")

        # 3. Reviews panel observation
        panel_info = page.evaluate("""() => {
            // Find panel count text
            const countHeaders = Array.from(document.querySelectorAll('div, span, button')).filter(e => 
                e.innerText && /\\b\\d+\\s+avaliações\\b/i.test(e.innerText)
            );
            return countHeaders.map(e => e.innerText.trim());
        }""")
        print("Panel info matches:", panel_info[:5])

        # Scroll reviews container
        # The scrollable container in Google Maps reviews is div.m6QErb[aria-label*="Avaliações"] or similar
        print("Scrolling reviews panel to collect all entries...")
        
        # Click "Mais" on all truncated reviews
        for _ in range(15):
            more_buttons = page.locator("button.w8nwRe, button:has-text('Mais')")
            for i in range(more_buttons.count()):
                try:
                    more_buttons.nth(i).click(timeout=500)
                except:
                    pass

            # Scroll the reviews container
            page.evaluate("""() => {
                const scrollable = document.querySelector('div.m6QErb.DxyBCb, div.m6QErb[aria-label*="Avaliações"], div.review-dialog-list') 
                    || document.querySelector('div[role="region"]') 
                    || document.querySelector('div.m6QErb');
                if (scrollable) {
                    scrollable.scrollTop += 2000;
                } else {
                    window.scrollBy(0, 1000);
                }
            }""")
            page.wait_for_timeout(1500)

        # 4. Extract all reviews in DOM
        extracted = page.evaluate("""() => {
            // Review containers usually have class jftiEf
            const items = Array.from(document.querySelectorAll('div.jftiEf'));
            return items.map((el, idx) => {
                const nativeReviewId = el.getAttribute('data-review-id') || null;
                const authorEl = el.querySelector('div.d4r55, .TSUbDb');
                const author = authorEl ? authorEl.innerText.trim() : null;
                
                const starsEl = el.querySelector('span.kvMYJc');
                let rating = null;
                if (starsEl) {
                    const label = starsEl.getAttribute('aria-label') || '';
                    const match = label.match(/(\\d+)/);
                    if (match) rating = parseInt(match[1], 10);
                }
                
                const dateEl = el.querySelector('span.rsqaWe');
                const dateLabel = dateEl ? dateEl.innerText.trim() : null;
                
                const textEl = el.querySelector('span.wiI7m, .MyEned');
                const text = textEl ? textEl.innerText.trim() : '';
                
                return {
                    idx,
                    nativeReviewId,
                    author,
                    rating,
                    dateLabel,
                    text,
                    hasText: text.length > 0
                };
            });
        }""")

        print(f"Extracted {len(extracted)} reviews:")
        for r in extracted[:5]:
            print(f" - [{r['rating']}*] {r['author']} ({r['dateLabel']}): {r['text'][:60]}...")

        # Save raw extraction to inspect
        with open("research/design-pilot/raw_reviews.json", "w", encoding="utf-8") as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)

        browser.close()

if __name__ == "__main__":
    traverse_reviews()
