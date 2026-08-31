#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed scanner for credentials accidentally embedded in production QA code.

This is deliberately narrow enough to avoid flagging synthetic fixtures while
blocking the exact dangerous class of mistake where a live dashboard/site test
contains plaintext Basic/Bearer credentials or literal passwords.

It scans tracked text files by default and exits non-zero on findings.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_HOST_MARKERS = (
    "prospector.autocora.com.br",
    "autocora.com.br/clientes/",
)

PATTERNS = [
    (
        "literal_basic_payload",
        re.compile(r"base64\.b64encode\(\s*b?[\"'][^\"'\r\n]{1,100}:[^\"'\r\n]{1,200}[\"']", re.IGNORECASE),
    ),
    (
        "literal_authorization_basic",
        re.compile(r"Authorization[\"']?\s*[:=]\s*[\"']Basic\s+[A-Za-z0-9+/=]{8,}[\"']", re.IGNORECASE),
    ),
    (
        "literal_authorization_bearer",
        re.compile(r"Authorization[\"']?\s*[:=]\s*[\"']Bearer\s+[A-Za-z0-9._~+\-/=]{8,}[\"']", re.IGNORECASE),
    ),
    (
        "literal_password_assignment",
        re.compile(r"(?im)^\s*(?:password|passwd|pwd|auth_password)\s*=\s*[\"'][^\"'\r\n]{6,}[\"']\s*$"),
    ),
]

ALLOWED_ENV_PATTERNS = (
    "os.environ.get(",
    "os.getenv(",
    "process.env.",
)


def tracked_files() -> list[Path]:
    try:
        output = subprocess.check_output(
            ["git", "ls-files"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        )
    except Exception as exc:
        raise SystemExit(f"Could not enumerate tracked files: {exc}")
    paths = []
    for raw in output.splitlines():
        p = ROOT / raw.strip()
        if p.is_file():
            paths.append(p)
    return paths


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in {
        ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".json",
        ".yaml", ".yml", ".md", ".html", ".sh", ".ps1", ".bat", ".toml",
    }


def scan_file(path: Path) -> list[tuple[str, int]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    # Synthetic/offline fixtures may intentionally contain fake passwords.
    # This guard becomes strict when code references a real production host.
    is_production_test = any(marker in text for marker in PRODUCTION_HOST_MARKERS)
    if not is_production_test:
        return []

    findings: list[tuple[str, int]] = []
    for name, pattern in PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            snippet = match.group(0)
            # Explicit environment lookups are safe and should not match in
            # normal code, but preserve a defensive exception.
            if any(token in snippet for token in ALLOWED_ENV_PATTERNS):
                continue
            findings.append((name, line))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan tracked production QA code for embedded credentials")
    parser.parse_args()

    findings: list[tuple[str, str, int]] = []
    for path in tracked_files():
        if not is_text_candidate(path):
            continue
        for name, line in scan_file(path):
            findings.append((str(path.relative_to(ROOT)), name, line))

    if findings:
        print("PRODUCTION QA SECRET HYGIENE: FAIL")
        for file, kind, line in findings:
            # Never print matched secret material.
            print(f"- {file}:{line}: {kind}")
        return 1

    print("PRODUCTION QA SECRET HYGIENE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
