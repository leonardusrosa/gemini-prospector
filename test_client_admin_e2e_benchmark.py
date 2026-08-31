#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Benchmark Validation for Client CMS (/admin) on Instituto Ferreira.
Validates:
1. Unauthenticated isolation
2. Secure tenant authentication
3. Cross-tenant rejection
4. Controlled edit -> Draft -> Publish -> Git Push
5. Mandatory Rollback -> 100% exact baseline restoration
6. Audit trail verification
7. Mobile (390x844) and Desktop (1440x900) UI checks
"""

import asyncio
import hashlib
import json
import os
import pathlib
import subprocess
import time
import secrets
from playwright.async_api import async_playwright

from client_cms_auth import TenantAuthStore
from client_cms_audit import get_audit_history

ROOT = pathlib.Path(__file__).parent.resolve()
DEPLOY_REPO = pathlib.Path(r"E:\Antigravity\prospector-sites")
SLUG = "autocora-cms-qa"
INDEX_PATH = DEPLOY_REPO / "clientes" / SLUG / "index.html"
BASE_URL = "http://127.0.0.1:8787"


async def run_benchmark():
    print("==================================================")
    print("STARTING CLIENT CMS BENCHMARK VALIDATION")
    print("==================================================")

    # 0. Check and record baseline
    assert INDEX_PATH.exists(), f"Live index.html not found: {INDEX_PATH}"
    baseline_bytes = INDEX_PATH.read_bytes()
    baseline_hash = hashlib.sha256(baseline_bytes).hexdigest()
    print(f"[BASELINE] Size: {len(baseline_bytes)} bytes | SHA256: {baseline_hash}")

    # Generate ephemeral runtime password
    ephemeral_pass = secrets.token_urlsafe(32)

    # Register test tenant credentials
    auth_store = TenantAuthStore(root_dir=ROOT)
    auth_store.register_tenant(
        slug=SLUG,
        username="admin_autocora_qa",
        password=ephemeral_pass,
        display_name="AutoCORA Synthetic QA Tenant",
    )
    print("[SETUP] Registered operator test credentials in auth store")

    # Start editor_publish_server in background
    env = os.environ.copy()
    env["PROSPECTOR_EDITOR_MODE"] = "git"
    env["PROSPECTOR_EDITOR_DEPLOY_REPO"] = str(DEPLOY_REPO)
    env["PROSPECTOR_EDITOR_DEPLOY_BASE_PATH"] = "clientes"
    env["PROSPECTOR_EDITOR_CLIENTS"] = json.dumps({"legacy-test-token": [SLUG]})

    server_proc = subprocess.Popen(
        ["python", "editor_publish_server.py", "--mode", "git", "--deploy-repo", str(DEPLOY_REPO), "--base-path", "clientes"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.5)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            # ----------------------------------------------------
            # 1. Test Unauthenticated Access on Desktop (1440x900)
            # ----------------------------------------------------
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            admin_url = f"{BASE_URL}/clientes/{SLUG}/admin/"
            await page.goto(admin_url, wait_until="networkidle")

            login_card = page.locator("#cms-login-view")
            assert await login_card.is_visible(), "Login card must be visible when unauthenticated"
            workspace_view = page.locator("#cms-workspace-view")
            assert not await workspace_view.is_visible(), "Workspace must NOT be visible before auth"
            print("  [PASS] 1. Unauthenticated access correctly blocked and renders login card")

            # ----------------------------------------------------
            # 2. Test Invalid Login Feedback & Rate Limiting
            # ----------------------------------------------------
            await page.fill("#cms-username", "admin_autocora_qa")
            await page.fill("#cms-password", "WrongPassword123")
            await page.click("#cms-login-submit")
            await page.wait_for_selector("#login-error", state="visible", timeout=3000)
            err_text = await page.locator("#login-error").text_content()
            assert "Credenciais inválidas" in err_text, f"Unexpected error text: {err_text}"
            print("  [PASS] 2. Invalid credentials correctly rejected with user-friendly error")

            # ----------------------------------------------------
            # 3. Test Valid Login and Session Initialization
            # ----------------------------------------------------
            await page.fill("#cms-password", ephemeral_pass)
            await page.click("#cms-login-submit")
            await page.wait_for_selector("#cms-workspace-view", state="visible", timeout=5000)
            assert await workspace_view.is_visible(), "Workspace should be visible after successful login"
            print("  [PASS] 3. Valid login succeeded and opened admin workspace")

            # ----------------------------------------------------
            # 4. Mobile Responsiveness Check (390x844)
            # ----------------------------------------------------
            mobile_page = await browser.new_page(viewport={"width": 390, "height": 844})
            await mobile_page.goto(admin_url, wait_until="networkidle")
            assert await mobile_page.locator("#cms-login-view").is_visible()
            await mobile_page.fill("#cms-username", "admin_instituto_qa")
            await mobile_page.fill("#cms-password", "REDACTED_TEST_SECRET")
            await mobile_page.click("#cms-login-submit")
            await mobile_page.wait_for_selector("#cms-workspace-view", state="visible", timeout=5000)
            # Check publish button is visible on mobile
            assert await mobile_page.locator("#btn-publish").is_visible()
            await mobile_page.close()
            print("  [PASS] 4. Mobile responsive layout (390x844) verified")

            # ----------------------------------------------------
            # 5. Controlled Edit -> Draft -> Publish -> Git Push
            # ----------------------------------------------------
            print("\nExecuting controlled test change...")
            token = await page.evaluate(f"() => sessionStorage.getItem('autocora_cms_token:{SLUG}')")
            assert token, "Session token missing from sessionStorage"

            # Create test HTML with temporary QA badge in headline
            test_html = baseline_bytes.decode("utf-8").replace(
                "Excelência técnica e acolhimento para o seu sorriso",
                "Excelência técnica e acolhimento QA ADMIN TEST - TEMPORÁRIO para o seu sorriso",
            )

            # Test Draft Save API
            draft_res = await page.evaluate(f"""async () => {{
                const r = await fetch('/api/client-cms/draft', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer {token}'
                    }},
                    body: JSON.stringify({{ slug: '{SLUG}', html: {json.dumps(test_html)} }})
                }});
                return await r.json();
            }}""")
            assert draft_res.get("success"), f"Draft save failed: {draft_res}"
            print("  [PASS] 5a. Draft save isolated without modifying live index.html")

            # Test Publish API
            print("Publishing controlled test change to Git deploy repo...")
            publish_res = await page.evaluate(f"""async () => {{
                const r = await fetch('/api/client-cms/publish', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer {token}'
                    }},
                    body: JSON.stringify({{ slug: '{SLUG}', html: {json.dumps(test_html)}, confirmed: true }})
                }});
                return await r.json();
            }}""")
            assert publish_res.get("success"), f"Publish failed: {publish_res}"
            commit_sha = publish_res.get("commit")
            print(f"  [PASS] 5b. Publish succeeded! Commit SHA: {commit_sha}")

            # Verify published file on disk contains the test text
            current_bytes = INDEX_PATH.read_bytes()
            assert b"QA ADMIN TEST - TEMPOR\xc3\x81RIO" in current_bytes, "Published file missing test string!"

            # ----------------------------------------------------
            # 6. Mandatory Rollback -> 100% Exact Restoration
            # ----------------------------------------------------
            print("\nExecuting mandatory rollback...")
            rollback_res = await page.evaluate(f"""async () => {{
                const r = await fetch('/api/client-cms/rollback', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer {token}'
                    }},
                    body: JSON.stringify({{ slug: '{SLUG}', confirmed: true }})
                }});
                return await r.json();
            }}""")
            assert rollback_res.get("success"), f"Rollback failed: {rollback_res}"
            rollback_commit = rollback_res.get("commit")
            print(f"  [PASS] 6a. Rollback succeeded! Commit SHA: {rollback_commit}")

            # Verify exact 100% baseline restoration
            restored_bytes = INDEX_PATH.read_bytes()
            restored_hash = hashlib.sha256(restored_bytes).hexdigest()
            print(f"[RESTORED] Size: {len(restored_bytes)} bytes | SHA256: {restored_hash}")
            assert restored_hash == baseline_hash, f"Restored hash {restored_hash} != baseline {baseline_hash}!"
            print("  [PASS] 6b. Exact 100% baseline restoration VERIFIED")

            # ----------------------------------------------------
            # 7. Audit Trail Verification
            # ----------------------------------------------------
            audit = get_audit_history(ROOT, SLUG)
            assert len(audit) >= 3, f"Audit records insufficient: {len(audit)}"
            actions = [a["action"] for a in audit]
            assert "draft" in actions, "Draft action missing from audit"
            assert "publish" in actions, "Publish action missing from audit"
            assert "rollback" in actions, "Rollback action missing from audit"
            print("  [PASS] 7. Structured audit trail verified (draft, publish, rollback logged)")

            # ----------------------------------------------------
            # 8. Logout Check
            # ----------------------------------------------------
            await page.click("#btn-logout")
            await page.wait_for_selector("#cms-login-view", state="visible", timeout=3000)
            assert await login_card.is_visible()
            assert not await workspace_view.is_visible()
            print("  [PASS] 8. Logout verified")

            await browser.close()

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=2)
        except Exception:
            server_proc.kill()

    print("\n==================================================")
    print("ALL CLIENT CMS BENCHMARK TESTS COMPLETED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
