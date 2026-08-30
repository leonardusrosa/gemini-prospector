#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import pathlib
import unittest
from playwright.async_api import async_playwright

async def run_qa():
    html_path = pathlib.Path(__file__).resolve().parent.parent / "prospector-sites" / "clientes" / "instituto-ferreira-odontologia-rio-claro" / "index.html"
    file_url = html_path.as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto(file_url, wait_until="networkidle")

        # Wait for fonts / masonry observer to settle
        await page.wait_for_timeout(300)

        # 1. Section Heading & Neutral Copy
        section = page.locator("#avaliacoes")
        assert await section.is_visible()
        title = await section.locator("h2.section-title").text_content()
        print(f"Section title: {title.strip()}")
        assert title.strip() == "O que nossos pacientes dizem"

        kicker = await section.locator(".section-kicker").text_content()
        print(f"Section kicker: {kicker.strip()}")
        assert kicker.strip() == "Experiência dos pacientes"

        desc = await section.locator(".section-description").text_content()
        print(f"Section description: {desc.strip()}")
        assert "Relatos de pacientes" in desc

        # 2. Aggregate Box
        score = await section.locator(".aggregate-score").text_content()
        meta = await section.locator(".aggregate-meta").text_content()
        print(f"Aggregate: {score.strip()} | Meta: {meta.strip()}")
        assert score.strip() == "5,0"
        assert meta.strip() == "36 avaliações"
        assert "Google" not in meta

        # 3. Carousel UI Must Be Completely Removed
        assert await page.locator("#reviewsCarousel").count() == 0
        assert await page.locator("#reviewsTrack").count() == 0
        assert await page.locator("#prevReview").count() == 0
        assert await page.locator("#nextReview").count() == 0
        assert await page.locator("#carouselIndicators").count() == 0

        # 4. Masonry Grid Layout Verification (Desktop 1440x900 - 3 Columns)
        grid = section.locator("#reviewsMasonry")
        assert await grid.is_visible()
        cards = grid.locator(".review-card")
        card_count = await cards.count()
        print(f"Total review cards in masonry: {card_count}")
        assert card_count == 5

        # Card bounding boxes on desktop
        boxes_1440 = []
        for i in range(card_count):
            box = await cards.nth(i).bounding_box()
            boxes_1440.append(box)
            print(f"Card {i+1}: x={box['x']:.1f}, y={box['y']:.1f}, w={box['width']:.1f}, h={box['height']:.1f}")

        # Verify 3 distinct column x-coordinates on 1440px
        col_xs = sorted(list({round(b['x'], 0) for b in boxes_1440}))
        print(f"Desktop 1440px unique column X positions: {col_xs}")
        assert len(col_xs) == 3, f"Expected 3 columns on desktop, got {len(col_xs)}: {col_xs}"

        # Heights must be intrinsic: Kelly (long) > Milena (medium) > Rosilene (short)
        h1 = boxes_1440[0]['height']
        h2 = boxes_1440[1]['height']
        h3 = boxes_1440[2]['height']
        print(f"Intrinsic heights: Kelly={h1:.1f}px, Milena={h2:.1f}px, Rosilene={h3:.1f}px")
        assert h1 > h2 > h3, f"Expected intrinsic heights h1({h1}) > h2({h2}) > h3({h3})"

        # Verify dense Pinterest flow: cards in same column do not overlap
        for i in range(card_count):
            for j in range(i + 1, card_count):
                b1, b2 = boxes_1440[i], boxes_1440[j]
                # If in same column (similar x), ensure y does not overlap
                if abs(b1['x'] - b2['x']) < 10:
                    overlap = (b1['y'] < b2['y'] + b2['height']) and (b2['y'] < b1['y'] + b1['height'])
                    assert not overlap, f"Overlap detected on desktop between card {i+1} and card {j+1}"

        # Gaps must be natural (no large artificial empty area)
        for i in range(card_count):
            gap = await cards.nth(i).evaluate("""el => {
                const textEl = el.querySelector('.review-text');
                const footerEl = el.querySelector('.review-footer');
                return footerEl.getBoundingClientRect().top - textEl.getBoundingClientRect().bottom;
            }""")
            assert gap <= 40, f"Card {i+1} has artificial blank area: {gap:.1f}px"

        # Neutrality check & provenance
        for i in range(card_count):
            card = cards.nth(i)
            text = await card.evaluate("el => el.innerText")
            assert "Google" not in text, f"Card {i+1} has visible Google text: {text}"
            prov = card.locator(".review-provenance svg")
            assert await prov.count() == 1, f"Card {i+1} missing provenance svg"

        # 5. Tablet Responsiveness (800x900 - 2 Columns)
        tablet_page = await browser.new_page(viewport={"width": 800, "height": 900})
        await tablet_page.goto(file_url, wait_until="networkidle")
        await tablet_page.wait_for_timeout(300)
        t_cards = tablet_page.locator("#reviewsMasonry .review-card")
        boxes_800 = []
        for i in range(await t_cards.count()):
            boxes_800.append(await t_cards.nth(i).bounding_box())
        t_col_xs = sorted(list({round(b['x'], 0) for b in boxes_800}))
        print(f"Tablet 800px unique column X positions: {t_col_xs}")
        assert len(t_col_xs) == 2, f"Expected 2 columns on tablet, got {len(t_col_xs)}: {t_col_xs}"
        await tablet_page.close()

        # 6. Mobile Responsiveness (390x844 - 1 Column Stacked DOM order)
        mobile_page = await browser.new_page(viewport={"width": 390, "height": 844})
        await mobile_page.goto(file_url, wait_until="networkidle")
        await mobile_page.wait_for_timeout(300)
        m_section = mobile_page.locator("#avaliacoes")
        assert await m_section.is_visible()
        m_cards = m_section.locator(".review-card")
        assert await m_cards.count() == 5
        boxes_390 = []
        for i in range(5):
            boxes_390.append(await m_cards.nth(i).bounding_box())
        m_col_xs = sorted(list({round(b['x'], 0) for b in boxes_390}))
        print(f"Mobile 390px unique column X positions: {m_col_xs}")
        assert len(m_col_xs) == 1, f"Expected 1 column on mobile, got {len(m_col_xs)}: {m_col_xs}"
        # Strictly increasing top y
        for i in range(4):
            assert boxes_390[i]['y'] + boxes_390[i]['height'] <= boxes_390[i+1]['y'] + 1, f"Mobile card {i+1} overlaps card {i+2}"
        print("Mobile layout verified.")
        await mobile_page.close()

        await browser.close()
        print("[PASS] Local site QA checks passed successfully!")

        # 7. Live Vercel Production QA
        live_browser = await p.chromium.launch(headless=True)
        live_page = await live_browser.new_page(viewport={"width": 1440, "height": 900})
        await live_page.goto("https://prospector-sites-beta.vercel.app/clientes/instituto-ferreira-odontologia-rio-claro/", wait_until="networkidle")
        await live_page.wait_for_timeout(500)

        live_section = live_page.locator("#avaliacoes")
        assert await live_section.is_visible()
        live_title = await live_section.locator("h2.section-title").text_content()
        assert live_title.strip() == "O que nossos pacientes dizem"
        live_meta = await live_section.locator(".aggregate-meta").text_content()
        assert live_meta.strip() == "36 avaliações"
        assert "Google" not in live_meta

        assert await live_page.locator("#reviewsCarousel").count() == 0
        assert await live_page.locator("#reviewsTrack").count() == 0
        assert await live_page.locator("#prevReview").count() == 0
        assert await live_page.locator("#nextReview").count() == 0

        live_grid = live_section.locator("#reviewsMasonry")
        assert await live_grid.is_visible()
        live_cards = live_grid.locator(".review-card")
        assert await live_cards.count() == 5

        live_boxes_1440 = []
        for i in range(5):
            b = await live_cards.nth(i).bounding_box()
            live_boxes_1440.append(b)
            t = await live_cards.nth(i).evaluate("el => el.innerText")
            assert "Google" not in t

        live_col_xs = sorted(list({round(b['x'], 0) for b in live_boxes_1440}))
        print(f"Live Vercel 1440px unique column X positions: {live_col_xs}")
        assert len(live_col_xs) == 3, f"Expected 3 columns on live desktop, got {len(live_col_xs)}: {live_col_xs}"

        # Mobile on Live Vercel
        live_mobile = await live_browser.new_page(viewport={"width": 390, "height": 844})
        await live_mobile.goto("https://prospector-sites-beta.vercel.app/clientes/instituto-ferreira-odontologia-rio-claro/", wait_until="networkidle")
        await live_mobile.wait_for_timeout(500)
        live_m_section = live_mobile.locator("#avaliacoes")
        assert await live_m_section.is_visible()
        live_m_cards = live_m_section.locator(".review-card")
        assert await live_m_cards.count() == 5

        live_drawer = live_mobile.locator("#mobileDrawer a[href='#avaliacoes']")
        assert (await live_drawer.text_content()).strip() == "Avaliações"

        await live_browser.close()
        print("[PASS] Live Vercel Production QA passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_qa())
