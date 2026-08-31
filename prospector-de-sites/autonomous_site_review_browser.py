#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Browser-level autonomous review for Prospector websites.

Requires Playwright for Python and a Chromium installation.

Usage:
    python prospector-de-sites/autonomous_site_review_browser.py \
      --url http://127.0.0.1:8000/sites/example/example.html \
      --manifest sites/example/review-manifest.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

try:
    from playwright.async_api import async_playwright
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Playwright is required for browser review. Install it in the QA environment before claiming PASS. "
        f"Import error: {exc}"
    )


VIEWPORT_DEFAULTS = {
    "desktop": [1440, 900],
    "tablet": [800, 1024],
    "mobile": [390, 844],
}


class Review:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def check(self, key: str, ok: bool, detail: str, viewport: str | None = None) -> None:
        self.checks.append(
            {
                "key": key,
                "status": "PASS" if ok else "FAIL",
                "detail": detail,
                "viewport": viewport,
            }
        )

    @property
    def failed(self) -> list[dict[str, Any]]:
        return [item for item in self.checks if item["status"] == "FAIL"]

    def emit(self) -> int:
        print(
            json.dumps(
                {
                    "browserReviewPass": not bool(self.failed),
                    "blockingFailures": len(self.failed),
                    "checks": self.checks,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if self.failed else 0


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Manifest root must be an object")
    return data


def cfg(manifest: dict[str, Any], key: str) -> dict[str, Any]:
    value = manifest.get(key, {})
    return value if isinstance(value, dict) else {}


def overlap(a: dict[str, float] | None, b: dict[str, float] | None) -> bool:
    if not a or not b:
        return False
    return not (
        a["x"] + a["width"] <= b["x"]
        or b["x"] + b["width"] <= a["x"]
        or a["y"] + a["height"] <= b["y"]
        or b["y"] + b["height"] <= a["y"]
    )


async def visible_box(locator):
    try:
        if await locator.count() < 1 or not await locator.first.is_visible():
            return None
        return await locator.first.bounding_box()
    except Exception:
        return None


async def review_viewport(browser, url: str, manifest: dict[str, Any], name: str, size: list[int], review: Review):
    width, height = int(size[0]), int(size[1])
    context = await browser.new_context(viewport={"width": width, "height": height})
    page = await context.new_page()
    console_errors: list[str] = []
    request_failures: list[str] = []

    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("requestfailed", lambda req: request_failures.append(f"{req.method} {req.url}: {req.failure}"))

    response = await page.goto(url, wait_until="networkidle")
    review.check(f"{name}_http", bool(response and response.ok), f"HTTP status {response.status if response else 'none'}", name)

    overflow = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    review.check(f"{name}_horizontal_overflow", overflow <= 1, f"horizontal overflow = {overflow}px", name)

    h1 = page.locator("h1")
    review.check(f"{name}_h1_visible", await h1.count() > 0 and await h1.first.is_visible(), "Primary heading must be visible", name)

    # Hero visual requirement.
    hero_cfg = cfg(manifest, "heroVisual")
    if hero_cfg.get("required", True):
        hero = page.locator('[data-role="hero"]')
        hero_exists = await hero.count() > 0
        review.check(f"{name}_hero_hook", hero_exists, "Hero must expose data-role=hero", name)

        hero_image = hero.locator('img[data-role="hero-image"]') if hero_exists else page.locator('img[data-role="hero-image"]')
        image_exists = await hero_image.count() > 0
        image_visible = image_exists and await hero_image.first.is_visible()
        review.check(
            f"{name}_hero_image_visible",
            image_visible,
            "Every hero needs a visible relevant img[data-role=hero-image], even without an expert photo",
            name,
        )
        if image_visible:
            box = await hero_image.first.bounding_box()
            min_width = 180 if name == "mobile" else 220
            min_height = 110 if name == "mobile" else 140
            geometry_ok = bool(box and box["width"] >= min_width and box["height"] >= min_height)
            review.check(
                f"{name}_hero_image_geometry",
                geometry_ok,
                f"hero image box={box}, minimum={min_width}x{min_height}",
                name,
            )
            src = (await hero_image.first.get_attribute("src") or "").strip()
            alt = (await hero_image.first.get_attribute("alt") or "").strip()
            loading = (await hero_image.first.get_attribute("loading") or "").strip().lower()
            review.check(f"{name}_hero_image_src", bool(src), f"src={src!r}", name)
            review.check(f"{name}_hero_image_alt", bool(alt), f"alt={alt!r}", name)
            review.check(f"{name}_hero_image_not_lazy", loading != "lazy", f"loading={loading!r}", name)

            source_type = str(hero_cfg.get("sourceType") or "").strip().lower()
            represents_actual = bool(hero_cfg.get("representsActualBusiness", False))
            disclosure_required = bool(hero_cfg.get("illustrativeDisclosureRequired", True))
            if source_type in {"stock", "generated"} and not represents_actual and disclosure_required:
                image_context = (await hero_image.first.get_attribute("data-image-context") or "").strip().lower()
                review.check(
                    f"{name}_hero_image_illustrative_context",
                    image_context == "illustrative",
                    f"data-image-context={image_context!r}",
                    name,
                )

    # Embedded map requirement.
    address_cfg = cfg(manifest, "address")
    if address_cfg.get("verified") and address_cfg.get("public", True) and address_cfg.get("mapEmbedRequired", True):
        map_iframe = page.locator("iframe[src*='maps.google'], iframe[src*='google.com/maps']")
        map_visible = await map_iframe.count() > 0 and await map_iframe.first.is_visible()
        review.check(f"{name}_map_visible", map_visible, "Verified address must render an embedded map iframe", name)
        if map_visible:
            box = await map_iframe.first.bounding_box()
            box_ok = bool(box and box["width"] >= 180 and box["height"] >= 120)
            review.check(f"{name}_map_geometry", box_ok, f"map box={box}", name)

    # Instagram presence/state.
    ig_cfg = cfg(manifest, "instagram")
    ig_state = str(ig_cfg.get("state") or "not_applicable").lower()
    if ig_state in {"verified", "unverified"}:
        ig = page.locator('[data-social="instagram"]')
        ig_visible = await ig.count() > 0 and await ig.first.is_visible()
        review.check(f"{name}_instagram_visible", ig_visible, f"Instagram UI state={ig_state}", name)
        if ig_visible and ig_state == "unverified":
            aria_disabled = await ig.first.get_attribute("aria-disabled")
            href = await ig.first.get_attribute("href")
            review.check(f"{name}_instagram_disabled", aria_disabled == "true", f"aria-disabled={aria_disabled!r}", name)
            review.check(
                f"{name}_instagram_no_fake_href",
                not href or "instagram.com" not in href.lower(),
                f"href={href!r}",
                name,
            )

    # Motion and scroll-aware header.
    motion_cfg = cfg(manifest, "motion")
    if motion_cfg.get("required", True):
        reveal_count = await page.locator('[data-motion="reveal"]').count()
        minimum = int(motion_cfg.get("minimumRevealGroups", 2) or 0)
        review.check(f"{name}_reveal_hooks", reveal_count >= minimum, f"reveal hooks={reveal_count}, expected>={minimum}", name)

        if motion_cfg.get("headerScrollStateRequired", False):
            header = page.locator('[data-role="site-header"]')
            header_exists = await header.count() > 0
            review.check(f"{name}_header_hook", header_exists, "data-role=site-header required", name)
            if header_exists:
                before = await header.first.evaluate(
                    "el => ({cls:el.className,bg:getComputedStyle(el).backgroundColor,shadow:getComputedStyle(el).boxShadow})"
                )
                await page.evaluate("window.scrollTo(0, Math.min(document.body.scrollHeight * 0.55, 1200))")
                await page.wait_for_timeout(450)
                after = await header.first.evaluate(
                    "el => ({cls:el.className,bg:getComputedStyle(el).backgroundColor,shadow:getComputedStyle(el).boxShadow})"
                )
                review.check(
                    f"{name}_header_changes_on_scroll",
                    before != after,
                    f"before={before}, after={after}",
                    name,
                )

    # WhatsApp behavior and floating UI.
    wa_cfg = cfg(manifest, "whatsapp")
    if wa_cfg.get("verified"):
        wa_links = page.locator('a[href^="https://wa.me/"]')
        review.check(f"{name}_whatsapp_visible", await wa_links.count() > 0, f"wa.me links={await wa_links.count()}", name)

        if wa_cfg.get("floatingRequired", True):
            floating = page.locator('[data-role="floating-whatsapp"]')
            review.check(f"{name}_floating_whatsapp_exists", await floating.count() > 0, "floating WhatsApp hook required", name)
            if await floating.count() > 0:
                # Scroll below hero and require the floating CTA to become visible.
                hero = page.locator('[data-role="hero"]')
                if await hero.count() > 0:
                    hero_box = await hero.first.bounding_box()
                    if hero_box:
                        await page.evaluate(f"window.scrollTo(0, {int(hero_box['y'] + hero_box['height'] + 80)})")
                        await page.wait_for_timeout(400)
                visible_after = await floating.first.is_visible()
                review.check(f"{name}_floating_whatsapp_after_hero", visible_after, "floating CTA should be visible after hero leaves viewport", name)

                # If hero is visible at top, floating CTA should not compete.
                await page.evaluate("window.scrollTo(0,0)")
                await page.wait_for_timeout(300)
                visible_top = await floating.first.is_visible()
                if motion_cfg.get("floatingCtaSyncRequired", False):
                    review.check(
                        f"{name}_floating_whatsapp_hidden_on_hero",
                        not visible_top,
                        "floating CTA must not compete with hero CTA while hero is visible",
                        name,
                    )

    # Assistant collision geometry after scrolling below hero.
    assistant_cfg = cfg(manifest, "assistant")
    if assistant_cfg.get("present") and assistant_cfg.get("collisionCheckRequired", True):
        await page.evaluate("window.scrollTo(0, Math.min(document.body.scrollHeight * 0.65, 1600))")
        await page.wait_for_timeout(400)
        launcher = page.locator('[data-role="assistant-launcher"]')
        floating = page.locator('[data-role="floating-whatsapp"]')
        launcher_box = await visible_box(launcher)
        floating_box = await visible_box(floating)
        review.check(
            f"{name}_assistant_whatsapp_no_overlap",
            not overlap(launcher_box, floating_box),
            f"assistant={launcher_box}, whatsapp={floating_box}",
            name,
        )

    # Visible content after bottom scroll to trigger actual reveal implementation.
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(500)
    if motion_cfg.get("required", True):
        invisible_reveals = await page.locator('[data-motion="reveal"]').evaluate_all(
            "els => els.filter(el => { const s=getComputedStyle(el); const r=el.getBoundingClientRect(); return s.visibility==='hidden' || parseFloat(s.opacity||'1') < 0.15 || r.height < 1; }).length"
        )
        review.check(
            f"{name}_reveals_resolve_visible",
            invisible_reveals == 0,
            f"invisible reveal groups after scroll={invisible_reveals}",
            name,
        )

    review.check(
        f"{name}_console_errors",
        not console_errors,
        "console errors: " + (" | ".join(console_errors[:5]) if console_errors else "none"),
        name,
    )
    review.check(
        f"{name}_request_failures",
        not request_failures,
        "request failures: " + (" | ".join(request_failures[:5]) if request_failures else "none"),
        name,
    )

    await context.close()


async def review_no_js(browser, url: str, manifest: dict[str, Any], review: Review):
    qa_cfg = cfg(manifest, "qa")
    if not qa_cfg.get("noJsRequired", True):
        return
    size = qa_cfg.get("mobile") or VIEWPORT_DEFAULTS["mobile"]
    context = await browser.new_context(viewport={"width": int(size[0]), "height": int(size[1])}, java_script_enabled=False)
    page = await context.new_page()
    response = await page.goto(url, wait_until="domcontentloaded")
    h1_visible = await page.locator("h1").count() > 0 and await page.locator("h1").first.is_visible()
    body_text = (await page.locator("body").inner_text()).strip()
    review.check("no_js_http", bool(response and response.ok), f"HTTP={response.status if response else 'none'}", "no-js")
    review.check("no_js_primary_content", h1_visible and len(body_text) > 100, f"h1={h1_visible}, body chars={len(body_text)}", "no-js")

    hero_cfg = cfg(manifest, "heroVisual")
    if hero_cfg.get("required", True):
        hero_image = page.locator('[data-role="hero"] img[data-role="hero-image"]')
        hero_image_visible = await hero_image.count() > 0 and await hero_image.first.is_visible()
        review.check("no_js_hero_image_visible", hero_image_visible, "Hero image must remain visible without JavaScript", "no-js")

    await context.close()


async def review_reduced_motion(browser, url: str, manifest: dict[str, Any], review: Review):
    qa_cfg = cfg(manifest, "qa")
    if not qa_cfg.get("reducedMotionRequired", True):
        return
    context = await browser.new_context(viewport={"width": 800, "height": 1024}, reduced_motion="reduce")
    page = await context.new_page()
    response = await page.goto(url, wait_until="networkidle")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(250)
    invisible = await page.locator('[data-motion="reveal"]').evaluate_all(
        "els => els.filter(el => { const s=getComputedStyle(el); return s.visibility==='hidden' || parseFloat(s.opacity||'1') < 0.15; }).length"
    )
    review.check("reduced_motion_http", bool(response and response.ok), f"HTTP={response.status if response else 'none'}", "reduced-motion")
    review.check("reduced_motion_content_visible", invisible == 0, f"hidden reveal groups={invisible}", "reduced-motion")
    await context.close()


async def async_main(args) -> int:
    manifest = load_manifest(Path(args.manifest))
    qa_cfg = cfg(manifest, "qa")
    review = Review()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for name in ("desktop", "tablet", "mobile"):
                size = qa_cfg.get(name) or VIEWPORT_DEFAULTS[name]
                await review_viewport(browser, args.url, manifest, name, size, review)
            await review_no_js(browser, args.url, manifest, review)
            await review_reduced_motion(browser, args.url, manifest, review)
        finally:
            await browser.close()

    return review.emit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Prospector browser autonomous site review")
    parser.add_argument("--url", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    return asyncio.run(async_main(args))


if __name__ == "__main__":
    sys.exit(main())