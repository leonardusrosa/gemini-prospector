#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic validator for Google Reviews evidence used by Prospector sites.

This module does not fetch Google. It validates that a collector/browser pass has
captured enough same-profile evidence to safely render aggregate rating and a
review carousel.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


VERIFIED_STRONG = "VERIFIED_STRONG"
VERIFIED_AGGREGATE_ONLY = "VERIFIED_AGGREGATE_ONLY"
PROFILE_CONFLICT = "PROFILE_CONFLICT"
NO_USABLE_REVIEWS = "NO_USABLE_REVIEWS"


@dataclass
class EvidenceResult:
    status: str
    carousel_required: bool
    errors: List[str]
    warnings: List[str]
    verified_review_count: int

    @property
    def pass_for_carousel(self) -> bool:
        return self.status == VERIFIED_STRONG and self.carousel_required and not self.errors


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_timestamp(value: Any) -> bool:
    if not _nonempty(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_evidence(data: Dict[str, Any], minimum_reviews: int = 3) -> EvidenceResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(data, dict):
        return EvidenceResult(PROFILE_CONFLICT, False, ["Evidence root must be an object."], [], 0)

    profile_name = data.get("profileName")
    profile_url = data.get("profileUrl")
    place_id = data.get("placeIdOrCid")
    rating = data.get("aggregateRating")
    count = data.get("reviewCount")
    collected_at = data.get("collectedAt")
    reviews = data.get("reviews") or []
    profile_conflict = bool(data.get("profileConflict"))

    if profile_conflict:
        return EvidenceResult(PROFILE_CONFLICT, False, ["Profile identity conflict is unresolved."], [], 0)

    if not _nonempty(profile_name):
        errors.append("profileName is required.")
    if not (_nonempty(profile_url) or _nonempty(place_id)):
        errors.append("profileUrl or placeIdOrCid is required to anchor profile identity.")
    if not isinstance(rating, (int, float)) or not (0 <= float(rating) <= 5):
        errors.append("aggregateRating must be a number between 0 and 5.")
    if not isinstance(count, int) or count < 0:
        errors.append("reviewCount must be a non-negative integer.")
    if not _valid_timestamp(collected_at):
        errors.append("collectedAt must be an ISO-8601 timestamp from the current collection pass.")
    if not isinstance(reviews, list):
        errors.append("reviews must be an array.")
        reviews = []

    verified_reviews: List[Dict[str, Any]] = []
    fingerprints = set()
    for index, review in enumerate(reviews):
        if not isinstance(review, dict):
            warnings.append(f"reviews[{index}] ignored: not an object.")
            continue

        author = review.get("author")
        review_rating = review.get("rating")
        text = review.get("text")
        date_label = review.get("dateLabel")

        missing = []
        if not _nonempty(author):
            missing.append("author")
        if not isinstance(review_rating, (int, float)) or not (1 <= float(review_rating) <= 5):
            missing.append("rating")
        if not _nonempty(text):
            missing.append("text")
        if not _nonempty(date_label):
            missing.append("dateLabel")

        if missing:
            warnings.append(f"reviews[{index}] ignored: missing/invalid {', '.join(missing)}.")
            continue

        fp = (str(author).strip().casefold(), str(text).strip().casefold())
        if fp in fingerprints:
            warnings.append(f"reviews[{index}] ignored: duplicate review.")
            continue
        fingerprints.add(fp)
        verified_reviews.append(review)

    if errors:
        return EvidenceResult(PROFILE_CONFLICT, False, errors, warnings, len(verified_reviews))

    if len(verified_reviews) >= minimum_reviews:
        return EvidenceResult(VERIFIED_STRONG, True, [], warnings, len(verified_reviews))

    if isinstance(count, int) and count >= minimum_reviews:
        warnings.append(
            f"Google profile reports {count} reviews, but only {len(verified_reviews)} verified text reviews were captured. "
            "Do not silently omit the carousel; continue collection or request human evidence."
        )
        return EvidenceResult(VERIFIED_AGGREGATE_ONLY, False, [], warnings, len(verified_reviews))

    return EvidenceResult(NO_USABLE_REVIEWS, False, [], warnings, len(verified_reviews))


def load_and_validate(path: str | Path, minimum_reviews: int = 3) -> EvidenceResult:
    p = Path(path)
    if not p.is_file():
        return EvidenceResult(PROFILE_CONFLICT, False, [f"Evidence file not found: {p}"], [], 0)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return EvidenceResult(PROFILE_CONFLICT, False, [f"Invalid evidence JSON: {exc}"], [], 0)
    return validate_evidence(data, minimum_reviews=minimum_reviews)


def qa_lines(result: EvidenceResult) -> List[str]:
    return [
        f"GOOGLE REVIEWS STATUS: {result.status}",
        f"VERIFIED TEXT REVIEWS: {result.verified_review_count}",
        f"CAROUSEL REQUIRED: {'YES' if result.carousel_required else 'NO'}",
        f"GOOGLE REVIEWS QA: {'PASS' if result.pass_for_carousel or result.status == NO_USABLE_REVIEWS else 'BLOCKED'}",
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate Prospector Google Reviews evidence JSON.")
    parser.add_argument("evidence")
    parser.add_argument("--minimum-reviews", type=int, default=3)
    args = parser.parse_args()

    result = load_and_validate(args.evidence, minimum_reviews=args.minimum_reviews)
    for line in qa_lines(result):
        print(line)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    raise SystemExit(0 if (result.pass_for_carousel or result.status == NO_USABLE_REVIEWS) else 2)
