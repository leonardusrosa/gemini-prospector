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

        # 1. Section Heading & Copy
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

        # 3. Review Cards & Intrinsic Height Verification
        cards = section.locator(".review-card")
        card_count = await cards.count()
        print(f"Total review cards: {card_count}")
        assert card_count == 5

        # Check track and slide alignment
        track_align = await page.eval_on_selector(".reviews-track", "el => getComputedStyle(el).alignItems")
        slide_align = await page.eval_on_selector(".review-slide", "el => getComputedStyle(el).alignSelf")
        assert track_align == "flex-start", f"Track alignItems must be flex-start, got {track_align}"
        assert slide_align == "flex-start", f"Slide alignSelf must be flex-start, got {slide_align}"

        # Heights must be intrinsic: Kelly (long) > Milena (medium) > Rosilene (short)
        h1 = await cards.nth(0).evaluate("el => el.getBoundingClientRect().height")
        h2 = await cards.nth(1).evaluate("el => el.getBoundingClientRect().height")
        h3 = await cards.nth(2).evaluate("el => el.getBoundingClientRect().height")
        print(f"Card heights: Kelly={h1:.1f}px, Milena={h2:.1f}px, Rosilene={h3:.1f}px")
        assert h1 > h2 > h3, f"Expected intrinsic heights h1({h1}) > h2({h2}) > h3({h3})"

        # Gaps must be natural (no large artificial empty area)
        for i in range(3):
            gap = await cards.nth(i).evaluate("""el => {
                const textEl = el.querySelector('.review-text');
                const footerEl = el.querySelector('.review-footer');
                return footerEl.getBoundingClientRect().top - textEl.getBoundingClientRect().bottom;
            }""")
            assert gap <= 40, f"Card {i+1} has artificial blank area: {gap:.1f}px"

        for i in range(card_count):
            card = cards.nth(i)
            text = await card.evaluate("el => el.innerText")
            assert "Google" not in text, f"Card {i+1} has visible Google text: {text}"
            prov = card.locator(".review-provenance svg")
            assert await prov.count() == 1, f"Card {i+1} missing provenance svg"

        # 4. Navigation
        nav_link = page.locator("nav a[href='#avaliacoes']")
        nav_text = await nav_link.text_content()
        print(f"Desktop nav: {nav_text.strip()}")
        assert nav_text.strip() == "Avaliações"

        drawer_link = page.locator("#mobileDrawer a[href='#avaliacoes']")
        drawer_text = await drawer_link.text_content()
        print(f"Mobile drawer nav: {drawer_text.strip()}")
        assert drawer_text.strip() == "Avaliações"

        # 5. Carousel Motion & Interactions
        next_btn = page.locator("#nextReview")
        prev_btn = page.locator("#prevReview")
        track = page.locator("#reviewsTrack")

        initial_transform = await track.evaluate("el => el.style.transform")
        await next_btn.click()
        await asyncio.sleep(0.6)
        after_next = await track.evaluate("el => el.style.transform")
        print(f"Track transform after next: {after_next}")
        assert after_next != initial_transform

        await prev_btn.click()
        await asyncio.sleep(0.6)
        after_prev = await track.evaluate("el => el.style.transform")
        print(f"Track transform after prev: {after_prev}")

        # 6. Mobile Responsiveness (390x844)
        mobile_page = await browser.new_page(viewport={"width": 390, "height": 844})
        await mobile_page.goto(file_url, wait_until="networkidle")
        m_section = mobile_page.locator("#avaliacoes")
        assert await m_section.is_visible()
        m_card = m_section.locator(".review-card").first
        assert await m_card.is_visible()
        print("Mobile layout verified.")

        await browser.close()
        print("[PASS] Local site QA checks passed successfully!")

        # Live Vercel QA
        live_browser = await p.chromium.launch(headless=True)
        live_page = await live_browser.new_page(viewport={"width": 1440, "height": 900})
        await live_page.goto("https://prospector-sites-beta.vercel.app/clientes/instituto-ferreira-odontologia-rio-claro/", wait_until="networkidle")
        live_section = live_page.locator("#avaliacoes")
        assert await live_section.is_visible()
        live_title = await live_section.locator("h2.section-title").text_content()
        assert live_title.strip() == "O que nossos pacientes dizem"
        live_meta = await live_section.locator(".aggregate-meta").text_content()
        assert live_meta.strip() == "36 avaliações"
        assert "Google" not in live_meta

        live_cards = live_section.locator(".review-card")
        assert await live_cards.count() == 5
        for i in range(5):
            t = await live_cards.nth(i).evaluate("el => el.innerText")
            assert "Google" not in t

        live_mobile = await live_browser.new_page(viewport={"width": 390, "height": 844})
        await live_mobile.goto("https://prospector-sites-beta.vercel.app/clientes/instituto-ferreira-odontologia-rio-claro/", wait_until="networkidle")
        live_m_section = live_mobile.locator("#avaliacoes")
        assert await live_m_section.is_visible()
        live_drawer = live_mobile.locator("#mobileDrawer a[href='#avaliacoes']")
        assert (await live_drawer.text_content()).strip() == "Avaliações"

        await live_browser.close()
        print("[PASS] Live Vercel Production QA passed successfully!")

if __name__ == "__main__":
    asyncio.run(run_qa())
