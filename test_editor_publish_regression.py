#!/usr/bin/env python3
"""Reusable regression test for editor publication source-independence & animation sanitization."""

import asyncio
import re
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
SLUG = "instituto-ferreira-odontologia-rio-claro"
PUBLIC_PATH = ROOT / "sites" / SLUG / f"{SLUG}.html"
EDITOR_PATH = ROOT / "sites" / SLUG / f"{SLUG}-editor.html"
BACKUP_CLEAN = ROOT / ".prospector-editor" / "backups" / SLUG / "20260826-190040-911938.html"
BASE_URL = "http://127.0.0.1:8787"


def assert_clean_html(html: str, stage_name: str):
    # 1. No editor UI
    assert "data-pe-ui" not in html, f"[{stage_name}] data-pe-ui leaked into public HTML"
    assert "pe-publish-script" not in html, f"[{stage_name}] pe-publish-script leaked"
    assert "pe-script" not in html, f"[{stage_name}] pe-script leaked"
    assert "contenteditable" not in html, f"[{stage_name}] contenteditable leaked"

    # 2. No DarkReader artifacts
    assert "data-darkreader" not in html, f"[{stage_name}] data-darkreader leaked"
    assert "--darkreader" not in html, f"[{stage_name}] --darkreader leaked"

    # 3. No GSAP runtime inline animation styles (opacity: 0, translate: none, transform: translate)
    bad_styles = re.findall(r'style="([^"]*(?:translate:\s*none|opacity:\s*0(?![.\d])|transform:\s*translate)[^"]*)"', html, re.I)
    assert not bad_styles, f"[{stage_name}] Found serialized runtime animation styles: {bad_styles[:3]}"

    print(f"  [PASS] {stage_name}: HTML markup clean & free of runtime artifacts")


async def run_publish_test(page, scroll_target: str, edit_suffix: str = ""):
    # 1. Open editor
    editor_url = f"{BASE_URL}/sites/{SLUG}/{SLUG}-editor.html"
    await page.goto(editor_url, wait_until="networkidle")
    await page.wait_for_timeout(300)

    # 2. Set scroll position
    if scroll_target == "top":
        await page.evaluate("() => window.scrollTo(0, 0)")
    elif scroll_target == "mid":
        await page.evaluate("() => window.scrollTo(0, Math.floor(document.documentElement.scrollHeight / 2))")
    elif scroll_target == "bottom":
        await page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
    await page.wait_for_timeout(300)

    # 3. Perform text edit if requested
    if edit_suffix:
        await page.evaluate(f"""() => {{
            const h1 = document.querySelector('h1.hero-headline');
            if (h1) {{
                h1.textContent = 'Excelência técnica e acolhimento em odontologia {edit_suffix}';
            }}
        }}""")

    # 4. Handle confirm dialog automatically and click publish
    page.once("dialog", lambda d: asyncio.create_task(d.accept()))
    publish_btn = page.locator("#pe-publish")
    await publish_btn.click()
    await page.wait_for_selector("#pe-publish-status.pe-ok", timeout=5000)
    await page.wait_for_timeout(500)

    # 5. Read resulting published file
    published_html = PUBLIC_PATH.read_text(encoding="utf-8")
    assert_clean_html(published_html, f"Publish at scroll {scroll_target}")
    return published_html


async def main():
    print("==================================================")
    print("STARTING EDITOR PUBLISH SOURCE-INDEPENDENCE TEST")
    print("==================================================")

    # Restore known good backup before test
    assert BACKUP_CLEAN.exists(), f"Backup clean file not found: {BACKUP_CLEAN}"
    shutil.copy2(BACKUP_CLEAN, PUBLIC_PATH)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Test 1: Publish at TOP
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        html_top = await run_publish_test(page, "top", "")

        # Test 2: Publish at MID
        html_mid = await run_publish_test(page, "mid", "")

        # Test 3: Publish at BOTTOM
        html_bottom = await run_publish_test(page, "bottom", "")

        # Test 4: Verify SOURCE INDEPENDENCE EQUIVALENCE
        print("\nVerifying equivalence between TOP, MID, and BOTTOM publishes...")
        assert html_top == html_mid, "Top publish and Mid publish outputs differed!"
        assert html_top == html_bottom, "Top publish and Bottom publish outputs differed!"
        print("  [PASS] Source independence PASS: Output at scrollY=0, scrollY=mid, scrollY=bottom is 100% IDENTICAL")

        # Test 5: Verify Public Page Reload & Visibility
        print("\nVerifying public page reload and reveal behavior...")
        public_url = f"{BASE_URL}/sites/{SLUG}/{SLUG}.html"
        await page.goto(public_url, wait_until="networkidle")

        # Check all key sections exist and become visible
        sections = [
            ".hero-headline",
            ".section-header-block",
            ".treatment-card",
            ".facility-feature-box",
            ".facility-card-primary",
            ".doctor-image-frame",
            ".location-card",
            ".cta-banner-inner"
        ]

        # Scroll page to trigger ScrollTrigger
        scroll_height = await page.evaluate("() => document.documentElement.scrollHeight")
        for y in range(0, scroll_height + 400, 400):
            await page.evaluate("(y) => window.scrollTo(0, y)", y)
            await page.wait_for_timeout(80)

        # Allow 0.5s GSAP reveal transitions to complete
        await page.wait_for_timeout(700)

        for sel in sections:
            count = await page.locator(sel).count()
            assert count > 0, f"Section selector {sel} not found on public page"
            # Verify opacity is not stuck at 0
            opacities = await page.eval_on_selector_all(sel, "(els) => els.map(e => window.getComputedStyle(e).opacity)")
            for i, op in enumerate(opacities):
                assert float(op) > 0.8, f"Element {sel}[{i}] stuck at opacity: {op}"

        print("  [PASS] All key sections and animated elements verified VISIBLE (opacity > 0.5)")

        # Test 6: Reduced motion check
        print("\nVerifying reduced-motion mode...")
        await page.emulate_media(reduced_motion="reduce")
        await page.goto(public_url, wait_until="networkidle")
        for sel in [".treatment-card", ".facility-feature-box", ".doctor-image-frame"]:
            opacities = await page.eval_on_selector_all(sel, "(els) => els.map(e => window.getComputedStyle(e).opacity)")
            for i, op in enumerate(opacities):
                assert float(op) > 0.5, f"Reduced motion: {sel}[{i}] not visible"
        print("  [PASS] Reduced-motion mode verified PASS")

        # Test 7: Authored inline opacity & transform preservation test
        print("\nVerifying authored inline opacity & transform preservation...")
        # Inject fixture elements with legitimate author opacity & transform
        fixture_html = BACKUP_CLEAN.read_text(encoding="utf-8")
        fixture_needle = "</body>"
        fixture_insert = (
            '<div id="author-fixture-opacity" style="opacity: 0.85; margin: 10px;">Authored Opacity</div>\n'
            '<div id="author-fixture-transform" style="transform: rotate(-2deg); padding: 5px;">Authored Transform</div>\n'
        )
        fixture_html = fixture_html.replace(fixture_needle, fixture_insert + fixture_needle)
        PUBLIC_PATH.write_text(fixture_html, encoding="utf-8")

        # Regenerate editor for fixture
        import subprocess
        subprocess.run(["python", "create_editor.py", str(PUBLIC_PATH)], check=True)

        # Open editor and publish
        page_fixture = await browser.new_page(viewport={"width": 1440, "height": 900})
        html_fixture_published = await run_publish_test(page_fixture, "mid", "")

        assert 'id="author-fixture-opacity"' in html_fixture_published, "Author opacity fixture missing"
        assert 'opacity: 0.85' in html_fixture_published or 'opacity:0.85' in html_fixture_published, "Authored opacity: 0.85 was destroyed!"
        assert 'id="author-fixture-transform"' in html_fixture_published, "Author transform fixture missing"
        assert 'rotate(-2deg)' in html_fixture_published, "Authored transform: rotate(-2deg) was destroyed!"
        print("  [PASS] Authored inline opacity: 0.85 PRESERVED")
        print("  [PASS] Authored inline transform: rotate(-2deg) PRESERVED")

        # Restore clean backup after fixture test
        shutil.copy2(BACKUP_CLEAN, PUBLIC_PATH)
        subprocess.run(["python", "create_editor.py", str(PUBLIC_PATH)], check=True)

        await browser.close()

    print("\n==================================================")
    print("ALL EDITOR REGRESSION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
