#!/usr/bin/env python3
"""Fail-closed static review for competing fixed conversion launchers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ASSISTANT_LAUNCHER_RE = re.compile(r'data-role\s*=\s*["\']assistant-launcher["\']', re.IGNORECASE)
FLOATING_WHATSAPP_RE = re.compile(r'data-role\s*=\s*["\']floating-whatsapp["\']', re.IGNORECASE)


def inspect_html(html: str) -> dict:
    assistant_present = bool(ASSISTANT_LAUNCHER_RE.search(html))
    floating_whatsapp_present = bool(FLOATING_WHATSAPP_RE.search(html))
    failures: list[dict[str, str]] = []

    if assistant_present and floating_whatsapp_present:
        failures.append(
            {
                "key": "assistant_floating_whatsapp_conflict",
                "detail": (
                    "Assistant is present, so it must be the only persistent fixed bottom conversion launcher. "
                    "Remove data-role=\"floating-whatsapp\" and keep WhatsApp available through normal page CTAs "
                    "and assistant escalation/handoff."
                ),
            }
        )

    return {
        "assistantPresent": assistant_present,
        "floatingWhatsAppPresent": floating_whatsapp_present,
        "failures": failures,
        "pass": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Review fixed conversion-control exclusivity")
    parser.add_argument("--html", required=True)
    args = parser.parse_args()

    html = Path(args.html).read_text(encoding="utf-8")
    result = inspect_html(html)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
