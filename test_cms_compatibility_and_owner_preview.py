"""Offline regression: mandatory AutoCORA CMS and private owner-preview media."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "prospector-de-sites" / "automation"))
sys.path.insert(0, str(ROOT / "prospector-de-sites"))
import cms_compatibility
import market_scope
import site_research

SAMPLE_HTML = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sample Café</title></head><body>
<h1>Local Coffee & Fresh Pastries</h1><p>Welcome to our café</p>
<p>Open daily</p><img src="assets/interior.webp" alt="Interior photograph">
<a href="https://example.org/menu">View menu</a>
</body></html>"""


class MarketPriorityTests(unittest.TestCase):
    def test_priority_verticals_multilingual(self):
        examples = {
            "restaurant": ["restaurant", "Restaurant", "restaurante", "ristorante", "brasserie"],
            "pizzeria": ["pizzeria", "pizzaria", "pizza restaurant", "pizza shop"],
            "cafe": ["café", "coffee shop", "cafeteria", "coffeehouse"],
            "dentistry": ["dentist", "dental clinic", "clínica odontológica", "dentiste", "ortodontia"],
            "clinic": ["medical clinic", "clínica de saúde", "Klinik"],
        }
        for expected, phrases in examples.items():
            for phrase in phrases:
                with self.subTest(phrase=phrase):
                    self.assertEqual(market_scope.priority_niche(phrase), expected)
        self.assertIsNone(market_scope.priority_niche("automotive detailing"))

    def test_healthcare_needs_special_fact_review_but_not_contact(self):
        value = market_scope.assess_research_candidate({
            "country": "FR", "nicho": "cabinet dental",
            "nota": 4.9, "avaliacoes": 115,
        })
        self.assertEqual(value["priorityNiche"], "dentistry")
        self.assertTrue(value["regulatedClinicalClaimsReview"])
        self.assertFalse(value["outreachAuthorized"])
        self.assertFalse(value["callbackAuthorized"])


class CmsHtmlGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.html = Path(self.temp.name) / "sample-cafe" / "index.html"
        self.html.parent.mkdir()
        self.html.write_text(SAMPLE_HTML, encoding="utf-8")

    def audit(self, html=None):
        if html is not None:
            self.html.write_text(html, encoding="utf-8")
        return cms_compatibility.audit_html_file(self.html, "sample-cafe")

    def test_static_html_compatible_without_embedded_cms_chrome(self):
        result = self.audit()
        self.assertEqual(result["result"], "STRUCTURE_PASS", result)
        self.assertFalse(result["tenantProvisioned"])
        self.assertFalse(result["runtimeCmsSmokePassed"])
        self.assertTrue(result["requirements"]["operatorProvisioningNeeded"])
        self.assertFalse(result["publicReleaseAuthorized"])

    def test_rejects_next_runtime_editor(self):
        self.assertEqual(self.audit(SAMPLE_HTML + '<script src="/_next/static/main.js"></script>')["result"], "BLOCK")

    def test_rejects_cms_chrome_persisted_in_site(self):
        self.assertEqual(self.audit(SAMPLE_HTML + '<div data-pe-ui="true"></div>')["result"], "BLOCK")

    def test_rejects_contenteditable_editor_state(self):
        self.assertEqual(self.audit(SAMPLE_HTML.replace("<h1>", '<h1 contenteditable="true">'))["result"], "BLOCK")

    def test_rejects_duplicate_element_ids(self):
        html = SAMPLE_HTML.replace("<h1>", '<h1 id="same">').replace(
            "<p>Welcome", '<p id="same">Welcome')
        self.assertEqual(self.audit(html)["result"], "BLOCK")

    def test_rejects_missing_actions(self):
        html = SAMPLE_HTML.replace('<a href="https://example.org/menu">View menu</a>', '')
        self.assertEqual(self.audit(html)["result"], "BLOCK")

    def test_nonlatin_site_content_not_rejected(self):
        html = SAMPLE_HTML.replace("Sample Café", "Café & Pizzeria").replace(
            "Open daily", "Bienvenue — 样板网站")
        self.assertEqual(self.audit(html)["result"], "STRUCTURE_PASS")


class OwnerPreviewTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "schemaVersion": 1, "leadSlug": "sample-cafe", "country": "CA",
            "noOutbound": True, "mode": "READ_ONLY_RESEARCH",
            "researchChecks": {
                "businessIdentityVerified": True,
                "websiteClassificationVerified": True,
                "factualSourceManifestComplete": True,
                "mediaRightsReviewed": False,
            },
            "ownerPreviewPolicy": {
                "previewPurpose": "BUSINESS_OWNER_REVIEW",
                "accessProtected": True, "ownerOnlyAudience": True,
                "noSearchIndexing": True, "noPublicRelease": True,
            },
            "socialProfiles": [{
                "platform": "instagram",
                "url": "https://www.instagram.com/samplecafe/",
                "identityVerified": True,
                "identityEvidence": "https://samplecafe.example/about",
                "checkedAt": "2026-11-21T12:00:00Z",
                "linkActive": False,
            }],
            "assets": [{
                "id": "brand-photo-01", "origin": "instagram",
                "profileUrl": "https://www.instagram.com/samplecafe/",
                "sourceUrl": "https://cdn.example.org/brand-image.webp",
                "sourcePage": "https://www.instagram.com/samplecafe/p/photo01/",
                "mediaType": "image", "identityVerified": True,
                "rightsStatus": "UNCONFIRMED",
                "useInProtectedOwnerPreview": True,
                "previewPath": ".prospector/owner-preview/assets/brand-image.webp",
                "usedInSite": False,
            }],
        }
        self.probe = {
            "unauthenticatedAccessDenied": True,
            "noIndexHeadersVerified": True,
            "recipientRestricted": True,
            "reviewedBy": "independent-browser-qa",
            "probeAt": "2026-11-21T15:00:00Z",
        }

    def test_owner_preview_does_not_require_rights_to_plan(self):
        decision = site_research.audit_protected_owner_preview(self.manifest)
        self.assertEqual(decision["result"], "PREVIEW_ACCESS_REVIEW_REQUIRED")
        self.assertEqual(decision["rightsUnconfirmedCount"], 1)
        self.assertFalse(decision["rightsAuditRequiredBeforeInternalPreview"])
        self.assertFalse(decision["publicReleaseAuthorized"])
        self.assertEqual(decision["brandAssetsUsableInInternalPreview"], 1)

    def test_private_preview_proof_allows_only_protected_draft(self):
        decision = site_research.audit_protected_owner_preview(
            self.manifest, access_evidence=self.probe)
        self.assertEqual(decision["result"], "STRUCTURE_READY_FOR_PRIVATE_PREVIEW")
        self.assertFalse(decision["productionReleaseAuthorized"])
        self.assertTrue(decision["independentAccessReviewRequired"])

    def test_unverified_social_owner_blocks_preview(self):
        self.manifest["socialProfiles"][0]["identityVerified"] = False
        self.assertEqual(site_research.audit_protected_owner_preview(
            self.manifest, access_evidence=self.probe)["result"], "BLOCK")

    def test_public_assets_directory_blocks_unlicensed_preview_mode(self):
        self.manifest["assets"][0]["localPath"] = "assets/brand-photo.webp"
        self.assertEqual(site_research.audit_protected_owner_preview(
            self.manifest, access_evidence=self.probe)["result"], "BLOCK")

    def test_open_anonymous_preview_blocked(self):
        self.manifest["ownerPreviewPolicy"]["accessProtected"] = False
        self.assertEqual(site_research.audit_protected_owner_preview(
            self.manifest, access_evidence=self.probe)["result"], "BLOCK")

    def test_google_maps_photo_not_silently_copied(self):
        self.manifest["assets"][0]["origin"] = "google_maps"
        self.assertEqual(site_research.audit_protected_owner_preview(
            self.manifest, access_evidence=self.probe)["result"], "BLOCK")

    def test_publication_audit_still_blocks_unlicensed_public_use(self):
        self.manifest["assets"][0]["usedInSite"] = True
        result = site_research.audit_research_manifest(self.manifest)
        self.assertEqual(result["result"], "BLOCK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
