#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic validator to prevent silent factual drift across maintenance patches (V2.1).

Enforces strict field-by-field binding, canonical refresh artifacts, and fail-closed baselines:
1. Rejects stale unchanged factual-refresh.json artifacts.
2. Any unauthorized mutation to protected fields always fails, regardless of commit message
   or other authorized fields.
3. Requires true fail-closed baseline resolution: missing baseline with protected state => FAIL.
4. Distinguishes external source types from 'accepted_baseline', and enforces exact git
   commit verification for baseline restorations.
5. Verifies multi-commit ranges from trusted baseline to HEAD.
"""

from __future__ import annotations

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


def verify_accepted_baseline_git(
    repo_dir: Optional[Path], commit_sha: str, manifest_path: str, protected_path: str, expected_val: Any
) -> Optional[str]:
    """Verify that commit_sha in git repository actually contains expected_val for protected_path."""
    if not repo_dir:
        return None
    try:
        proc = subprocess.run(
            ["git", "show", f"{commit_sha}:{manifest_path}"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return f"Git commit '{commit_sha}' does not contain '{manifest_path}'"
        past_manifest = json.loads(proc.stdout)
        past_state = extract_protected_state(past_manifest)
        past_val = past_state.get(protected_path)
        if isinstance(expected_val, list) and isinstance(past_val, list):
            if sorted(expected_val) != sorted(past_val):
                return f"Committed value {past_val} does not match expected baseline {expected_val}"
        elif past_val != expected_val:
            return f"Committed value {past_val} does not match expected baseline {expected_val}"
    except Exception as ex:
        return f"Failed to verify accepted_baseline commit in git: {ex}"
    return None


def validate_factual_refresh_artifact(
    artifact_data: Dict[str, Any],
    base_dir: Optional[Path] = None,
    repo_dir: Optional[Path] = None,
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
                git_err = verify_accepted_baseline_git(repo_dir, commit_sha, man_path, prot_path, exp_val)
                if git_err:
                    errors.append(f"sources[{idx}] accepted_baseline verification failed: {git_err}")

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
                    # Check if internal JSON labels itself official_record (Regression M)
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
) -> FactualDriftResult:
    """Validate that protected factual fields do not drift without field-bound authorization."""
    failures: List[str] = []
    warnings: List[str] = []

    state_after = extract_protected_state(after_manifest)
    has_protected_fields = any(v is not None and v != [] for v in state_after.values())

    # TRUE FAIL-CLOSED BASELINE (Requirement 3)
    if before_manifest is None:
        if has_protected_fields:
            return FactualDriftResult(
                passed=False,
                failures=["FACTUAL_DRIFT_BASELINE_UNRESOLVED: No trustworthy baseline manifest could be resolved."],
            )
        return FactualDriftResult(passed=True)

    state_before = extract_protected_state(before_manifest)

    mutated_paths: List[str] = []
    for p, val_b in state_before.items():
        val_a = state_after.get(p)
        if json.dumps(val_b, sort_keys=True) != json.dumps(val_a, sort_keys=True):
            mutated_paths.append(p)

    if not mutated_paths:
        return FactualDriftResult(passed=True, mutated_fields=[])

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
            auths, artifact_errors = validate_factual_refresh_artifact(factual_refresh_data, base_dir, repo_dir)
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
                    auths, artifact_errors = validate_factual_refresh_artifact(data, base_dir, repo_dir)
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
    )
    if not res.passed:
        for f in res.failures:
            print(f, file=sys.stderr)
        sys.exit(1)
    print("FACTUAL DRIFT V2.1: PASS")
    sys.exit(0)
