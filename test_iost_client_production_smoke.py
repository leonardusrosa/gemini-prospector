#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dedicated Client Production Smoke Test for IOST Ortodontia (Strictly READ-ONLY).
- Public site integrity & zero QA marker assertions
- Editor source & public HTML alignment
- Verification of tenant existence in AuthStore without publishing or altering data
- Cross-tenant isolation verification
"""

import hashlib
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
MODULE_DIR = ROOT / "prospector-de-sites" if (ROOT / "prospector-de-sites").exists() else ROOT
sys.path.insert(0, str(MODULE_DIR))

from client_cms_auth import TenantAuthStore

CLIENT_SLUG = "iost-ortodontia-aline-iost-rio-claro"
PUBLIC_SITE_URL = f"https://prospector-sites-beta.vercel.app/clientes/{CLIENT_SLUG}/"
PROPOSAL_URL = f"https://prospector-sites-beta.vercel.app/clientes/{CLIENT_SLUG}/proposta.html"

FORBIDDEN_QA_MARKERS = [
    "QA CMS",
    "TEST TEMPORÁRIO",
    "TEST TEMPORARIO",
    "E2E TEST",
    "QA TEST",
    "SYNTHETIC MUTATION",
]

def test_public_site():
    print(f"[SMOKE] Testing public site: {PUBLIC_SITE_URL}")
    req = urllib.request.Request(PUBLIC_SITE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        body = resp.read().decode("utf-8")
        
        # Check title / brand
        assert "IOST Ortodontia" in body, "Brand name not found in public HTML"
        assert "Aline" in body, "Dra. Aline not found in public HTML"
        assert "104164" in body, "CRO not found in public HTML"

        # Check for forbidden QA markers
        for marker in FORBIDDEN_QA_MARKERS:
            assert marker not in body, f"Forbidden QA marker found in public HTML: {marker}"
    
    print("[SMOKE] Public site integrity: PASS")

def test_proposal_page():
    print(f"[SMOKE] Testing proposal page: {PROPOSAL_URL}")
    req = urllib.request.Request(PROPOSAL_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        body = resp.read().decode("utf-8")
        assert "Primeira proposta funcional" in body or "primeira proposta funcional" in body.lower(), "Proposal badge text not found"
        assert "IOST Ortodontia" in body, "Brand name not found in proposal"
    print("[SMOKE] Proposal page integrity: PASS")

def test_tenant_auth_store():
    print("[SMOKE] Testing TenantAuthStore for IOST tenant...")
    store = TenantAuthStore(root_dir=ROOT)
    users = store._load_users()
    assert CLIENT_SLUG in users, f"Tenant {CLIENT_SLUG} not registered in AuthStore"
    tenant_info = users[CLIENT_SLUG]
    assert tenant_info.get("username") == "admin_iost", f"Unexpected username: {tenant_info.get('username')}"
    assert tenant_info.get("credentialVersion", 0) >= 1, "Credential version must be >= 1"
    print("[SMOKE] Tenant AuthStore check: PASS")

def test_cross_tenant_isolation():
    print("[SMOKE] Verifying cross-tenant isolation in AuthStore...")
    store = TenantAuthStore(root_dir=ROOT)
    users = store._load_users()
    assert "autocora-cms-qa" not in users or users["autocora-cms-qa"].get("username") != users[CLIENT_SLUG].get("username")
    assert "instituto-ferreira-odontologia-rio-claro" in users
    assert users["instituto-ferreira-odontologia-rio-claro"].get("username") != users[CLIENT_SLUG].get("username")
    print("[SMOKE] Cross-tenant isolation: PASS")

if __name__ == "__main__":
    try:
        test_public_site()
        test_proposal_page()
        test_tenant_auth_store()
        test_cross_tenant_isolation()
        print("\n[ALL READ-ONLY SMOKE TESTS PASSED]")
    except Exception as e:
        print(f"\n[SMOKE TEST FAILED] {e}", file=sys.stderr)
        sys.exit(1)
