"""Offline, dependency-free regressions for the isolated Prospector QA queue."""
import contextlib
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "prospector-de-sites" / "automation"))
import crm_source
import job_store
import worker


class SiteAutomationPilotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.crm = self.root / "prospector.db"
        self.queue = self.root / ".prospector" / "queue.sqlite3"
        self.sites = self.root / "prospector-sites"
        self.slug = "verified-clinic"

        db = sqlite3.connect(self.crm)
        db.execute(
            """CREATE TABLE leads (
                 slug TEXT PRIMARY KEY, status TEXT, verified_contact_methods TEXT,
                 email TEXT, email_verification_status TEXT,
                 email_verified_at TEXT, email_verification_source TEXT
            )"""
        )
        self.verified_method = [{
            "method": "instagram_dm",
            "target": "https://instagram.com/example",
            "status": "verified",
            "actionable_now": True,
            "verified_at": "2026-11-11T00:00:00Z",
            "verification_source": "manual compose check",
        }]
        db.execute("INSERT INTO leads(slug,status,verified_contact_methods) VALUES (?,?,?)",
                   (self.slug, "qualified", json.dumps(self.verified_method)))
        db.commit()
        db.close()
        self.sites.mkdir()
        (self.sites / "package.json").write_text('{"scripts":{"site-review":"node scripts/predeploy-site-gate.mjs"}}')
        client = self.sites / "clientes" / self.slug
        client.mkdir(parents=True)
        for name in ("index.html", "proposta.html", "review-manifest.json"):
            (client / name).write_text("{}")

        job_store.initialize(self.queue)

    def test_queue_is_separate_and_canonical_crm_remains_unchanged(self):
        digest_before = hashlib.sha256(self.crm.read_bytes()).digest()
        lead = crm_source.read_lead(self.crm, self.slug)
        self.assertEqual(crm_source.eligibility_issues(lead), [])
        self.assertTrue(job_store.enqueue(self.queue, self.slug, now=100))
        self.assertFalse(job_store.enqueue(self.queue, self.slug, now=200))
        self.assertEqual(len(job_store.list_jobs(self.queue)), 1)
        self.assertEqual(hashlib.sha256(self.crm.read_bytes()).digest(), digest_before)

    def test_non_verified_or_sms_only_never_enqueued(self):
        db = sqlite3.connect(self.crm)
        for method in ("sms", "instagram_dm"):
            evidence = [dict(self.verified_method[0], method=method)]
            if method != "sms":
                evidence[0]["verification_source"] = ""
            db.execute("UPDATE leads SET verified_contact_methods=? WHERE slug=?",
                       (json.dumps(evidence), self.slug))
            db.commit()
            self.assertTrue(crm_source.eligibility_issues(crm_source.read_lead(self.crm, self.slug)))
        db.close()

    def test_verified_email_alternative_and_stage_gate(self):
        db = sqlite3.connect(self.crm)
        db.execute(
            """UPDATE leads SET verified_contact_methods='[]', email='owner@example.com',
                 email_verification_status='verified', email_verified_at='2026-11-11',
                 email_verification_source='verified provider' WHERE slug=?""",
            (self.slug,),
        )
        db.commit()
        self.assertEqual(crm_source.eligibility_issues(crm_source.read_lead(self.crm, self.slug)), [])
        db.execute("UPDATE leads SET status='published' WHERE slug=?", (self.slug,))
        db.commit()
        db.close()
        self.assertTrue(crm_source.eligibility_issues(crm_source.read_lead(self.crm, self.slug)))

    def test_single_atomic_claim_and_lease_fencing(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        first = job_store.claim(self.queue, "worker-a", now=110, lease_seconds=10)
        self.assertIsNotNone(first)
        self.assertEqual(first["attempts"], 1)
        self.assertIsNone(job_store.claim(self.queue, "worker-b", now=111, lease_seconds=10))
        replacement = job_store.claim(self.queue, "worker-b", now=121, lease_seconds=10)
        self.assertEqual(replacement["id"], first["id"])
        self.assertNotEqual(replacement["lease_token"], first["lease_token"])
        self.assertEqual(replacement["attempts"], 2)
        with self.assertRaises(RuntimeError):
            job_store.finish(self.queue, first["id"], first["lease_token"],
                             "ready_for_review", now=122)
        job_store.finish(self.queue, replacement["id"], replacement["lease_token"],
                         "ready_for_review", sites_sha="a" * 40, gate_exit=0, now=123)
        self.assertEqual(job_store.list_jobs(self.queue)[0]["state"], "ready_for_review")
        self.assertIsNone(job_store.claim(self.queue, "worker-c", now=124))

    def test_retry_backoff_and_explicit_requeue(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        first = job_store.claim(self.queue, "worker-a", now=101)
        job_store.finish(self.queue, first["id"], first["lease_token"],
                         "retry", reason="transient", now=102)
        self.assertIsNone(job_store.peek(self.queue, now=131))
        self.assertIsNotNone(job_store.peek(self.queue, now=132))
        self.assertTrue(job_store.requeue(self.queue, self.slug, now=103))
        self.assertIsNotNone(job_store.peek(self.queue, now=104))

    def test_dry_run_does_not_mutate_queue_or_invoke_gates(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        before = job_store.list_jobs(self.queue)
        out = io.StringIO()
        with mock.patch.object(worker, "run_existing_gates", side_effect=AssertionError("must not run")):
            with contextlib.redirect_stdout(out):
                result = worker.main(["--crm-db", str(self.crm), "--queue-db", str(self.queue),
                                      "run", "--sites-repo", str(self.sites)])
        self.assertEqual(result, 0)
        payload = json.loads(out.getvalue())
        self.assertFalse(payload["mutated"])
        self.assertEqual(payload["issues"], [])
        self.assertEqual(job_store.list_jobs(self.queue), before)

    def test_explicit_local_gates_end_at_review_not_publication(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        before = hashlib.sha256(self.crm.read_bytes()).digest()
        with mock.patch.object(worker, "git_snapshot", return_value=("a" * 40, None)):
            with mock.patch.object(worker, "run_existing_gates", return_value=0) as gate:
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    result = worker.execute_one(self.queue, self.crm, self.sites, 5)
        self.assertEqual(result, 0)
        gate.assert_called_once_with(self.sites, 5)
        self.assertEqual(job_store.list_jobs(self.queue)[0]["state"], "ready_for_review")
        payload = json.loads(out.getvalue())
        self.assertFalse(payload["published"])
        self.assertFalse(payload["outreach_sent"])
        self.assertFalse(payload["crm_updated"])
        self.assertEqual(hashlib.sha256(self.crm.read_bytes()).digest(), before)

    def test_missing_artifacts_block_before_gates(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        (self.sites / "clientes" / self.slug / "proposta.html").unlink()
        with mock.patch.object(worker, "run_existing_gates", side_effect=AssertionError("must not run")):
            with contextlib.redirect_stdout(io.StringIO()):
                result = worker.execute_one(self.queue, self.crm, self.sites, 5)
        self.assertEqual(result, 1)
        self.assertEqual(job_store.list_jobs(self.queue)[0]["state"], "blocked")

    def test_existing_site_review_is_only_command_run(self):
        cp = subprocess_completed_process(["npm", "run", "site-review"], 0)
        with mock.patch.object(worker.subprocess, "run", return_value=cp) as run:
            self.assertEqual(worker.run_existing_gates(self.sites, 60), 0)
        self.assertEqual(run.call_args.args[0], ["npm", "run", "site-review"])
        self.assertEqual(run.call_args.kwargs["cwd"], self.sites)

    def test_wrong_slug_cannot_traverse_filesystem(self):
        self.assertTrue(crm_source.artifact_issues(self.sites, "../secret"))
        with self.assertRaises(ValueError):
            crm_source.read_lead(self.crm, "../secret")


def subprocess_completed_process(args, code):
    import subprocess
    return subprocess.CompletedProcess(args, code, "", "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
