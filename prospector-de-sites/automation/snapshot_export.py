"""Operator-exported queue status: deliberately excludes PII, logs and leases.

Export is read-only and stdout-only. No database or network mutations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import time

import job_store

SNAPSHOT_SOURCE = "prospector-local-qa"
SNAPSHOT_VERSION = 1
MAX_SNAPSHOT_JOBS = 500
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_STATES = frozenset({"pending", "leased", "retry", "blocked", "ready_for_review"})


def build_snapshot(queue_path: Path, *, now: int | None = None) -> dict:
    """Read only selected metadata from the local queue, no CRM access required."""
    rows = job_store.list_jobs(queue_path)
    if len(rows) > MAX_SNAPSHOT_JOBS:
        raise ValueError("Queue exceeds the safe snapshot row limit")
    jobs = []
    seen = set()
    for row in rows:
        slug, state = row["lead_slug"], row["state"]
        if not SLUG_RE.fullmatch(slug) or slug in seen or state not in ALLOWED_STATES:
            raise ValueError("Queue contains an invalid or duplicate job")
        seen.add(slug)
        sha = row["last_sites_sha"]
        if sha is not None and not SHA_RE.fullmatch(sha):
            raise ValueError("Queue contains an invalid sites SHA")
        attempts, updated = row["attempts"], row["updated_at"]
        if not isinstance(attempts, int) or attempts < 0 or not isinstance(updated, int) or updated < 0:
            raise ValueError("Queue contains invalid metadata")
        gate_exit = row["last_gate_exit"]
        if gate_exit is not None and not isinstance(gate_exit, int):
            raise ValueError("Queue contains invalid gate exit")
        jobs.append({
            "leadSlug": slug,
            "state": state,
            "attempts": attempts,
            "updatedAt": updated,
            "nextAttemptAt": row["next_attempt_at"] if state == "retry" else None,
            "leaseUntil": row["lease_until"] if state == "leased" else None,
            "sitesSha": sha,
            "lastGateExit": gate_exit,
        })
    ts = int(time.time()) if now is None else int(now)
    return {
        "schemaVersion": SNAPSHOT_VERSION,
        "source": SNAPSHOT_SOURCE,
        "generatedAt": datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "manual-snapshot",
        "canExecute": False,
        "jobs": jobs,
    }
