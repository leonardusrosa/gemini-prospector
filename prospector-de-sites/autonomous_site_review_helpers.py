#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Helper utilities and constants for Prospector autonomous site review."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MOTION_CODE_PATTERNS = [
    r"IntersectionObserver",
    r"ScrollTrigger",
    r"\bgsap\.",
    r"addEventListener\(\s*['\"]scroll['\"]",
]

MAP_EMBED_PATTERN = re.compile(
    r"<iframe\b[^>]*\bsrc\s*=\s*['\"][^'\"]*(?:maps\.google\.|google\.com/maps)[^'\"]*(?:output=embed|embed)[^'\"]*['\"][^>]*>",
    re.IGNORECASE | re.DOTALL,
)

WA_LINK_PATTERN = re.compile(
    r"href\s*=\s*['\"]https://wa\.me/([0-9]+)(?:\?[^'\"]*)?['\"]",
    re.IGNORECASE,
)

SOCIAL_TAG_PATTERNS = {
    "instagram": re.compile(
        r"<[^>]+data-social\s*=\s*['\"]instagram['\"][^>]*>",
        re.IGNORECASE | re.DOTALL,
    ),
    "whatsapp": re.compile(
        r"<[^>]+data-social\s*=\s*['\"]whatsapp['\"][^>]*>",
        re.IGNORECASE | re.DOTALL,
    ),
}

INSTAGRAM_ACTIVE_PATTERN = re.compile(
    r"<a\b[^>]*data-social\s*=\s*['\"]instagram['\"][^>]*href\s*=\s*['\"]https?://(?:www\.)?instagram\.com/[^'\"]+['\"][^>]*>",
    re.IGNORECASE | re.DOTALL,
)

HERO_SECTION_PATTERN = re.compile(
    r"<section\b[^>]*data-role\s*=\s*['\"]hero['\"][^>]*>(.*?)</section>",
    re.IGNORECASE | re.DOTALL,
)

HERO_IMAGE_PATTERN = re.compile(
    r"<img\b[^>]*data-role\s*=\s*['\"]hero-image['\"][^>]*>",
    re.IGNORECASE | re.DOTALL,
)

REVIEWS_SECTION_PATTERN = re.compile(
    r"<section\b[^>]*(?:data-role\s*=\s*['\"]reviews['\"]|id\s*=\s*['\"]avaliacoes['\"])[^>]*>(.*?)</section>",
    re.IGNORECASE | re.DOTALL,
)

REVIEWS_TAG_PATTERN = re.compile(
    r"<section\b[^>]*(?:data-role\s*=\s*['\"]reviews['\"]|id\s*=\s*['\"]avaliacoes['\"])[^>]*>",
    re.IGNORECASE | re.DOTALL,
)


class Review:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def check(self, key: str, ok: bool, detail: str, blocking: bool = True) -> None:
        self.checks.append(
            {
                "key": key,
                "status": "PASS" if ok else "FAIL",
                "blocking": bool(blocking),
                "detail": detail,
            }
        )

    @property
    def failed(self) -> list[dict[str, Any]]:
        return [item for item in self.checks if item["status"] == "FAIL" and item["blocking"]]

    def emit(self) -> int:
        payload = {
            "autonomousReviewPass": not bool(self.failed),
            "blockingFailures": len(self.failed),
            "checks": self.checks,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if self.failed else 0


def _direct_maps_url(value: Any) -> bool:
    return isinstance(value, str) and bool(re.search(r"google\.[^/]+/maps", value, re.IGNORECASE))


def _parse_review_count(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"([0-9][0-9\s.,]*)\s*(?:avalia(?:ção|ções)|reviews?|ratings?)\b", value, re.IGNORECASE)
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(1))
    return int(digits) if digits else None


def _parse_rating(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"([0-5](?:[.,][0-9]+)?)", value)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _same_place_google_review_count(gr: dict[str, Any]) -> int:
    reviews = gr.get("reviews")
    if not isinstance(reviews, list):
        return 0
    place_id = str(gr.get("placeId") or gr.get("googleMapsFeatureId") or gr.get("placeIdOrCid") or "").strip()
    cid = str(gr.get("cid") or "").strip()
    accepted = {x for x in {place_id, cid, f"cid:{cid}" if cid else ""} if x}
    count = 0
    for item in reviews:
        if not isinstance(item, dict):
            continue
        if item.get("verified") is not True:
            continue
        if str(item.get("source") or "").strip().lower() != "google_maps":
            continue
        if str(item.get("placeIdOrCid") or "").strip() not in accepted:
            continue
        if not str(item.get("author") or "").strip() or not str(item.get("text") or "").strip():
            continue
        count += 1
    return count


def _apply_review_integrity_guard(data: dict[str, Any]) -> None:
    """Fail closed before autonomous QA can reinterpret incomplete Google evidence.

    This guard deliberately runs inside load_json(), before site-specific review logic.
    It prevents a secondary platform review from upgrading an incomplete Google Maps
    collection to VERIFIED_STRONG and requires two direct count observations.
    Legacy synthetic fixtures without sourceSurface=direct_google_maps are left alone.
    """
    gr = data.get("googleReviews")
    if not isinstance(gr, dict):
        return
    if str(gr.get("sourceSurface") or "").strip().lower() != "direct_google_maps":
        return

    errors: list[str] = []
    state = str(gr.get("state") or "").strip().upper()
    count = gr.get("ratingCount")
    if count is None:
        count = gr.get("reviewCount")
    usable = gr.get("usableTextReviews")
    if usable is None:
        usable = gr.get("capturedTextReviewCount")
    if usable is None:
        usable = len(gr.get("reviews", [])) if isinstance(gr.get("reviews"), list) else 0
    usable = usable if isinstance(usable, int) and usable >= 0 else 0

    if not isinstance(count, int) or count < 0:
        errors.append("ratingCount/reviewCount must be a non-negative integer")
    if not str(gr.get("placeId") or gr.get("googleMapsFeatureId") or gr.get("placeIdOrCid") or "").strip():
        errors.append("direct Google Maps evidence requires a place ID or Maps feature identifier")

    if isinstance(count, int) and count > 0:
        allowed_methods = {"playwright_direct_maps", "browser_direct_maps", "manual_direct_maps"}
        if str(gr.get("collectionMethod") or "").strip().lower() not in allowed_methods:
            errors.append("direct Google Maps evidence requires an allowed collectionMethod")
        if gr.get("profileHeaderObserved") is not True:
            errors.append("profileHeaderObserved=true is required")
        if gr.get("reviewsPanelOpened") is not True:
            errors.append("reviewsPanelOpened=true is required")
        if gr.get("textReviewCollectionAttempted") is not True:
            errors.append("textReviewCollectionAttempted=true is required")

        header = gr.get("aggregateObservation")
        if not isinstance(header, dict):
            errors.append("aggregateObservation is required")
        else:
            header_count = _parse_review_count(header.get("countText"))
            header_rating = _parse_rating(header.get("ratingText"))
            if not _direct_maps_url(header.get("surfaceUrl")):
                errors.append("aggregateObservation.surfaceUrl must be direct Google Maps")
            if header_count != count:
                errors.append(f"aggregateObservation count must match ratingCount={count}")
            rating = gr.get("aggregateRating")
            if not isinstance(rating, (int, float)) or header_rating is None or abs(header_rating - float(rating)) >= 0.01:
                errors.append("aggregateObservation rating must match aggregateRating")

        panel = gr.get("reviewsPanelObservation")
        if not isinstance(panel, dict):
            errors.append("reviewsPanelObservation is required")
        else:
            panel_count = _parse_review_count(panel.get("countText"))
            if not _direct_maps_url(panel.get("surfaceUrl")):
                errors.append("reviewsPanelObservation.surfaceUrl must be direct Google Maps")
            if panel_count != count:
                errors.append(f"reviewsPanelObservation count must match ratingCount={count}")

        observed_rating_entries = gr.get("observedRatingEntries")
        if observed_rating_entries is not None and observed_rating_entries != count:
            errors.append(f"observedRatingEntries ({observed_rating_entries}) must equal ratingCount ({count})")

        observed_text_entries = gr.get("observedTextReviewEntries")
        captured_text_count = gr.get("capturedTextReviewCount")
        if observed_text_entries is not None and captured_text_count is not None and captured_text_count != observed_text_entries:
            errors.append(f"capturedTextReviewCount ({captured_text_count}) must equal observedTextReviewEntries ({observed_text_entries})")

        if gr.get("reviewsPanelFullyTraversed") is not True:
            errors.append("reviewsPanelFullyTraversed=true is required")

    same_place_count = _same_place_google_review_count(gr)
    if state == "VERIFIED_STRONG" and usable < 3:
        errors.append(f"VERIFIED_STRONG requires >=3 verified Google text reviews, found {usable}")
    elif state == "VERIFIED_TEXT_LIMITED" and usable not in (1, 2):
        errors.append(f"VERIFIED_TEXT_LIMITED requires 1 or 2 verified Google text reviews, found {usable}")
    elif state == "VERIFIED_AGGREGATE_ONLY" and usable > 0:
        errors.append(f"VERIFIED_AGGREGATE_ONLY requires 0 text reviews, found {usable}")

    if state in {"VERIFIED_STRONG", "VERIFIED_TEXT_LIMITED"} and same_place_count != usable:
        errors.append(f"{state} requires {usable} same-place googleReviews.reviews evidence records, found {same_place_count}")

    if errors:
        gr["state"] = "COLLECTION_INCOMPLETE"
        gr["_integrityErrors"] = errors


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Manifest not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid manifest JSON {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("Manifest root must be a JSON object")
    _apply_review_integrity_guard(data)
    return data


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"{label} not found: {path}")


def section(manifest: dict[str, Any], key: str) -> dict[str, Any]:
    value = manifest.get(key, {})
    return value if isinstance(value, dict) else {}


def contains_real_motion(html: str) -> bool:
    return any(re.search(pattern, html, re.IGNORECASE) for pattern in MOTION_CODE_PATTERNS)


def extract_motion_score(design_read: str) -> int | None:
    match = re.search(r"(?im)^\s*Motion\s*:\s*(\d{1,2})(?:\s*/\s*10)?\s*$", design_read)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def first_map_iframe(html: str) -> str | None:
    match = MAP_EMBED_PATTERN.search(html)
    return match.group(0) if match else None


def normalize_digits(value: Any) -> str:
    return re.sub(r"\D+", "", str(value or ""))


def extract_design_value(design_read: str, key: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", design_read)
    return match.group(1).strip() if match else None


def social_tag(html: str, name: str) -> str | None:
    match = SOCIAL_TAG_PATTERNS[name].search(html)
    return match.group(0) if match else None


def extract_attr(tag: str | None, name: str) -> str | None:
    if not tag:
        return None
    match = re.search(rf"\b{re.escape(name)}\s*=\s*['\"]([^'\"]*)['\"]", tag, re.IGNORECASE)
    return match.group(1) if match else None


def disabled_social_tag_is_safe(tag: str | None) -> tuple[bool, str]:
    if not tag:
        return False, "control not found"
    aria_disabled = bool(re.search(r"aria-disabled\s*=\s*['\"]true['\"]", tag, re.IGNORECASE))
    href = re.search(r"\bhref\s*=\s*['\"]([^'\"]*)['\"]", tag, re.IGNORECASE)
    safe_href = href is None
    detail = f"aria-disabled={aria_disabled}, href={href.group(1)!r}" if href else f"aria-disabled={aria_disabled}, href=ABSENT"
    return aria_disabled and safe_href, detail


def find_canonical_template_manifest(base_dir: Path | None = None) -> tuple[Path | None, dict[str, Any] | None]:
    candidates = [
        Path(__file__).resolve().parent / "templates" / "hero-expert" / "manifest.json",
        Path("prospector-de-sites/templates/hero-expert/manifest.json").resolve(),
        Path("templates/hero-expert/manifest.json").resolve(),
    ]
    if base_dir:
        candidates.insert(0, base_dir / "templates" / "hero-expert" / "manifest.json")
        candidates.insert(1, base_dir / "prospector-de-sites" / "templates" / "hero-expert" / "manifest.json")

    for cand in candidates:
        if cand.is_file():
            try:
                data = json.loads(cand.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "templates" in data:
                    return cand, data
            except Exception:
                continue
    return None, None
