"""Offline Engine C -> Client CMS collection annotation and release gate tests."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "prospector-de-sites" / "automation"))
import cms_collections_handoff as handoff
import cms_compatibility
import site_review_rounds as rounds
import site_research

HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fictional Pizzeria (QA)</title></head><body>
<h1>Fictional Pizzeria</h1><p>A test fixture, not a real company.</p>
<h2>Menu</h2><div id="menu-grid" class="grid">
  <article id="pizza-one" class="card"><h3>Fictional Pizza One</h3>
    <p>$12</p><img src="assets/qa-one.webp" alt="Synthetic menu card"></article>
  <article id="pizza-two" class="card"><h3>Fictional Pizza Two</h3>
    <p>$14</p><img src="assets/qa-two.webp" alt="Synthetic menu card"></article>
</div><a href="#menu-grid">View menu</a></body></html>"""


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class EngineToCmsCollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "index.html"
        self.source.write_text(HTML, encoding="utf-8")
        self.output = self.root / "cms-ready.html"
        self.fact_evidence = self.root / "browser-source-review.txt"
        self.fact_evidence.write_text(
            "SYNTHETIC QA ONLY: This fictional menu is not a real business fact.",
            encoding="utf-8",
        )
        self.manifest = {
            "schemaVersion": 1,
            "leadSlug": "fictional-pizzeria-qa",
            "noOutbound": True,
            "country": "US",
            "assessment": {"scope": "ALLOW", "priorityNiche": "pizzeria"},
            "cmsSourceHtmlSha256": handoff.sha_file(self.source),
            "cmsCollections": [{
                "kind": "menu", "containerId": "menu-grid",
                "itemIds": ["pizza-one", "pizza-two"],
                "sourcePage": "https://example.org/fictional-menu",
                "sourceEvidence": {
                    "path": str(self.fact_evidence),
                    "sha256": handoff.sha_file(self.fact_evidence),
                },
            }],
        }
        self.plan = self.root / "plan.json"
        self.write_plan()

    def write_plan(self):
        self.plan.write_text(json.dumps(self.manifest, indent=2), encoding="utf-8")

    def test_annotates_existing_cards_without_rewriting_content(self):
        result = handoff.annotate_file(self.source, self.plan, self.output)
        self.assertEqual(result["result"], "STRUCTURE_PASS", result)
        self.assertTrue(result["bytesChanged"])
        updated = self.output.read_text(encoding="utf-8")
        self.assertIn('id="menu-grid" class="grid" data-pe-collection="menu"', updated)
        self.assertIn('id="pizza-one" class="card" data-pe-item', updated)
        self.assertIn('id="pizza-two" class="card" data-pe-item', updated)
        self.assertIn("$12", updated)
        self.assertIn("$14", updated)
        self.assertEqual(self.source.read_text(encoding="utf-8"), HTML)
        self.assertEqual(cms_compatibility.audit_html_file(self.output)["result"], "STRUCTURE_PASS")
        self.assertFalse(result["clientHandoffAuthorized"])
        self.assertFalse(result["productionReleaseAuthorized"])

    def test_idempotent_for_previously_tagged_valid_html(self):
        prepared = handoff.annotate_html(HTML, self.manifest)
        self.assertEqual(handoff.annotate_html(prepared, self.manifest), prepared)
        self.assertEqual(handoff.audit_html(prepared, self.manifest)["result"], "STRUCTURE_PASS")

    def test_missing_explicit_plan_blocks_priority_niche(self):
        self.manifest["cmsCollections"] = []
        with self.assertRaisesRegex(ValueError, "source-reviewed CMS collection"):
            handoff.annotate_html(HTML, self.manifest)

    def test_cannot_invent_card_from_wrong_plan_id(self):
        self.manifest["cmsCollections"][0]["itemIds"].append("imaginary-price-card")
        with self.assertRaisesRegex(ValueError, "[Vv]erified card IDs differ|HTML ID"):
            handoff.annotate_html(HTML, self.manifest)

    def test_unplanned_direct_child_blocks(self):
        html = HTML.replace('</div><a href="#menu-grid">', '<article id="unauthorized"><p>Fake menu</p></article></div><a href="#menu-grid">')
        with self.assertRaisesRegex(ValueError, "Unplanned direct child"):
            handoff.annotate_html(html, self.manifest)

    def test_wrong_source_hash_refused_without_touching_output(self):
        self.manifest["cmsSourceHtmlSha256"] = "0" * 64
        self.write_plan()
        with self.assertRaisesRegex(ValueError, "HTML SHA"):
            handoff.annotate_file(self.source, self.plan, self.output)
        self.assertFalse(self.output.exists())

    def test_stale_review_evidence_hash_blocks(self):
        self.fact_evidence.write_text("tampered synthetic evidence", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing or stale"):
            handoff.annotate_html(HTML, self.manifest)

    def test_cannot_overwrite_input_or_existing_output(self):
        self.write_plan()
        with self.assertRaises(FileExistsError):
            handoff.annotate_file(self.source, self.plan, self.source)
        self.output.write_text("preserve me")
        with self.assertRaises(FileExistsError):
            handoff.annotate_file(self.source, self.plan, self.output)
        self.assertEqual(self.output.read_text(), "preserve me")

    def test_unlicensed_public_images_are_not_authorized(self):
        annotated = handoff.annotate_html(HTML, self.manifest)
        self.assertIn("sourcePage", self.manifest["cmsCollections"][0])
        self.assertIn("clientHandoffAuthorized", handoff.audit_html(annotated, self.manifest))
        self.assertFalse(handoff.audit_html(annotated, self.manifest)["productionReleaseAuthorized"])

    def test_clinic_claims_and_services_require_explicit_review(self):
        self.manifest["assessment"] = {
            "scope": "ALLOW", "priorityNiche": "dentistry",
            "regulatedClinicalClaimsReview": True,
        }
        self.manifest["cmsCollections"][0]["kind"] = "services"
        with self.assertRaisesRegex(ValueError, "[Cc]linical.*claims review"):
            handoff.annotate_html(HTML, self.manifest)
        self.manifest["cmsCollections"][0]["clinicalClaimsReviewed"] = True
        result = handoff.annotate_html(HTML, self.manifest)
        self.assertIn('data-pe-collection="services"', result)

    def test_rejects_cross_card_global_sync_keys(self):
        modified = HTML.replace('<h3>Fictional Pizza One</h3>', '<h3 data-pe-field="menu.name">Fictional Pizza One</h3>')
        with self.assertRaisesRegex(ValueError, "global CMS sync"):
            handoff.annotate_html(modified, self.manifest)

    def test_rejects_unreviewed_existing_markers(self):
        modified = HTML.replace('<div id="menu-grid" class="grid">', '<div id="menu-grid" class="grid" data-pe-collection="gallery">')
        with self.assertRaisesRegex(ValueError, "Conflicting collection marker"):
            handoff.annotate_html(modified, self.manifest)

    def test_nonpriority_site_with_no_collections_is_unchanged(self):
        self.manifest["assessment"]["priorityNiche"] = None
        self.manifest["cmsCollections"] = []
        self.assertEqual(handoff.annotate_html(HTML, self.manifest), HTML)

    def make_qa_run(self):
        research = {
            "schemaVersion": 1,
            "leadSlug": self.manifest["leadSlug"],
            "country": "US",
            "noOutbound": True,
            "mode": "READ_ONLY_RESEARCH",
            "assessment": {"scope": "ALLOW", "priorityNiche": "pizzeria"},
            "socialProfiles": [],
            "assets": [],
            "researchChecks": {},
        }
        path = self.root / "research.json"
        path.write_text(json.dumps(research), encoding="utf-8")
        run = rounds.new_run(path)
        run["currentStageIndex"] = rounds.STAGES.index("CLIENT_CMS_COMPATIBILITY")
        self.manifest["sourceManifestSha256"] = run["sourceManifestSha256"]
        self.write_plan()
        return run

    def stage_artifact(self, run):
        handoff.annotate_file(self.source, self.plan, self.output)
        data = {
            "schemaVersion": 1,
            "stage": "CLIENT_CMS_COMPATIBILITY",
            "sourceManifestSha256": run["sourceManifestSha256"],
            "htmlFile": str(self.output),
            "htmlSha256": handoff.sha_file(self.output),
            "unannotatedHtmlFile": str(self.source),
            "unannotatedHtmlSha256": handoff.sha_file(self.source),
            "cmsCollectionPlanFile": str(self.plan),
            "cmsCollectionPlanSha256": handoff.sha_file(self.plan),
        }
        artifact = self.root / "cms-stage.json"
        artifact.write_text(json.dumps(data), encoding="utf-8")
        return artifact

    def test_priority_niche_qa_stage_checks_real_source_plan_and_output(self):
        run = self.make_qa_run()
        artifact = self.stage_artifact(run)
        rounds.submit_artifact(
            run, "CLIENT_CMS_COMPATIBILITY", artifact, "build-generator"
        )
        self.assertEqual(
            run["stageState"]["CLIENT_CMS_COMPATIBILITY"]["status"],
            "AWAITING_REVIEW",
        )
        self.assertFalse(run["productionReleaseAuthorized"])
        rounds.verify_chain(run)

    def test_priority_niche_cms_stage_fails_when_no_plan_provided(self):
        run = self.make_qa_run()
        artifact = self.stage_artifact(run)
        data = json.loads(artifact.read_text(encoding="utf-8"))
        del data["cmsCollectionPlanFile"]
        artifact.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "requires a CMS collection plan"):
            rounds.submit_artifact(
                run, "CLIENT_CMS_COMPATIBILITY", artifact, "build-generator"
            )

    def test_priority_niche_cms_stage_rejects_changed_original(self):
        run = self.make_qa_run()
        artifact = self.stage_artifact(run)
        self.source.write_text(HTML + " ", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            rounds.submit_artifact(
                run, "CLIENT_CMS_COMPATIBILITY", artifact, "build-generator"
            )

    def test_priority_niche_cms_stage_rejects_wrong_research_sha(self):
        run = self.make_qa_run()
        artifact = self.stage_artifact(run)
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        plan["sourceManifestSha256"] = "0" * 64
        self.plan.write_text(json.dumps(plan), encoding="utf-8")
        meta = json.loads(artifact.read_text(encoding="utf-8"))
        meta["cmsCollectionPlanSha256"] = handoff.sha_file(self.plan)
        artifact.write_text(json.dumps(meta), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "immutable research manifest"):
            rounds.submit_artifact(
                run, "CLIENT_CMS_COMPATIBILITY", artifact, "build-generator"
            )

    def test_malformed_hydrated_html_still_blocked_by_existing_cms_gate(self):
        html = handoff.annotate_html(HTML, self.manifest) + '<script src="/_next/static/main.js"></script>'
        path = self.root / "hydrated.html"
        path.write_text(html, encoding="utf-8")
        self.assertEqual(cms_compatibility.audit_html_file(path)["result"], "BLOCK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
