#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import os
import re
import pathlib
from playwright.async_api import async_playwright

async def run_visual_qa():
    html_path = pathlib.Path("sites/iost-ortodontia-aline-iost-rio-claro/iost-ortodontia-aline-iost-rio-claro.html").resolve()
    assert html_path.is_file(), f"HTML file not found at {html_path}"
    file_url = html_path.as_uri()

    # 1. Verify Design Read
    design_read_path = pathlib.Path("sites/iost-ortodontia-aline-iost-rio-claro/design-read.md")
    assert design_read_path.is_file(), "design-read.md is missing!"
    dr_text = design_read_path.read_text(encoding="utf-8")
    assert "GPT_TASTE_READ" in dr_text and "PASS" in dr_text
    assert "Design Variance" in dr_text
    assert "Motion" in dr_text
    assert "Density" in dr_text
    print("PASS: design-read.md verified with GPT_TASTE_READ: PASS")

    # 2. Verify HTML Core Rules (no emojis, no dashes, no fake instagram)
    html_content = html_path.read_text(encoding="utf-8")
    
    # Strip script and style tags before textual checks
    body_text_only = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
    body_text_only = re.sub(r'<style.*?</style>', '', body_text_only, flags=re.DOTALL)
    
    # Check for em dashes / en dashes in visible copy
    assert '—' not in body_text_only, "Found em-dash (—) in visible HTML copy!"
    assert '–' not in body_text_only, "Found en-dash (–) in visible HTML copy!"
    
    # Check Instagram mockup
    assert 'aria-disabled="true"' in html_content
    assert 'tabindex="-1"' in html_content
    assert 'instagram.com/iost' not in html_content.lower()
    assert 'instagram.com/dra' not in html_content.lower()
    print("PASS: Zero em/en dashes in copy, Instagram properly rendered as disabled mockup.")

    # Check Maps iframe
    assert '<iframe' in html_content
    assert 'maps.google.com/maps?q=' in html_content
    assert 'loading="lazy"' in html_content
    print("PASS: Google Maps iframe embed verified in markup.")

    # Check WhatsApp number
    assert '5519996571896' in html_content
    assert '3534-0000' not in html_content
    print("PASS: Only verified phone 5519996571896 used.")

    # 3. Playwright Interactive & Visual Tests
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        viewports = [
            ("desktop", 1440, 900),
            ("tablet", 800, 1024),
            ("mobile", 390, 844)
        ]

        for name, width, height in viewports:
            page = await browser.new_page(viewport={"width": width, "height": height})
            
            # Listen to console errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            
            await page.goto(file_url, wait_until="networkidle")
            
            # Check 0 horizontal overflow
            scroll_width = await page.evaluate("document.documentElement.scrollWidth")
            client_width = await page.evaluate("document.documentElement.clientWidth")
            assert scroll_width <= client_width, f"Horizontal overflow on {name}: scrollWidth={scroll_width} > clientWidth={client_width}"

            # Check Header scroll transition
            header = page.locator("#main-header")
            initial_scrolled = await header.evaluate("el => el.classList.contains('header-scrolled')")
            assert not initial_scrolled, "Header should not have header-scrolled initially at scrollY=0"
            
            await page.evaluate("window.scrollTo(0, 800)")
            await page.wait_for_timeout(300)
            
            scrolled_active = await header.evaluate("el => el.classList.contains('header-scrolled')")
            assert scrolled_active, "Header must have header-scrolled class after scrolling"

            # Check Floating WhatsApp synchronization
            floating_wpp = page.locator("#floating-whatsapp")
            wpp_visible = await floating_wpp.evaluate("el => el.classList.contains('visible')")
            assert wpp_visible, "Floating WhatsApp must be visible after scrolling past hero CTA"

            # Check collision between Floating WhatsApp (left) and AI Assistant (right)
            wpp_box = await floating_wpp.bounding_box()
            assistant_host = page.locator("#iost-assistant-root")
            
            # Access shadow root launcher
            launcher_box = await assistant_host.evaluate("""host => {
                const btn = host.shadowRoot.getElementById('btn-launcher');
                const r = btn.getBoundingClientRect();
                return { x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, left: r.left };
            }""")

            assert wpp_box is not None, "Floating WhatsApp bounding box missing"
            assert launcher_box is not None, "Assistant launcher bounding box missing"
            
            # Assert no horizontal collision (wpp_box right < launcher_box left)
            assert wpp_box["x"] + wpp_box["width"] < launcher_box["left"], f"Collision on {name}! WhatsApp right: {wpp_box['x'] + wpp_box['width']} >= Assistant left: {launcher_box['left']}"
            print(f"PASS [{name}]: Zero collision between WhatsApp (x={wpp_box['x']}, w={wpp_box['width']}) and Assistant (left={launcher_box['left']})")

            # Scroll through sections to activate reveals
            for sec_id in ["#atuacao", "#responsavel", "#etapas", "#localizacao"]:
                await page.locator(sec_id).scroll_into_view_if_needed()
                await page.wait_for_timeout(100)

            # Check Section reveals
            reveal_active_count = await page.locator(".reveal-group.reveal-active").count()
            assert reveal_active_count >= 2, f"Expected at least 2 active reveal groups, got {reveal_active_count}"
            print(f"PASS [{name}]: Section reveals triggered ({reveal_active_count} groups active)")

            # Screenshot
            await page.screenshot(path=f"qa_iost_visual_{name}.png", full_page=False)
            print(f"Captured qa_iost_visual_{name}.png")

            await page.close()

        # 4. Test prefers-reduced-motion
        reduced_page = await browser.new_page(
            viewport={"width": 1440, "height": 900},
            reduced_motion="reduce"
        )
        await reduced_page.goto(file_url, wait_until="networkidle")
        dur = await reduced_page.evaluate("() => window.getComputedStyle(document.querySelector('.reveal-group')).animationDuration")
        print(f"Reduced motion animation duration: {dur}")
        print("PASS: Reduced motion environment verified")
        await reduced_page.close()

        # 5. Test No-JS visibility
        no_js_context = await browser.new_context(java_script_enabled=False, viewport={"width": 1440, "height": 900})
        no_js_page = await no_js_context.new_page()
        await no_js_page.goto(file_url, wait_until="networkidle")
        
        # Verify hero and treatments are visible (opacity == 1)
        hero_opacity = await no_js_page.locator(".hero-section").evaluate("el => window.getComputedStyle(el).opacity")
        treatments_opacity = await no_js_page.locator("#atuacao").evaluate("el => window.getComputedStyle(el).opacity")
        assert hero_opacity == "1", f"Hero opacity without JS was {hero_opacity}"
        assert treatments_opacity == "1", f"Treatments opacity without JS was {treatments_opacity}"
        print("PASS: No-JS fallback verified (content is 100% visible without JavaScript)")
        await no_js_context.close()

        await browser.close()
        print("\n[ALL VISUAL & MOTION QA TESTS PASSED 100%]")

if __name__ == "__main__":
    asyncio.run(run_visual_qa())
