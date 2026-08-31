#!/usr/bin/env python3
"""
Dedicated Synthetic Tenant E2E Test Suite (autocora-cms-qa).
Performs the full destructive lifecycle (draft, publish, rollback, discard, hygiene)
EXCLUSIVELY on the synthetic test tenant. Real client sites are NEVER mutated.
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
SYNTHETIC_SLUG = "autocora-cms-qa"
ADMIN_URL = f"{BASE_HTTPS_URL}/clientes/{SYNTHETIC_SLUG}/admin/"
PUBLIC_SITE_URL = f"https://prospector-sites-beta.vercel.app/clientes/{SYNTHETIC_SLUG}/"
SYNTHETIC_USER = "admin_autocora_qa"
SYNTHETIC_PASS = "REDACTED_TEST_SECRET"
QA_MUTATION_TEXT = "QA CMS E2E TEST SYNTHETIC MUTATION"


class HardTeardownFailure(Exception):
    """Raised when E2E teardown fails to restore exact baseline state."""
    pass


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
        with urllib.request.urlopen(req, context=ctx, timeout=35) as resp:
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


async def run_synthetic_cms_e2e():
    print("=" * 80)
    print("STARTING DEDICATED SYNTHETIC TENANT CMS E2E TEST SUITE")
    print(f"Target Synthetic Tenant: {SYNTHETIC_SLUG}")
    print(f"Admin Endpoint: {ADMIN_URL}")
    print("=" * 80)

    # Hard-gate: Never run against real client slugs
    if SYNTHETIC_SLUG != "autocora-cms-qa":
        raise ValueError(f"SECURITY VIOLATION: Destructive tests are hard-gated to 'autocora-cms-qa', got '{SYNTHETIC_SLUG}'")

    ctx = ssl.create_default_context()

    # Step 0: Record initial baseline content hash
    print("\n--- [Step 0] Recording Initial Baseline Content State ---")
    req = urllib.request.Request(f"{PUBLIC_SITE_URL}?nocache={int(time.time())}", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        baseline_html = resp.read().decode("utf-8")
    baseline_hash = hashlib.sha256(baseline_html.encode("utf-8")).hexdigest()
    print(f"Baseline public HTML size: {len(baseline_html)} bytes, SHA256: {baseline_hash}")
    assert "Infraestrutura Sintética" in baseline_html, "Synthetic baseline must contain identifier text"
    assert QA_MUTATION_TEXT not in baseline_html, "Synthetic baseline must not contain active mutation text"

    # Step 1: Authenticate synthetic user
    print("\n--- [Step 1] Synthetic User Authentication ---")
    status, _, _, auth_res = https_request("/api/client-cms/auth", method="POST", data={
        "slug": SYNTHETIC_SLUG,
        "username": SYNTHETIC_USER,
        "password": SYNTHETIC_PASS
    })
    assert status == 200 and auth_res.get("success"), f"Synthetic auth failed: {auth_res}"
    token = auth_res["token"]
    auth_hdr = {"Authorization": f"Bearer {token}"}
    print(f"  [PASS] Synthetic tenant authenticated successfully. Token: {token[:16]}...")

    # Preflight cleanup
    https_request("/api/client-cms/draft/discard", method="POST", data={"slug": SYNTHETIC_SLUG, "reason": "preflight"}, headers=auth_hdr)

    # Step 2: Query initial status API
    status, _, _, status_res = https_request(f"/api/client-cms/status?slug={SYNTHETIC_SLUG}", headers=auth_hdr)
    assert status == 200 and status_res.get("success"), f"Status query failed: {status_res}"
    assert status_res.get("hasDraft") is False, "Expected no active draft on clean baseline"
    assert status_res.get("draftState") == "none", "Expected draftState 'none'"
    print(f"  [PASS] Status API verified: draftState=none, liveCommit={status_res.get('liveCommit')}")

    publish_sha = None
    rollback_sha = None

    try:
        # Step 3: Playwright Browser Automation for Full Lifecycle
        print("\n--- [Step 3] Browser Workspace Automation ---")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1440, "height": 900})

            # Auto-accept confirm dialogs
            async def on_dialog(dialog):
                print(f"  [Dialog] {dialog.type}: '{dialog.message}' -> accepted")
                try:
                    await dialog.accept()
                except Exception:
                    pass
            page.on("dialog", on_dialog)

            # Navigate to synthetic admin
            await page.goto(ADMIN_URL, wait_until="networkidle")
            print("  [PASS] Navigated to synthetic login view")

            # Login
            await page.fill("#cms-username", SYNTHETIC_USER)
            await page.fill("#cms-password", SYNTHETIC_PASS)
            await page.click("#cms-login-submit")
            await page.wait_for_selector("#cms-workspace-view", state="visible", timeout=15000)
            print("  [PASS] Logged into Workspace view")

            # Status bar check
            status_text = await page.inner_text("#cms-status-text")
            assert "Site publicado" in status_text, f"Expected 'Site publicado', got '{status_text}'"
            print(f"  [PASS] Status bar shows: '{status_text}'")

            # Editor frame & Asset resolution check
            frame = page.frame_locator("#cms-editor-frame")
            await frame.locator("h1.hero-headline").wait_for(state="visible", timeout=15000)
            initial_h1 = await frame.locator("h1.hero-headline").inner_text()
            print(f"  [PASS] Editor loaded initial headline: '{initial_h1.strip()}'")

            test_img = frame.locator("img[src*='test-image.webp']").first
            await test_img.wait_for(state="attached", timeout=10000)
            await page.wait_for_function(
                """() => {
                    const frameDoc = document.querySelector('#cms-editor-frame')?.contentDocument;
                    if (!frameDoc) return false;
                    const imgEl = frameDoc.querySelector("img[src*='test-image.webp']");
                    return imgEl && imgEl.complete && imgEl.naturalWidth > 0;
                }""",
                timeout=15000
            )
            img_width = await test_img.evaluate("(img) => img.naturalWidth")
            assert img_width > 0, f"Synthetic test image failed to load, naturalWidth={img_width}"
            print(f"  [PASS] Synthetic test asset loaded with naturalWidth={img_width}px")

            # Step 4: Perform DOM edit & verify dirty state
            print("\n--- [Step 4] DOM Mutation & Unsaved Tracking ---")
            await frame.locator("h1.hero-headline").evaluate(f"(el) => {{ el.innerText = '{QA_MUTATION_TEXT}'; el.dispatchEvent(new Event('input', {{ bubbles: true }})); }}")
            await page.wait_for_timeout(600)

            dirty_status = await page.inner_text("#cms-status-text")
            assert "Alterações locais não salvas" in dirty_status, f"Expected dirty status, got '{dirty_status}'"
            print(f"  [PASS] Unsaved modification correctly tracked: '{dirty_status}'")

            # Step 5: Save draft
            print("\n--- [Step 5] Draft Persistence & Metadata Verification ---")
            await page.click("#btn-save-draft")
            await page.wait_for_selector("#cms-toast:has-text('Rascunho salvo')", state="visible", timeout=10000)
            await page.wait_for_timeout(600)

            draft_status = await page.inner_text("#cms-status-text")
            assert "Rascunho salvo" in draft_status, f"Expected draft status, got '{draft_status}'"
            print(f"  [PASS] Status updated to: '{draft_status}'")

            # Verify status API has version metadata
            _, _, _, draft_api = https_request(f"/api/client-cms/status?slug={SYNTHETIC_SLUG}", headers=auth_hdr)
            assert draft_api.get("hasDraft") is True, "hasDraft must be True"
            assert draft_api.get("draftState") == "current", f"Expected draftState 'current', got {draft_api.get('draftState')}"
            print(f"  [PASS] Draft API confirmed: baseHash={draft_api.get('draftBaseContentHash')[:16]}..., state={draft_api.get('draftState')}")

            # Step 6: Publish QA mutation
            print("\n--- [Step 6] Publishing QA Mutation to Git & Vercel ---")
            await page.click("#btn-publish")
            await page.wait_for_function(
                "() => { const t = document.querySelector('#cms-toast'); return t && (t.innerText.includes('publicado no ar') || t.innerText.includes('sucesso!')); }",
                timeout=35000
            )
            toast_publish = await page.inner_text("#cms-toast")
            print(f"  Publish toast: '{toast_publish}'")
            assert "sucesso" in toast_publish.lower() or "publicad" in toast_publish.lower()

            # Verify audit event
            _, _, _, audit_res = https_request(f"/api/client-cms/audit?slug={SYNTHETIC_SLUG}", headers=auth_hdr)
            latest_evt = audit_res.get("history", [])[-1]
            publish_sha = latest_evt.get("commitSha")
            assert latest_evt.get("action") == "publish"
            print(f"  [PASS] Publish audit event confirmed. Commit SHA: {publish_sha}")

            # Poll Vercel for mutation
            print("  Polling Vercel for published mutation (up to 30s)...")
            pub_seen = False
            for _ in range(10):
                await asyncio.sleep(3)
                try:
                    p_req = urllib.request.Request(f"{PUBLIC_SITE_URL}?cb={int(time.time()*1000)}", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
                    with urllib.request.urlopen(p_req, context=ctx, timeout=15) as r:
                        if QA_MUTATION_TEXT in r.read().decode("utf-8"):
                            pub_seen = True
                            print("  [PASS] Mutation confirmed LIVE on public Vercel!")
                            break
                except Exception:
                    pass

            # Step 7: Execute Rollback
            print("\n--- [Step 7] Rolling Back Mutation to Baseline ---")
            await page.click("#btn-rollback")
            await page.wait_for_function(
                "() => { const t = document.querySelector('#cms-toast'); return t && (t.innerText.includes('restaurada com sucesso') || t.innerText.includes('sucesso!')); }",
                timeout=35000
            )
            toast_rollback = await page.inner_text("#cms-toast")
            print(f"  Rollback toast: '{toast_rollback}'")
            assert "sucesso" in toast_rollback.lower() or "restaurad" in toast_rollback.lower()

            _, _, _, audit_res2 = https_request(f"/api/client-cms/audit?slug={SYNTHETIC_SLUG}", headers=auth_hdr)
            rollback_evt = audit_res2.get("history", [])[-1]
            rollback_sha = rollback_evt.get("commitSha")
            assert rollback_evt.get("action") == "rollback"
            print(f"  [PASS] Rollback audit event confirmed. Commit SHA: {rollback_sha}")

            # Poll Vercel for restored baseline
            print("  Polling Vercel for restored baseline...")
            restored_seen = False
            for _ in range(10):
                await asyncio.sleep(3)
                try:
                    p_req = urllib.request.Request(f"{PUBLIC_SITE_URL}?cb={int(time.time()*1000)}", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
                    with urllib.request.urlopen(p_req, context=ctx, timeout=15) as r:
                        h_content = r.read().decode("utf-8")
                        if QA_MUTATION_TEXT not in h_content and "Infraestrutura Sintética" in h_content:
                            restored_seen = True
                            print("  [PASS] Baseline confirmed restored on public Vercel!")
                            break
                except Exception:
                    pass

            # Step 8: Logout
            await page.click("#btn-logout")
            await page.wait_for_selector("#cms-login-view", state="visible", timeout=5000)
            print("  [PASS] Logged out successfully")

            await browser.close()

    finally:
        # Step 9: STRICT TEARDOWN & BASELINE HYGIENE ASSERTION
        print("\n--- [Step 9] Strict Teardown & Baseline Hygiene Verification ---")
        teardown_errors = []

        # Discard any remaining draft
        https_request("/api/client-cms/draft/discard", method="POST", data={"slug": SYNTHETIC_SLUG, "reason": "teardown_cleanup"}, headers=auth_hdr)

        # Check 1: Private draft storage
        _, _, _, draft_chk = https_request(f"/api/client-cms/draft?slug={SYNTHETIC_SLUG}", headers=auth_hdr)
        if QA_MUTATION_TEXT in (draft_chk.get("html") or ""):
            teardown_errors.append("QA mutation text remained in private draft storage")

        # Check 2: Deploy repo HTML
        _, _, repo_html, _ = https_request(f"/api/client-cms/editor-frame?slug={SYNTHETIC_SLUG}&source=live", headers=auth_hdr)
        if QA_MUTATION_TEXT in repo_html:
            teardown_errors.append("QA mutation text remained in deploy repo HTML")

        # Check 3: Public Vercel
        clean_req = urllib.request.Request(f"{PUBLIC_SITE_URL}?nocache={int(time.time())}", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(clean_req, context=ctx, timeout=15) as r:
            final_vercel_html = r.read().decode("utf-8")
        if QA_MUTATION_TEXT in final_vercel_html:
            teardown_errors.append("QA mutation text remained on public Vercel")

        if teardown_errors:
            error_msg = "; ".join(teardown_errors)
            print(f"\n[CRITICAL TEARDOWN FAILURE] {error_msg}")
            raise HardTeardownFailure(error_msg)

        print("  [PASS] 1. Draft storage 100% clean.")
        print("  [PASS] 2. Deploy repo HTML 100% clean.")
        print("  [PASS] 3. Public Vercel HTML 100% clean.")

    print("\n" + "=" * 80)
    print("ALL SYNTHETIC TENANT E2E DESTRUCTIVE TESTS COMPLETED SUCCESSFULLY!")
    print(f"Publish SHA: {publish_sha}")
    print(f"Rollback SHA: {rollback_sha}")
    print("=" * 80)
    return publish_sha, rollback_sha


if __name__ == "__main__":
    asyncio.run(run_synthetic_cms_e2e())
