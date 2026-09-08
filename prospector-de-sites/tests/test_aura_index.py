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
    validate_media_entry,
    merge_index_items,
    cmd_index,
    cmd_import_selected,
    cmd_inspect_bundled_media,
    cmd_vendor_selected_media,
    load_aura_index,
    load_aura_media_index,
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


def test_media_entry_unverified_source_reverts_commercial_use():
    """Unverified source cannot claim confirmed commercial use."""
    raw = {
        "templateId": "test-tmpl",
        "templateUrl": "https://example.com",
        "commercialUse": "confirmed",
        "sourceVerification": "UNVERIFIED_SOURCE",
        "licenseEvidenceUrl": "https://example.com/license",
    }
    norm = validate_media_entry(raw)
    assert norm["sourceVerification"] == "UNVERIFIED_SOURCE"
    assert norm["commercialUse"] == "unconfirmed"


def test_media_entry_missing_license_evidence_reverts_commercial_use():
    """Verified source without licenseEvidenceUrl or licenseEvidenceRecord cannot claim confirmed commercial use."""
    raw = {
        "templateId": "test-tmpl",
        "templateUrl": "https://example.com",
        "commercialUse": "confirmed",
        "sourceVerification": "VERIFIED_SOURCE",
        # Missing license evidence
    }
    norm = validate_media_entry(raw)
    assert norm["sourceVerification"] == "VERIFIED_SOURCE"
    assert norm["commercialUse"] == "unconfirmed"


def test_media_entry_verified_source_with_license_evidence_confirmed():
    """Verified source with license evidence retains confirmed commercial use."""
    raw = {
        "templateId": "test-tmpl",
        "templateUrl": "https://example.com",
        "commercialUse": "confirmed",
        "sourceVerification": "VERIFIED_SOURCE",
        "licenseEvidenceUrl": "https://example.com/terms",
    }
    norm = validate_media_entry(raw)
    assert norm["sourceVerification"] == "VERIFIED_SOURCE"
    assert norm["commercialUse"] == "confirmed"


def test_vendor_selected_media_unverified_source_fails():
    """cmd_vendor_selected_media strictly refuses unverified source."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        idx_p = tmp_p / "media-index.json"
        out_p = tmp_p / "assets"

        entry = {
            "templateId": "unverified-tmpl",
            "templateUrl": "https://example.com",
            "sourceVerification": "UNVERIFIED_SOURCE",
            "commercialUse": "unconfirmed",
        }
        cmd_inspect_bundled_media([entry], media_index_path=idx_p)

        ok, msg = cmd_vendor_selected_media("unverified-tmpl", out_p, media_index_path=idx_p)
        assert not ok
        assert "not 'VERIFIED_SOURCE'" in msg


def test_vendor_selected_media_verified_confirmed_succeeds():
    """cmd_vendor_selected_media succeeds when source is verified, commercial use confirmed, and license evidence present."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        idx_p = tmp_p / "media-index.json"
        out_p = tmp_p / "assets"

        # Create dummy media file
        media_f = tmp_p / "sample.mp4"
        media_f.write_bytes(b"dummy video")
        poster_f = tmp_p / "poster.webp"
        poster_f.write_bytes(b"dummy poster")

        entry = {
            "templateId": "verified-tmpl",
            "templateUrl": "https://example.com/tmpl",
            "sourceVerification": "VERIFIED_SOURCE",
            "commercialUse": "confirmed",
            "licenseEvidenceUrl": "https://example.com/license",
            "heroMediaType": "video",
        }
        cmd_inspect_bundled_media([entry], media_index_path=idx_p)

        ok, msg = cmd_vendor_selected_media(
            "verified-tmpl",
            out_p,
            media_file=media_f,
            poster_file=poster_f,
            media_index_path=idx_p,
        )
        assert ok
        assert "Successfully vendored" in msg
        assert (out_p / "hero-video.mp4").is_file()
        assert (out_p / "hero-poster.webp").is_file()

