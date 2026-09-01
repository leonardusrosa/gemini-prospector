from playwright.sync_api import sync_playwright
import json
import re

url = "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(locale="pt-BR")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    # Click on the reviews button inside the sidebar
    # In Google Maps sidebar, there is a button with "12 avaliações" or "Avaliações" tab or div.F7nice
    btn = page.locator('button[aria-label*="avaliações"], button[aria-label*="Avaliações"], div.F7nice').first
    if btn.count() > 0:
        btn.click()
        page.wait_for_timeout(4000)

    # Extract all reviews
    cards = page.locator('div.jftiEf, div[data-review-id]').all()
    print(f"Cards found immediately: {len(cards)}")
    
    seen = {}
    sidebar = page.locator('div[role="main"], div.m6QErb.DxyBCb.kA9KIf.dS8AEf, div.m6QErb').first

    for i in range(30):
        # Click "Mais"
        for more_btn in page.locator('button.w8nwRe, button:has-text("Mais")').all():
            try:
                more_btn.click(timeout=100)
            except Exception:
                pass

        cards = page.locator('div.jftiEf, div[data-review-id]').all()
        for card in cards:
            r_id = card.get_attribute("data-review-id") or ""
            author_el = card.locator('.d4r55, .fontHeadlineSmall, div.WNxFhc').first
            author = author_el.inner_text().strip() if author_el.count() > 0 else ""
            date_el = card.locator('.rsqaWe, span.rsqaWe').first
            date = date_el.inner_text().strip() if date_el.count() > 0 else ""
            stars_el = card.locator('span.kvMYJc').first
            stars_text = stars_el.get_attribute("aria-label") if stars_el.count() > 0 else ""
            rating = 5
            if stars_text:
                match = re.search(r"(\d+)", stars_text)
                if match:
                    rating = int(match.group(1))
            text_el = card.locator('.wiI7pd, .MyEned').first
            text = text_el.inner_text().strip() if text_el.count() > 0 else ""

            key = r_id or f"{author}|{date}|{rating}"
            if key and key not in seen:
                seen[key] = {
                    "nativeReviewId": r_id,
                    "author": author,
                    "rating": rating,
                    "dateLabel": date,
                    "hasText": bool(text),
                    "text": text
                }

        print(f"Step {i}: {len(seen)} captured", flush=True)
        if len(seen) >= 12:
            break

        if sidebar.count() > 0:
            sidebar.evaluate("el => el.scrollBy(0, 1000)")
        page.wait_for_timeout(800)

    print(f"Total: {len(seen)}")
    with open("collected_iost_reviews.json", "w", encoding="utf-8") as f:
        json.dump(list(seen.values()), f, ensure_ascii=False, indent=2)
    browser.close()
