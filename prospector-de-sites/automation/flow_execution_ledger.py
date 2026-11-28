"""Flow operator/browser execution ledger; no network, credentials or generation calls.

Persist each reservation BEFORE the browser submits a generation. An unresolved
reservation blocks further submissions, including account rotation and retries.
Only a single trusted browser operator may write a given job at a time.
"""
from __future__ import annotations

import json
import copy
import os
import tempfile
from pathlib import Path
from hero_motion import ACCOUNT_ALIASES, MAX_TOTAL_GENERATIONS, sha_file, SHA256, validate_plan, is_storyboard, storyboard_source_refs

STEPS = ("desktop_start", "desktop_end", "mobile_start", "mobile_end",
         "desktop_video", "mobile_video")

STORYBOARD_STEPS = ("desktop_storyboard", "mobile_storyboard", "desktop_video", "mobile_video")

def _steps(job):
    return STORYBOARD_STEPS if job.get("route")=="storyboard" else STEPS

def new_job(plan, plan_hash, cap=None, *, reconciliation_evidence=None):
    validate_plan(plan)
    if not isinstance(plan_hash, str) or not SHA256.fullmatch(plan_hash):
        raise ValueError("Exact plan hash required")
    if cap is not None:
        _credits(cap)
    extra={}
    if is_storyboard(plan):
        if reconciliation_evidence is None:
            raise ValueError("Prior request reconciliation evidence required")
        extra={"route":"storyboard","sourceReferences":[_evidence(ref["path"]) for ref in storyboard_source_refs(plan)],
               "priorReconciliationEvidence":_evidence(reconciliation_evidence)}
    return {"schemaVersion": 1, **extra, "leadSlug": plan["leadSlug"], "planSha256": plan_hash,
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

def reserve(job, step, alias, model, balance, cost, quote_evidence, *, retry=False, reference_evidence=None, reference_hashes=None):
    if job["pending"] is not None:
        raise ValueError("Reconcile the pending request before any new submission")
    steps=_steps(job)
    if step not in steps or alias not in ACCOUNT_ALIASES or not isinstance(model, str) or not model.strip():
        raise ValueError("Unknown step, account or model")
    balance, cost = _credits(balance), _credits(cost)
    entries = job["entries"]
    if len(entries) >= len(steps)+2:
        raise ValueError("Generation budget exhausted")
    used = {e["step"] for e in entries}
    if retry:
        if step not in used or sum(e["retry"] for e in entries) >= 2:
            raise ValueError("Retry is not available")
        if step.endswith("_video") is False and any(e["step"] == step.split("_")[0] + "_video" for e in entries):
            raise ValueError("Changing a frame after its video exists requires a new job")
    elif step != next((s for s in steps if s not in used), None):
        raise ValueError("Unexpected or duplicate base generation")
    if step.endswith("_video"):
        prefix = step.split("_")[0]
        for frame in ((prefix+"_storyboard",) if steps==STORYBOARD_STEPS else (prefix+"_start",prefix+"_end")):
            latest = next((e for e in reversed(entries) if e["step"] == frame), None)
            if latest is None or latest["outcome"] != "downloaded":
                raise ValueError("Required reference downloads missing before video")
    extra={}
    if steps==STORYBOARD_STEPS:
        _check_ref(job["priorReconciliationEvidence"])
        if reference_evidence is None:
            raise ValueError("Reference selection evidence required")
        if step.endswith("_video"):
            expected=[latest["artifact"]["sha256"]]
            _check_ref(latest["artifact"])
            if latest["accountAlias"]!=alias:
                raise ValueError("Use the same account for a storyboard and its video")
        else:
            expected=[ref["sha256"] for ref in job["sourceReferences"]]
            for ref in job["sourceReferences"]:
                _check_ref(ref)
        if not isinstance(reference_hashes,list) or sorted(reference_hashes)!=sorted(expected):
            raise ValueError("Reference hashes do not match the approved input")
        extra={"referenceEvidence":_evidence(reference_evidence),"referenceHashes":expected}
    if balance < cost:
        raise ValueError("Insufficient verified account balance")
    cap = job["creditCap"]
    if cap is not None and sum(e["creditsSpent"] for e in entries) + cost > cap:
        raise ValueError("Credit cap would be exceeded")
    job["pending"] = {**extra, "step": step, "accountAlias": alias, "model": model,
                      "balanceBefore": balance, "quotedCredits": cost,
                      "quoteEvidence": _evidence(quote_evidence), "retry": bool(retry)}
    return job["pending"]

def reconcile(job, alias, balance_after, charge_evidence, *, outcome, artifact=None):
    pending = job["pending"]
    if pending is None or alias != pending["accountAlias"]:
        raise ValueError("No pending request for this account")
    _check_ref(pending["quoteEvidence"])
    if job.get("route")=="storyboard":
        _check_ref(pending["referenceEvidence"])
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
    steps=_steps(job)
    if set(latest) != set(steps) or any(e["outcome"] != "downloaded" for e in latest.values()):
        raise ValueError("All required storyboard/frame and video downloads must succeed")
    for e in job["entries"]:
        _check_ref(e["quoteEvidence"])
        _check_ref(e["chargeEvidence"])
        if e["artifact"] is not None:
            _check_ref(e["artifact"])
    if steps==STORYBOARD_STEPS:
        _check_ref(job["priorReconciliationEvidence"])
        for e in job["entries"]:
            _check_ref(e["referenceEvidence"])
        return {"storyboards":{s.split("_")[0]:dict(latest[s]["artifact"]) for s in steps[:2]},
                "videos":{s.split("_")[0]:dict(latest[s]["artifact"]) for s in steps[2:]},
                "creditLedger":copy.deepcopy(job["entries"]),"priorReconciliationEvidence":dict(job["priorReconciliationEvidence"]),
                "creditCap":job["creditCap"],"creditsSpent":sum(e["creditsSpent"] for e in job["entries"]),
                "manualApprovalRequired":True,"publicReleaseAuthorized":False}
    return {"frames": {s: latest[s]["artifact"] for s in STEPS[:4]},
            "videos": {s.split("_")[0]: latest[s]["artifact"] for s in STEPS[4:]},
            "creditLedger": job["entries"],
            "creditsSpent": sum(e["creditsSpent"] for e in job["entries"]),
            "manualApprovalRequired": True, "publicReleaseAuthorized": False}

def verify_storyboard_delivery(plan, delivery):
    """Replay the offline ledger, including all evidence hashes and dependencies."""
    evidence=delivery.get("priorReconciliationEvidence")
    if not isinstance(evidence,dict):
        raise ValueError("Prior reconciliation evidence missing")
    _check_ref(evidence)
    replay=new_job(plan,delivery["planSha256"],delivery.get("creditCap"),
                   reconciliation_evidence=evidence["path"])
    for entry in delivery["creditLedger"]:
        try:
            reserve(replay,entry["step"],entry["accountAlias"],entry["model"],
                    entry["balanceBefore"],entry["quotedCredits"],entry["quoteEvidence"]["path"],
                    retry=entry["retry"],reference_evidence=entry["referenceEvidence"]["path"],
                    reference_hashes=entry["referenceHashes"])
            actual=reconcile(replay,entry["accountAlias"],entry["balanceAfter"],
                    entry["chargeEvidence"]["path"],outcome=entry["outcome"],
                    artifact=entry["artifact"]["path"] if entry["artifact"] else None)
        except (KeyError,TypeError,OSError) as exc:
            raise ValueError("Invalid storyboard ledger evidence") from exc
        if actual!=entry:
            raise ValueError("Storyboard ledger evidence mismatch")
    actual=delivery_inputs(replay)
    for name in ("desktop","mobile"):
        for kind in ("storyboards","videos"):
            if actual[kind][name]["sha256"]!=delivery[kind][name]["sha256"]:
                raise ValueError("Delivered storyboard/video does not match ledger")
    return actual

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
