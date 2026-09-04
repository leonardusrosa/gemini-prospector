#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic validator to prevent silent factual drift across maintenance patches (V2.2.2).

Shallow-clone safe trusted baseline resolution with immutable anchors:
1. Targeted fetch helper: ensure_git_commit_available(ref, repo_dir, is_ci)
2. External hash anchor: FACTUAL_DRIFT_BASELINE_SHA256
3. Hash-only mode: if historical commit is unavailable, identical protected state PASSES,
   mutations FAIL CLOSED with FACTUAL_DRIFT_HISTORY_REQUIRED_FOR_MUTATION.
4. No HEAD~1 fallback in CI/production under any circumstances.
5. Strict resolution priority:
   - EXPLICIT_REF
   - VERCEL_PREVIOUS_SHA
   - CI_BASE_REF
   - EXTERNAL_SHA256
   - PERSISTED_FETCHED_COMMIT
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

PRESENTATION_FILE_PATTERN = re.compile(
    r"(?i)(?:\.html|\.css|\.scss|\.js|\.jsx|\.tsx|\.ts|design-read\.md|\/assets\/|hero|templates)"
)

LAYOUT_INTENT_PATTERN = re.compile(
    r"(?i)\b(?:layout|responsive|navbar|header|nav|css|mobile|desktop|tablet|style|spacing|padding|visual|hero|motion|drawer|overflow|chore|cleanup|refactor|fix)\b"
)

VALID_EXTERNAL_SOURCE_TYPES = {
    "official_site",
    "official_record",
    "direct_maps",
    "operator_provided",
}

VALID_SOURCE_TYPES = VALID_EXTERNAL_SOURCE_TYPES | {"accepted_baseline"}

PROTECTED_PATHS = {
    "businessName",
    "doctorName",
    "credentials",
    "factualEvidence.verifiedServices",
    "phone",
    "whatsapp",
    "address",
    "cnpj",
    "pricing",
    "googleReviews.profileName",
    "googleReviews.profileUrl",
    "googleReviews.placeId",
    "googleReviews.cid",
    "googleReviews.googleMapsFeatureId",
    "googleReviews.aggregateRating",
    "googleReviews.ratingCount",
    "googleReviews.observedEntries",
    "googleReviews.reviews",
}


@dataclass
class FactualDriftResult:
    passed: bool
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    mutated_fields: List[str] = field(default_factory=list)
    authorized_fields: List[str] = field(default_factory=list)
    baseline_mode: Optional[str] = None
    baseline_sha: Optional[str] = None


def is_presentation_patch(
    changed_files: Optional[List[str]] = None, commit_message: str = ""
) -> bool:
    """Return True if changed files or commit message indicate presentation/maintenance sensitivity."""
    if changed_files:
        for f in changed_files:
            f_clean = f.replace("\\", "/")
            if PRESENTATION_FILE_PATTERN.search(f_clean):
                return True
    if commit_message and LAYOUT_INTENT_PATTERN.search(commit_message):
        return True
    return False


def normalize_services(manifest: Dict[str, Any]) -> List[str]:
    """Extract normalized list of service claims."""
    raw = (
        manifest.get("factualServices")
        or manifest.get("verifiedServices")
        or (manifest.get("factualEvidence") or {}).get("verifiedServices")
        or []
    )
    res = []
    for item in raw:
        if isinstance(item, dict):
            claim = str(item.get("claim") or "").strip()
            if claim:
                res.append(claim)
        elif isinstance(item, str) and item.strip():
            res.append(item.strip())
    return sorted(res)


def extract_protected_state(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Extract comparable values for all protected canonical paths."""
    state: Dict[str, Any] = {}
    if not manifest or not isinstance(manifest, dict):
        return state

    state["businessName"] = manifest.get("businessName") or manifest.get("profileName")
    state["doctorName"] = manifest.get("doctorName") or manifest.get("expertName")
    state["credentials"] = manifest.get("credentials") or manifest.get("cro") or manifest.get("crm")
    state["factualEvidence.verifiedServices"] = normalize_services(manifest)

    state["phone"] = manifest.get("phone") or (manifest.get("whatsapp") or {}).get("number")
    state["whatsapp"] = manifest.get("whatsapp")
    state["address"] = manifest.get("address")
    state["cnpj"] = manifest.get("cnpj")
    state["pricing"] = manifest.get("pricing") or manifest.get("prices")

    gr = manifest.get("googleReviews") or {}
    state["googleReviews.profileName"] = gr.get("profileName")
    state["googleReviews.profileUrl"] = gr.get("profileUrl")
    state["googleReviews.placeId"] = gr.get("placeId")
    state["googleReviews.cid"] = gr.get("cid")
    state["googleReviews.googleMapsFeatureId"] = gr.get("googleMapsFeatureId")
    state["googleReviews.aggregateRating"] = gr.get("aggregateRating")
    state["googleReviews.ratingCount"] = gr.get("ratingCount") if gr.get("ratingCount") is not None else gr.get("reviewCount")

    state["googleReviews.observedEntries"] = [
        (e.get("fingerprint"), e.get("author"), e.get("rating"), e.get("hasText"))
        for e in (gr.get("observedEntries") or [])
        if isinstance(e, dict)
    ]
    state["googleReviews.reviews"] = [
        (r.get("id"), r.get("author"), r.get("rating"), r.get("text"))
        for r in (gr.get("reviews") or [])
        if isinstance(r, dict)
    ]

    return state


def ensure_git_commit_available(
    ref: Optional[str], repo_dir: Optional[Path] = None, is_ci: bool = False
) -> Optional[str]:
    """Ensure git commit is available locally, performing a targeted fetch if needed in CI."""
    if not ref or not isinstance(ref, str) or not ref.strip():
        return None
    clean_ref = ref.strip()

    if repo_dir:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--verify", f"{clean_ref}^{{commit}}"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except Exception:
            pass

        if is_ci:
            try:
                subprocess.run(
                    ["git", "fetch", "--no-tags", "--depth=1", "origin", clean_ref],
                    cwd=str(repo_dir),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                proc2 = subprocess.run(
                    ["git", "rev-parse", "--verify", f"{clean_ref}^{{commit}}"],
                    cwd=str(repo_dir),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc2.returncode == 0 and proc2.stdout.strip():
                    return proc2.stdout.strip()
            except Exception:
                pass

    return None


def calculate_baseline_sha256(file_bytes: bytes) -> str:
    """Compute SHA-256 with normalized LF line endings."""
    norm = file_bytes.decode("utf-8", errors="replace").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(norm).hexdigest()


def verify_accepted_baseline(
    repo_dir: Optional[Path],
    commit_sha: str,
    manifest_path: str,
    protected_path: str,
    expected_val: Any,
    trusted_persisted_baseline: Optional[Dict[str, Any]] = None,
    is_ci: bool = False,
) -> Optional[str]:
    """Verify that commit_sha contains expected_val via git or trusted prior baseline file.

    Fetches targeted commit in shallow CI checkout if absent locally.
    """
    if repo_dir:
        resolved_sha = ensure_git_commit_available(commit_sha, repo_dir, is_ci)
        if resolved_sha:
            try:
                proc = subprocess.run(
                    ["git", "show", f"{resolved_sha}:{manifest_path}"],
                    cwd=str(repo_dir),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode == 0:
                    past_manifest = json.loads(proc.stdout)
                    past_state = extract_protected_state(past_manifest)
                    past_val = past_state.get(protected_path)
                    if isinstance(expected_val, list) and isinstance(past_val, list):
                        if sorted(expected_val) != sorted(past_val):
                            return f"Committed value {past_val} does not match expected baseline {expected_val}"
                    elif past_val != expected_val:
                        return f"Committed value {past_val} does not match expected baseline {expected_val}"
                    return None
            except Exception:
                pass

    # Check trusted prior baseline history (from trusted baseline commit, NOT current HEAD)
    if trusted_persisted_baseline:
        history = trusted_persisted_baseline.get("acceptedBaselineHistory", {}).get(commit_sha)
        if history:
            for slug, fields in history.items():
                if slug in manifest_path and fields.get(protected_path) is not None:
                    h_val = fields.get(protected_path)
                    if isinstance(expected_val, list) and isinstance(h_val, list):
                        if sorted(expected_val) == sorted(h_val):
                            return None
                    elif h_val == expected_val:
                        return None

    return f"Git commit '{commit_sha}' could not be verified in git history or trusted prior baseline file"


def validate_factual_refresh_artifact(
    artifact_data: Dict[str, Any],
    base_dir: Optional[Path] = None,
    repo_dir: Optional[Path] = None,
    trusted_persisted_baseline: Optional[Dict[str, Any]] = None,
    is_ci: bool = False,
) -> tuple[Set[str], List[str]]:
    """Validate factual-refresh.json artifact and return authorized field paths."""
    errors: List[str] = []
    authorized_paths: Set[str] = set()

    if not isinstance(artifact_data, dict):
        return authorized_paths, ["factual-refresh artifact root must be a JSON object"]

    if artifact_data.get("schemaVersion") != 1:
        errors.append("factual-refresh artifact requires schemaVersion: 1")
    if not artifact_data.get("collectedAt"):
        errors.append("factual-refresh artifact requires collectedAt ISO-8601 timestamp")

    sources = artifact_data.get("sources")
    if not isinstance(sources, list) or len(sources) == 0:
        errors.append("factual-refresh artifact requires non-empty sources array")
        return authorized_paths, errors

    declared_sources: Dict[str, Dict[str, Any]] = {}
    for idx, s in enumerate(sources):
        if not isinstance(s, dict):
            errors.append(f"sources[{idx}] must be an object")
            continue
        s_id = s.get("id")
        s_type = s.get("type")

        if not s_id or not isinstance(s_id, str):
            errors.append(f"sources[{idx}] missing valid 'id'")
        elif s_id in declared_sources:
            errors.append(f"duplicate source id '{s_id}'")
        else:
            declared_sources[s_id] = s

        if s_type not in VALID_SOURCE_TYPES:
            errors.append(f"sources[{idx}] type must be one of {sorted(VALID_SOURCE_TYPES)}, got '{s_type}'")
            continue

        if s_type == "accepted_baseline":
            commit_sha = s.get("commitSha")
            man_path = s.get("manifestPath")
            prot_path = s.get("protectedPath")
            exp_val = s.get("expectedValue")
            if not commit_sha or not man_path or not prot_path or exp_val is None:
                errors.append(
                    f"sources[{idx}] of type='accepted_baseline' requires commitSha, manifestPath, protectedPath, expectedValue"
                )
            else:
                verify_err = verify_accepted_baseline(
                    repo_dir, commit_sha, man_path, prot_path, exp_val, trusted_persisted_baseline, is_ci
                )
                if verify_err:
                    errors.append(f"sources[{idx}] accepted_baseline verification failed: ${verify_err}")

        elif s_type in VALID_EXTERNAL_SOURCE_TYPES:
            art_path = s.get("artifactPath")
            if not art_path or not isinstance(art_path, str):
                errors.append(f"sources[{idx}] missing 'artifactPath'")
            elif base_dir:
                full_path = (base_dir / art_path).resolve()
                if not full_path.exists() or not full_path.is_file():
                    errors.append(f"sources[{idx}] artifactPath does not exist: {art_path}")
                elif full_path.stat().st_size == 0:
                    errors.append(f"sources[{idx}] artifactPath is empty placeholder: {art_path}")
                else:
                    if full_path.suffix.lower() == ".json":
                        try:
                            content = full_path.read_text(encoding="utf-8")
                            if s_type == "official_record" and (
                                '"justification"' in content and "baseline" in content.lower()
                            ):
                                errors.append(
                                    f"sources[{idx}] internal baseline summary at '{art_path}' cannot declare itself 'official_record'. Use type='accepted_baseline'."
                                )
                        except Exception:
                            pass

    changed_fields = artifact_data.get("changedFields")
    if not isinstance(changed_fields, list) or len(changed_fields) == 0:
        errors.append("factual-refresh artifact requires non-empty changedFields array")
        return authorized_paths, errors

    for idx, cf in enumerate(changed_fields):
        if not isinstance(cf, dict):
            errors.append(f"changedFields[{idx}] must be an object")
            continue
        p_path = cf.get("path")
        ev_ids = cf.get("evidenceIds")

        if not p_path or not isinstance(p_path, str):
            errors.append(f"changedFields[{idx}] missing valid 'path'")
            continue

        if not isinstance(ev_ids, list) or len(ev_ids) == 0:
            errors.append(f"changedFields[{idx}] for path '{p_path}' must have non-empty evidenceIds array")
            continue

        for eid in ev_ids:
            if eid not in declared_sources:
                errors.append(
                    f"changedFields[{idx}] path '{p_path}' references undeclared evidenceId '{eid}'"
                )

        authorized_paths.add(p_path)

    return authorized_paths, errors


def check_factual_drift(
    before_manifest: Optional[Dict[str, Any]],
    after_manifest: Dict[str, Any],
    commit_message: str = "",
    changed_files: Optional[List[str]] = None,
    factual_refresh_data: Optional[Dict[str, Any]] = None,
    factual_refresh_modified: bool = True,
    base_dir: Optional[Path] = None,
    repo_dir: Optional[Path] = None,
    trusted_persisted_baseline: Optional[Dict[str, Any]] = None,
    is_ci: bool = False,
    baseline_mode: Optional[str] = None,
    baseline_sha: Optional[str] = None,
    history_available: bool = True,
) -> FactualDriftResult:
    """Validate that protected factual fields do not drift without field-bound authorization."""
    failures: List[str] = []
    warnings: List[str] = []

    state_after = extract_protected_state(after_manifest)
    has_protected_fields = any(v is not None and v != [] for v in state_after.values())

    # TRUE FAIL-CLOSED BASELINE (Requirement 3 & 6)
    if before_manifest is None:
        if has_protected_fields or is_ci:
            return FactualDriftResult(
                passed=False,
                failures=["FACTUAL_DRIFT_BASELINE_UNRESOLVED: No trustworthy baseline manifest could be resolved."],
                baseline_mode=baseline_mode,
                baseline_sha=baseline_sha,
            )
        return FactualDriftResult(passed=True, baseline_mode=baseline_mode, baseline_sha=baseline_sha)

    state_before = extract_protected_state(before_manifest)

    mutated_paths: List[str] = []
    for p, val_b in state_before.items():
        val_a = state_after.get(p)
        if json.dumps(val_b, sort_keys=True) != json.dumps(val_a, sort_keys=True):
            mutated_paths.append(p)

    # If no protected fields mutated: PASS
    if not mutated_paths:
        return FactualDriftResult(
            passed=True,
            mutated_fields=[],
            baseline_mode=baseline_mode,
            baseline_sha=baseline_sha,
        )

    # HASH-ONLY MODE PROTECTION (V2.2.2):
    # If historical commit is unavailable, mutations cannot be authorized without diff provenance.
    if not history_available:
        return FactualDriftResult(
            passed=False,
            failures=[
                "FACTUAL_DRIFT_HISTORY_REQUIRED_FOR_MUTATION: Protected factual fields were mutated, "
                "but historical baseline commit is unavailable to verify artifact provenance and staleness."
            ],
            mutated_fields=mutated_paths,
            baseline_mode=baseline_mode,
            baseline_sha=baseline_sha,
        )

    # STALE REFRESH MUST NOT AUTHORIZE (Requirement 1)
    is_refresh_in_files = False
    if changed_files:
        for f in changed_files:
            if "factual-refresh.json" in f.replace("\\", "/"):
                is_refresh_in_files = True
                break

    refresh_active = factual_refresh_modified or is_refresh_in_files

    authorized_paths: Set[str] = set()
    if factual_refresh_data is not None:
        if not refresh_active:
            failures.append(
                "[factual-drift] research/factual-refresh.json was not added or modified in this change set and cannot authorize factual mutations (stale refresh)."
            )
        else:
            auths, artifact_errors = validate_factual_refresh_artifact(
                factual_refresh_data, base_dir, repo_dir, trusted_persisted_baseline, is_ci
            )
            failures.extend(artifact_errors)
            authorized_paths = auths
    elif base_dir:
        rf_path = base_dir / "research" / "factual-refresh.json"
        if rf_path.exists() and rf_path.is_file():
            if not refresh_active:
                failures.append(
                    "[factual-drift] research/factual-refresh.json was not added or modified in this change set and cannot authorize factual mutations (stale refresh)."
                )
            else:
                try:
                    data = json.loads(rf_path.read_text(encoding="utf-8"))
                    auths, artifact_errors = validate_factual_refresh_artifact(
                        data, base_dir, repo_dir, trusted_persisted_baseline, is_ci
                    )
                    failures.extend(artifact_errors)
                    authorized_paths = auths
                except Exception as ex:
                    failures.append(f"Failed to parse research/factual-refresh.json: {ex}")

    # UNAUTHORIZED MUTATION ALWAYS FAILS (Requirement 2)
    for p in mutated_paths:
        is_authorized = (
            p in authorized_paths
            or any(p.startswith(a + ".") for a in authorized_paths)
            or (p.startswith("factualEvidence.") and p.split(".", 1)[1] in authorized_paths)
        )
        if not is_authorized:
            failures.append(
                f"[factual-drift] Protected factual field '{p}' was mutated without explicit authorization "
                f"in factual-refresh.json."
            )

    passed = len(failures) == 0
    return FactualDriftResult(
        passed=passed,
        failures=failures,
        warnings=warnings,
        mutated_fields=mutated_paths,
        authorized_fields=list(authorized_paths),
        baseline_mode=baseline_mode,
        baseline_sha=baseline_sha,
    )


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Validate that patch does not induce factual drift.")
    parser.add_argument("--before", default="", help="Path to manifest before patch")
    parser.add_argument("--after", required=True, help="Path to manifest after patch")
    parser.add_argument("--intent", default="", help="Commit message")
    parser.add_argument("--files", nargs="*", default=[], help="Changed files list")
    parser.add_argument("--refresh", default="", help="Path to factual-refresh.json")
    parser.add_argument("--dir", default=".", help="Base directory for artifact path resolution")
    parser.add_argument("--ci", action="store_true", help="Run in strict CI mode")
    args = parser.parse_args()

    b_data = json.loads(Path(args.before).read_text(encoding="utf-8")) if args.before else None
    a_data = json.loads(Path(args.after).read_text(encoding="utf-8"))
    r_data = json.loads(Path(args.refresh).read_text(encoding="utf-8")) if args.refresh else None
    b_dir = Path(args.dir).resolve()

    res = check_factual_drift(
        b_data,
        a_data,
        commit_message=args.intent,
        changed_files=args.files,
        factual_refresh_data=r_data,
        base_dir=b_dir,
        is_ci=args.ci,
    )
    if not res.passed:
        for f in res.failures:
            print(f, file=sys.stderr)
        sys.exit(1)
    print("FACTUAL DRIFT V2.2.2: PASS")
    sys.exit(0)
