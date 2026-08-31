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


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Manifest not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid manifest JSON {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("Manifest root must be a JSON object")
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
