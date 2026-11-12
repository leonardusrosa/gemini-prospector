#!/usr/bin/env python3
"""Prospector site-automation pilot: plan or run LOCAL QA, never deploy/send.

The default run is read-only. --execute-gates explicitly leases ONE job and
runs the existing prospector-sites deterministic gate suite. Even a PASS ends
at ready_for_review; no commit, push, deploy, CRM write, or outreach exists.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

import crm_source
import job_store


def emit(data: dict | list) -> None:
    print(json.dumps(data, ensure_ascii=False, sort_keys=True))


def git_snapshot(sites_repo: Path) -> tuple[str | None, str | None]:
    """A clean SHA is necessary to associate evidence with an exact source tree."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=sites_repo,
            text=True, capture_output=True, timeout=15, check=False,
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=sites_repo,
            text=True, capture_output=True, timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, "Git check unavailable"
    if sha.returncode or dirty.returncode or len(sha.stdout.strip()) != 40:
        return None, "Git repository/HEAD unavailable"
    if dirty.stdout.strip():
        return None, "prospector-sites working tree is not clean"
    return sha.stdout.strip(), None


def run_existing_gates(sites_repo: Path, timeout: int) -> int:
    """Use the existing authoritative tests. Never install dependencies or deploy."""
    result = subprocess.run(
        ["npm", "run", "site-review"],
        cwd=sites_repo, text=True, capture_output=True,
        timeout=timeout, check=False,
    )
    # Do not persist command output, which might contain private business data.
    return result.returncode


def preview(job: dict | None, crm_db: Path, sites_repo: Path) -> dict:
    if job is None:
        return {"mode": "dry-run", "queue": "empty", "mutated": False}
    slug = job["lead_slug"]
    lead = crm_source.read_lead(crm_db, slug)
    issues = crm_source.eligibility_issues(lead) + crm_source.artifact_issues(sites_repo, slug)
    return {
        "mode": "dry-run",
        "lead_slug": slug,
        "state": job["state"],
        "issues": issues,
        "gate_command_if_authorized": "npm run site-review",
        "requires_after_gate": [
            "exact-SHA rendered browser QA", "proposal review",
            "assistant deployed smoke test when applicable",
            "human release approval",
        ],
        "mutated": False,
        "deploy_performed": False,
        "outreach_sent": False,
    }


def execute_one(queue_db: Path, crm_db: Path, sites_repo: Path, timeout: int) -> int:
    if timeout < 1 or timeout > 1800:
        raise ValueError("gate-timeout must be between 1 and 1800 seconds")
    job = job_store.claim(queue_db, owner=f"pilot-{os.getpid()}-{uuid.uuid4().hex[:8]}",
                          lease_seconds=timeout + 120)
    if job is None:
        emit({"mode": "local-gates-only", "queue": "empty"})
        return 0

    slug, job_id, token = job["lead_slug"], job["id"], job["lease_token"]
    sha = None
    try:
        lead = crm_source.read_lead(crm_db, slug)
        issues = crm_source.eligibility_issues(lead) + crm_source.artifact_issues(sites_repo, slug)
        if issues:
            job_store.finish(queue_db, job_id, token, "blocked",
                             reason="; ".join(issues))
            emit({"lead_slug": slug, "state": "blocked", "issues": issues})
            return 1

        sha, git_error = git_snapshot(sites_repo)
        if git_error:
            job_store.finish(queue_db, job_id, token, "blocked", reason=git_error)
            emit({"lead_slug": slug, "state": "blocked", "reason": git_error})
            return 1

        gate_exit = run_existing_gates(sites_repo, timeout)
        if gate_exit:
            job_store.finish(queue_db, job_id, token, "blocked",
                             reason=f"Existing site-review gate failed (exit {gate_exit})",
                             sites_sha=sha, gate_exit=gate_exit)
            emit({"lead_slug": slug, "state": "blocked", "gate_exit": gate_exit, "sites_sha": sha})
            return 1

        job_store.finish(queue_db, job_id, token, "ready_for_review", sites_sha=sha, gate_exit=0)
        emit({
            "lead_slug": slug, "state": "ready_for_review", "local_gates": "PASS",
            "sites_sha": sha, "published": False, "crm_updated": False,
            "outreach_sent": False, "human_review_required": True,
        })
        return 0
    except (OSError, subprocess.TimeoutExpired, sqlite3.OperationalError) as exc:
        # Retry only operational errors. Do not leak subprocess stderr/tokens.
        safe_type = type(exc).__name__
        job_store.finish(queue_db, job_id, token, "retry",
                         reason=f"Transient local execution error ({safe_type})",
                         sites_sha=sha)
        emit({"lead_slug": slug, "state": "retry", "reason": safe_type})
        return 2
    except Exception:
        # Unknown failures are fail-closed; keep a concise error with no secrets.
        job_store.finish(queue_db, job_id, token, "blocked",
                         reason="Unexpected worker error (details intentionally withheld)",
                         sites_sha=sha)
        emit({"lead_slug": slug, "state": "blocked", "reason": "unexpected_worker_error"})
        return 2



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crm-db", type=Path, default=Path("prospector.db"))
    parser.add_argument("--queue-db", type=Path,
                        default=Path(".prospector/auto-deploy-queue.sqlite3"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create isolated queue database (never touch CRM)")
    p_enqueue = commands.add_parser("enqueue", help="Enqueue one verified qualified CRM lead")
    p_enqueue.add_argument("--slug", required=True)
    commands.add_parser("list", help="List queue statuses")
    p_retry = commands.add_parser("requeue", help="Manually reset a blocked/reviewed job")
    p_retry.add_argument("--slug", required=True)
    p_run = commands.add_parser("run", help="Read-only plan by default; never deploy or send")
    p_run.add_argument("--sites-repo", type=Path, required=True)
    p_run.add_argument("--execute-gates", action="store_true",
                       help="Explicitly claim ONE job and run local npm site-review")
    p_run.add_argument("--gate-timeout", type=int, default=900)
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            if not args.crm_db.is_file():
                raise FileNotFoundError(f"Canonical CRM not found: {args.crm_db}")
            job_store.initialize(args.queue_db)
            emit({"queue": str(args.queue_db), "initialized": True, "crm_mutated": False})
        elif args.command == "enqueue":
            lead = crm_source.read_lead(args.crm_db, args.slug)
            issues = crm_source.eligibility_issues(lead)
            if issues:
                emit({"lead_slug": args.slug, "enqueued": False, "issues": issues})
                return 1
            added = job_store.enqueue(args.queue_db, args.slug)
            emit({"lead_slug": args.slug, "enqueued": added, "already_exists": not added})
        elif args.command == "list":
            emit(job_store.list_jobs(args.queue_db))
        elif args.command == "requeue":
            emit({"lead_slug": args.slug, "requeued": job_store.requeue(args.queue_db, args.slug)})
        elif args.command == "run":
            if not args.execute_gates:
                emit(preview(job_store.peek(args.queue_db), args.crm_db, args.sites_repo))
            else:
                return execute_one(args.queue_db, args.crm_db, args.sites_repo, args.gate_timeout)
        return 0
    except (OSError, ValueError) as exc:
        emit({"error": type(exc).__name__, "message": str(exc)[:250]})
        return 2


if __name__ == "__main__":
    sys.exit(main())
