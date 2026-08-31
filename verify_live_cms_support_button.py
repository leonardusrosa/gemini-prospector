#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live production QA for Global Client CMS WhatsApp Support button on Phoenix."""

import os
import sys
import pathlib
import urllib.parse
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

def run_live_qa():
    inst_user = os.environ.get("PROSPECTOR_SMOKE_INSTITUTO_USERNAME")
    inst_pass = os.environ.get("PROSPECTOR_SMOKE_INSTITUTO_PASSWORD")
    iost_user = os.environ.get("PROSPECTOR_SMOKE_IOST_USERNAME")
    iost_pass = os.environ.get("PROSPECTOR_SMOKE_IOST_PASSWORD")

    assert inst_user and inst_pass, "Missing Instituto QA credentials in .env.test.local"
    assert iost_user and iost_pass, "Missing IOST QA credentials in .env.test.local"

    tenants = [
        {
            "name": "Instituto Ferreira",
            "slug": "instituto-ferreira-odontologia-rio-claro",
            "url": "https://prospector.autocora.com.br/clientes/instituto-ferreira-odontologia-rio-claro/admin/",
            "user": inst_user,
            "pwd": inst_pass,
            "expected_name_substr": "Instituto",
        },
        {
            "name": "IOST Ortodontia",
            "slug": "iost-ortodontia-aline-iost-rio-claro",
            "url": "https://prospector.autocora.com.br/clientes/iost-ortodontia-aline-iost-rio-claro/admin/",
            "user": iost_user,
            "pwd": iost_pass,
            "expected_name_substr": "Iost",
        }
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for t in tenants:
            slug = t["slug"]
            name = t["name"]
            print(f"\n--- Testing Live Tenant: {name} ({slug}) ---")

            # 1. Desktop 1440x900
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(t["url"], wait_until="networkidle")

            # Fill login form
            page.locator("#cms-username").fill(t["user"])
            page.locator("#cms-password").fill(t["pwd"])
            page.locator("#cms-login-submit").click()

            # Wait for workspace view
            page.wait_for_selector("#cms-workspace-view", state="visible", timeout=10000)
            print(f"[{name}] Login successful, workspace displayed")

            # Check Support button
            btn_support = page.locator("#btn-support")
            assert btn_support.is_visible(), f"[{name}] Suporte button is NOT visible!"
            
            # Check attributes
            target = btn_support.get_attribute("target")
            rel = btn_support.get_attribute("rel")
            aria_label = btn_support.get_attribute("aria-label")
            href = btn_support.get_attribute("href")

            assert target == "_blank", f"[{name}] target is '{target}', expected '_blank'"
            assert "noopener" in rel and "noreferrer" in rel, f"[{name}] rel is '{rel}'"
            assert aria_label == "Falar com o suporte pelo WhatsApp"
            assert href is not None and href.startswith("https://wa.me/"), f"[{name}] invalid href: {href}"
            
            # Parse query params
            parsed_href = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed_href.query)
            msg = qs.get("text", [""])[0]
            assert msg.startswith("Olá! Preciso de ajuda com o painel do site "), f"[{name}] unexpected prefill message: {msg}"
            assert t["expected_name_substr"].lower() in msg.lower(), f"[{name}] expected name '{t['expected_name_substr']}' in message: {msg}"
            print(f"[{name}] Suporte link validated: target='{target}', rel='{rel}', prefill contains tenant name")

            # Check Desktop header overflow
            scroll_w = page.evaluate("document.getElementById('cms-header-bar').scrollWidth")
            client_w = page.evaluate("document.getElementById('cms-header-bar').clientWidth")
            assert scroll_w <= client_w, f"[{name}] Desktop header overflow: {scroll_w} > {client_w}"

            # Screenshot Desktop
            scr_desktop = f"qa_live_cms_support_{slug}_desktop.png"
            page.screenshot(path=scr_desktop)
            print(f"[{name}] Desktop screenshot captured: {scr_desktop}")
            page.close()

            # 2. Mobile 390x844
            page_m = browser.new_page(viewport={"width": 390, "height": 844})
            page_m.goto(t["url"], wait_until="networkidle")
            page_m.locator("#cms-username").fill(t["user"])
            page_m.locator("#cms-password").fill(t["pwd"])
            page_m.locator("#cms-login-submit").click()
            page_m.wait_for_selector("#cms-workspace-view", state="visible", timeout=10000)

            btn_support_m = page_m.locator("#btn-support")
            assert btn_support_m.is_visible(), f"[{name}] Mobile Suporte button is NOT visible!"
            btn_pub_m = page_m.locator("#btn-publish")
            assert btn_pub_m.is_visible(), f"[{name}] Mobile Publicar button is NOT visible!"

            # Check 0 horizontal overflow on Mobile
            m_header_scroll_w = page_m.evaluate("document.getElementById('cms-header-bar').scrollWidth")
            m_header_client_w = page_m.evaluate("document.getElementById('cms-header-bar').clientWidth")
            assert m_header_scroll_w <= m_header_client_w, f"[{name}] Mobile header overflow: scrollWidth={m_header_scroll_w} > clientWidth={m_header_client_w}"

            m_doc_scroll_w = page_m.evaluate("document.documentElement.scrollWidth")
            m_doc_client_w = page_m.evaluate("document.documentElement.clientWidth")
            assert m_doc_scroll_w <= m_doc_client_w, f"[{name}] Mobile page overflow: scrollWidth={m_doc_scroll_w} > clientWidth={m_doc_client_w}"

            # Screenshot Mobile
            scr_mobile = f"qa_live_cms_support_{slug}_mobile.png"
            page_m.screenshot(path=scr_mobile)
            print(f"[{name}] Mobile screenshot captured: {scr_mobile}")
            page_m.close()

        browser.close()
        print("\n[ALL LIVE PRODUCTION CMS SUPPORT TESTS PASSED 100%]")

if __name__ == "__main__":
    run_live_qa()
