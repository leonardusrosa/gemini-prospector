#!/usr/bin/env python3
"""
Dedicated Client Production Smoke Test Suite (Strictly READ-ONLY).
Runs non-mutating smoke checks against real client production deployments:
- Login authentication & invalid credential rejection
- Public site integrity & zero QA marker assertions
- Editor frame rendering & base URI injection
- Complete media asset HTTP 200 & natural dimension verification
- Status API and cross-tenant isolation enforcement
- NO CONTENT MUTATIONS, NO DRAFTS, NO PUBLISHING, NO ROLLBACK.
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

import os
import pathlib

BASE_HTTPS_URL = "https://prospector.autocora.com.br"
CLIENT_SLUG = "instituto-ferreira-odontologia-rio-claro"
ADMIN_URL = f"{BASE_HTTPS_URL}/clientes/{CLIENT_SLUG}/admin/"
PUBLIC_SITE_URL = f"https://prospector-sites-beta.vercel.app/clientes/{CLIENT_SLUG}/"


def require_env(name: str) -> str:
    """Reads credential strictly from env vars or private chmod 600 env files. Fails closed if missing."""
    val = os.environ.get(name)
    if val:
        return val.strip()

    # Fallback to private local/system env file (ignored by Git)
    for p in [pathlib.Path(".env.test.local"), pathlib.Path("/etc/prospector-cms-test.env"), pathlib.Path.home() / ".prospector-cms-test.env"]:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith(f"{name}="):
                        return line.split("=", 1)[1].strip()
            except Exception:
                pass

    raise RuntimeError(f"Required private test credential missing: {name}")


CLIENT_USER = require_env("PROSPECTOR_SMOKE_INSTITUTO_USERNAME")
CLIENT_PASS = require_env("PROSPECTOR_SMOKE_INSTITUTO_PASSWORD")

FORBIDDEN_QA_MARKERS = [
    "QA CMS",
    "TEST TEMPORÁRIO",
    "TEST TEMPORARIO",
    "E2E TEST",
    "QA TEST",
    "SYNTHETIC MUTATION",
]

EXPECTED_MEDIA_ASSETS = [
    "logo.png",
    "hero-ferreira-mobile.webp",
    "recepcao.webp",
    "cirurgico-raiox.webp",
    "odontopediatria.webp",
    "consultorio.webp",
    "esterilizacao.webp",
    "fachada.webp",
    "dr-cassio.webp",
]


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


async def run_client_production_smoke():
    print("=" * 80)
    print("STARTING READ-ONLY CLIENT PRODUCTION SMOKE TEST")
    print(f"Target Client: {CLIENT_SLUG}")
    print(f"Public URL: {PUBLIC_SITE_URL}")
    print(f"Admin URL: {ADMIN_URL}")
    print("DIRECTIVE: STRICTLY READ-ONLY (ZERO CONTENT MUTATIONS)")
    print("=" * 80)

    ctx = ssl.create_default_context()

    # Step 1: Public live website verification
    print("\n--- [Step 1] Public Live Website Smoke Check ---")
    req = urllib.request.Request(f"{PUBLIC_SITE_URL}?nocache={int(time.time())}", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        public_html = resp.read().decode("utf-8")
        pub_status = resp.status

    assert pub_status == 200, f"Public site returned HTTP {pub_status}"
    assert "Instituto Ferreira" in public_html, "Public site missing business brand name"
    assert "Dr. Cássio" in public_html or "Dr. Cssio" in public_html, "Public site missing technical director name"

    for marker in FORBIDDEN_QA_MARKERS:
        assert marker not in public_html, f"FORBIDDEN QA marker '{marker}' detected on public client site!"
    print("  [PASS] Public live site returns 200 OK with authentic client copy and ZERO QA markers.")

    # Step 2: Unauthenticated admin isolation & security headers
    print("\n--- [Step 2] Unauthenticated Isolation & Security Headers ---")
    status, headers, body, _ = https_request(f"/clientes/{CLIENT_SLUG}/admin/")
    assert status == 200, f"Admin login returned status {status}"
    assert "AutoCORA Client CMS" in body, "Expected Client CMS login portal"
    assert "contenteditable" not in body, "Unauthenticated portal must not leak editable DOM"
    assert headers.get("X-Content-Type-Options") == "nosniff", "Missing nosniff header"
    print("  [PASS] Unauthenticated admin portal serves login card only, zero leakage.")

    # Step 3: Authentication verification
    print("\n--- [Step 3] Authentication & Credential Validation ---")
    # Invalid password check
    code, _, _, bad_auth = https_request("/api/client-cms/auth", method="POST", data={
        "slug": CLIENT_SLUG,
        "username": CLIENT_USER,
        "password": "WrongPassword2026!"
    })
    assert code == 401 and not bad_auth.get("success"), f"Expected 401 for wrong password, got {code}"
    print("  [PASS] Invalid credentials properly rejected (401).")

    # Valid login check
    code, _, _, auth_res = https_request("/api/client-cms/auth", method="POST", data={
        "slug": CLIENT_SLUG,
        "username": CLIENT_USER,
        "password": CLIENT_PASS
    })
    assert code == 200 and auth_res.get("success"), f"Valid authentication failed: {auth_res}"
    token = auth_res["token"]
    auth_hdr = {"Authorization": f"Bearer {token}"}
    print("  [PASS] Authentication succeeded.")

    # Step 4: Status API & Source State Verification
    print("\n--- [Step 4] Status API & Source State Verification ---")
    code, _, _, status_res = https_request(f"/api/client-cms/status?slug={CLIENT_SLUG}", headers=auth_hdr)
    assert code == 200 and status_res.get("success"), f"Status API failed: {status_res}"
    assert status_res.get("authorized") is True, "Status must confirm authorized session"
    assert status_res.get("hasDraft") is False, "Production client site must not have unapproved draft"
    assert status_res.get("draftState") == "none", f"Expected draftState 'none', got {status_res.get('draftState')}"
    assert status_res.get("liveCommit"), "liveCommit must be non-empty"
    assert status_res.get("liveContentHash"), "liveContentHash must be non-empty"
    print(f"  [PASS] Status API verified: draftState={status_res.get('draftState')}, liveCommit={status_res.get('liveCommit')[:12]}...")

    # Step 5: Editor frame & Injected Base URI verification
    print("\n--- [Step 5] Editor Frame & Base URI Verification ---")
    code, _, frame_html, _ = https_request(f"/api/client-cms/editor-frame?slug={CLIENT_SLUG}&source=live", headers=auth_hdr)
    assert code == 200, f"Editor frame request failed: {code}"
    expected_base_href = f"https://prospector-sites-beta.vercel.app/clientes/{CLIENT_SLUG}/"
    assert f'href="{expected_base_href}"' in frame_html, f"Missing or incorrect base tag in editor frame: expected {expected_base_href}"
    for marker in FORBIDDEN_QA_MARKERS:
        assert marker not in frame_html, f"FORBIDDEN QA marker '{marker}' found in editor frame HTML!"
    print(f"  [PASS] Editor frame contains clean HTML with valid base tag: {expected_base_href}")

    # Step 6: Cross-Tenant Isolation Enforcement
    print("\n--- [Step 6] Cross-Tenant Isolation Denial Checks ---")
    code, _, _, cross_status = https_request("/api/client-cms/status?slug=autocora-cms-qa", headers=auth_hdr)
    assert code in (401, 403), f"Cross-tenant status request should be denied (401/403), got {code}"
    code, _, _, cross_frame = https_request("/api/client-cms/editor-frame?slug=autocora-cms-qa&source=live", headers=auth_hdr)
    assert code in (401, 403), f"Cross-tenant editor-frame request should be denied (401/403), got {code}"
    print("  [PASS] Cross-tenant access strictly denied with 401/403.")

    # Step 7: Browser UI & Media Asset Verification via Playwright
    print("\n--- [Step 7] Browser UI & Media Asset Verification (Playwright) ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        await page.goto(ADMIN_URL, wait_until="networkidle")
        await page.fill("#cms-username", CLIENT_USER)
        await page.fill("#cms-password", CLIENT_PASS)
        await page.click("#cms-login-submit")
        await page.wait_for_selector("#cms-workspace-view", state="visible", timeout=15000)
        print("  [PASS] Desktop browser logged in to client workspace.")

        # Check status indicator in UI
        status_text = await page.inner_text("#cms-status-text")
        assert "Site publicado" in status_text, f"Expected 'Site publicado', got '{status_text}'"
        print(f"  [PASS] Workspace status indicator confirms: '{status_text}'")

        # Frame asset resolution check
        frame = page.frame_locator("#cms-editor-frame")
        await frame.locator("h1.hero-headline").wait_for(state="visible", timeout=15000)
        rendered_headline = await frame.locator("h1.hero-headline").inner_text()
        assert "Excelência técnica" in rendered_headline, f"Unexpected headline rendered: {rendered_headline}"
        for marker in FORBIDDEN_QA_MARKERS:
            assert marker not in rendered_headline, f"QA marker in headline: {rendered_headline}"
        print(f"  [PASS] Rendered headline: '{rendered_headline.strip()}'")

        # Verify all media assets inside iframe
        print("  Verifying all client media assets load with HTTP 200 & natural dimensions...")
        for asset in EXPECTED_MEDIA_ASSETS:
            img_loc = frame.locator(f"img[src*='{asset}']").first
            await img_loc.wait_for(state="attached", timeout=10000)
            await page.wait_for_function(
                f"""() => {{
                    const frameDoc = document.querySelector('#cms-editor-frame')?.contentDocument;
                    if (!frameDoc) return false;
                    const imgEl = frameDoc.querySelector("img[src*='{asset}']");
                    return imgEl && imgEl.complete && imgEl.naturalWidth > 0;
                }}""",
                timeout=15000
            )
            dims = await img_loc.evaluate("img => ({ width: img.naturalWidth, height: img.naturalHeight, complete: img.complete, src: img.currentSrc || img.src })")
            print(f"    - Asset '{asset}': resolved='{dims['src']}', naturalWidth={dims['width']}px, naturalHeight={dims['height']}px [200 OK]")

        # Mobile viewport check
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(1000)
        hero_mobile = frame.locator("img[src*='hero-ferreira-mobile.webp']").first
        m_dims = await hero_mobile.evaluate("img => ({ width: img.naturalWidth, height: img.naturalHeight, complete: img.complete })")
        assert m_dims["complete"] and m_dims["width"] > 0, f"Mobile hero asset failed: {m_dims}"
        print(f"  [PASS] Mobile viewport (390x844) verified with responsive media rendering.")

        # Logout
        await page.click("#btn-logout")
        await page.wait_for_selector("#cms-login-view", state="visible", timeout=5000)
        print("  [PASS] Logged out cleanly.")

        await browser.close()

    print("\n" + "=" * 80)
    print(f"CLIENT PRODUCTION SMOKE TEST PASSED (100% READ-ONLY, ZERO MUTATIONS)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_client_production_smoke())
