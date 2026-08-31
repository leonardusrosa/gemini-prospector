import asyncio
import json
from playwright.async_api import async_playwright

async def inspect_place():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="pt-BR",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        url = "https://www.google.com/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138409,-47.5600884,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk"
        
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(4000)

        # Check for consent
        try:
            reject_btn = await page.query_selector('button[aria-label="Rejeitar tudo"], button:has-text("Rejeitar tudo")')
            if reject_btn:
                await reject_btn.click()
                await page.wait_for_timeout(2000)
        except Exception:
            pass

        # Title
        h1 = await page.query_selector('h1')
        title = await h1.inner_text() if h1 else ""
        print("TITLE:", title)

        # Extract all buttons/spans that have rating or review information
        spans = await page.query_selector_all('div[role="main"] span, div[role="main"] button, div[role="main"] div')
        info_lines = []
        for s in spans:
            try:
                aria = await s.get_attribute("aria-label")
                txt = await s.inner_text()
                if aria and ("estrela" in aria.lower() or "avalia" in aria.lower() or "review" in aria.lower()):
                    info_lines.append(f"ARIA: {aria}")
                if txt and ("estrela" in txt.lower() or "avalia" in txt.lower() or "coment" in txt.lower()):
                    info_lines.append(f"TXT: {txt}")
            except Exception:
                pass
        
        print("RATING/REVIEW INFO:")
        for l in set(info_lines):
            safe_l = l.encode('ascii', errors='replace').decode('ascii')
            print("  ", safe_l)

        # Extract address, phone, website from details panel
        items_data = []
        buttons = await page.query_selector_all('button[data-item-id]')
        for b in buttons:
            item_id = await b.get_attribute("data-item-id")
            aria = await b.get_attribute("aria-label")
            txt = await b.inner_text()
            items_data.append({"item_id": item_id, "aria": aria, "txt": txt})

        # Let's check for "Avaliações" tab or button
        reviews_data = []
        reviews_tab = await page.query_selector('button[aria-label*="Avaliações"], button:has-text("Avaliações")')
        if reviews_tab:
            await reviews_tab.click()
            await page.wait_for_timeout(3000)
            
            review_cards = await page.query_selector_all('div[data-review-id], div.jftiEf')
            for card in review_cards:
                author_el = await card.query_selector('.d4r55, .WNxF4')
                author = await author_el.inner_text() if author_el else ""
                rating_el = await card.query_selector('span[aria-label*="estrela"]')
                rating = await rating_el.get_attribute("aria-label") if rating_el else ""
                text_el = await card.query_selector('.wiI7pd, .MyEned')
                text = await text_el.inner_text() if text_el else ""
                date_el = await card.query_selector('.rsqaWe')
                date_label = await date_el.inner_text() if date_el else ""
                reviews_data.append({
                    "author": author,
                    "rating": rating,
                    "text": text,
                    "dateLabel": date_label
                })

        output = {
            "title": title,
            "url": page.url,
            "items": items_data,
            "rating_info": list(set(info_lines)),
            "reviews": reviews_data
        }
        with open("place_info.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print("WROTE place_info.json successfully. Total reviews found:", len(reviews_data))

        # Screenshot
        await page.screenshot(path="maps_place_detail.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_place())
