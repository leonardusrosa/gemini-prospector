#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic validator to prevent silent factual drift during layout/responsive patches.

A visual, layout, or responsive maintenance patch must not silently mutate the factual
allowlist (verifiedServices, credentials, phone, address, CNPJ, reviews, prices)
without explicit factual-refresh provenance.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

LAYOUT_INTENT_PATTERN = re.compile(
    r"(?i)\b(?:layout|responsive|navbar|header|nav|css|mobile|desktop|tablet|style|spacing|padding|visual|hero|motion|drawer|overflow)\b"
)

FACTUAL_FIELDS = (
    "verifiedServices",
    "factualEvidence",
    "credentials",
    "whatsapp",
    "phone",
    "address",
    "cnpj",
    "googleReviews",
    "pricing",
    "prices",
)


@dataclass
class FactualDriftResult:
    passed: bool
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def extract_services(manifest: Dict[str, Any]) -> List[str]:
    """Extract normalized list of verified service claims from manifest."""
    services = (
        manifest.get("factualServices")
        or manifest.get("verifiedServices")
        or (manifest.get("factualEvidence") or {}).get("verifiedServices")
        or []
    )
    result = []
    for item in services:
        if isinstance(item, dict):
            claim = str(item.get("claim") or "").strip()
            if claim:
                result.append(claim)
        elif isinstance(item, str) and item.strip():
            result.append(item.strip())
    return sorted(result)


def is_layout_responsive_intent(intent: str) -> bool:
    """Return True if intent or commit message indicates a visual/layout/responsive patch."""
    return bool(LAYOUT_INTENT_PATTERN.search(intent or ""))


def check_factual_drift(
    before_manifest: Optional[Dict[str, Any]],
    after_manifest: Dict[str, Any],
    patch_intent: str,
    evidence_artifacts: Optional[List[str]] = None,
    explicit_refresh_provenance: bool = False,
) -> FactualDriftResult:
    """Validate that layout/responsive patches do not silently mutate factual data.

    If patch intent is layout/responsive and factual data changed without an explicit
    evidence artifact or refresh provenance, BLOCK.
    """
    failures = []
    warnings = []

    if before_manifest is None:
        return FactualDriftResult(passed=True, failures=[], warnings=[])

    is_layout = is_layout_responsive_intent(patch_intent)
    has_evidence_refresh = explicit_refresh_provenance or bool(
        evidence_artifacts and len(evidence_artifacts) > 0
    )

    # 1. Check verifiedServices drift
    services_before = extract_services(before_manifest)
    services_after = extract_services(after_manifest)

    if services_before != services_after:
        if is_layout and not has_evidence_refresh:
            failures.append(
                f"[factual-drift] PATCH INTENT '{patch_intent}' is layout/responsive but verifiedServices mutated "
                f"from {services_before} to {services_after} without explicit factual-refresh evidence artifact."
            )

    # 2. Check other factual fields
    for field_name in ("credentials", "whatsapp", "phone", "address", "cnpj", "pricing", "prices"):
        val_before = before_manifest.get(field_name)
        val_after = after_manifest.get(field_name)
        if val_before != val_after:
            if is_layout and not has_evidence_refresh:
                failures.append(
                    f"[factual-drift] PATCH INTENT '{patch_intent}' is layout/responsive but '{field_name}' mutated "
                    f"from {val_before} to {val_after} without explicit factual-refresh evidence artifact."
                )

    # 3. Check reviews aggregate / state mutation
    reviews_before = before_manifest.get("googleReviews") or {}
    reviews_after = after_manifest.get("googleReviews") or {}
    for r_key in ("aggregateRating", "ratingCount", "reviewCount", "placeId", "cid", "state"):
        r_before = reviews_before.get(r_key)
        r_after = reviews_after.get(r_key)
        if r_before != r_after:
            if is_layout and not has_evidence_refresh:
                failures.append(
                    f"[factual-drift] PATCH INTENT '{patch_intent}' is layout/responsive but googleReviews.{r_key} mutated "
                    f"from {r_before} to {r_after} without explicit factual-refresh evidence artifact."
                )

    return FactualDriftResult(passed=len(failures) == 0, failures=failures, warnings=warnings)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Validate that patch does not induce factual drift.")
    parser.add_argument("--before", help="Path to manifest before patch")
    parser.add_argument("--after", required=True, help="Path to manifest after patch")
    parser.add_argument("--intent", default="", help="Patch intent / commit message")
    parser.add_argument("--evidence", nargs="*", default=[], help="Evidence artifacts provided with patch")
    args = parser.parse_args()

    before_data = json.loads(Path(args.before).read_text(encoding="utf-8")) if args.before else None
    after_data = json.loads(Path(args.after).read_text(encoding="utf-8"))

    res = check_factual_drift(before_data, after_data, args.intent, args.evidence)
    if not res.passed:
        for f in res.failures:
            print(f, file=sys.stderr)
        sys.exit(1)
    print("FACTUAL DRIFT CHECK: PASS")
    sys.exit(0)
