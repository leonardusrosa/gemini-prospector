#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = ROOT / "test_autonomous_site_review_regression.py"
SPEC = importlib.util.spec_from_file_location("portable_fixture", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["portable_fixture"] = mod
SPEC.loader.exec_module(mod)

DESIGN_JUDGE = ROOT / "prospector-de-sites" / "skills" / "design-judge" / "SKILL.md"
SHA = hashlib.sha256(DESIGN_JUDGE.read_bytes()).hexdigest()


def portable_design(design: str, _: pathlib.Path, sha: str = SHA) -> str:
    lines = [
        line
        for line in design.splitlines()
        if not line.startswith(("GPT_TASTE_READ:", "GPT_TASTE_PATH:", "GPT_TASTE_SHA256:"))
    ]
    lines[0:0] = [
        "DESIGN_JUDGE_READ: PASS",
        "DESIGN_JUDGE_SOURCE: repository",
        "DESIGN_JUDGE_PATH: prospector-de-sites/skills/design-judge/SKILL.md",
        f"DESIGN_JUDGE_SHA256: {sha}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    code, payload = mod.run_case(design_transform=portable_design)
    assert code == 0, payload
    assert payload["autonomousReviewPass"] is True

    bad = "0" * 64
    code, payload = mod.run_case(
        design_transform=lambda d, p: portable_design(d, p, bad)
    )
    assert code == 1, payload
    failed = mod.failed_keys(payload)
    assert "design_judge_sha_matches" in failed, failed

    print("[PASS] repository design-judge fallback")
    print("[PASS] stale design-judge hash blocked")
    print("2/2 agent-runtime portability regressions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
