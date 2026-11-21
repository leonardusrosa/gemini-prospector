"""Offline regression tests for the supervised Engine C review-cycle protocol."""
from __future__ import annotations

import copy
import hashlib
import json
import zlib
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "prospector-de-sites" / "automation"))
sys.path.insert(0, str(HERE / "prospector-de-sites"))
import site_review_rounds as cycle


def make_png(path: Path, width: int, height: int):
    """Minimal valid RGB image for test-only structural verification."""
    def chunk(t: bytes, b: bytes):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b))
    # Compress a black RGB image without external image dependencies.
    row = b"\x00" + b"\x00" * (width * 3)
    raw = row * height
    payload = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw))
               + chunk(b"IEND", b""))
    path.write_bytes(payload)


class ReviewCycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / ".prospector"
        self.folder.mkdir()
        self.manifest = self.folder / "research.json"
        self.run_file = self.folder / "run.json"
        self.manifest.write_text(json.dumps({
            "schemaVersion": 1,
            "leadSlug": "pilot-detailing",
            "country": "US",
            "noOutbound": True,
            "mode": "READ_ONLY_RESEARCH",
            "socialProfiles": [], "assets": [],
            "researchChecks": {
                "businessIdentityVerified": True,
                "websiteClassificationVerified": True,
                "mediaRightsReviewed": True,
                "factualSourceManifestComplete": True,
                "socialProfileIdentityVerified": True,
            },
        }), encoding="utf-8")
        self.run = cycle.new_run(self.manifest)
        self.evidence = self.folder / "independent-source-witness.txt"
        self.evidence.write_text("source inspection recorded in offline synthetic fixture", encoding="utf-8")

    def artifact(self, stage=None, version=1, **kwargs):
        stage = stage or cycle.current_stage(self.run)
        document = {
            "schemaVersion": 1, "stage": stage,
            "sourceManifestSha256": self.run["sourceManifestSha256"],
            "revision": version,
            **kwargs,
        }
        path = self.folder / f"artifact-{stage}-{version}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def report(self, verdict, stage=None, reviewer="independent-reviewer",
               observations=True, artifact_sha=None):
        stage = stage or cycle.current_stage(self.run)
        entry = self.run["stageState"][stage]
        data = {
            "schemaVersion": 1, "stage": stage,
            "artifactSha256": artifact_sha or entry["artifactSha256"],
            "reviewerId": reviewer, "verdict": verdict,
            "observations": [{
                "type": "source_recheck",
                "evidencePath": str(self.evidence),
                "evidenceSha256": cycle.file_hash(self.evidence),
            }] if observations else [],
        }
        path = self.folder / f"report-{stage}-{verdict}-{reviewer}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def submit(self, version=1, **extra):
        stage = cycle.current_stage(self.run)
        path = self.artifact(stage, version, **extra)
        cycle.submit_artifact(self.run, stage, path, "generation-agent")
        return path

    def test_reviewer_must_be_different_and_evidence_bound(self):
        self.submit()
        with self.assertRaisesRegex(ValueError, "Self-reviewed"):
            cycle.independent_review(self.run, self.report("PASS", reviewer="generation-agent"))
        with self.assertRaisesRegex(ValueError, "artifact SHA"):
            cycle.independent_review(self.run, self.report("PASS", artifact_sha="0" * 64))
        with self.assertRaisesRegex(ValueError, "concrete observations"):
            cycle.independent_review(self.run, self.report("PASS", observations=False))
        cycle.independent_review(self.run, self.report("PASS"))
        self.assertEqual(cycle.current_stage(self.run), "MEDIA_RIGHTS_AND_RELEVANCE")
        self.assertFalse(self.run["productionReleaseAuthorized"])

    def test_fail_then_two_corrections_then_block(self):
        self.submit(1)
        cycle.independent_review(self.run, self.report("FAIL"))
        self.assertEqual(self.run["stageState"][cycle.STAGES[0]]["status"], "NEEDS_CORRECTION")
        self.submit(2)
        cycle.independent_review(self.run, self.report("FAIL"))
        self.assertEqual(cycle.status(self.run)["correctionRound"], 1)
        self.submit(3)
        cycle.independent_review(self.run, self.report("FAIL"))
        self.assertEqual(self.run["state"], "BLOCKED")
        self.assertEqual(cycle.status(self.run)["correctionRound"], 2)
        with self.assertRaisesRegex(ValueError, "blocked"):
            self.submit(4)

    def test_correction_same_bytes_refused_and_stale_artifact_invalid(self):
        doc = self.submit(1)
        cycle.independent_review(self.run, self.report("FAIL"))
        with self.assertRaisesRegex(ValueError, "change artifact"):
            cycle.submit_artifact(self.run, cycle.STAGES[0], doc, "generation-agent")
        self.submit(2)
        doc2 = Path(self.run["stageState"][cycle.STAGES[0]]["artifact"])
        doc2.write_text(doc2.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed after submission"):
            cycle.independent_review(self.run, self.report("PASS"))

    def test_unfinished_rights_research_cannot_clear_media_gate(self):
        doc = json.loads(self.manifest.read_text())
        doc["researchChecks"]["mediaRightsReviewed"] = False
        self.manifest.write_text(json.dumps(doc), encoding="utf-8")
        self.run = cycle.new_run(self.manifest)
        self.submit()
        cycle.independent_review(self.run, self.report("PASS"))
        self.submit()
        with self.assertRaisesRegex(ValueError, "Unresolved research"):
            cycle.independent_review(self.run, self.report("PASS"))

    def test_manifest_drift_fails_closed(self):
        self.submit()
        self.manifest.write_text(self.manifest.read_text() + " ", encoding="utf-8")
        self.assertNotEqual(cycle.file_hash(self.manifest), self.run["sourceManifestSha256"])
        self.assertFalse(self.run["readyForHumanPreview"])

    def test_three_image_candidates_hash_and_independence(self):
        self.run["currentStageIndex"] = cycle.STAGES.index("ENGINE_C_CANDIDATES")
        imgs = []
        for index, name in enumerate(("A", "B", "C")):
            p = self.folder / f"candidate-{name}.png"
            make_png(p, 1200 + index, 800)
            imgs.append({"id": name, "generatorId": "generation-agent",
                         "imageFile": str(p), "imageSha256": cycle.file_hash(p)})
        self.submit(candidates=imgs)
        cycle.independent_review(self.run, self.report("PASS"))
        self.assertEqual(cycle.current_stage(self.run), "INDEPENDENT_DESIGN_DIRECTION")

        self.run["currentStageIndex"] = cycle.STAGES.index("ENGINE_C_CANDIDATES")
        self.run["stageState"]["ENGINE_C_CANDIDATES"]["status"] = "AWAITING_ARTIFACT"
        with self.assertRaisesRegex(ValueError, "must not share"):
            self.submit(2, candidates=imgs[:2] + [dict(imgs[2], imageSha256=imgs[0]["imageSha256"],
                          imageFile=imgs[0]["imageFile"])])

    def test_browser_stage_requires_real_files_both_viewports_and_checks(self):
        self.run["currentStageIndex"] = cycle.STAGES.index("BROWSER_VISUAL_AND_INTERACTIONS")
        with self.assertRaisesRegex(ValueError, "screenshots"):
            self.submit()
        images = {}
        for v in ("desktop", "mobile"):
            p = self.folder / f"{v}.png"
            make_png(p, 1440 if v == "desktop" else 390,
                     900 if v == "desktop" else 844)
            images[v] = {"path": str(p), "sha256": cycle.file_hash(p)}
        with self.assertRaisesRegex(ValueError, "observed check"):
            self.submit(2, screenshots=images, checks={"pageErrorsZero": True})
        checks = {key: True for key in ("pageErrorsZero", "noHorizontalOverflow",
                                        "primaryCtaVisible", "navigationWorks")}
        self.submit(3, screenshots=images, checks=checks)
        cycle.independent_review(self.run, self.report("PASS"))
        self.assertEqual(cycle.current_stage(self.run), "FACTUAL_AND_CONVERSION_RECHECK")

    def test_chain_rejects_a_previously_passed_witness_changed_after_review(self):
        self.submit()
        cycle.independent_review(self.run, self.report("PASS"))
        cycle.verify_chain(self.run)
        self.evidence.write_text("post-approval tampering", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "witness changed"):
            cycle.verify_chain(self.run)

    def test_single_writer_lock_fails_closed(self):
        with cycle.exclusive_run_lock(self.run_file):
            with self.assertRaises(FileExistsError):
                with cycle.exclusive_run_lock(self.run_file):
                    pass
        self.assertFalse(Path(str(self.run_file) + ".lock").exists())

    def test_isolated_cli_and_no_output_in_git(self):
        command = [
            sys.executable,
            str(HERE / "prospector-de-sites" / "automation" / "site_review_rounds.py"),
            "init", "--research", str(self.manifest),
            "--run", str(self.run_file),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        value = json.loads(proc.stdout)
        self.assertEqual(value["stage"], "FACTS_AND_IDENTITIES")
        self.assertFalse(value["outreachAuthorized"])
        self.assertTrue(self.run_file.is_file())
        proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Cannot overwrite existing run", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
