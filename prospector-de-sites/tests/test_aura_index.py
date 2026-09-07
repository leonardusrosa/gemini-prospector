#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for Aura index & selective importer (tools/aura_index.py)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from aura_index import (
    validate_metadata_entry,
    merge_index_items,
    cmd_index,
    cmd_import_selected,
    load_aura_index,
)


def test_metadata_parse():
    raw = {
        "id": "Aura Hero Dark",
        "sourceUrl": "https://aura.build/components/hero-dark",
        "name": "Hero Dark 01",
        "type": "hero",
        "free": True,
        "license": "MIT",
        "commercialUse": "confirmed",
        "tags": ["hero", "dark", "cinematic"],
        "cinematicScore": "9",
    }
    normalized = validate_metadata_entry(raw)
    assert normalized["id"] == "aura-hero-dark"
    assert normalized["commercialUse"] == "confirmed"
    assert normalized["cinematicScore"] == 9
    assert normalized["codeStatus"] == "NOT_IMPORTED"
    assert "cinematic" in normalized["tags"]


def test_duplicate_url_and_id_merge():
    item1 = {
        "id": "item-1",
        "sourceUrl": "https://aura.build/1",
        "name": "First Entry",
        "commercialUse": "unconfirmed",
    }
    item2 = {
        "id": "item-1-rename",
        "sourceUrl": "https://aura.build/1",
        "name": "Updated Entry",
        "commercialUse": "confirmed",
    }
    merged = merge_index_items([item1], [item2])
    assert len(merged) == 1
    assert merged[0]["name"] == "Updated Entry"
    assert merged[0]["commercialUse"] == "confirmed"


def test_license_unknown_sets_reference_only_on_import():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        idx_p = tmp_p / "index.json"
        imp_dir = tmp_p / "imported"

        entry = {
            "id": "creative-gallery",
            "sourceUrl": "https://aura.build/gallery",
            "name": "Creative Gallery",
            "license": "unknown",
            "commercialUse": "unconfirmed",
        }
        cmd_index([entry], index_path=idx_p)

        code = "<section class='aura-gallery'>Gallery</section>"
        ok, msg = cmd_import_selected("creative-gallery", code, index_path=idx_p, import_dir=imp_dir)
        assert ok
        assert "IMPORTED_FOR_REFERENCE" in msg

        updated = load_aura_index(idx_p)
        assert updated["items"][0]["codeStatus"] == "IMPORTED_FOR_REFERENCE"
        assert (imp_dir / "creative-gallery.html").is_file()
        assert "CommercialUse: unconfirmed" in (imp_dir / "creative-gallery.html").read_text(encoding="utf-8")


def test_no_raw_code_mass_import_by_default():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        idx_p = tmp_p / "index.json"
        imp_dir = tmp_p / "imported"

        entries = [
            {"id": f"item-{i}", "sourceUrl": f"https://aura.build/{i}", "name": f"Item {i}"}
            for i in range(10)
        ]
        cmd_index(entries, index_path=idx_p)

        # In index mode, zero raw html files should be created in imported directory
        assert not imp_dir.exists()
        idx = load_aura_index(idx_p)
        assert len(idx["items"]) == 10
        assert all(it["codeStatus"] == "NOT_IMPORTED" for it in idx["items"])


def test_prohibited_commercial_use_denies_import():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        idx_p = tmp_p / "index.json"
        imp_dir = tmp_p / "imported"

        entry = {
            "id": "restricted-card",
            "sourceUrl": "https://aura.build/restricted",
            "name": "Restricted Card",
            "commercialUse": "prohibited",
        }
        cmd_index([entry], index_path=idx_p)

        ok, msg = cmd_import_selected("restricted-card", "<div>Test</div>", index_path=idx_p, import_dir=imp_dir)
        assert not ok
        assert "Import denied" in msg
