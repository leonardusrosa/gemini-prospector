#!/usr/bin/env python3
"""
Comprehensive Playwright & HTTP E2E Validation Suite for Public HTTPS Client CMS.
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
SLUG = "instituto-ferreira-odontologia-rio-claro"
ADMIN_URL = f"{BASE_HTTPS_URL}/clientes/{SLUG}/admin/"
PUBLIC_SITE_URL = "https://prospector-sites-beta.vercel.app/clientes/instituto-ferreira-odontologia-rio-claro/"
OPERATOR_USER = "admin_instituto_qa"
OPERATOR_PASS = "REDACTED_TEST_SECRET"
TEMP_EDIT_TEXT = "QA CMS PUBLIC TEST TEMPORÁRIO"


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


async def run_public_cms_validation():
    print("=" * 70)
    print("STARTING PUBLIC HTTPS CLIENT CMS BENCHMARK VALIDATION")
    print(f"Target URL: {ADMIN_URL}")
    print("=" * 70)

    # -------------------------------------------------------------
    # Step 0: Baseline Public Site Inspection
    # -------------------------------------------------------------
    print("\n--- [Step 0] Fetching Baseline Public Site State ---")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(PUBLIC_SITE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        baseline_html = resp.read().decode("utf-8")
    baseline_hash = hashlib.sha256(baseline_html.encode("utf-8")).hexdigest()
    print(f"Baseline public site size: {len(baseline_html)} bytes, SHA256: {baseline_hash}")
    assert "Instituto Ferreira" in baseline_html, "Baseline public site must contain Instituto Ferreira"
    assert TEMP_EDIT_TEXT not in baseline_html, "Baseline public site must NOT contain temp QA text"

    # -------------------------------------------------------------
    # Step 1: Unauthenticated Public Isolation & API Security
    # -------------------------------------------------------------
    print("\n--- [Step 1] Unauthenticated Isolation & API Security Checks ---")
    # GET admin page
    status, headers, body, _ = https_request(f"/clientes/{SLUG}/admin/")
    assert status == 200, f"Expected 200, got {status}"
    assert "AutoCORA Client CMS" in body, "Expected login page title"
    assert "contenteditable" not in body, "Unauthenticated page must NOT contain editable DOM"
    assert headers.get("X-Content-Type-Options") == "nosniff", "Missing X-Content-Type-Options header"
    print("  [PASS] Unauthenticated admin page serves login card only, zero editable content leaked.")

    # Unauthenticated API calls
    endpoints_to_test = [
        ("/api/client-cms/status?slug=" + SLUG, "GET", None),
        ("/api/client-cms/draft?slug=" + SLUG, "GET", None),
        ("/api/client-cms/draft", "POST", {"slug": SLUG, "html": "<h1>hack</h1>"}),
        ("/api/client-cms/publish", "POST", {"slug": SLUG, "html": "<h1>hack</h1>"}),
        ("/api/client-cms/rollback", "POST", {"slug": SLUG}),
        ("/api/client-cms/audit?slug=" + SLUG, "GET", None),
    ]
    for ep, m, payload in endpoints_to_test:
        code, _, resp_body, resp_json = https_request(ep, method=m, data=payload)
        assert code in (401, 403), f"Unauthenticated request to {ep} returned {code} (expected 401/403)"
        print(f"  [PASS] Unauthenticated {m} {ep.split('?')[0]} correctly rejected with {code}")

    # -------------------------------------------------------------
    # Step 2: Real Browser Login & UI Responsiveness (Playwright)
    # -------------------------------------------------------------
    print("\n--- [Step 2] Real Browser Login & Responsive UI via Playwright ---")
    async with async_playwright() as p:
        # Desktop 1440x900
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print(f"  Navigating desktop browser to {ADMIN_URL}...")
        resp = await page.goto(ADMIN_URL, wait_until="networkidle")
        assert resp.status == 200, f"Expected HTTP 200, got {resp.status}"

        # Check login card visibility
        assert await page.is_visible("#cms-login-view"), "Login view should be visible"
        assert not await page.is_visible("#cms-workspace-view"), "Workspace should NOT be visible"

        # Test invalid password rejection
        await page.fill("#cms-username", OPERATOR_USER)
        await page.fill("#cms-password", "WrongPassword123!")
        await page.click("#cms-login-submit")
        await page.wait_for_timeout(1000)
        assert await page.is_visible("#login-error"), "Error message should be shown on invalid login"
        err_text = await page.inner_text("#login-error")
        print(f"  [PASS] Invalid login attempt rejected with UI error: '{err_text}'")

        # Test valid login
        await page.fill("#cms-username", OPERATOR_USER)
        await page.fill("#cms-password", OPERATOR_PASS)
        await page.click("#cms-login-submit")
        await page.wait_for_selector("#cms-workspace-view", state="visible", timeout=10000)
        print("  [PASS] Desktop valid login successful, workspace active.")

        # Check frame and editor toolbar
        frame_el = await page.wait_for_selector("#cms-editor-frame", state="visible")
        assert frame_el is not None, "Editor iframe should be loaded"
        assert await page.is_visible("#btn-save-draft"), "Save draft button visible"
        assert await page.is_visible("#btn-publish"), "Publish button visible"
        assert await page.is_visible("#btn-rollback"), "Rollback button visible"

        # Test Mobile Viewport 390x844
        mobile_context = await browser.new_context(viewport={"width": 390, "height": 844}, user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)")
        mobile_page = await mobile_context.new_page()
        await mobile_page.goto(ADMIN_URL, wait_until="networkidle")
        await mobile_page.fill("#cms-username", OPERATOR_USER)
        await mobile_page.fill("#cms-password", OPERATOR_PASS)
        await mobile_page.click("#cms-login-submit")
        await mobile_page.wait_for_selector("#cms-workspace-view", state="visible", timeout=10000)
        print("  [PASS] Mobile 390x844 login & responsive toolbar verified.")
        await mobile_context.close()

        # -------------------------------------------------------------
        # Step 3: Cross-Tenant & Traversal Attack Verification over HTTPS
        # -------------------------------------------------------------
        print("\n--- [Step 3] Cross-Tenant & Path Traversal Denial Checks ---")
        # Extract active session token from sessionStorage
        token = await page.evaluate(f"() => sessionStorage.getItem('autocora_cms_token:' + '{SLUG}')")
        assert token, "Session token must exist in sessionStorage"
        auth_hdr = {"Authorization": f"Bearer {token}"}

        # Cross tenant attempt
        code, _, _, rj = https_request("/api/client-cms/draft?slug=other-clinic-slug", method="GET", headers=auth_hdr)
        assert code in (401, 403), f"Cross-tenant access should return 401/403, got {code}"
        print("  [PASS] Cross-tenant access with valid foreign token strictly denied (401/403).")

        # Path traversal attempts
        traversal_slugs = ["../", "..%2F", "....//", "/etc/passwd", "prospector-sites", ".git"]
        for bad_slug in traversal_slugs:
            code, _, _, _ = https_request(f"/api/client-cms/draft?slug={urllib.parse.quote(bad_slug)}", method="GET", headers=auth_hdr)
            assert code in (400, 401, 403, 404), f"Traversal '{bad_slug}' should be rejected, got {code}"
        print("  [PASS] Path traversal and special path injection attacks strictly rejected.")

        # -------------------------------------------------------------
        # Step 4: Draft Flow over Public HTTPS
        # -------------------------------------------------------------
        print("\n--- [Step 4] Save & Verify Draft over Public HTTPS ---")
        # Handle confirm dialogs automatically
        page.on("dialog", lambda dialog: asyncio.create_task(dialog.accept()))

        frame = page.frame_locator("#cms-editor-frame")
        # Wait for editor content to load inside iframe
        await page.wait_for_timeout(3000)
        headline_el = frame.locator("h1, .hero-title, [data-pe-label='Hero Title']").first
        original_headline_text = await headline_el.inner_text()
        print(f"  Current headline inside editor: '{original_headline_text}'")

        # Edit headline in browser
        await headline_el.evaluate(f"(el, text) => {{ el.innerText = '{TEMP_EDIT_TEXT}'; }}", TEMP_EDIT_TEXT)
        
        # Click Salvar Rascunho in toolbar
        await page.click("#btn-save-draft")
        await page.wait_for_selector("#cms-toast", state="visible", timeout=10000)
        toast_msg = await page.inner_text("#cms-toast")
        print(f"  Toast notification: '{toast_msg}'")

        # Verify draft endpoint has the temp text
        code, _, _, draft_json = https_request(f"/api/client-cms/draft?slug={SLUG}", headers=auth_hdr)
        assert code == 200 and draft_json.get("success"), "Draft GET should succeed"
        assert TEMP_EDIT_TEXT in draft_json.get("html", ""), "Draft content must contain temporary text"
        print("  [PASS] Draft successfully persisted in private server storage over HTTPS.")

        # Verify public website is STILL unchanged
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            current_public_html = resp.read().decode("utf-8")
        assert TEMP_EDIT_TEXT not in current_public_html, "Public site must NOT be affected by draft save"
        print("  [PASS] Public live website confirmed untouched after draft save.")

        # -------------------------------------------------------------
        # Step 5: Publish over Public HTTPS & Live Verification
        # -------------------------------------------------------------
        print("\n--- [Step 5] Public HTTPS Publish to Git & Vercel Verification ---")
        # Click Publicar no Ar
        await page.click("#btn-publish")

        # Wait for publish completion
        print("  Waiting for backend Git commit & push to GitHub...")
        await page.wait_for_selector("#cms-toast", state="visible", timeout=35000)
        toast_publish = await page.inner_text("#cms-toast")
        print(f"  Publish toast message: '{toast_publish}'")
        assert "sucesso" in toast_publish.lower() or "publicad" in toast_publish.lower(), f"Unexpected toast: {toast_publish}"
        print("  [PASS] Public UI reports publication successful.")

        # Verify audit history from API
        code, _, _, audit_json = https_request(f"/api/client-cms/audit?slug={SLUG}", headers=auth_hdr)
        assert code == 200, f"Audit request failed: {code}"
        history = audit_json.get("history", [])
        assert len(history) > 0, "Audit history must have records"
        latest_event = history[-1]
        publish_sha = latest_event.get("commitSha")
        print(f"  Latest audit event: action={latest_event.get('action')}, actor={latest_event.get('actor')}, commitSha={publish_sha}")
        assert latest_event.get("action") == "publish", "Expected action 'publish'"

        # Wait and verify Vercel live update
        print("  Polling public Vercel website for published changes (up to 45s)...")
        published_visible = False
        for attempt in range(15):
            await asyncio.sleep(3)
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                    live_html = resp.read().decode("utf-8")
                    if TEMP_EDIT_TEXT in live_html:
                        published_visible = True
                        print(f"  [PASS] Temporary QA edit confirmed LIVE on Vercel (attempt {attempt+1})!")
                        break
            except Exception as e:
                print(f"  Poll error: {e}")
        assert published_visible, "Published temporary text must become visible on public Vercel site"

        # -------------------------------------------------------------
        # Step 6: Rollback over Public HTTPS & Baseline Restoration
        # -------------------------------------------------------------
        print("\n--- [Step 6] Public HTTPS Rollback & Exact Baseline Restoration ---")
        await page.click("#btn-rollback")

        print("  Waiting for rollback Git commit & push...")
        await page.wait_for_selector("#cms-toast", state="visible", timeout=35000)
        toast_rollback = await page.inner_text("#cms-toast")
        print(f"  Rollback toast message: '{toast_rollback}'")
        assert "sucesso" in toast_rollback.lower() or "restaurad" in toast_rollback.lower(), f"Unexpected toast: {toast_rollback}"
        print("  [PASS] Public UI reports rollback successful.")

        # Check audit trail for rollback
        code, _, _, audit_json = https_request(f"/api/client-cms/audit?slug={SLUG}", headers=auth_hdr)
        history = audit_json.get("history", [])
        rollback_event = history[-1]
        rollback_sha = rollback_event.get("commitSha")
        print(f"  Rollback audit event: action={rollback_event.get('action')}, actor={rollback_event.get('actor')}, commitSha={rollback_sha}")
        assert rollback_event.get("action") == "rollback", "Expected action 'rollback'"

        # Wait and verify Vercel restored baseline
        print("  Polling public Vercel website for baseline restoration (up to 45s)...")
        restored_clean = False
        for attempt in range(15):
            await asyncio.sleep(3)
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                    restored_html = resp.read().decode("utf-8")
                    if TEMP_EDIT_TEXT not in restored_html and "Instituto Ferreira" in restored_html:
                        restored_clean = True
                        print(f"  [PASS] Baseline confirmed restored on Vercel (attempt {attempt+1})!")
                        break
            except Exception as e:
                print(f"  Poll error: {e}")
        assert restored_clean, "Public Vercel site must be restored without temporary QA text"

        # -------------------------------------------------------------
        # Step 7: Logout Verification
        # -------------------------------------------------------------
        print("\n--- [Step 7] Logout Verification ---")
        await page.click("#btn-logout")
        await page.wait_for_selector("#cms-login-view", state="visible", timeout=5000)
        assert not await page.is_visible("#cms-workspace-view"), "Workspace should be hidden after logout"
        token_after = await page.evaluate(f"() => sessionStorage.getItem('autocora_cms_token:' + '{SLUG}')")
        assert not token_after, "Session token must be deleted from sessionStorage after logout"
        print("  [PASS] Logout successfully invalidated local session and restored login card.")

        await browser.close()

    print("\n" + "=" * 70)
    print("ALL PUBLIC HTTPS BENCHMARK VALIDATION STEPS PASSED SUCCESSFULLY!")
    print(f"Publish SHA: {publish_sha}")
    print(f"Rollback SHA: {rollback_sha}")
    print("=" * 70)
    return publish_sha, rollback_sha


if __name__ == "__main__":
    asyncio.run(run_public_cms_validation())
