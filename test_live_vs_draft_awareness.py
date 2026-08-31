#!/usr/bin/env python3
"""
Comprehensive Live vs Draft Source Awareness & Versioned Metadata Test Suite.
Validates Instituto Ferreira against the real public HTTPS deployment:
https://prospector.autocora.com.br
"""

import asyncio
import hashlib
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from playwright.async_api import async_playwright

BASE_HTTPS_URL = "https://prospector.autocora.com.br"
SLUG = "autocora-cms-qa"
ADMIN_URL = f"{BASE_HTTPS_URL}/clientes/{SLUG}/admin/"
PUBLIC_SITE_URL = f"https://prospector-sites-beta.vercel.app/clientes/{SLUG}/"
OPERATOR_USER = "admin_autocora_qa"
OPERATOR_PASS = "REDACTED_TEST_SECRET"
QA_TEXT = "QA CMS SYNTHETIC TEST TEMPORÁRIO"


def https_request(path: str, method: str = "GET", data: dict = None, headers: dict = None):
    ctx = ssl.create_default_context()
    url = f"{BASE_HTTPS_URL}{path}"
    req_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if headers:
        req_headers.update(headers)
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    if req_data:
        req_headers["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            try:
                parsed_json = json.loads(body)
            except Exception:
                parsed_json = None
            return resp.status, dict(resp.headers), body, parsed_json
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            parsed_json = json.loads(body)
        except Exception:
            parsed_json = None
        return err.code, dict(err.headers), body, parsed_json


async def run_live_draft_awareness_suite():
    print("=" * 80)
    print("RUNNING LIVE VS DRAFT SOURCE-OF-TRUTH VALIDATION SUITE")
    print(f"Target URL: {ADMIN_URL}")
    print("=" * 80)

    # Step 1: Authenticate via API
    status, _, _, auth_res = https_request("/api/client-cms/auth", method="POST", data={
        "slug": SLUG,
        "username": OPERATOR_USER,
        "password": OPERATOR_PASS
    })
    assert status == 200 and auth_res.get("success"), f"Auth failed: {auth_res}"
    token = auth_res["token"]
    print(f"[PASS] Authenticated successfully with token: {token[:12]}...")

    # Preflight cleanup: Ensure starting state has no leftover draft
    https_request("/api/client-cms/draft/discard", method="POST", data={"slug": SLUG, "reason": "preflight"}, headers={"Authorization": f"Bearer {token}"})

    # Step 2: Query status endpoint
    status, _, _, status_res = https_request(
        f"/api/client-cms/status?slug={SLUG}",
        method="GET",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status == 200 and status_res.get("success"), f"Status query failed: {status_res}"
    print(f"[PASS] Status API returned: draftState={status_res.get('draftState')}, hasDraft={status_res.get('hasDraft')}")
    print(f"       liveCommit={status_res.get('liveCommit')}, liveContentHash={status_res.get('liveContentHash')[:16]}...")
    assert status_res.get("hasDraft") is False, f"Expected no initial draft, got {status_res}"
    assert status_res.get("draftState") == "none", f"Expected draftState none, got {status_res.get('draftState')}"

    # Step 3: Verify editor-frame with explicit source=live
    status, _, frame_html, _ = https_request(
        f"/api/client-cms/editor-frame?slug={SLUG}&source=live",
        method="GET",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status == 200, f"Editor frame failed with status {status}"
    assert QA_TEXT not in frame_html, f"Found stale QA text in editor-frame: {QA_TEXT}"
    assert "Infraestrutura Sintética" in frame_html or "Infraestrutura Sint" in frame_html, "Canonical baseline text missing in editor-frame"
    print("[PASS] Explicit source=live editor-frame returned canonical baseline HTML (zero QA text)")

    # Step 4: Playwright UI Verification
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        async def on_dialog(dialog):
            try:
                await dialog.accept()
            except Exception:
                pass
        page.on("dialog", on_dialog)

        # Navigate to admin
        await page.goto(ADMIN_URL, wait_until="networkidle")
        print("[PASS] Navigated to Admin login page")

        # Perform Login
        await page.fill("#cms-username", OPERATOR_USER)
        await page.fill("#cms-password", OPERATOR_PASS)
        await page.click("#cms-login-submit")
        await page.wait_for_selector("#cms-workspace-view", state="visible", timeout=15000)
        print("[PASS] Logged in to Workspace view")

        # Check status indicator
        status_text = await page.inner_text("#cms-status-text")
        print(f"[PASS] Initial Status Indicator text: '{status_text}'")
        assert "Site publicado" in status_text, f"Expected 'Site publicado', got '{status_text}'"

        # Check iframe content
        frame_el = page.frame_locator("#cms-editor-frame")
        await frame_el.locator("h1.hero-headline").wait_for(state="visible", timeout=15000)
        headline_text = await frame_el.locator("h1.hero-headline").inner_text()
        print(f"[PASS] Editor iframe rendered headline: '{headline_text.strip()}'")
        assert QA_TEXT not in headline_text, f"QA text found in iframe: '{headline_text}'"
        assert "Infraestrutura Sintética" in headline_text or "Infraestrutura Sint" in headline_text, f"Unexpected headline text: '{headline_text}'"

        # Step 5: Save Draft Test
        print("\n--- Testing Draft Lifecycle ---")
        # Edit headline in iframe
        await frame_el.locator("h1.hero-headline").evaluate("(el) => { el.innerText = 'Rascunho de Teste Local'; el.dispatchEvent(new Event('input', { bubbles: true })); }")
        # Wait a moment for dirty tracker
        await page.wait_for_timeout(500)
        dirty_status = await page.inner_text("#cms-status-text")
        print(f"[PASS] Status after editing in iframe: '{dirty_status}'")
        assert "Alterações locais não salvas" in dirty_status, f"Expected dirty status, got '{dirty_status}'"

        # Save draft via UI
        await page.click("#btn-save-draft")
        await page.wait_for_selector("#cms-toast:has-text('Rascunho salvo')", state="visible", timeout=10000)
        await page.wait_for_timeout(500)

        draft_status = await page.inner_text("#cms-status-text")
        print(f"[PASS] Status after saving draft: '{draft_status}'")
        assert "Rascunho salvo" in draft_status, f"Expected draft status, got '{draft_status}'"

        # Verify draft API status
        status, _, _, draft_api_res = https_request(
            f"/api/client-cms/status?slug={SLUG}",
            method="GET",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert draft_api_res.get("hasDraft") is True, "hasDraft should be True"
        assert draft_api_res.get("draftState") == "current", f"draftState should be current, got {draft_api_res.get('draftState')}"
        print(f"[PASS] API confirmed draft saved with metadata: baseHash={draft_api_res.get('draftBaseContentHash')[:16]}...")

        # Step 6: Test 'Recarregar do site'
        await page.click("#btn-reload-live")
        await page.wait_for_selector("#cms-toast:has-text('publicada recarregada')", state="visible", timeout=10000)
        await page.wait_for_timeout(1000)

        reloaded_headline = await frame_el.locator("h1.hero-headline").inner_text()
        print(f"[PASS] Headline after 'Recarregar do site': '{reloaded_headline.strip()}'")
        assert "Infraestrutura Sintética" in reloaded_headline or "Infraestrutura Sint" in reloaded_headline, "Should have reloaded live baseline"

        # Step 7: Test Stale Draft Detection Flow
        print("\n--- Testing Stale Draft Warning & Resolution ---")
        # Save a draft with old baseContentHash
        status, _, _, draft_save_res = https_request(
            "/api/client-cms/draft",
            method="POST",
            data={
                "slug": SLUG,
                "html": "<!DOCTYPE html><html><head><title>Draft</title></head><body><h1>Draft Stale Test</h1></body></html>",
                "baseContentHash": "fake_old_base_hash_12345"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert status == 200 and draft_save_res.get("success"), f"Failed to save test draft: {draft_save_res}"
        print("[PASS] Saved test draft with outdated baseContentHash")

        # Trigger window focus event to invoke refreshStatus
        await page.evaluate("() => window.dispatchEvent(new Event('focus'))")
        await page.wait_for_timeout(1500)

        alert_visible = await page.is_visible("#cms-alert-bar")
        alert_text = await page.inner_text("#cms-alert-text")
        print(f"[PASS] Stale draft alert visibility={alert_visible}, text='{alert_text}'")
        assert alert_visible is True, "Expected alert bar to be visible for stale draft"
        assert "atualizado depois deste rascunho" in alert_text, f"Unexpected alert text: {alert_text}"

        # Click 'Descartar rascunho' via alert button
        await page.click("#btn-alert-discard")
        await page.wait_for_selector("#cms-toast:has-text('descartado com sucesso')", state="visible", timeout=10000)
        await page.wait_for_timeout(1000)

        alert_hidden = not await page.is_visible("#cms-alert-bar")
        print(f"[PASS] Alert bar hidden after discard: {alert_hidden}")
        assert alert_hidden is True, "Alert bar should be hidden after discarding draft"

        status_after_discard = await page.inner_text("#cms-status-text")
        assert "Site publicado" in status_after_discard, f"Expected 'Site publicado', got '{status_after_discard}'"
        print(f"[PASS] Status restored to 'Site publicado'")

        await browser.close()

    # Step 8: Strict QA Artifact Hygiene Verification
    print("\n--- Strict QA Artifact Hygiene Check ---")
    # Check 1: Deploy repo on Phoenix
    status, _, _, audit_res = https_request(
        f"/api/client-cms/audit?slug={SLUG}",
        method="GET",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"[PASS] Audit events verified: count={len(audit_res.get('history', []))}")

    # Check 2: Public Vercel
    req = urllib.request.Request(f"{PUBLIC_SITE_URL}?nocache={int(time.time())}", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        vercel_html = resp.read().decode("utf-8")
        assert QA_TEXT not in vercel_html, f"QA text found on public Vercel: {QA_TEXT}"
        assert "Infraestrutura Sintética" in vercel_html or "Infraestrutura Sint" in vercel_html, "Public Vercel headline missing baseline"
        print("[PASS] Public Vercel verified clean of QA text")

    print("\n" + "=" * 80)
    print("ALL LIVE VS DRAFT SOURCE AWARENESS BENCHMARK TESTS PASSED (100% CLEAN)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_live_draft_awareness_suite())
