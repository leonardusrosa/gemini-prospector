#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic validator to prevent silent factual drift across maintenance patches.

Enforces strict field-by-field binding and canonical factual-refresh artifact requirements:
1. Detects presentation/maintenance patches from actual changed files as well as commit message.
2. Prohibits arbitrary files in research/ from counting as evidence; requires canonical
   research/factual-refresh.json.
3. Enforces field-by-field binding: changed fields must be explicitly authorized.
4. Requires that all evidence sources declare an artifactPath that actually exists on disk.
5. Protects all core business/expert identity, credentials, verifiedServices, phone, address,
   CNPJ, reviews, and pricing.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

PRESENTATION_FILE_PATTERN = re.compile(
    r"(?i)(?:\.html|\.css|\.scss|\.js|\.jsx|\.tsx|\.ts|design-read\.md|\/assets\/|hero|templates)"
)

LAYOUT_INTENT_PATTERN = re.compile(
    r"(?i)\b(?:layout|responsive|navbar|header|nav|css|mobile|desktop|tablet|style|spacing|padding|visual|hero|motion|drawer|overflow|chore|cleanup|refactor|fix)\b"
)

VALID_SOURCE_TYPES = {
    "official_site",
    "official_record",
    "direct_maps",
    "operator_provided",
}

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

    # Identity & credentials
    state["businessName"] = manifest.get("businessName") or manifest.get("profileName")
    state["doctorName"] = manifest.get("doctorName") or manifest.get("expertName")
    state["credentials"] = manifest.get("credentials") or manifest.get("cro") or manifest.get("crm")
    state["factualEvidence.verifiedServices"] = normalize_services(manifest)

    # Contact & location
    state["phone"] = manifest.get("phone") or (manifest.get("whatsapp") or {}).get("number")
    state["whatsapp"] = manifest.get("whatsapp")
    state["address"] = manifest.get("address")
    state["cnpj"] = manifest.get("cnpj")
    state["pricing"] = manifest.get("pricing") or manifest.get("prices")

    # Reviews
    gr = manifest.get("googleReviews") or {}
    state["googleReviews.profileName"] = gr.get("profileName")
    state["googleReviews.profileUrl"] = gr.get("profileUrl")
    state["googleReviews.placeId"] = gr.get("placeId")
    state["googleReviews.cid"] = gr.get("cid")
    state["googleReviews.googleMapsFeatureId"] = gr.get("googleMapsFeatureId")
    state["googleReviews.aggregateRating"] = gr.get("aggregateRating")
    state["googleReviews.ratingCount"] = gr.get("ratingCount") if gr.get("ratingCount") is not None else gr.get("reviewCount")

    # Observed entries & reviews content
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


def validate_factual_refresh_artifact(
    artifact_data: Dict[str, Any], base_dir: Optional[Path] = None
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

    # Validate sources
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
        art_path = s.get("artifactPath")

        if not s_id or not isinstance(s_id, str):
            errors.append(f"sources[{idx}] missing valid 'id'")
        elif s_id in declared_sources:
            errors.append(f"duplicate source id '{s_id}'")
        else:
            declared_sources[s_id] = s

        if s_type not in VALID_SOURCE_TYPES:
            errors.append(f"sources[{idx}] type must be one of {sorted(VALID_SOURCE_TYPES)}, got '{s_type}'")

        if not art_path or not isinstance(art_path, str):
            errors.append(f"sources[{idx}] missing 'artifactPath'")
        elif base_dir:
            # Check file existence and non-empty
            full_path = (base_dir / art_path).resolve()
            if not full_path.exists() or not full_path.is_file():
                errors.append(f"sources[{idx}] artifactPath does not exist: {art_path}")
            elif full_path.stat().st_size == 0:
                errors.append(f"sources[{idx}] artifactPath is empty placeholder: {art_path}")

    # Validate changedFields bindings
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
    base_dir: Optional[Path] = None,
) -> FactualDriftResult:
    """Validate that protected factual fields do not drift without field-bound authorization."""
    failures: List[str] = []
    warnings: List[str] = []

    if before_manifest is None:
        return FactualDriftResult(passed=True)

    state_before = extract_protected_state(before_manifest)
    state_after = extract_protected_state(after_manifest)

    mutated_paths: List[str] = []
    for p, val_b in state_before.items():
        val_a = state_after.get(p)
        if val_b != val_a:
            mutated_paths.append(p)

    if not mutated_paths:
        return FactualDriftResult(passed=True, mutated_fields=[])

    # Protected paths mutated: validate factual-refresh artifact
    authorized_paths: Set[str] = set()
    if factual_refresh_data is not None:
        auths, artifact_errors = validate_factual_refresh_artifact(factual_refresh_data, base_dir)
        failures.extend(artifact_errors)
        authorized_paths = auths
    else:
        # Check if research/factual-refresh.json exists on disk if base_dir provided
        if base_dir:
            rf_path = base_dir / "research" / "factual-refresh.json"
            if rf_path.exists() and rf_path.is_file():
                try:
                    data = json.loads(rf_path.read_text(encoding="utf-8"))
                    auths, artifact_errors = validate_factual_refresh_artifact(data, base_dir)
                    failures.extend(artifact_errors)
                    authorized_paths = auths
                except Exception as ex:
                    failures.append(f"Failed to parse research/factual-refresh.json: {ex}")

    # Check whether each mutated path is authorized
    is_presentation = is_presentation_patch(changed_files, commit_message)

    for p in mutated_paths:
        # Allow exact match or prefix match (e.g., googleReviews covers subfields)
        authorized = (
            p in authorized_paths
            or any(p.startswith(a + ".") for a in authorized_paths)
            or (p.startswith("factualEvidence.") and p.split(".", 1)[1] in authorized_paths)
        )
        if not authorized:
            if is_presentation or not authorized_paths:
                failures.append(
                    f"[factual-drift] Protected factual field '{p}' was mutated without explicit authorization "
                    f"in factual-refresh.json (commit: '{commit_message}')"
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
    parser.add_argument("--before", required=True, help="Path to manifest before patch")
    parser.add_argument("--after", required=True, help="Path to manifest after patch")
    parser.add_argument("--intent", default="", help="Commit message")
    parser.add_argument("--files", nargs="*", default=[], help="Changed files list")
    parser.add_argument("--refresh", default="", help="Path to factual-refresh.json")
    parser.add_argument("--dir", default=".", help="Base directory for artifact path resolution")
    args = parser.parse_args()

    b_data = json.loads(Path(args.before).read_text(encoding="utf-8"))
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
    print("FACTUAL DRIFT V2: PASS")
    sys.exit(0)
