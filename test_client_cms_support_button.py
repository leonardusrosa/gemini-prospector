#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression test suite for Global Client CMS WhatsApp Support button."""

import os
import re
import json
import pathlib
import pytest
import subprocess
import time
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent.resolve()

def load_test_env():
    env_file = ROOT / ".env.test.local"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_test_env()

def test_template_support_button_contract():
    """Test Section 9A: Template contract for support button."""
    tpl_paths = [
        ROOT / "prospector-de-sites" / "client_admin_template.html",
        ROOT / "client_admin_template.html",
    ]
    for tpl_path in tpl_paths:
        assert tpl_path.is_file(), f"Template not found at {tpl_path}"
        html = tpl_path.read_text(encoding="utf-8")

        # 1. Element exists as anchor
        assert '<a id="btn-support"' in html, "Anchor #btn-support must exist in template"
        
        # 2. Text 'Suporte'
        assert '<span>Suporte</span>' in html, "Span with text 'Suporte' must exist"
        
        # 3. Target and rel attributes
        assert 'target="_blank"' in html
        assert 'rel="noopener noreferrer"' in html
        
        # 4. Accessibility
        assert 'aria-label="Falar com o suporte pelo WhatsApp"' in html
        assert 'aria-hidden="true"' in html
        assert '<svg' in html
        
        # 5. Zero hard-coded wa.me or phone numbers in template
        assert "wa.me/" not in html, "Found hardcoded wa.me URL in static template!"
        raw_phone = os.environ.get("PROSPECTOR_CMS_SUPPORT_WHATSAPP", "").strip()
        if raw_phone:
            digits = re.sub(r"\D", "", raw_phone)
            assert digits not in html, "Found configured operator phone in static template!"
        
        # 6. Zero emojis
        body_no_svg = re.sub(r'<svg.*?</svg>', '', html, flags=re.DOTALL)
        emojis = re.findall(r'[\U00010000-\U0010ffff]', body_no_svg)
        assert len(emojis) == 0, f"Found emojis in template: {emojis}"

def test_publish_config_support_env_normalization(monkeypatch):
    """Test Section 9B, 9C, 9D: Server config parsing and normalization."""
    import argparse
    from editor_publish_server import PublishConfig

    # Valid env with formatting (dummy number for test)
    monkeypatch.setenv("PROSPECTOR_CMS_SUPPORT_WHATSAPP", "+55 (11) 98765-4321")
    cfg = PublishConfig(argparse.Namespace(root=str(ROOT), host="127.0.0.1", port=8787, mode="local", deploy_repo="", base_path="clientes", branch="main", remote="origin"))
    assert cfg.support_enabled is True
    assert cfg.support_whatsapp == "5511987654321"
    assert cfg.support_base_url == "https://wa.me/5511987654321"

    # Missing env
    monkeypatch.setenv("PROSPECTOR_CMS_SUPPORT_WHATSAPP", "")
    cfg_missing = PublishConfig(argparse.Namespace(root=str(ROOT), host="127.0.0.1", port=8787, mode="local", deploy_repo="", base_path="clientes", branch="main", remote="origin"))
    assert cfg_missing.support_enabled is False
    assert cfg_missing.support_whatsapp is None
    assert cfg_missing.support_base_url is None

    # Malformed too short (<8 digits)
    monkeypatch.setenv("PROSPECTOR_CMS_SUPPORT_WHATSAPP", "12345")
    cfg_short = PublishConfig(argparse.Namespace(root=str(ROOT), host="127.0.0.1", port=8787, mode="local", deploy_repo="", base_path="clientes", branch="main", remote="origin"))
    assert cfg_short.support_enabled is False

    # Malformed alpha only
    monkeypatch.setenv("PROSPECTOR_CMS_SUPPORT_WHATSAPP", "invalid_phone")
    cfg_alpha = PublishConfig(argparse.Namespace(root=str(ROOT), host="127.0.0.1", port=8787, mode="local", deploy_repo="", base_path="clientes", branch="main", remote="origin"))
    assert cfg_alpha.support_enabled is False

    # Malformed too long (>15 digits)
    monkeypatch.setenv("PROSPECTOR_CMS_SUPPORT_WHATSAPP", "12345678901234567")
    cfg_long = PublishConfig(argparse.Namespace(root=str(ROOT), host="127.0.0.1", port=8787, mode="local", deploy_repo="", base_path="clientes", branch="main", remote="origin"))
    assert cfg_long.support_enabled is False

def test_status_endpoint_support_leakage():
    """Test Section 9E: Ensure unauthenticated requests do not leak support details."""
    import subprocess
    import tempfile
    
    test_number = os.environ.get("PROSPECTOR_CMS_SUPPORT_WHATSAPP") or "5511987654321"
    env = os.environ.copy()
    env["PROSPECTOR_CMS_SUPPORT_WHATSAPP"] = test_number
    env["PROSPECTOR_CMS_DATA_DIR"] = str(ROOT)

    proc = subprocess.Popen(
        ["python", "editor_publish_server.py", "--host", "127.0.0.1", "--port", "8799", "--mode", "local"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    try:
        # Unauthenticated status request
        req = urllib.request.Request("http://127.0.0.1:8799/api/client-cms/status?slug=test-slug")
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            data = json.loads(e.read().decode("utf-8"))

        assert data.get("authorized") is False
        assert "support" not in data, "Unauthenticated response must NOT contain support object"
        raw_digits = re.sub(r"\D", "", test_number)
        assert raw_digits not in json.dumps(data), "Unauthenticated response leaked support phone!"
    finally:
        proc.terminate()
        proc.wait()

def test_browser_support_button_e2e():
    """Test Section 9F: Browser rendering, interaction, prefill, and mobile responsive behavior."""
    test_number = os.environ.get("PROSPECTOR_CMS_SUPPORT_WHATSAPP") or "5511987654321"
    raw_digits = re.sub(r"\D", "", test_number)
    env = os.environ.copy()
    env["PROSPECTOR_CMS_SUPPORT_WHATSAPP"] = test_number
    env["PROSPECTOR_CMS_DATA_DIR"] = str(ROOT)

    proc = subprocess.Popen(
        ["python", "editor_publish_server.py", "--host", "127.0.0.1", "--port", "8798", "--mode", "local"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # Test 1: Desktop 1440x900
            page_desktop = browser.new_page(viewport={"width": 1440, "height": 900})
            page_desktop.goto("http://127.0.0.1:8798/clientes/instituto-de-ortopedia-e-traumatologia-rio-claro/admin/")
            
            # Inject session token directly for testing UI workspace
            token_key = "autocora_cms_token:instituto-de-ortopedia-e-traumatologia-rio-claro"
            # Get valid token via auth store
            from client_cms_auth import TenantAuthStore
            auth_store = TenantAuthStore(ROOT)
            auth_store.register_tenant("instituto-de-ortopedia-e-traumatologia-rio-claro", "admin_qa", "qa_pass_123", display_name="Instituto de Ortopedia")
            ok, token, err = auth_store.authenticate("instituto-de-ortopedia-e-traumatologia-rio-claro", "admin_qa", "qa_pass_123")
            assert ok and token, f"Auth failed: {err}"
            
            page_desktop.evaluate(f"sessionStorage.setItem('{token_key}', '{token}')")
            page_desktop.reload()
            page_desktop.wait_for_selector("#cms-workspace-view", state="visible", timeout=5000)

            # Verify Support button visible
            btn_support = page_desktop.locator("#btn-support")
            assert btn_support.is_visible(), "Suporte button must be visible after login"
            
            # Verify href and prefill
            href = btn_support.get_attribute("href")
            assert href.startswith(f"https://wa.me/{raw_digits}?text="), f"Invalid href: {href}"
            assert "Instituto" in href or "instituto" in href.lower()
            assert "painel%20do%20site" in href.lower() or "painel do site" in href.lower() or "ajuda" in href.lower()

            # Verify header overflow is 0
            header_scroll_w = page_desktop.evaluate("document.getElementById('cms-header-bar').scrollWidth")
            header_client_w = page_desktop.evaluate("document.getElementById('cms-header-bar').clientWidth")
            assert header_scroll_w <= header_client_w, f"Desktop header overflow: {header_scroll_w} > {header_client_w}"

            # Capture Desktop screenshot
            page_desktop.screenshot(path="qa_cms_support_desktop_verified.png")
            page_desktop.close()

            # Test 2: Mobile 390x844
            page_mobile = browser.new_page(viewport={"width": 390, "height": 844})
            page_mobile.goto("http://127.0.0.1:8798/clientes/instituto-de-ortopedia-e-traumatologia-rio-claro/admin/")
            page_mobile.evaluate(f"sessionStorage.setItem('{token_key}', '{token}')")
            page_mobile.reload()
            page_mobile.wait_for_selector("#cms-workspace-view", state="visible", timeout=5000)

            btn_support_mobile = page_mobile.locator("#btn-support")
            assert btn_support_mobile.is_visible(), "Suporte button must remain visible on mobile 390x844"
            btn_pub_mobile = page_mobile.locator("#btn-publish")
            assert btn_pub_mobile.is_visible(), "Publicar button must remain visible on mobile 390x844"

            # Check 0 horizontal overflow on mobile
            m_scroll_w = page_mobile.evaluate("document.getElementById('cms-header-bar').scrollWidth")
            m_client_w = page_mobile.evaluate("document.getElementById('cms-header-bar').clientWidth")
            assert m_scroll_w <= m_client_w, f"Mobile header overflow: scrollWidth={m_scroll_w} > clientWidth={m_client_w}"

            doc_scroll_w = page_mobile.evaluate("document.documentElement.scrollWidth")
            doc_client_w = page_mobile.evaluate("document.documentElement.clientWidth")
            assert doc_scroll_w <= doc_client_w, f"Mobile page horizontal overflow: {doc_scroll_w} > {doc_client_w}"

            # Capture Mobile screenshot
            page_mobile.screenshot(path="qa_cms_support_mobile_verified.png")
            page_mobile.close()

            browser.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    pytest.main(["-v", str(pathlib.Path(__file__).resolve())])
