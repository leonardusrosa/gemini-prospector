"""Flow operator/browser execution ledger; no network, credentials or generation calls.

Persist each reservation BEFORE the browser submits a generation. An unresolved
reservation blocks further submissions, including account rotation and retries.
Only a single trusted browser operator may write a given job at a time.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from hero_motion import ACCOUNT_ALIASES, MAX_TOTAL_GENERATIONS, sha_file, SHA256, validate_plan

STEPS = ("desktop_start", "desktop_end", "mobile_start", "mobile_end",
         "desktop_video", "mobile_video")

def new_job(plan, plan_hash, cap=None):
    validate_plan(plan)
    if not isinstance(plan_hash, str) or not SHA256.fullmatch(plan_hash):
        raise ValueError("Exact plan hash required")
    if cap is not None:
        _credits(cap)
    return {"schemaVersion": 1, "leadSlug": plan["leadSlug"], "planSha256": plan_hash,
            "creditCap": cap, "entries": [], "pending": None,
            "publicReleaseAuthorized": False, "humanApprovalReceived": False}

def _credits(value):
    if type(value) is not int or value < 0:
        raise ValueError("Credits must be observed nonnegative integers")
    return value

def _evidence(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Evidence must be a nonempty file")
    return {"path": str(path), "sha256": sha_file(path)}

def _check_ref(ref):
    if _evidence(ref["path"]) != ref:
        raise ValueError("Evidence changed after capture")

def reserve(job, step, alias, model, balance, cost, quote_evidence, *, retry=False):
    if job["pending"] is not None:
        raise ValueError("Reconcile the pending request before any new submission")
    if step not in STEPS or alias not in ACCOUNT_ALIASES or not isinstance(model, str) or not model.strip():
        raise ValueError("Unknown step, account or model")
    balance, cost = _credits(balance), _credits(cost)
    entries = job["entries"]
    if len(entries) >= MAX_TOTAL_GENERATIONS:
        raise ValueError("Generation budget exhausted")
    used = {e["step"] for e in entries}
    if retry:
        if step not in used or sum(e["retry"] for e in entries) >= 2:
            raise ValueError("Retry is not available")
        if step.endswith("_video") is False and any(e["step"] == step.split("_")[0] + "_video" for e in entries):
            raise ValueError("Changing a frame after its video exists requires a new job")
    elif step != next((s for s in STEPS if s not in used), None):
        raise ValueError("Unexpected or duplicate base generation")
    if step.endswith("_video"):
        prefix = step.split("_")[0]
        for frame in (prefix + "_start", prefix + "_end"):
            latest = next((e for e in reversed(entries) if e["step"] == frame), None)
            if latest is None or latest["outcome"] != "downloaded":
                raise ValueError("Both frame downloads required before video")
    if balance < cost:
        raise ValueError("Insufficient verified account balance")
    cap = job["creditCap"]
    if cap is not None and sum(e["creditsSpent"] for e in entries) + cost > cap:
        raise ValueError("Credit cap would be exceeded")
    job["pending"] = {"step": step, "accountAlias": alias, "model": model,
                      "balanceBefore": balance, "quotedCredits": cost,
                      "quoteEvidence": _evidence(quote_evidence), "retry": bool(retry)}
    return job["pending"]

def reconcile(job, alias, balance_after, charge_evidence, *, outcome, artifact=None):
    pending = job["pending"]
    if pending is None or alias != pending["accountAlias"]:
        raise ValueError("No pending request for this account")
    _check_ref(pending["quoteEvidence"])
    after = _credits(balance_after)
    spent = pending["balanceBefore"] - after
    if spent < 0 or spent != pending["quotedCredits"]:
        raise ValueError("Charge mismatch; keep request unresolved for manual investigation")
    if outcome not in {"downloaded", "failed"}:
        raise ValueError("Explicit outcome required")
    if (outcome == "downloaded") != (artifact is not None):
        raise ValueError("Successful requests require an exact downloaded artifact")
    ref = _evidence(artifact) if artifact is not None else None
    if ref is not None:
        ext = Path(ref["path"]).suffix.lower()
        allowed = {".mp4", ".webm"} if pending["step"].endswith("_video") else {".png", ".jpg", ".jpeg", ".webp"}
        if ext not in allowed:
            raise ValueError("Wrong downloaded asset format")
    entry = {**pending, "balanceAfter": after, "creditsSpent": spent,
             "uiCostChecked": True, "chargeEvidence": _evidence(charge_evidence),
             "outcome": outcome, "artifact": ref}
    job["entries"].append(entry)
    job["pending"] = None
    return entry

def delivery_inputs(job):
    if job["pending"] is not None:
        raise ValueError("Unresolved generation")
    latest = {e["step"]: e for e in job["entries"]}
    if set(latest) != set(STEPS) or any(e["outcome"] != "downloaded" for e in latest.values()):
        raise ValueError("Four frames and two successful clips required")
    for e in job["entries"]:
        _check_ref(e["quoteEvidence"])
        _check_ref(e["chargeEvidence"])
        if e["artifact"] is not None:
            _check_ref(e["artifact"])
    return {"frames": {s: latest[s]["artifact"] for s in STEPS[:4]},
            "videos": {s.split("_")[0]: latest[s]["artifact"] for s in STEPS[4:]},
            "creditLedger": job["entries"],
            "creditsSpent": sum(e["creditsSpent"] for e in job["entries"]),
            "manualApprovalRequired": True, "publicReleaseAuthorized": False}

def save_job(path, job):
    """Atomic checkpoint; reserve must be saved before the browser clicks generate."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".flow-job-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
