"""Offline regression for international prospecting and media rights gates."""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "prospector-de-sites"))
sys.path.insert(0, str(ROOT / "prospector-de-sites" / "automation"))
import market_scope
import discovery_service
import site_research


class MarketScopeTests(unittest.TestCase):
    def test_only_usa_canada_and_europe_admitted(self):
        for country in ("US", "CA", "GB", "IE", "CH", "FR", "PT",
                        "PL", "IS", "UA", "AL", "VA"):
            with self.subTest(country=country):
                self.assertIsNone(market_scope.scope_issue(country))
        for country in ("BR", "MX", "CL", "CR", "AU", "JP", "ZA", "", "unknown", None):
            with self.subTest(country=country):
                self.assertIsNotNone(market_scope.scope_issue(country))
        self.assertEqual(market_scope.region("Ca"), "NORTH_AMERICA")
        self.assertEqual(market_scope.region("DE"), "EUROPE")

    def test_research_scoring_independent_of_call_permissions(self):
        ideal = {
            "country": "US", "nota": 4.9, "avaliacoes": 138,
            "websiteStatus": "existing_weak",
            "classificationEvidence": "https://example.org/site-observation",
            "verifiedPhotoSources": ["https://example.org/photos"],
            "verifiedServices": ["service"],
            "identityVerified": True,
            "verifiedContactEvidence": True,
            "verifiedSocialProfiles": ["https://instagram.com/valid"],
        }
        result = market_scope.assess_research_candidate(ideal)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["action"], "RESEARCH_NEXT")
        self.assertFalse(result["outreachAuthorized"])
        self.assertFalse(result["callbackAuthorized"])
        ideal["country"] = "BR"
        self.assertEqual(market_scope.assess_research_candidate(ideal)["scope"], "BLOCK")


class NewLeadDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        discovery_service.setup_db(self.db)
        self.addCleanup(self.db.close)

    def test_blocks_new_leads_outside_scope_without_writes(self):
        for country in ("BR", "MX", "CL", None, "ZZ"):
            before = self.db.total_changes
            result = discovery_service.upsert_lead_discovery(
                self.db, {"nome": "Test", "cidade": "City", "country": country,
                          "slug": "target-" + str(country).lower()}
            )
            self.assertFalse(result["ok"])
            self.assertTrue(result["blocked"])
            self.assertEqual(self.db.total_changes, before)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM leads").fetchone()[0], 0)

    def test_accepts_verified_country_and_preserves_legacy_updates(self):
        for country in ("US", "CA", "PT", "NL"):
            result = discovery_service.upsert_lead_discovery(
                self.db, {"slug": "site-" + country.lower(), "nome": "Site " + country,
                          "cidade": "City", "country": country})
            self.assertTrue(result["ok"], result)
        self.db.execute(
            "INSERT INTO leads (slug,nome,country,status) VALUES (?,?,?,?)",
            ("historic-br", "Legacy Brazil", "BR", "publicado")
        )
        self.db.commit()
        result = discovery_service.upsert_lead_discovery(
            self.db, {"slug": "historic-br", "nome": "Legacy Brazil",
                      "country": "BR", "cidade": "Rio Claro"})
        self.assertTrue(result["ok"])
        self.assertEqual(self.db.execute(
            "SELECT status FROM leads WHERE slug='historic-br'").fetchone()[0], "publicado")

    def test_cross_country_merge_is_blocked(self):
        discovery_service.upsert_lead_discovery(
            self.db, {"slug": "original", "nome": "Original", "country": "US"})
        before = self.db.total_changes
        result = discovery_service.upsert_lead_discovery(
            self.db, {"slug": "original", "nome": "Original", "country": "CA"})
        self.assertFalse(result["ok"])
        self.assertEqual(result["policy"], "DISCOVERY_CROSS_COUNTRY_MERGE_BLOCK")
        self.assertEqual(self.db.total_changes, before)


class SocialResearchTests(unittest.TestCase):
    def setUp(self):
        self.lead = {
            "slug": "example-detailing", "country": "CA",
            "siteAntigo": "https://exampledetail.ca/",
            "socialUrls": json.dumps({
                "instagram": "https://www.instagram.com/exampledetail/",
                "facebook": "https://www.facebook.com/exampledetail/",
                "malicious": "https://instagram.com.evil.tld/impersonator",
                "notKnown": "javascript:alert(1)",
            }),
        }

    def test_plan_extracts_literals_but_never_claims_verified(self):
        plan = site_research.research_plan(self.lead)
        self.assertEqual(plan["mode"], "READ_ONLY_RESEARCH")
        self.assertEqual(len(plan["socialProfiles"]), 2)
        self.assertTrue(all(not p["linkActive"] and not p["identityVerified"]
                            for p in plan["socialProfiles"]))
        self.assertEqual(plan["assets"], [])
        self.assertFalse(plan["assessment"]["callbackAuthorized"])
        self.assertEqual(site_research.audit_research_manifest(plan)["result"], "REVIEW_REQUIRED")

    def test_social_hostname_and_private_urls(self):
        self.assertFalse(site_research.official_social(
            "https://www.instagram.com.evil.tld/example", "instagram"))
        self.assertFalse(site_research.official_social(
            "https://www.instagram.com@evil.tld/example", "instagram"))
        self.assertFalse(site_research.https_url("https://127.0.0.1/resource"))
        self.assertFalse(site_research.https_url("https://[::1]/resource"))

    def test_rejects_unlicensed_media_and_unverified_public_social(self):
        plan = site_research.research_plan(self.lead)
        plan["socialProfiles"][0]["linkActive"] = True
        plan["assets"] = [{
            "id": "ig-photo-001", "origin": "instagram",
            "mediaType": "image",
            "sourceUrl": "https://cdn.example.com/asset.jpg",
            "sourcePage": "https://www.instagram.com/exampledetail/p/foo",
            "rightsStatus": "UNCONFIRMED", "identityVerified": False,
            "usedInSite": True, "localPath": "assets/ig-photo-001.webp",
        }]
        result = site_research.audit_research_manifest(plan)
        self.assertEqual(result["result"], "BLOCK")
        self.assertEqual(result["approvedSiteMedia"], 0)
        self.assertTrue(any("rights" in msg for msg in result["findings"]))

    def test_requires_rights_evidence_then_allows_bounded_handoff(self):
        plan = site_research.research_plan(self.lead)
        plan["researchChecks"] = {
            "businessIdentityVerified": True,
            "websiteClassificationVerified": True,
            "socialProfileIdentityVerified": True,
            "mediaRightsReviewed": True,
            "factualSourceManifestComplete": True,
        }
        plan["socialProfiles"][0].update({
            "identityVerified": True,
            "identityEvidence": "https://exampledetail.ca/about",
            "checkedAt": "2026-11-21T12:00:00Z",
            "linkActive": True,
        })
        plan["assets"] = [{
            "id": "consented-001", "origin": "user_provided",
            "mediaType": "image",
            "sourceUrl": "https://exampledetail.ca/assets/photo.jpg",
            "sourcePage": "https://exampledetail.ca/gallery",
            "rightsStatus": "CONFIRMED", "identityVerified": True,
            "permissionEvidence": "https://exampledetail.ca/media-permission.txt",
            "rightsVerifiedBy": "admin review",
            "usedInSite": True, "localPath": "assets/consented-001.webp",
        }]
        result = site_research.audit_research_manifest(plan)
        self.assertEqual(result["result"], "STRUCTURE_PASS", result)
        self.assertFalse(result["readyForDesign"])
        self.assertTrue(result["independentEvidenceReviewRequired"])
        self.assertEqual(result["approvedSiteMedia"], 1)
        self.assertFalse(result["outreachAuthorized"])

    def test_verified_rights_without_verified_social_profile_still_block(self):
        plan = site_research.research_plan(self.lead)
        plan["researchChecks"] = {
            "businessIdentityVerified": True,
            "websiteClassificationVerified": True,
            "socialProfileIdentityVerified": True,
            "mediaRightsReviewed": True,
            "factualSourceManifestComplete": True,
        }
        plan["assets"] = [{
            "id": "ig-photo-002", "origin": "instagram",
            "mediaType": "image", "profileUrl": "https://www.instagram.com/exampledetail/",
            "sourceUrl": "https://cdn.example.com/photo.webp",
            "sourcePage": "https://www.instagram.com/p/test/",
            "rightsStatus": "CONFIRMED", "identityVerified": True,
            "permissionEvidence": "https://exampledetail.ca/consent",
            "rightsVerifiedBy": "admin review",
            "usedInSite": True, "localPath": "assets/ig-photo.webp",
        }]
        result = site_research.audit_research_manifest(plan)
        self.assertEqual(result["result"], "BLOCK")
        self.assertTrue(any("verified official profile" in s for s in result["findings"]))
        plan["socialProfiles"][0].update({
            "identityVerified": True,
            "identityEvidence": "https://exampledetail.ca/about",
            "checkedAt": "2026-11-21T12:00:00Z",
        })
        result = site_research.audit_research_manifest(plan)
        self.assertEqual(result["result"], "STRUCTURE_PASS", result)

    def test_prevents_asset_path_traversal(self):
        plan = site_research.research_plan(self.lead)
        plan["assets"] = [{
            "id": "photo-path", "origin": "user_provided",
            "mediaType": "image",
            "sourceUrl": "https://exampledetail.ca/assets/photo.jpg",
            "sourcePage": "https://exampledetail.ca/gallery",
            "rightsStatus": "CONFIRMED", "identityVerified": True,
            "permissionEvidence": "https://exampledetail.ca/consent",
            "rightsVerifiedBy": "operator review",
            "usedInSite": True, "localPath": "assets/../../private/contact.txt",
        }]
        self.assertEqual(site_research.audit_research_manifest(plan)["result"], "BLOCK")
        self.assertTrue(any("localPath" in reason for reason in
                            site_research.audit_research_manifest(plan)["findings"]))

    def test_cli_plan_is_offline_and_is_no_contact(self):
        with tempfile.TemporaryDirectory() as path:
            folder = Path(path)
            src = folder / "lead.json"
            dest = folder / "research-plan.json"
            src.write_text(json.dumps(self.lead), encoding="utf-8")
            proc = subprocess.run([
                sys.executable,
                str(ROOT / "prospector-de-sites" / "automation" / "site_research.py"),
                "plan", "--lead-json", str(src), "--output", str(dest),
            ], capture_output=True, text=True, timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            saved = json.loads(dest.read_text(encoding="utf-8"))
            self.assertTrue(saved["noOutbound"])
            self.assertFalse(saved["socialProfiles"][0]["linkActive"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
