#!/usr/bin/env python3
"""Fail-closed static gate for expert-led hero presentation.

Usage:
    python prospector-de-sites/expert_hero_full_bleed_review.py \
        --html sites/<slug>/<slug>.html \
        --design-read sites/<slug>/design-read.md \
        --manifest sites/<slug>/review-manifest.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXPERT_KINDS = {"expert", "expert-placeholder"}
REQUIRED_DESIGN_MARKERS = (
    "EXPERT_HERO_FULL_BLEED",
    "EXPERT_HERO_DESKTOP_FULL_WIDTH",
    "EXPERT_HERO_MOBILE_FULL_WIDTH",
    "EXPERT_HERO_GPT_TASTE_JUDGED",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _attr(tag: str, name: str) -> str | None:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*['\"]([^'\"]*)['\"]", tag, re.I)
    return match.group(1) if match else None


def _design_marker(text: str, key: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else None


def validate(manifest: dict, html: str, design_read: str) -> list[str]:
    errors: list[str] = []
    hero = manifest.get("heroVisual") or {}
    kind = str(hero.get("kind") or "").strip().lower()
    if kind not in EXPERT_KINDS:
        return errors

    for key in ("expertBackgroundRequired", "desktopFullWidthRequired", "mobileFullWidthRequired"):
        if hero.get(key) is not True:
            errors.append(f"heroVisual.{key} must be true for expert-led heroes")

    for marker in REQUIRED_DESIGN_MARKERS:
        if _design_marker(design_read, marker) != "PASS":
            errors.append(f"design-read must contain {marker}: PASS")

    hero_tag_match = re.search(r"<section\b[^>]*data-role\s*=\s*['\"]hero['\"][^>]*>", html, re.I)
    if not hero_tag_match:
        errors.append('expert hero requires <section data-role="hero">')
        return errors

    hero_tag = hero_tag_match.group(0)
    if _attr(hero_tag, "data-hero-layout") != "full-bleed-background":
        errors.append('expert hero requires data-hero-layout="full-bleed-background"')
    if _attr(hero_tag, "data-hero-expert-presentation") != "background":
        errors.append('expert hero requires data-hero-expert-presentation="background"')
    if _attr(hero_tag, "data-hero-mobile-layout") != "full-width-background":
        errors.append('expert hero requires data-hero-mobile-layout="full-width-background"')

    hero_section_match = re.search(
        r"<section\b[^>]*data-role\s*=\s*['\"]hero['\"][^>]*>([\s\S]*?)</section>",
        html,
        re.I,
    )
    if not hero_section_match:
        errors.append("unable to inspect expert hero section contents")
        return errors

    inner = hero_section_match.group(1)
    if not re.search(r"<img\b[^>]*data-role\s*=\s*['\"]hero-image['\"][^>]*>", inner, re.I):
        errors.append('expert hero requires <img data-role="hero-image">')

    picture = re.search(r"<picture\b[^>]*>([\s\S]*?)</picture>", inner, re.I)
    if not picture:
        errors.append("expert hero requires responsive <picture> markup")
    else:
        has_mobile_source = re.search(
            r"<source\b[^>]*media\s*=\s*['\"][^'\"]*max-width[^'\"]*['\"][^>]*srcset\s*=",
            picture.group(1),
            re.I,
        )
        if not has_mobile_source:
            errors.append("expert hero requires a mobile <source media=...max-width... srcset=...>")

    forbidden_presentation = re.search(
        r"data-hero-expert-presentation\s*=\s*['\"](?:framed|card|tile|split|inset)['\"]",
        hero_tag,
        re.I,
    )
    if forbidden_presentation:
        errors.append("expert hero cannot use framed/card/tile/split/inset presentation")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Expert hero full-bleed static review")
    parser.add_argument("--html", required=True)
    parser.add_argument("--design-read", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    html_path = Path(args.html)
    design_path = Path(args.design_read)
    manifest_path = Path(args.manifest)

    manifest = json.loads(_read(manifest_path))
    errors = validate(manifest, _read(html_path), _read(design_path))
    if errors:
        print("[expert-hero-full-bleed] BLOCK")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[expert-hero-full-bleed] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
