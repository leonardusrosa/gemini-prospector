#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector Client CMS — Audit Trail Logging Module.
Records immutable structured JSONL logs of all administrative actions
(draft, publish, rollback, media_upload) without exposing credentials.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
from typing import Any, Dict, List, Optional


def log_audit_event(
    root_dir: pathlib.Path,
    slug: str,
    actor: str,
    action: str,
    commit_sha: Optional[str] = None,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Appends an audit record to .prospector-editor/audit/<slug>.jsonl.
    Never stores passwords, tokens, API keys or secret auth headers.
    """
    audit_dir = root_dir / ".prospector-editor" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / f"{slug}.jsonl"

    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "slug": slug,
        "actor": actor or "unknown",
        "action": action,
        "commitSha": commit_sha or "",
        "status": status,
        "details": details or {},
    }

    # Sanitize details to guarantee zero secrets leakage
    sanitized_details = {}
    for k, v in (details or {}).items():
        if any(secret_term in k.lower() for secret_term in ["token", "key", "secret", "password", "auth", "hash"]):
            continue
        sanitized_details[k] = v
    record["details"] = sanitized_details

    line = json.dumps(record, ensure_ascii=False)
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return record


def get_audit_history(root_dir: pathlib.Path, slug: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves the recent audit trail for a specific tenant."""
    audit_file = root_dir / ".prospector-editor" / "audit" / f"{slug}.jsonl"
    if not audit_file.exists():
        return []

    records = []
    try:
        with open(audit_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        return []

    return records[-limit:]
