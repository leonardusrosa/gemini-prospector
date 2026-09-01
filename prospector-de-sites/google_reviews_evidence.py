#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic validator for Google Reviews evidence used by Prospector sites.

The validator is intentionally fail-closed. Aggregate rating/count must come from
an explicitly observed direct Google Maps place profile, not from cached snippets,
CRM state, search summaries, or the number of captured text reviews.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


VERIFIED_STRONG = "VERIFIED_STRONG"
VERIFIED_TEXT_LIMITED = "VERIFIED_TEXT_LIMITED"
VERIFIED_AGGREGATE_ONLY = "VERIFIED_AGGREGATE_ONLY"
COLLECTION_INCOMPLETE = "COLLECTION_INCOMPLETE"
PROFILE_CONFLICT = "PROFILE_CONFLICT"
NO_USABLE_REVIEWS = "NO_USABLE_REVIEWS"

PASSING_STATUSES = {VERIFIED_STRONG, VERIFIED_TEXT_LIMITED, VERIFIED_AGGREGATE_ONLY, NO_USABLE_REVIEWS}
DIRECT_SOURCE_SURFACE = "direct_google_maps"
DIRECT_COLLECTION_METHODS = {
    "playwright_direct_maps",
    "browser_direct_maps",
    "manual_direct_maps",
}


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

    @property
    def pass_for_publish(self) -> bool:
        return self.status in PASSING_STATUSES and not self.errors


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_timestamp(value: Any) -> datetime | None:
    if not _nonempty(value):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_count_label(value: Any) -> int | None:
    if not _nonempty(value):
        return None
    text = str(value).strip().casefold()
    match = re.search(r"([0-9][0-9\s.,]*)\s*(?:avalia(?:ção|ções)|reviews?|ratings?)\b", text)
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(1))
    return int(digits) if digits else None


def _parse_rating_label(value: Any) -> float | None:
    if not _nonempty(value):
        return None
    match = re.search(r"([0-5](?:[.,][0-9]+)?)", str(value))
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _direct_maps_url(value: Any) -> bool:
    return _nonempty(value) and "google." in str(value).lower() and "/maps" in str(value).lower()


def _validate_direct_maps_provenance(data: Dict[str, Any], errors: List[str]) -> None:
    source_surface = str(data.get("sourceSurface") or "").strip().lower()
    collection_method = str(data.get("collectionMethod") or "").strip().lower()
    header_observed = data.get("profileHeaderObserved") is True
    reviews_panel_opened = data.get("reviewsPanelOpened") is True
    text_collection_attempted = data.get("textReviewCollectionAttempted") is True
    count = data.get("ratingCount") if data.get("ratingCount") is not None else data.get("reviewCount")
    rating = data.get("aggregateRating")
    observation = data.get("aggregateObservation")
    panel_observation = data.get("reviewsPanelObservation")

    if source_surface != DIRECT_SOURCE_SURFACE:
        errors.append("sourceSurface must be 'direct_google_maps'; cached/search/CRM surfaces are not publishable evidence.")
    if collection_method not in DIRECT_COLLECTION_METHODS:
        errors.append(f"collectionMethod must be one of {sorted(DIRECT_COLLECTION_METHODS)}.")
    if not header_observed:
        errors.append("profileHeaderObserved=true is required; aggregate values must be read from the live Maps place header.")
    if isinstance(count, int) and count > 0 and not reviews_panel_opened:
        errors.append("reviewsPanelOpened=true is required when the profile reports ratings/reviews.")
    if isinstance(count, int) and count > 0 and not text_collection_attempted:
        errors.append("textReviewCollectionAttempted=true is required when the profile reports ratings/reviews.")

    if not isinstance(observation, dict):
        errors.append("aggregateObservation object is required to preserve the exact live Maps header observation.")
    else:
        raw_rating = observation.get("ratingText")
        raw_count = observation.get("countText")
        surface_url = observation.get("surfaceUrl")
        observed_rating = _parse_rating_label(raw_rating)
        observed_count = _parse_count_label(raw_count)

        if not _direct_maps_url(surface_url):
            errors.append("aggregateObservation.surfaceUrl must be the direct Google Maps place URL used for this collection pass.")
        if observed_rating is None:
            errors.append("aggregateObservation.ratingText must contain the visible aggregate rating from the Maps header.")
        elif isinstance(rating, (int, float)) and abs(observed_rating - float(rating)) >= 0.01:
            errors.append(f"aggregateRating={rating!r} does not match direct Maps header ratingText={raw_rating!r}.")
        if observed_count is None:
            errors.append("aggregateObservation.countText must contain the visible rating/review count from the Maps header.")
        elif isinstance(count, int) and observed_count != count:
            errors.append(f"reviewCount={count!r} does not match direct Maps header countText={raw_count!r} ({observed_count}).")

    # Independent second count observation from the opened reviews panel. This is
    # required specifically to catch selectors that accidentally capture an
    # individual review element or a stale search-summary count.
    if isinstance(count, int) and count > 0:
        if not isinstance(panel_observation, dict):
            errors.append("reviewsPanelObservation object is required when reviewCount > 0.")
        else:
            panel_count_text = panel_observation.get("countText")
            panel_url = panel_observation.get("surfaceUrl")
            panel_count = _parse_count_label(panel_count_text)
            if not _direct_maps_url(panel_url):
                errors.append("reviewsPanelObservation.surfaceUrl must be the same direct Google Maps place surface.")
            if panel_count is None:
                errors.append("reviewsPanelObservation.countText must preserve the count visible in the opened reviews panel.")
            elif panel_count != count:
                errors.append(
                    f"reviewCount={count!r} does not match opened reviews-panel countText={panel_count_text!r} ({panel_count})."
                )


def _validate_operator_observation(data: Dict[str, Any], errors: List[str]) -> None:
    """A newer operator-supplied direct Maps observation forces recollection on conflict."""
    operator = data.get("operatorObservation")
    if not isinstance(operator, dict):
        return

    if str(operator.get("sourceSurface") or "").strip().lower() != DIRECT_SOURCE_SURFACE:
        errors.append("operatorObservation must identify sourceSurface='direct_google_maps'.")
        return

    observed_at = _parse_timestamp(operator.get("observedAt"))
    collected_at = _parse_timestamp(data.get("collectedAt"))
    if observed_at is None:
        errors.append("operatorObservation.observedAt must be an ISO-8601 timestamp.")
        return
    if collected_at is not None and observed_at < collected_at:
        return

    op_count = operator.get("reviewCount")
    op_rating = operator.get("aggregateRating")
    count = data.get("reviewCount")
    rating = data.get("aggregateRating")
    if isinstance(op_count, int) and isinstance(count, int) and op_count != count:
        errors.append(
            f"Newer direct Maps operator observation reports reviewCount={op_count}, but active evidence says {count}. "
            "Mark active evidence stale and recollect before PASS."
        )
    if isinstance(op_rating, (int, float)) and isinstance(rating, (int, float)) and abs(float(op_rating) - float(rating)) >= 0.01:
        errors.append(
            f"Newer direct Maps operator observation reports aggregateRating={op_rating}, but active evidence says {rating}. "
            "Mark active evidence stale and recollect before PASS."
        )


def validate_evidence(data: Dict[str, Any], minimum_reviews: int = 3) -> EvidenceResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(data, dict):
        return EvidenceResult(PROFILE_CONFLICT, False, ["Evidence root must be an object."], [], 0)

    profile_name = data.get("profileName")
    profile_url = data.get("profileUrl")
    place_id = data.get("placeIdOrCid")
    rating = data.get("aggregateRating")
    count = data.get("ratingCount") if data.get("ratingCount") is not None else data.get("reviewCount")
    collected_at = data.get("collectedAt")
    reviews = data.get("reviews") or []
    profile_conflict = bool(data.get("profileConflict"))

    if profile_conflict:
        return EvidenceResult(PROFILE_CONFLICT, False, ["Profile identity conflict is unresolved."], [], 0)

    if not _nonempty(profile_name):
        errors.append("profileName is required.")
    if not (_nonempty(profile_url) and _nonempty(place_id)):
        errors.append("Both profileUrl and placeIdOrCid are required to anchor the exact Maps profile.")
    if not isinstance(rating, (int, float)) or not (0 <= float(rating) <= 5):
        errors.append("aggregateRating must be a number between 0 and 5.")
    if not isinstance(count, int) or count < 0:
        errors.append("ratingCount or reviewCount must be a non-negative integer.")
    if _parse_timestamp(collected_at) is None:
        errors.append("collectedAt must be an ISO-8601 timestamp from the current direct Maps collection pass.")
    if not isinstance(reviews, list):
        errors.append("reviews must be an array.")
        reviews = []

    _validate_direct_maps_provenance(data, errors)
    _validate_operator_observation(data, errors)

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
        source = str(review.get("source") or "").strip().lower()
        review_place_id = str(review.get("placeIdOrCid") or "").strip()

        missing = []
        if not _nonempty(author):
            missing.append("author")
        if not isinstance(review_rating, (int, float)) or not (1 <= float(review_rating) <= 5):
            missing.append("rating")
        if not _nonempty(text):
            missing.append("text")
        if not _nonempty(date_label):
            missing.append("dateLabel")
        if source != "google_maps":
            missing.append("source=google_maps")
        if not review_place_id or review_place_id != str(place_id or "").strip():
            missing.append("matching placeIdOrCid")

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

    # Panel completeness checks:
    # A profile can have total ratings but only a subset of entries with text.
    # We require observedRatingEntries == ratingCount and capturedTextReviewCount == observedTextReviewEntries.
    observed_rating_entries = data.get("observedRatingEntries")
    observed_text_entries = data.get("observedTextReviewEntries")
    captured_text_count = data.get("capturedTextReviewCount")

    if isinstance(count, int) and count > 0:
        if observed_rating_entries is not None and observed_rating_entries != count:
            errors.append(
                f"Direct Maps panel traversal incomplete: observedRatingEntries ({observed_rating_entries}) != ratingCount ({count}). "
                "COLLECTION_INCOMPLETE: keep scrolling until all entries are traversed or request human review."
            )
            return EvidenceResult(COLLECTION_INCOMPLETE, False, errors, warnings, len(verified_reviews))

        if observed_text_entries is not None and len(verified_reviews) != observed_text_entries:
            errors.append(
                f"Discovered {observed_text_entries} textual reviews during panel traversal, but only {len(verified_reviews)} verified records were captured. "
                "COLLECTION_INCOMPLETE: all observed textual reviews must be captured as evidence or deterministically rejected."
            )
            return EvidenceResult(COLLECTION_INCOMPLETE, False, errors, warnings, len(verified_reviews))

        if captured_text_count is not None and captured_text_count != len(verified_reviews):
            errors.append(
                f"capturedTextReviewCount ({captured_text_count}) does not match captured review count ({len(verified_reviews)})."
            )
            return EvidenceResult(COLLECTION_INCOMPLETE, False, errors, warnings, len(verified_reviews))

    # Review status determination based on captured verified textual reviews
    if len(verified_reviews) >= minimum_reviews:
        return EvidenceResult(VERIFIED_STRONG, True, [], warnings, len(verified_reviews))

    if len(verified_reviews) in {1, 2}:
        return EvidenceResult(VERIFIED_TEXT_LIMITED, True, [], warnings, len(verified_reviews))

    if isinstance(count, int) and count > 0:
        return EvidenceResult(VERIFIED_AGGREGATE_ONLY, False, [], warnings, 0)

    return EvidenceResult(NO_USABLE_REVIEWS, False, [], warnings, 0)


FORBIDDEN_VISIBLE_PATTERNS = [
    r"\bGoogle\s+Reviews\b",
    r"\bAvaliações\s+(?:no|do|de|da)?\s*Google\b",
    r"\bAvaliações\s+Google\b",
    r"\bO\s+que\s+dizem\s+no\s+Google\b",
    r"\bGoogle\s+Meu\s+Negócio\b",
    r"\bGoogle\s+Business\s+Profile\b",
    r"\bVeja\s+nossas\s+avaliações\s+no\s+Google\b",
    r"\b[0-9]+\s+avalia(?:ção|ções)\s+Google\b",
]


def extract_reviews_section(html: str) -> str:
    m = re.search(r'(<section\b[^>]*(?:reviews-section|id=["\']avaliacoes["\'])[^>]*>.*?</section>)', html, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else html


def extract_visible_text(html_snippet: str) -> str:
    s = re.sub(r'<!--.*?-->', ' ', html_snippet, flags=re.DOTALL)
    s = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', ' ', s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r'<svg\b[^>]*>.*?</svg>', ' ', s, flags=re.DOTALL | re.IGNORECASE)
    aria_matches = re.findall(r'aria-label=["\']([^"\']+)["\']', s, flags=re.IGNORECASE)
    clean_text = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', clean_text + ' ' + ' '.join(aria_matches)).strip()


def validate_reviews_public_copy(html: str) -> List[str]:
    violations: List[str] = []
    section = extract_reviews_section(html)
    visible_section = extract_visible_text(section)
    for pattern in FORBIDDEN_VISIBLE_PATTERNS:
        if re.search(pattern, visible_section, re.IGNORECASE):
            violations.append(f"Forbidden visible review copy matched pattern: {pattern}")

    nav_links = re.findall(r'<a\b[^>]*href=["\']#avaliacoes["\'][^>]*>(.*?)</a>', html, flags=re.DOTALL | re.IGNORECASE)
    for link_html in nav_links:
        link_text = extract_visible_text(link_html)
        for pattern in FORBIDDEN_VISIBLE_PATTERNS:
            if re.search(pattern, link_text, re.IGNORECASE):
                violations.append(f"Forbidden navigation label pointing to reviews: '{link_text}'")
    return violations


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
        f"REVIEW DISPLAY REQUIRED: {'YES' if result.status == VERIFIED_STRONG else 'NO/CONDITIONAL'}",
        f"GOOGLE REVIEWS QA: {'PASS' if result.pass_for_publish else 'BLOCKED'}",
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate direct Google Maps review evidence and public review copy.")
    parser.add_argument("evidence")
    parser.add_argument("--html", default="", help="Optional HTML file path to validate public copy neutrality.")
    parser.add_argument("--minimum-reviews", type=int, default=3)
    args = parser.parse_args()

    result = load_and_validate(args.evidence, minimum_reviews=args.minimum_reviews)
    for line in qa_lines(result):
        print(line)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")

    html_ok = True
    if args.html:
        html_path = Path(args.html)
        if html_path.is_file():
            html_violations = validate_reviews_public_copy(html_path.read_text(encoding="utf-8"))
            if html_violations:
                html_ok = False
                for violation in html_violations:
                    print(f"ERROR [PUBLIC_SOURCE_NEUTRALITY]: {violation}")
            else:
                print("PUBLIC SOURCE NEUTRALITY: PASS")

    raise SystemExit(0 if result.pass_for_publish and html_ok else 2)
