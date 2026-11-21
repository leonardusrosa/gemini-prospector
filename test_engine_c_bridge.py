"""Independent offline Engine C selection/provenance gate tests."""
from __future__ import annotations
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "prospector-de-sites" / "automation"))
import engine_c_bridge


class EngineCBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        (self.path / "mocks").mkdir()
        (self.path / "evaluations").mkdir()
        self.config = {
            "candidate_ids": ["A", "B", "C"], "candidate_count": 3,
            "hard_gates": ["factual_drift_zero", "identity_match"],
            "scoring": {
                "min_total": 78,
                "criteria": {
                    "visual_hierarchy": 40,
                    "conversion_clarity": 30,
                    "business_fit": 30,
                },
                "tie_breakers": ["business_fit", "candidate_id"]
            },
        }
        (self.path / "engine-c.config.json").write_text(json.dumps(self.config))
        self.entries = []
        for index, candidate in enumerate("ABC"):
            image = self.path / "mocks" / f"candidate-{candidate.lower()}.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n" + bytes([index]) * 60)
            entry = {
                "candidate_id": candidate,
                "hard_gates": {"factual_drift_zero": True, "identity_match": True},
                "scores": {name: 8 + (index == 2) for name in self.config["scoring"]["criteria"]},
                "provenance": {
                    "generatorId": "image-agent",
                    "evaluatorId": "independent-judge",
                    "generationContextSha256": "a" * 64,
                    "evaluationContextSha256": "b" * 64,
                    "mockSha256": engine_c_bridge.sha(image)
                }
            }
            (self.path / "evaluations" / f"candidate-{candidate.lower()}.json").write_text(json.dumps(entry))
            scored = engine_c_bridge.score(self.config, entry)
            self.entries.append({
                "candidate_id": candidate,
                "total": scored["score"],
                "hard_gate_pass": scored["hardGatesPass"]
            })
        self.selection = {
            "action": "CONTINUE", "winner": "C",
            "results": self.entries,
        }
        (self.path / "selection.json").write_text(json.dumps(self.selection))

    def test_independent_score_and_exact_mock_hash_verified(self):
        result = engine_c_bridge.audit_experiment(self.path)
        self.assertEqual(result["status"], "CONTRACT_VERIFIED", result)
        self.assertEqual(result["recomputedWinner"], "C")
        self.assertTrue(result["independentVisionReviewStillRequired"])
        self.assertFalse(result["productionReleaseAuthorized"])

    def test_stale_mock_rejected(self):
        (self.path / "mocks/candidate-b.png").write_bytes(b"changed")
        result = engine_c_bridge.audit_experiment(self.path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("stale mock" in x for x in result["blockers"]))

    def test_missing_blind_review_metadata_rejected(self):
        file = self.path / "evaluations/candidate-c.json"
        data = json.loads(file.read_text())
        del data["provenance"]
        file.write_text(json.dumps(data))
        result = engine_c_bridge.audit_experiment(self.path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("independent evaluation provenance missing" in x
                            for x in result["blockers"]))

    def test_generator_reviewer_self_review_blocked(self):
        file = self.path / "evaluations/candidate-a.json"
        data = json.loads(file.read_text())
        data["provenance"]["evaluatorId"] = "image-agent"
        file.write_text(json.dumps(data))
        self.assertEqual(engine_c_bridge.audit_experiment(self.path)["status"], "BLOCKED")

    def test_tampered_selected_winner_blocked(self):
        file = self.path / "selection.json"
        data = json.loads(file.read_text())
        data["winner"] = "B"
        file.write_text(json.dumps(data))
        result = engine_c_bridge.audit_experiment(self.path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("recomputation" in x for x in result["blockers"]))

    def test_hard_gates_prevent_unfounded_high_score(self):
        file = self.path / "evaluations/candidate-c.json"
        data = json.loads(file.read_text())
        data["hard_gates"]["factual_drift_zero"] = False
        file.write_text(json.dumps(data))
        result = engine_c_bridge.audit_experiment(self.path)
        self.assertEqual(result["status"], "BLOCKED")
        # A/B both score 80 and have identical business_fit; candidate-id
        # tie-break chooses A, not the list order.
        self.assertEqual(result["recomputedWinner"], "A")

    def test_invalid_score_refused(self):
        file = self.path / "evaluations/candidate-b.json"
        data = json.loads(file.read_text())
        data["scores"]["business_fit"] = 11
        file.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "score value invalid"):
            engine_c_bridge.audit_experiment(self.path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
