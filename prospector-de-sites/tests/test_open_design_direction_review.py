#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from open_design_direction_review import validate_open_design_direction


def base_manifest() -> dict:
    return {
        "schemaVersion": 2,
        "siteMode": "new_site_concept",
        "openDesignDirection": {
            "required": True,
            "mcpServerName": "open-design",
            "mcpProbeAttempted": True,
            "status": "used",
            "directionsGenerated": 2,
            "selectedDirection": "clinical-editorial",
            "designMdPath": "open-design/DESIGN.md",
            "gptTasteSelectionReviewed": True,
        },
    }


def used_design_read() -> str:
    return "\n".join([
        "OPEN_DESIGN_DIRECTION: PASS",
        "OPEN_DESIGN_MCP: open-design",
        "OPEN_DESIGN_MCP_PROBE: PASS",
        "OPEN_DESIGN_DIRECTIONS_GENERATED: 2",
        "OPEN_DESIGN_SELECTED_DIRECTION: clinical-editorial",
        "OPEN_DESIGN_DESIGN_MD: open-design/DESIGN.md",
        "OPEN_DESIGN_IMPLEMENTATION_ROLE: DIRECTION_ONLY",
        "OPEN_DESIGN_GPT_TASTE_REVIEW: PASS",
    ]) + "\n"


def test_schema_v1_legacy_skips():
    manifest = {"schemaVersion": 1, "siteMode": "new_site_concept"}
    assert validate_open_design_direction(manifest, "", None) == []


def test_schema_v2_requires_block():
    manifest = {"schemaVersion": 2, "siteMode": "new_site_concept"}
    errors = validate_open_design_direction(manifest, "", None)
    assert any("require openDesignDirection" in e for e in errors)


def test_used_requires_two_directions():
    manifest = base_manifest()
    manifest["openDesignDirection"]["directionsGenerated"] = 1
    errors = validate_open_design_direction(manifest, used_design_read(), None)
    assert any("at least 2" in e for e in errors)


def test_used_requires_gpt_taste_review():
    manifest = base_manifest()
    manifest["openDesignDirection"]["gptTasteSelectionReviewed"] = False
    errors = validate_open_design_direction(manifest, used_design_read(), None)
    assert any("gptTasteSelectionReviewed" in e for e in errors)


def test_unavailable_fallback_passes():
    manifest = base_manifest()
    manifest["openDesignDirection"] = {
        "required": True,
        "mcpServerName": "open-design",
        "mcpProbeAttempted": True,
        "status": "unavailable",
        "unavailableReason": "daemon not reachable",
    }
    design = "\n".join([
        "OPEN_DESIGN_DIRECTION: UNAVAILABLE",
        "OPEN_DESIGN_MCP: open-design",
        "OPEN_DESIGN_MCP_PROBE: FAIL",
        "OPEN_DESIGN_UNAVAILABLE_REASON: daemon not reachable",
        "OPEN_DESIGN_FALLBACK: GPT_TASTE_ONLY",
    ]) + "\n"
    assert validate_open_design_direction(manifest, design, None) == []


def test_operator_skip_requires_explicit_override():
    manifest = base_manifest()
    manifest["openDesignDirection"] = {
        "required": True,
        "mcpServerName": "open-design",
        "mcpProbeAttempted": True,
        "status": "skipped_by_operator",
        "operatorOverride": False,
    }
    design = "\n".join([
        "OPEN_DESIGN_DIRECTION: SKIPPED_BY_OPERATOR",
        "OPEN_DESIGN_MCP: open-design",
        "OPEN_DESIGN_OPERATOR_OVERRIDE: true",
    ]) + "\n"
    errors = validate_open_design_direction(manifest, design, None)
    assert any("operatorOverride=true" in e for e in errors)


def test_used_passes_with_persisted_design_md():
    manifest = base_manifest()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        od = root / "open-design"
        od.mkdir()
        (od / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
        assert validate_open_design_direction(manifest, used_design_read(), root) == []


def test_used_passes_with_gpt_taste_design_decision():
    manifest = base_manifest()
    manifest["openDesignDirection"]["gptTasteSelectionReviewed"] = False
    manifest["openDesignDirection"]["gptTasteDesignDecision"] = "PASS"
    design = used_design_read().replace("OPEN_DESIGN_GPT_TASTE_REVIEW: PASS", "GPT_TASTE_DESIGN_DECISION: PASS")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        od = root / "open-design"
        od.mkdir()
        (od / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
        assert validate_open_design_direction(manifest, design, root) == []


def test_used_passes_with_gpt_taste_pass_after_direction_change():
    manifest = base_manifest()
    manifest["openDesignDirection"]["gptTasteSelectionReviewed"] = False
    manifest["openDesignDirection"]["gptTasteDesignDecision"] = "PASS_AFTER_DIRECTION_CHANGE"
    design = used_design_read().replace("OPEN_DESIGN_GPT_TASTE_REVIEW: PASS", "GPT_TASTE_DESIGN_DECISION: PASS_AFTER_DIRECTION_CHANGE")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        od = root / "open-design"
        od.mkdir()
        (od / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
        assert validate_open_design_direction(manifest, design, root) == []


def test_used_fails_with_gpt_taste_blocked_skill_unavailable():
    manifest = base_manifest()
    manifest["openDesignDirection"]["gptTasteDesignDecision"] = "BLOCKED_SKILL_UNAVAILABLE"
    design = used_design_read() + "\nGPT_TASTE_DESIGN_DECISION: BLOCKED_SKILL_UNAVAILABLE\n"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        od = root / "open-design"
        od.mkdir()
        (od / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
        errors = validate_open_design_direction(manifest, design, root)
        assert any("BLOCKED_SKILL_UNAVAILABLE" in e for e in errors)


if __name__ == "__main__":
    tests = [name for name in globals() if name.startswith("test_")]
    for name in sorted(tests):
        globals()[name]()
        print(f"[PASS] {name}")
    print(f"\n{len(tests)}/{len(tests)} OpenDesign direction regression cases passed")
