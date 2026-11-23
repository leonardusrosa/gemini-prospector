import json
import tempfile
import unittest
from pathlib import Path

from test_hero_motion import plan_fixture, SHA
import flow_execution_ledger as flow

class FlowExecutionLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.quote = self.root / "quote.png"
        self.charge = self.root / "charge.png"
        self.quote.write_bytes(b"quote evidence")
        self.charge.write_bytes(b"charge evidence")
        self.job = flow.new_job(plan_fixture(), SHA)

    def reserve(self, step, alias="flow-a", balance=100, cost=10, retry=False):
        return flow.reserve(self.job, step, alias, "model", balance, cost,
                            self.quote, retry=retry)

    def finish(self, step, alias="flow-a", balance=90, failed=False):
        artifact = self.root / (step + str(len(self.job["entries"])) +
                                (".mp4" if step.endswith("_video") else ".jpg"))
        artifact.write_bytes(step.encode())
        return flow.reconcile(self.job, alias, balance, self.charge,
                              outcome="failed" if failed else "downloaded",
                              artifact=None if failed else artifact)

    def test_full_sequence_and_account_rotation(self):
        for index, step in enumerate(flow.STEPS):
            alias = "flow-a" if index < 4 else "flow-b"
            self.reserve(step, alias)
            self.finish(step, alias)
        result = flow.delivery_inputs(self.job)
        self.assertEqual(result["creditsSpent"], 60)
        self.assertEqual(len(result["frames"]), 4)
        self.assertEqual(len(result["videos"]), 2)
        self.assertTrue(result["manualApprovalRequired"])
        self.assertFalse(result["publicReleaseAuthorized"])

    def test_resume_pending_without_duplicate_submission(self):
        self.reserve("desktop_start")
        path = self.root / "job.json"
        flow.save_job(path, self.job)
        self.job = json.loads(path.read_text())
        with self.assertRaises(ValueError):
            self.reserve("desktop_start", "flow-b")
        self.finish("desktop_start")

    def test_charge_mismatch_stays_pending(self):
        self.reserve("desktop_start")
        with self.assertRaises(ValueError):
            self.finish("desktop_start", balance=91)
        self.assertIsNotNone(self.job["pending"])

    def test_wrong_account_stays_pending(self):
        self.reserve("desktop_start")
        with self.assertRaises(ValueError):
            self.finish("desktop_start", "flow-b")

    def test_optional_cap_and_balance(self):
        self.job = flow.new_job(plan_fixture(), SHA, cap=5)
        with self.assertRaises(ValueError):
            self.reserve("desktop_start")
        self.job = flow.new_job(plan_fixture(), SHA)
        with self.assertRaises(ValueError):
            self.reserve("desktop_start", balance=9)

    def test_retry_limit(self):
        step = "desktop_start"
        self.reserve(step)
        self.finish(step, failed=True)
        for _ in range(2):
            self.reserve(step, retry=True)
            self.finish(step, failed=True)
        with self.assertRaises(ValueError):
            self.reserve(step, retry=True)

    def test_out_of_order_and_no_partial_delivery(self):
        with self.assertRaises(ValueError):
            self.reserve("desktop_video")
        with self.assertRaises(ValueError):
            flow.delivery_inputs(self.job)

    def test_changed_evidence_blocks_reconciliation(self):
        self.reserve("desktop_start")
        self.quote.write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.finish("desktop_start")

    def test_unknown_account_and_non_integer_cost(self):
        with self.assertRaises(ValueError):
            self.reserve("desktop_start", "other")
        with self.assertRaises(ValueError):
            self.reserve("desktop_start", cost=10.5)

if __name__ == "__main__":
    unittest.main()
