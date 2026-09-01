#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic OpenDesign direction contract reviewer for Prospector schema v2+ sites."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


FIRST_VERSION_MODES = {"new_site_concept", "redesign"}
VALID_STATUSES = {"used", "unavailable", "skipped_by_operator"}


def _marker(text: str, key: str) -> str | None:
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else None


def validate_open_design_direction(
    manifest: dict[str, Any],
    design_read: str,
    base_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []

    try:
        schema_version = int(manifest.get("schemaVersion", 1) or 1)
    except (TypeError, ValueError):
        errors.append("schemaVersion must be an integer.")
        return errors

    site_mode = str(manifest.get("siteMode") or "").strip().lower()
    cfg = manifest.get("openDesignDirection")

    # Legacy schema v1 remains untouched. Schema v2+ first versions are governed here.
    if schema_version < 2 and not cfg:
        return errors
    if schema_version < 2 and site_mode not in FIRST_VERSION_MODES:
        return errors

    if site_mode in FIRST_VERSION_MODES and schema_version >= 2:
        if not isinstance(cfg, dict):
            return ["schema v2+ first versions require openDesignDirection configuration."]
    elif not isinstance(cfg, dict):
        return errors

    if cfg.get("required") is not True:
        errors.append("openDesignDirection.required must be true for schema v2+ first versions.")

    if str(cfg.get("mcpServerName") or "").strip() != "open-design":
        errors.append("openDesignDirection.mcpServerName must be 'open-design'.")

    if cfg.get("mcpProbeAttempted") is not True:
        errors.append("openDesignDirection.mcpProbeAttempted must be true.")

    status = str(cfg.get("status") or "").strip().lower()
    if status not in VALID_STATUSES:
        errors.append(f"openDesignDirection.status must be one of {sorted(VALID_STATUSES)}.")
        return errors

    if _marker(design_read, "OPEN_DESIGN_MCP") != "open-design":
        errors.append("design-read must contain OPEN_DESIGN_MCP: open-design.")

    if status == "used":
        directions = cfg.get("directionsGenerated")
        if not isinstance(directions, int) or directions < 2:
            errors.append("OpenDesign used state requires at least 2 distinct directions.")

        selected = str(cfg.get("selectedDirection") or "").strip()
        if not selected:
            errors.append("OpenDesign used state requires selectedDirection.")

        design_md_path = str(cfg.get("designMdPath") or "").strip()
        if not design_md_path:
            errors.append("OpenDesign used state requires designMdPath.")
        elif base_dir is not None:
            candidate = (base_dir / design_md_path).resolve()
            try:
                candidate.relative_to(base_dir.resolve())
            except ValueError:
                errors.append("designMdPath must stay inside the site directory.")
            else:
                if not candidate.is_file():
                    errors.append(f"OpenDesign DESIGN.md file is missing: {design_md_path}")

        if cfg.get("gptTasteSelectionReviewed") is not True:
            errors.append("OpenDesign used state requires gptTasteSelectionReviewed=true.")

        expected_markers = {
            "OPEN_DESIGN_DIRECTION": "PASS",
            "OPEN_DESIGN_MCP_PROBE": "PASS",
            "OPEN_DESIGN_IMPLEMENTATION_ROLE": "DIRECTION_ONLY",
            "OPEN_DESIGN_GPT_TASTE_REVIEW": "PASS",
        }
        for key, expected in expected_markers.items():
            if _marker(design_read, key) != expected:
                errors.append(f"design-read must contain {key}: {expected}.")

        dr_directions = _marker(design_read, "OPEN_DESIGN_DIRECTIONS_GENERATED")
        if directions is not None and str(directions) != str(dr_directions):
            errors.append("design-read direction count must match manifest directionsGenerated.")

        if selected and _marker(design_read, "OPEN_DESIGN_SELECTED_DIRECTION") != selected:
            errors.append("design-read selected direction must match manifest selectedDirection.")

        if design_md_path and _marker(design_read, "OPEN_DESIGN_DESIGN_MD") != design_md_path:
            errors.append("design-read DESIGN.md path must match manifest designMdPath.")

    elif status == "unavailable":
        reason = str(cfg.get("unavailableReason") or "").strip()
        if not reason:
            errors.append("OpenDesign unavailable state requires unavailableReason.")
        if _marker(design_read, "OPEN_DESIGN_DIRECTION") != "UNAVAILABLE":
            errors.append("design-read must contain OPEN_DESIGN_DIRECTION: UNAVAILABLE.")
        if _marker(design_read, "OPEN_DESIGN_MCP_PROBE") != "FAIL":
            errors.append("design-read must contain OPEN_DESIGN_MCP_PROBE: FAIL.")
        if _marker(design_read, "OPEN_DESIGN_FALLBACK") != "GPT_TASTE_ONLY":
            errors.append("OpenDesign unavailable state requires OPEN_DESIGN_FALLBACK: GPT_TASTE_ONLY.")
        dr_reason = _marker(design_read, "OPEN_DESIGN_UNAVAILABLE_REASON")
        if not dr_reason:
            errors.append("design-read must preserve the actual OpenDesign unavailable reason.")

    elif status == "skipped_by_operator":
        if cfg.get("operatorOverride") is not True:
            errors.append("OpenDesign skipped_by_operator requires operatorOverride=true.")
        if _marker(design_read, "OPEN_DESIGN_DIRECTION") != "SKIPPED_BY_OPERATOR":
            errors.append("design-read must contain OPEN_DESIGN_DIRECTION: SKIPPED_BY_OPERATOR.")
        if (_marker(design_read, "OPEN_DESIGN_OPERATOR_OVERRIDE") or "").lower() != "true":
            errors.append("design-read must contain OPEN_DESIGN_OPERATOR_OVERRIDE: true.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Prospector OpenDesign direction contract reviewer")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--design-read", required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    design_read_path = Path(args.design_read)

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"OPEN DESIGN DIRECTION REVIEW: FAIL\n- manifest read failed: {exc}")
        return 1

    try:
        design_read = design_read_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"OPEN DESIGN DIRECTION REVIEW: FAIL\n- design-read failed: {exc}")
        return 1

    errors = validate_open_design_direction(manifest, design_read, base_dir=manifest_path.parent)
    if errors:
        print("OPEN DESIGN DIRECTION REVIEW: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("OPEN DESIGN DIRECTION REVIEW: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
