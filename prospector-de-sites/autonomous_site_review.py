#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent-agnostic launcher for Prospector deterministic site review.

External gpt-taste remains the preferred design critic when it is actually
installed/read. Runtimes without it may use the repository-owned design-judge
skill with explicit markers and a verified hash. All other review behavior is
delegated to autonomous_site_review_core.py.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import autonomous_site_review_core as core

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DESIGN_JUDGE = (
    Path(__file__).resolve().parent / "skills" / "design-judge" / "SKILL.md"
).resolve()


def _design_value(text: str, key: str) -> str | None:
    return core.extract_design_value(text, key)


def _portable_design_judge_check(manifest: dict, design_read: str, review: core.Review) -> None:
    cfg = core.section(manifest, "gptTaste")
    if not cfg.get("required", True):
        return

    if re.search(r"(?im)^\s*GPT_TASTE_READ\s*:\s*PASS\s*$", design_read):
        core._legacy_check_gpt_taste(manifest, design_read, review)
        return

    read_pass = bool(re.search(r"(?im)^\s*DESIGN_JUDGE_READ\s*:\s*PASS\s*$", design_read))
    source = (_design_value(design_read, "DESIGN_JUDGE_SOURCE") or "").strip().lower()
    path_raw = (_design_value(design_read, "DESIGN_JUDGE_PATH") or "").strip()
    sha_raw = (_design_value(design_read, "DESIGN_JUDGE_SHA256") or "").strip().lower()

    review.check(
        "design_judge_read",
        read_pass,
        "design-read must contain either a real GPT_TASTE_READ: PASS or DESIGN_JUDGE_READ: PASS",
    )
    review.check(
        "design_judge_source",
        source == "repository",
        "Portable design judge requires DESIGN_JUDGE_SOURCE: repository",
    )

    candidate = None
    if path_raw and "<" not in path_raw and ">" not in path_raw:
        p = Path(path_raw).expanduser()
        if not p.is_absolute():
            p = ROOT / p
        candidate = p.resolve()

    review.check(
        "design_judge_path",
        candidate == CANONICAL_DESIGN_JUDGE,
        "DESIGN_JUDGE_PATH must resolve to the canonical repository design-judge/SKILL.md",
    )
    review.check(
        "design_judge_skill_exists",
        bool(candidate and candidate.is_file()),
        f"Canonical design judge must exist: {CANONICAL_DESIGN_JUDGE}",
    )

    sha_ok = bool(re.fullmatch(r"[0-9a-f]{64}", sha_raw))
    review.check(
        "design_judge_sha_format",
        sha_ok,
        "design-read must contain DESIGN_JUDGE_SHA256 as 64-char hex",
    )
    if candidate and candidate.is_file() and sha_ok:
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        review.check(
            "design_judge_sha_matches",
            actual == sha_raw,
            "Recorded DESIGN_JUDGE_SHA256 must match the canonical repository design judge",
        )


core._legacy_check_gpt_taste = core.check_gpt_taste
core.check_gpt_taste = _portable_design_judge_check


if __name__ == "__main__":
    sys.exit(core.main())
