"""Independent transactional queue for Prospector site QA. Never writes CRM leads.

The queue belongs in the ignored .prospector directory, separate from prospector.db.
No scheduler, deployment, publishing, or outreach is implemented here.
"""
from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path

FINAL_STATES = frozenset({"ready_for_review", "blocked", "retry"})
MAX_RETRY_ATTEMPTS = 3


def _connect(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"Queue not initialized: {path}. Run init first.")
    db = sqlite3.connect(str(path), timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=10000")
    return db


def initialize(path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=10)
    try:
        db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS site_automation_jobs (
            id INTEGER PRIMARY KEY,
            lead_slug TEXT NOT NULL,
            job_kind TEXT NOT NULL DEFAULT 'preview_qa',
            state TEXT NOT NULL DEFAULT 'pending'
                CHECK (state IN ('pending','leased','retry','blocked','ready_for_review')),
            attempts INTEGER NOT NULL DEFAULT 0,
            next_attempt_at INTEGER NOT NULL DEFAULT 0,
            lease_owner TEXT,
            lease_token TEXT,
            lease_until INTEGER,
            last_error TEXT,
            last_sites_sha TEXT,
            last_gate_exit INTEGER,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            UNIQUE (lead_slug, job_kind)
        );
        CREATE TABLE IF NOT EXISTS site_automation_events (
            id INTEGER PRIMARY KEY,
            job_id INTEGER NOT NULL REFERENCES site_automation_jobs(id),
            occurred_at INTEGER NOT NULL,
            event TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS site_automation_due_idx
            ON site_automation_jobs (state, next_attempt_at, lease_until);
        """)
        db.commit()
    finally:
        db.close()


def enqueue(path: Path, slug: str, *, now: int | None = None) -> bool:
    now = int(time.time()) if now is None else int(now)
    db = _connect(Path(path))
    try:
        db.execute("BEGIN IMMEDIATE")
        cur = db.execute(
            """INSERT OR IGNORE INTO site_automation_jobs
               (lead_slug, job_kind, state, created_at, updated_at)
               VALUES (?, 'preview_qa', 'pending', ?, ?)""",
            (slug, now, now),
        )
        added = cur.rowcount == 1
        if added:
            db.execute(
                """INSERT INTO site_automation_events (job_id, occurred_at, event)
                   VALUES (?, ?, 'enqueued')""",
                (cur.lastrowid, now),
            )
        db.commit()
        return added
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _due_row(db: sqlite3.Connection, now: int):
    return db.execute(
        """SELECT * FROM site_automation_jobs
           WHERE ((state IN ('pending','retry') AND next_attempt_at <= ?)
                  OR (state = 'leased' AND lease_until <= ?))
           ORDER BY created_at, id LIMIT 1""",
        (now, now),
    ).fetchone()


def peek(path: Path, *, now: int | None = None) -> dict | None:
    """Read-only inspection; does not acquire or mutate a lease."""
    now = int(time.time()) if now is None else int(now)
    db = _connect(Path(path))
    try:
        row = _due_row(db, now)
        return dict(row) if row else None
    finally:
        db.close()


def claim(path: Path, owner: str, *, lease_seconds: int = 1800, now: int | None = None) -> dict | None:
    """Single-writer atomic claim. An expired lease may be reclaimed safely."""
    if not owner or lease_seconds < 1:
        raise ValueError("A non-empty owner and positive lease are required.")
    now = int(time.time()) if now is None else int(now)
    db = _connect(Path(path))
    try:
        db.execute("BEGIN IMMEDIATE")
        row = _due_row(db, now)
        if not row:
            db.commit()
            return None
        token = uuid.uuid4().hex
        db.execute(
            """UPDATE site_automation_jobs
               SET state='leased', attempts=attempts+1,
                   lease_owner=?, lease_token=?, lease_until=?, updated_at=?
               WHERE id=?""",
            (owner, token, now + lease_seconds, now, row["id"]),
        )
        db.execute(
            """INSERT INTO site_automation_events (job_id, occurred_at, event, detail)
               VALUES (?, ?, 'claimed', ?)""",
            (row["id"], now, "recovered_expired_lease" if row["state"] == "leased" else ""),
        )
        updated = db.execute("SELECT * FROM site_automation_jobs WHERE id=?", (row["id"],)).fetchone()
        db.commit()
        return dict(updated)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def finish(
    path: Path,
    job_id: int,
    lease_token: str,
    state: str,
    *,
    reason: str = "",
    sites_sha: str | None = None,
    gate_exit: int | None = None,
    now: int | None = None,
) -> None:
    """Lease-fenced completion. A stale worker cannot overwrite a new claim."""
    if state not in FINAL_STATES:
        raise ValueError(f"Unsupported completion state: {state}")
    if not lease_token:
        raise ValueError("lease_token is mandatory")
    now = int(time.time()) if now is None else int(now)
    db = _connect(Path(path))
    try:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT attempts, lease_until FROM site_automation_jobs WHERE id=? AND state='leased' AND lease_token=?",
            (job_id, lease_token),
        ).fetchone()
        if not row:
            raise RuntimeError("Stale or missing lease: completion refused")
        if row["lease_until"] is None or row["lease_until"] <= now:
            raise RuntimeError("Expired lease: completion refused")
        # Operational errors receive a bounded retry budget, with manual reset.
        if state == "retry" and row["attempts"] >= MAX_RETRY_ATTEMPTS:
            state = "blocked"
            reason = f"Retry budget exhausted ({MAX_RETRY_ATTEMPTS} attempts): {reason}"
        # Factual/QA blockers never retry silently.
        delay = min(3600, 30 * (2 ** min(max(row["attempts"] - 1, 0), 7))) if state == "retry" else 0
        db.execute(
            """UPDATE site_automation_jobs
               SET state=?, lease_owner=NULL, lease_token=NULL, lease_until=NULL,
                   next_attempt_at=?, last_error=?, last_sites_sha=?,
                   last_gate_exit=?, updated_at=?
               WHERE id=? AND lease_token=?""",
            (state, now + delay, reason[:500], sites_sha, gate_exit, now, job_id, lease_token),
        )
        db.execute(
            """INSERT INTO site_automation_events (job_id, occurred_at, event, detail)
               VALUES (?, ?, ?, ?)""",
            (job_id, now, state, reason[:500]),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def requeue(path: Path, slug: str, *, now: int | None = None) -> bool:
    """Operator-only reset. Never steals an active lease."""
    now = int(time.time()) if now is None else int(now)
    db = _connect(Path(path))
    try:
        db.execute("BEGIN IMMEDIATE")
        cur = db.execute(
            """UPDATE site_automation_jobs
               SET state='pending', attempts=0, next_attempt_at=0, last_error=NULL, updated_at=?
               WHERE lead_slug=? AND job_kind='preview_qa'
                 AND state IN ('blocked','retry','ready_for_review')""",
            (now, slug),
        )
        if cur.rowcount:
            db.execute(
                """INSERT INTO site_automation_events (job_id, occurred_at, event)
                   SELECT id, ?, 'operator_requeue'
                   FROM site_automation_jobs WHERE lead_slug=? AND job_kind='preview_qa'""",
                (now, slug),
            )
        db.commit()
        return cur.rowcount == 1
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def list_jobs(path: Path) -> list[dict]:
    db = _connect(Path(path))
    try:
        return [dict(row) for row in db.execute(
            """SELECT id, lead_slug, state, attempts, next_attempt_at, lease_until,
                      last_error, last_sites_sha, last_gate_exit, updated_at
               FROM site_automation_jobs ORDER BY created_at, id"""
        ).fetchall()]
    finally:
        db.close()
