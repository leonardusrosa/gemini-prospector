#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic pre-browser review for Prospector public websites.

This checker intentionally focuses on requirements that agents have historically
claimed as PASS without actually implementing them. It is not a substitute for
browser QA or factual research.

Usage:
    python prospector-de-sites/autonomous_site_review.py \
        --html sites/<slug>/<slug>.html \
        --design-read sites/<slug>/design-read.md \
        --manifest sites/<slug>/review-manifest.json

Exit 0 = deterministic gate passed.
Exit 1 = one or more blocking findings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
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


def disabled_social_tag_is_safe(tag: str | None) -> tuple[bool, str]:
    if not tag:
        return False, "control not found"
    aria_disabled = bool(re.search(r"aria-disabled\s*=\s*['\"]true['\"]", tag, re.IGNORECASE))
    href = re.search(r"\bhref\s*=\s*['\"]([^'\"]*)['\"]", tag, re.IGNORECASE)
    # Disabled mock controls must not navigate anywhere, including # or javascript:void(0).
    safe_href = href is None
    detail = f"aria-disabled={aria_disabled}, href={href.group(1)!r}" if href else f"aria-disabled={aria_disabled}, href=ABSENT"
    return aria_disabled and safe_href, detail


def main() -> int:
    parser = argparse.ArgumentParser(description="Prospector deterministic autonomous site review")
    parser.add_argument("--html", required=True)
    parser.add_argument("--design-read", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    html_path = Path(args.html)
    design_path = Path(args.design_read)
    manifest_path = Path(args.manifest)

    html = read_text(html_path, "HTML")
    design_read = read_text(design_path, "design-read")
    manifest = load_json(manifest_path)
    review = Review()

    # ---------------- gpt-taste ----------------
    gpt_cfg = section(manifest, "gptTaste")
    if gpt_cfg.get("required", True):
        gpt_pass = bool(re.search(r"(?im)^\s*GPT_TASTE_READ\s*:\s*PASS\s*$", design_read))
        gpt_path_raw = extract_design_value(design_read, "GPT_TASTE_PATH")
        path_ok = bool(gpt_path_raw and "<" not in gpt_path_raw and ">" not in gpt_path_raw)
        review.check("gpt_taste_read", gpt_pass, "design-read must contain GPT_TASTE_READ: PASS")
        review.check("gpt_taste_path", path_ok, "design-read must record the real gpt-taste SKILL.md path")

        if gpt_cfg.get("skillSha256Required", True) and path_ok:
            gpt_sha = (extract_design_value(design_read, "GPT_TASTE_SHA256") or "").lower()
            sha_format_ok = bool(re.fullmatch(r"[0-9a-f]{64}", gpt_sha))
            review.check("gpt_taste_sha_format", sha_format_ok, "design-read must contain GPT_TASTE_SHA256 with 64 lowercase/uppercase hex chars")

            actual_path = Path(str(gpt_path_raw)).expanduser()
            actual_exists = actual_path.is_file()
            review.check("gpt_taste_skill_exists", actual_exists, f"Recorded gpt-taste skill must exist locally: {actual_path}")
            if actual_exists and sha_format_ok:
                actual_sha = hashlib.sha256(actual_path.read_bytes()).hexdigest()
                review.check(
                    "gpt_taste_sha_matches",
                    actual_sha == gpt_sha,
                    "Recorded GPT_TASTE_SHA256 must match the exact current skill file that was read",
                )

    # ---------------- design dials / motion ----------------
    motion_cfg = section(manifest, "motion")
    motion_required = bool(motion_cfg.get("required", True))
    motion_score = extract_motion_score(design_read)
    if motion_required:
        review.check(
            "motion_score",
            motion_score is not None and motion_score > 0,
            f"Motion dial must be > 0 for this site; found {motion_score!r}",
        )
        review.check(
            "motion_runtime",
            contains_real_motion(html),
            "Page needs real scroll/reveal behavior; smooth scrolling alone is insufficient",
        )
        review.check(
            "reduced_motion_css",
            "prefers-reduced-motion" in html,
            "prefers-reduced-motion handling is required",
        )

        min_reveals = int(motion_cfg.get("minimumRevealGroups", 2) or 0)
        if min_reveals > 0:
            reveal_count = len(re.findall(r"data-motion\s*=\s*['\"]reveal['\"]", html, re.IGNORECASE))
            review.check(
                "motion_reveal_hooks",
                reveal_count >= min_reveals,
                f"Expected at least {min_reveals} data-motion=\"reveal\" groups; found {reveal_count}",
            )

        if motion_cfg.get("headerScrollStateRequired", False):
            has_header_hook = bool(re.search(r"data-role\s*=\s*['\"]site-header['\"]", html, re.IGNORECASE))
            review.check(
                "header_scroll_hook",
                has_header_hook,
                "Scroll-aware header must expose data-role=\"site-header\" for deterministic browser QA",
            )

    # ---------------- map ----------------
    address_cfg = section(manifest, "address")
    map_required = bool(
        address_cfg.get("verified")
        and address_cfg.get("public", True)
        and address_cfg.get("mapEmbedRequired", True)
    )
    if map_required:
        iframe = first_map_iframe(html)
        review.check("map_embed", iframe is not None, "Verified public address requires an embedded Google Maps preview")
        if iframe:
            review.check("map_lazy", "loading=\"lazy\"" in iframe.lower() or "loading='lazy'" in iframe.lower(), "Map iframe should lazy-load")
            review.check("map_title", bool(re.search(r"\btitle\s*=", iframe, re.IGNORECASE)), "Map iframe requires a meaningful title")
            review.check(
                "map_referrerpolicy",
                "referrerpolicy=" in iframe.lower(),
                "Map iframe should declare referrerpolicy",
            )

    # ---------------- WhatsApp ----------------
    wa_cfg = section(manifest, "whatsapp")
    if wa_cfg.get("verified"):
        expected = normalize_digits(wa_cfg.get("number"))
        links = WA_LINK_PATTERN.findall(html)
        normalized = [normalize_digits(item) for item in links]
        matches = [item for item in normalized if item == expected] if expected else normalized
        review.check(
            "whatsapp_verified_destination",
            bool(matches),
            f"Expected at least one wa.me link to verified number {expected or '[configured]'}",
        )
        wrong = sorted({item for item in normalized if expected and item != expected})
        review.check(
            "whatsapp_no_wrong_numbers",
            not wrong,
            "Unexpected WhatsApp destinations found: " + (", ".join(wrong) if wrong else "none"),
        )
        if wa_cfg.get("contactActionRequired", True):
            review.check(
                "whatsapp_multiple_conversion_points",
                len(matches) >= 2,
                f"Expected WhatsApp in primary/contact flow, found {len(matches)} verified wa.me links",
            )
        if wa_cfg.get("floatingRequired", True):
            floating = bool(re.search(r"data-role\s*=\s*['\"]floating-whatsapp['\"]", html, re.IGNORECASE))
            review.check(
                "floating_whatsapp_hook",
                floating,
                "Floating WhatsApp is required and must expose data-role=\"floating-whatsapp\"",
            )
    elif wa_cfg.get("mockAffordanceRequired", False):
        tag = social_tag(html, "whatsapp")
        review.check("whatsapp_mock_present", bool(tag), "Unverified WhatsApp still requires a disabled mockup affordance when requested")
        if tag:
            safe, detail = disabled_social_tag_is_safe(tag)
            review.check("whatsapp_mock_disabled_no_navigation", safe, detail)

    # ---------------- Instagram ----------------
    instagram_cfg = section(manifest, "instagram")
    instagram_state = str(instagram_cfg.get("state") or "not_applicable").strip().lower()
    if instagram_state == "verified":
        active_match = INSTAGRAM_ACTIVE_PATTERN.search(html)
        review.check("instagram_active", bool(active_match), "Verified Instagram requires active data-social=instagram link")
        expected_url = str(instagram_cfg.get("expectedUrl") or "").strip().rstrip("/").lower()
        if expected_url:
            review.check(
                "instagram_verified_url",
                expected_url in html.lower(),
                "Instagram href must match the verified profile URL",
            )
    elif instagram_state == "unverified" and instagram_cfg.get("mockAffordanceRequired", True):
        tag = social_tag(html, "instagram")
        review.check(
            "instagram_mock_present",
            bool(tag),
            "Unverified Instagram still requires a visible mockup affordance with data-social=instagram",
        )
        if tag:
            safe, detail = disabled_social_tag_is_safe(tag)
            review.check(
                "instagram_mock_disabled_no_navigation",
                safe,
                "Unverified Instagram control must be aria-disabled=true and have NO href at all. " + detail,
            )

    # ---------------- assistant/floating collision hooks ----------------
    assistant_cfg = section(manifest, "assistant")
    if assistant_cfg.get("present") and assistant_cfg.get("collisionCheckRequired", True):
        launcher = bool(re.search(r"data-role\s*=\s*['\"]assistant-launcher['\"]", html, re.IGNORECASE))
        floating = bool(re.search(r"data-role\s*=\s*['\"]floating-whatsapp['\"]", html, re.IGNORECASE))
        review.check("assistant_launcher_hook", launcher, "Assistant must expose data-role=\"assistant-launcher\" for collision QA")
        review.check("assistant_whatsapp_geometry_hooks", launcher and floating, "Assistant + floating WhatsApp need deterministic geometry hooks")

    # ---------------- preview/indexing ----------------
    if manifest.get("preview") is True:
        noindex = bool(
            re.search(
                r"<meta\b[^>]*name\s*=\s*['\"]robots['\"][^>]*content\s*=\s*['\"][^'\"]*noindex[^'\"]*nofollow[^'\"]*['\"]",
                html,
                re.IGNORECASE | re.DOTALL,
            )
        )
        review.check("preview_noindex", noindex, "Prospecting preview must be noindex,nofollow")

    # ---------------- common failure smells ----------------
    review.check(
        "fake_online_state",
        not bool(re.search(r">\s*Online\s*<|>\s*Estamos online\s*<", html, re.IGNORECASE)),
        "Do not simulate a human/online state",
    )

    return review.emit()


if __name__ == "__main__":
    sys.exit(main())
