from playwright.sync_api import sync_playwright
import json
import re

url = "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(locale="pt-BR")
    page = context.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    # Click on the reviews button
    reviews_tab = page.locator('button[role="tab"]:has-text("Avaliações"), button:has-text("avaliações")').first
    if reviews_tab.count() > 0:
        reviews_tab.click()
        page.wait_for_timeout(3000)
    
    # Try to find the scrollable container inside Maps sidebar
    scrollable = page.locator('div.m6QErb.DxyBCb.kA9KIf.dS8AEf, div[role="region"][aria-label*="Avaliações"]').first
    
    # Scroll multiple times to make sure all 12 reviews load
    for _ in range(15):
        if scrollable.count() > 0:
            scrollable.evaluate("el => el.scrollBy(0, 1500)")
        else:
            page.mouse.wheel(0, 1500)
        page.wait_for_timeout(600)

    # Expand any "Mais" buttons
    more_btns = page.locator('button:has-text("Mais"), button.w8nwRe')
    for i in range(more_btns.count()):
        try:
            more_btns.nth(i).click(timeout=1000)
        except Exception:
            pass

    cards = page.locator('div.jftiEf, div[data-review-id]')
    count = cards.count()
    print(f"Total cards found: {count}")

    results = []
    for i in range(count):
        card = cards.nth(i)
        
        # Author
        author_el = card.locator('.d4r55, .fontHeadlineSmall, div.WNxFhc').first
        author = author_el.inner_text().strip() if author_el.count() > 0 else ""
        
        # Date
        date_el = card.locator('.rsqaWe, span.rsqaWe').first
        date = date_el.inner_text().strip() if date_el.count() > 0 else ""
        
        # Stars
        stars_el = card.locator('span.kvMYJc').first
        stars_text = stars_el.get_attribute("aria-label") if stars_el.count() > 0 else ""
        rating = 5
        if stars_text:
            match = re.search(r"(\d+)", stars_text)
            if match:
                rating = int(match.group(1))

        # Text
        text_el = card.locator('.wiI7pd, .MyEned').first
        text = text_el.inner_text().strip() if text_el.count() > 0 else ""

        review_id = card.get_attribute("data-review-id") or ""

        results.append({
            "index": i + 1,
            "nativeReviewId": review_id,
            "author": author,
            "rating": rating,
            "dateLabel": date,
            "hasText": bool(text),
            "text": text
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))
    browser.close()
