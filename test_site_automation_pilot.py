"""Offline, dependency-free regressions for the isolated Prospector QA queue."""
import contextlib
import hashlib
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent / "prospector-de-sites" / "automation"))
import crm_source
import job_store
import snapshot_export
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



    def test_expired_lease_cannot_complete_even_without_new_claim(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        first = job_store.claim(self.queue, "worker-a", now=110, lease_seconds=10)
        with self.assertRaisesRegex(RuntimeError, "Expired lease"):
            job_store.finish(self.queue, first["id"], first["lease_token"],
                             "ready_for_review", now=120)
        self.assertEqual(job_store.list_jobs(self.queue)[0]["state"], "leased")
        replacement = job_store.claim(self.queue, "worker-b", now=120, lease_seconds=10)
        self.assertNotEqual(replacement["lease_token"], first["lease_token"])

    def test_bounded_retry_budget_and_manual_reset(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        for attempt, now in enumerate((110, 150, 230), start=1):
            job = job_store.claim(self.queue, "retry-worker", now=now)
            self.assertEqual(job["attempts"], attempt)
            job_store.finish(self.queue, job["id"], job["lease_token"],
                             "retry", reason="offline", now=now + 1)
        state = job_store.list_jobs(self.queue)[0]
        self.assertEqual(state["state"], "blocked")
        self.assertIn("Retry budget exhausted", state["last_error"])
        self.assertIsNone(job_store.peek(self.queue, now=999))
        self.assertTrue(job_store.requeue(self.queue, self.slug, now=999))
        reset = job_store.claim(self.queue, "manual-worker", now=1000)
        self.assertEqual(reset["attempts"], 1)

    def test_sha_or_worktree_change_during_gates_blocks_completion(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        with mock.patch.object(worker, "git_snapshot",
                               side_effect=[("a" * 40, None), ("b" * 40, None)]):
            with mock.patch.object(worker, "run_existing_gates", return_value=0):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = worker.execute_one(self.queue, self.crm, self.sites, 5)
        self.assertEqual(code, 1)
        self.assertEqual(job_store.list_jobs(self.queue)[0]["state"], "blocked")
        self.assertIn("changed", json.loads(out.getvalue())["reason"])

    def test_cli_fixture_dry_run_without_real_lead_or_provider(self):
        entrypoint = Path(worker.__file__).resolve()
        common = [sys.executable, str(entrypoint), "--crm-db", str(self.crm),
                  "--queue-db", str(self.queue)]
        before_crm = hashlib.sha256(self.crm.read_bytes()).digest()
        enqueued = subprocess.run(common + ["enqueue", "--slug", self.slug],
                                  capture_output=True, text=True, check=False)
        self.assertEqual(enqueued.returncode, 0, enqueued.stderr)
        self.assertTrue(json.loads(enqueued.stdout)["enqueued"])
        before_jobs = job_store.list_jobs(self.queue)
        planned = subprocess.run(common + ["run", "--sites-repo", str(self.sites)],
                                 capture_output=True, text=True, check=False)
        self.assertEqual(planned.returncode, 0, planned.stderr)
        payload = json.loads(planned.stdout)
        self.assertEqual(payload["mode"], "dry-run")
        self.assertFalse(payload["mutated"])
        self.assertFalse(payload["deploy_performed"])
        self.assertFalse(payload["outreach_sent"])
        self.assertEqual(job_store.list_jobs(self.queue), before_jobs)
        self.assertEqual(hashlib.sha256(self.crm.read_bytes()).digest(), before_crm)

    def test_research_contact_evidence_satisfies_verification(self):
        db = sqlite3.connect(self.crm)
        db.execute("UPDATE leads SET verified_contact_methods='[]', email=NULL WHERE slug=?",
                   (self.slug,))
        db.commit()
        db.close()
        lead = crm_source.read_lead(self.crm, self.slug)
        self.assertTrue(crm_source.eligibility_issues(lead))
        rdir = self.sites / "clientes" / self.slug / "research"
        rdir.mkdir(parents=True, exist_ok=True)
        (rdir / "whatsapp-profile-evidence.json").write_text(json.dumps({
            "number": "5519999999999", "verified": True,
            "collectedAt": "2026-11-11T12:00:00Z", "sourceSurface": "maps_public_listing",
        }))
        self.assertEqual(crm_source.eligibility_issues(lead, self.sites), [])


    def test_positive_canonical_42_column_research_evidence_through_cli(self):
        """A synthetic canonical-schema fixture reaches review through real git/npm.

        No real lead, external provider, Vercel, outreach, or CRM write occurs.
        The npm gate is deliberately a safe fixture stub; this does not attest
        to the full production site-review suite.
        """
        prod_crm = self.root / "canonical_positive.db"
        conn = sqlite3.connect(prod_crm)
        conn.execute("""CREATE TABLE leads (
            slug TEXT PRIMARY KEY, nome TEXT, nicho TEXT, cidade TEXT, nota REAL,
            avaliacoes INTEGER, email TEXT, telefone TEXT, whatsapp TEXT, siteAntigo TEXT,
            motivo TEXT, status TEXT DEFAULT 'novo', urlNova TEXT, dataProposta TEXT,
            valor REAL, obs TEXT, contratoStatus TEXT DEFAULT 'pendente', contratoEm TEXT,
            manutencao REAL, pago INTEGER DEFAULT 0, docCliente TEXT, endCliente TEXT,
            atualizado TEXT, placeId TEXT, opportunityType TEXT, opportunityScore INTEGER,
            classificationEvidence TEXT, mainRisk TEXT, factualContent TEXT, imageryLevel TEXT,
            socialUrls TEXT, mapsUrl TEXT, runId INTEGER, criadoEm TEXT, country TEXT,
            locale TEXT, language TEXT, phoneCountryCode TEXT, websiteStatus TEXT,
            siteMode TEXT, currency TEXT, marketTier TEXT
        )""")
        self.assertEqual(len(conn.execute("PRAGMA table_info(leads)").fetchall()), 42)
        conn.execute("INSERT INTO leads(slug, status, whatsapp) VALUES (?, ?, ?)",
                     (self.slug, "qualified", "0000000000000"))
        conn.commit()
        conn.close()

        sites = self.root / "isolated-sites-positive"
        client = sites / "clientes" / self.slug
        research = client / "research"
        research.mkdir(parents=True)
        for filename in ("index.html", "proposta.html", "review-manifest.json"):
            (client / filename).write_text("{}", encoding="utf-8")
        (research / "business-identity-evidence.json").write_text(json.dumps({
            "collectedAt": "2026-11-12T00:00:00Z",
            "whatsapp": {
                "verified": True, "number": "0000000000000",
                "source": "synthetic_fixture_not_real_evidence",
                "verifiedAt": "2026-11-12T00:00:00Z"
            },
        }), encoding="utf-8")
        (sites / "package.json").write_text(json.dumps({
            "private": True, "scripts": {"site-review": "node -e \"process.exit(0)\""}
        }), encoding="utf-8")

        def run_shell(*args):
            cp = subprocess.run(args, cwd=sites, capture_output=True, text=True,
                                check=False, timeout=30)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            return cp.stdout.strip()

        run_shell("git", "init")
        run_shell("git", "add", ".")
        run_shell("git", "-c", "user.name=Fixture", "-c",
                  "user.email=fixture@invalid.local", "-c",
                  "commit.gpgsign=false", "commit", "-m", "Synthetic fixture only")
        original_sha = run_shell("git", "rev-parse", "HEAD")
        self.assertEqual(len(original_sha), 40)
        db_before = hashlib.sha256(prod_crm.read_bytes()).hexdigest()
        queue = self.root / ".prospector" / "positive-queue.sqlite3"
        job_store.initialize(queue)

        entrypoint = Path(worker.__file__).resolve()
        common = [sys.executable, str(entrypoint), "--crm-db", str(prod_crm),
                  "--queue-db", str(queue)]

        def cli(*args):
            cp = subprocess.run(common + list(args), cwd=self.root,
                                capture_output=True, text=True, check=False,
                                timeout=60)
            self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
            return json.loads(cp.stdout)

        enqueued = cli("enqueue", "--slug", self.slug, "--sites-repo", str(sites))
        self.assertTrue(enqueued["enqueued"])
        self.assertEqual(job_store.list_jobs(queue)[0]["state"], "pending")
        dry = cli("run", "--sites-repo", str(sites))
        self.assertEqual(dry["issues"], [])
        self.assertFalse(dry["mutated"])
        self.assertEqual(job_store.list_jobs(queue)[0]["state"], "pending")

        executed = cli("run", "--sites-repo", str(sites), "--execute-gates")
        self.assertEqual(executed["state"], "ready_for_review")
        self.assertEqual(executed["sites_sha"], original_sha)
        self.assertEqual(executed["local_gates"], "PASS")
        self.assertFalse(executed["published"])
        self.assertFalse(executed["crm_updated"])
        self.assertFalse(executed["outreach_sent"])
        self.assertTrue(executed["human_review_required"])
        state = job_store.list_jobs(queue)[0]
        self.assertEqual(state["state"], "ready_for_review")
        self.assertEqual(state["attempts"], 1)
        self.assertEqual(state["last_gate_exit"], 0)
        self.assertEqual(state["last_sites_sha"], original_sha)
        self.assertEqual(run_shell("git", "status", "--porcelain"), "")
        self.assertEqual(hashlib.sha256(prod_crm.read_bytes()).hexdigest(), db_before)
        self.assertIsNone(job_store.peek(queue))


    def test_canonical_crm_schema_columns_tolerated_without_synthetic_fields(self):
        prod_crm = self.root / "canonical_prod.db"
        db = sqlite3.connect(prod_crm)
        db.execute("""CREATE TABLE leads (
            slug TEXT PRIMARY KEY, nome TEXT, nicho TEXT, cidade TEXT, nota REAL,
            avaliacoes INTEGER, email TEXT, telefone TEXT, whatsapp TEXT, siteAntigo TEXT,
            motivo TEXT, status TEXT DEFAULT 'novo', urlNova TEXT, dataProposta TEXT,
            valor REAL, obs TEXT, contratoStatus TEXT DEFAULT 'pendente', contratoEm TEXT,
            manutencao REAL, pago INTEGER DEFAULT 0, docCliente TEXT, endCliente TEXT,
            atualizado TEXT, placeId TEXT, opportunityType TEXT, opportunityScore INTEGER,
            classificationEvidence TEXT, mainRisk TEXT, factualContent TEXT, imageryLevel TEXT,
            socialUrls TEXT, mapsUrl TEXT, runId INTEGER, criadoEm TEXT, country TEXT,
            locale TEXT, language TEXT, phoneCountryCode TEXT, websiteStatus TEXT,
            siteMode TEXT, currency TEXT, marketTier TEXT
        )""")
        db.execute("INSERT INTO leads (slug, status, whatsapp, country) VALUES (?, ?, ?, ?)",
                   (self.slug, "qualified", "5519999999999", "BR"))
        db.commit()
        db.close()
        lead = crm_source.read_lead(prod_crm, self.slug)
        self.assertEqual(lead["slug"], self.slug)
        self.assertEqual(lead["country"], "BR")
        self.assertNotIn("verified_contact_methods", lead)


    def test_manual_snapshot_export_is_sanitized_and_does_not_touch_queue(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        active = job_store.claim(self.queue, "SECRET_OWNER", now=101, lease_seconds=100)
        jobs_before = job_store.list_jobs(self.queue)
        doc = snapshot_export.build_snapshot(self.queue, now=110)
        self.assertEqual(doc["schemaVersion"], 1)
        self.assertEqual(doc["source"], "prospector-local-qa")
        self.assertEqual(doc["mode"], "manual-snapshot")
        self.assertFalse(doc["canExecute"])
        self.assertEqual(doc["generatedAt"], "1970-01-01T00:01:50Z")
        self.assertEqual(doc["jobs"][0]["leadSlug"], self.slug)
        self.assertEqual(doc["jobs"][0]["state"], "leased")
        self.assertEqual(doc["jobs"][0]["leaseUntil"], 201)
        self.assertEqual(job_store.list_jobs(self.queue), jobs_before)
        exported = json.dumps(doc)
        for forbidden in (active["lease_token"], "SECRET_OWNER", "last_error",
                          "lease_token", "lease_owner", "crm_path",
                          "verified_contact_methods", "email"):
            self.assertNotIn(forbidden, exported)

        entrypoint = Path(worker.__file__).resolve()
        proc = subprocess.run(
            [sys.executable, str(entrypoint), "--queue-db", str(self.queue), "export"],
            capture_output=True, text=True, check=False, timeout=15
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["jobs"][0]["state"], "leased")

    def test_snapshot_refuses_oversized_queue_or_invalid_sha(self):
        job_store.enqueue(self.queue, self.slug, now=100)
        db = sqlite3.connect(self.queue)
        db.execute("UPDATE site_automation_jobs SET last_sites_sha=?",
                   ("insecure/not-a-sha",))
        db.commit()
        db.close()
        with self.assertRaisesRegex(ValueError, "sites SHA"):
            snapshot_export.build_snapshot(self.queue, now=105)
        with mock.patch.object(snapshot_export.job_store, "list_jobs",
                               return_value=[{"lead_slug": "x"}] * 501):
            with self.assertRaisesRegex(ValueError, "safe snapshot row limit"):
                snapshot_export.build_snapshot(self.queue, now=105)



def subprocess_completed_process(args, code):
    import subprocess
    return subprocess.CompletedProcess(args, code, "", "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
