#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aura indexing and selective asset importer for Prospector Design Framework V3.1.

Policy:
- index many, import few
- save metadata only during index mode
- commercialUse must be confirmed before raw code enters reusable library
- if license/rights unclear: reference only, no shipped copied code
- duplicate item IDs or source URLs must merge cleanly
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_PATH = ROOT / "prospector-de-sites" / "design-resources" / "aura" / "index.json"
DEFAULT_IMPORTED_DIR = ROOT / "prospector-de-sites" / "design-resources" / "aura" / "imported"

VALID_CODE_STATUSES = {"NOT_IMPORTED", "IMPORTED_FOR_REFERENCE", "APPROVED_PRIMITIVE"}


def normalize_item_id(val: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(val).strip().lower()).strip("-")
    return slug or "unnamed-item"


def validate_metadata_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Validates and normalizes an Aura metadata entry."""
    item_id = normalize_item_id(entry.get("id") or entry.get("name") or "item")
    source_url = str(entry.get("sourceUrl") or "").strip()
    name = str(entry.get("name") or item_id).strip()
    item_type = str(entry.get("type") or "layout").strip()
    is_free = bool(entry.get("free", True))
    license_type = str(entry.get("license") or "unknown").strip()
    commercial_use = str(entry.get("commercialUse") or "unconfirmed").strip().lower()
    if commercial_use not in {"confirmed", "unconfirmed", "prohibited"}:
        commercial_use = "unconfirmed"

    code_status = str(entry.get("codeStatus") or "NOT_IMPORTED").strip().upper()
    if code_status not in VALID_CODE_STATUSES:
        code_status = "NOT_IMPORTED"

    # If commercial use is not confirmed, it cannot be an APPROVED_PRIMITIVE
    if commercial_use != "confirmed" and code_status == "APPROVED_PRIMITIVE":
        code_status = "IMPORTED_FOR_REFERENCE"

    tags = [str(t).strip().lower() for t in entry.get("tags", []) if str(t).strip()]
    
    return {
        "id": item_id,
        "name": name,
        "sourceUrl": source_url,
        "type": item_type,
        "free": is_free,
        "license": license_type,
        "commercialUse": commercial_use,
        "thumbnail": str(entry.get("thumbnail") or ""),
        "tags": sorted(set(tags)),
        "heroGrammar": str(entry.get("heroGrammar") or "standard"),
        "layoutGrammar": str(entry.get("layoutGrammar") or "editorial"),
        "typographyFeel": str(entry.get("typographyFeel") or "modern"),
        "palette": str(entry.get("palette") or "monochrome"),
        "motion": str(entry.get("motion") or "subtle"),
        "cinematicScore": int(entry.get("cinematicScore") or 5),
        "nicheFit": [str(n).strip().lower() for n in entry.get("nicheFit", []) if str(n).strip()],
        "signaturePattern": str(entry.get("signaturePattern") or "none"),
        "codeStatus": code_status,
    }


def load_aura_index(path: Path | None = None) -> dict[str, Any]:
    target = path or DEFAULT_INDEX_PATH
    if not target.is_file():
        return {
            "version": "1.0.0",
            "source": "Aura",
            "items": []
        }
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {
            "version": "1.0.0",
            "source": "Aura",
            "items": []
        }


def save_aura_index(data: dict[str, Any], path: Path | None = None) -> None:
    target = path or DEFAULT_INDEX_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_index_items(existing_items: list[dict[str, Any]], new_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merges new items into existing items by id or sourceUrl."""
    by_id: dict[str, dict[str, Any]] = {}
    by_url: dict[str, str] = {}

    for it in existing_items:
        normalized = validate_metadata_entry(it)
        by_id[normalized["id"]] = normalized
        if normalized["sourceUrl"]:
            by_url[normalized["sourceUrl"]] = normalized["id"]

    for it in new_items:
        normalized = validate_metadata_entry(it)
        matched_id = None
        if normalized["id"] in by_id:
            matched_id = normalized["id"]
        elif normalized["sourceUrl"] and normalized["sourceUrl"] in by_url:
            matched_id = by_url[normalized["sourceUrl"]]

        if matched_id:
            # Merge fields, preserving existing imported codeStatus if higher
            existing = by_id[matched_id]
            prev_status = existing.get("codeStatus", "NOT_IMPORTED")
            existing.update(normalized)
            if prev_status in {"IMPORTED_FOR_REFERENCE", "APPROVED_PRIMITIVE"} and normalized["codeStatus"] == "NOT_IMPORTED":
                existing["codeStatus"] = prev_status
            by_id[matched_id] = existing
        else:
            by_id[normalized["id"]] = normalized
            if normalized["sourceUrl"]:
                by_url[normalized["sourceUrl"]] = normalized["id"]

    return sorted(by_id.values(), key=lambda x: str(x.get("id")))


def cmd_index(entries: list[dict[str, Any]], index_path: Path | None = None) -> dict[str, Any]:
    idx = load_aura_index(index_path)
    merged = merge_index_items(idx.get("items", []), entries)
    idx["items"] = merged
    save_aura_index(idx, index_path)
    return idx


def cmd_import_selected(item_id: str, raw_code: str, index_path: Path | None = None, import_dir: Path | None = None) -> tuple[bool, str]:
    idx = load_aura_index(index_path)
    items = idx.get("items", [])
    item = next((i for i in items if i.get("id") == item_id), None)
    if not item:
        return False, f"Item {item_id!r} not found in index."

    commercial = item.get("commercialUse", "unconfirmed")
    if commercial == "prohibited":
        return False, f"Commercial use prohibited for {item_id!r}. Import denied."

    # Status determination: if confirmed commercial use -> APPROVED_PRIMITIVE, else IMPORTED_FOR_REFERENCE
    new_status = "APPROVED_PRIMITIVE" if commercial == "confirmed" else "IMPORTED_FOR_REFERENCE"
    item["codeStatus"] = new_status

    out_dir = import_dir or DEFAULT_IMPORTED_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{item_id}.html"

    header = f"<!-- Source: {item.get('sourceUrl', 'Aura')} | License: {item.get('license')} | CommercialUse: {commercial} -->\n"
    out_file.write_text(header + raw_code, encoding="utf-8")

    save_aura_index(idx, index_path)
    return True, f"Imported {item_id} as {new_status} to {out_file}."


DEFAULT_MEDIA_INDEX_PATH = ROOT / "prospector-de-sites" / "design-resources" / "aura" / "media-index.json"


def validate_media_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Validates and normalizes an Aura bundled media entry."""
    template_id = normalize_item_id(entry.get("templateId") or entry.get("id") or "template")
    template_url = str(entry.get("templateUrl") or entry.get("sourceUrl") or "").strip()
    hero_media_present = bool(entry.get("heroMediaPresent", True))
    hero_media_type = str(entry.get("heroMediaType") or "video").strip().lower()
    if hero_media_type not in {"video", "image", "none"}:
        hero_media_type = "video"

    hero_asset_url = str(entry.get("heroAssetUrl") or "").strip()
    poster_url = str(entry.get("posterUrl") or "").strip()
    subject = str(entry.get("subject") or "automotive-detailing").strip()
    aspect_ratio = str(entry.get("aspectRatio") or "16:9").strip()
    motion_type = str(entry.get("motionType") or "ambient-loop").strip()
    mobile_suitability = str(entry.get("mobileSuitability") or "full-width-video").strip()
    license_str = str(entry.get("license") or "custom").strip()
    source_verification = str(entry.get("sourceVerification") or "UNVERIFIED_SOURCE").strip().upper()
    if source_verification not in {"VERIFIED_SOURCE", "UNVERIFIED_SOURCE"}:
        source_verification = "UNVERIFIED_SOURCE"

    commercial_use = str(entry.get("commercialUse") or "unconfirmed").strip().lower()
    if commercial_use not in {"confirmed", "unconfirmed", "prohibited"}:
        commercial_use = "unconfirmed"

    license_evidence_url = str(entry.get("licenseEvidenceUrl") or "").strip()
    license_evidence_record = str(entry.get("licenseEvidenceRecord") or "").strip()

    # Fail-closed: commercialUse cannot be confirmed if sourceVerification is UNVERIFIED_SOURCE
    # or if license evidence (URL or record) is missing
    if commercial_use == "confirmed":
        if source_verification != "VERIFIED_SOURCE" or not (license_evidence_url or license_evidence_record):
            commercial_use = "unconfirmed"

    template_bundled = bool(entry.get("templateBundled", True))
    code_status = str(entry.get("codeStatus") or "INDEXED_METADATA_ONLY").strip().upper()

    return {
        "templateId": template_id,
        "templateUrl": template_url,
        "heroMediaPresent": hero_media_present,
        "heroMediaType": hero_media_type,
        "heroAssetUrl": hero_asset_url,
        "posterUrl": poster_url,
        "subject": subject,
        "aspectRatio": aspect_ratio,
        "motionType": motion_type,
        "mobileSuitability": mobile_suitability,
        "license": license_str,
        "sourceVerification": source_verification,
        "commercialUse": commercial_use,
        "licenseEvidenceUrl": license_evidence_url,
        "licenseEvidenceRecord": license_evidence_record,
        "templateBundled": template_bundled,
        "codeStatus": code_status,
    }


def load_aura_media_index(path: Path | None = None) -> dict[str, Any]:
    target = path or DEFAULT_MEDIA_INDEX_PATH
    if not target.is_file():
        return {
            "version": "1.1.0",
            "source": "Aura",
            "policy": {
                "inspectOnly": True,
                "noAutomaticBulkDownload": True,
                "commercialUseVerificationRequired": True,
                "rule": "inspect-bundled-media saves metadata only; vendor-selected-media runs ONLY when sourceVerification=VERIFIED_SOURCE and commercialUse=CONFIRMED"
            },
            "items": []
        }
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {
            "version": "1.0.0",
            "source": "Aura",
            "items": []
        }


def save_aura_media_index(data: dict[str, Any], path: Path | None = None) -> None:
    target = path or DEFAULT_MEDIA_INDEX_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_inspect_bundled_media(entries: list[dict[str, Any]], media_index_path: Path | None = None) -> dict[str, Any]:
    """Inspects bundled media metadata and indexes it without downloading."""
    idx = load_aura_media_index(media_index_path)
    existing_items = idx.get("items", [])
    by_id: dict[str, dict[str, Any]] = {it.get("templateId"): it for it in existing_items if it.get("templateId")}

    for raw in entries:
        norm = validate_media_entry(raw)
        t_id = norm["templateId"]
        if t_id in by_id:
            by_id[t_id].update(norm)
        else:
            by_id[t_id] = norm

    idx["items"] = sorted(by_id.values(), key=lambda x: str(x.get("templateId")))
    save_aura_media_index(idx, media_index_path)
    return idx


def cmd_vendor_selected_media(
    template_id: str,
    output_dir: Path,
    media_file: Path | None = None,
    poster_file: Path | None = None,
    media_index_path: Path | None = None,
) -> tuple[bool, str]:
    """Vendors confirmed media locally. Strictly refuses unconfirmed commercial use."""
    idx = load_aura_media_index(media_index_path)
    items = idx.get("items", [])
    item = next((i for i in items if i.get("templateId") == template_id), None)

    if not item:
        return False, f"Template {template_id!r} not found in media-index.json."

    source_ver = str(item.get("sourceVerification", "UNVERIFIED_SOURCE")).upper()
    commercial = str(item.get("commercialUse", "unconfirmed")).lower()
    has_lic = bool(item.get("licenseEvidenceUrl") or item.get("licenseEvidenceRecord"))

    if source_ver != "VERIFIED_SOURCE":
        return False, (
            f"Source verification for template {template_id!r} is {source_ver!r} (not 'VERIFIED_SOURCE'). "
            "Cannot vendor media asset. Shipped assets require verified source."
        )

    if commercial != "confirmed":
        return False, (
            f"Commercial use for template {template_id!r} is {commercial!r} (not 'confirmed'). "
            "Cannot vendor media asset. Shipped assets must have confirmed commercial rights."
        )

    if not has_lic:
        return False, (
            f"Template {template_id!r} missing licenseEvidenceUrl or licenseEvidenceRecord. "
            "Cannot vendor media asset without documented license evidence."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    copied = []

    if media_file and media_file.is_file():
        target_name = "hero-video.mp4" if item.get("heroMediaType") == "video" else f"hero-{media_file.name}"
        dest = output_dir / target_name
        dest.write_bytes(media_file.read_bytes())
        copied.append(str(dest))

    if poster_file and poster_file.is_file():
        dest_poster = output_dir / "hero-poster.webp"
        dest_poster.write_bytes(poster_file.read_bytes())
        copied.append(str(dest_poster))

    item["codeStatus"] = "VENDORED_LOCAL"
    save_aura_media_index(idx, media_index_path)

    return True, f"Successfully vendored media for {template_id} to {output_dir}: {', '.join(copied)}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prospector Aura index, media index & selective importer")
    sub = parser.add_subparsers(dest="command", required=True)

    idx_parser = sub.add_parser("index", help="Index new Aura metadata entries")
    idx_parser.add_argument("--json-input", required=True, help="Path to JSON file containing list of Aura metadata entries")
    idx_parser.add_argument("--index-path", default=None, help="Optional path to index.json")

    sub.add_parser("crawl-index", help="Alias for index").add_argument("--json-input", required=True)

    import_parser = sub.add_parser("import-selected", help="Import raw code for selected indexed asset")
    import_parser.add_argument("--id", required=True, help="Aura item ID")
    import_parser.add_argument("--code-file", required=True, help="Path to raw code file to import")
    import_parser.add_argument("--index-path", default=None, help="Optional path to index.json")
    import_parser.add_argument("--import-dir", default=None, help="Optional target import directory")

    media_parser = sub.add_parser("inspect-bundled-media", help="Inspect bundled media metadata without downloading")
    media_parser.add_argument("--json-input", required=True, help="Path to JSON file with bundled media metadata")
    media_parser.add_argument("--media-index-path", default=None, help="Optional path to media-index.json")

    vendor_parser = sub.add_parser("vendor-selected-media", help="Vendor confirmed media asset locally")
    vendor_parser.add_argument("--template-id", required=True, help="Template ID from media-index.json")
    vendor_parser.add_argument("--output-dir", required=True, help="Target directory (e.g. assets/)")
    vendor_parser.add_argument("--media-file", default=None, help="Path to media asset file")
    vendor_parser.add_argument("--poster-file", default=None, help="Path to poster image file")
    vendor_parser.add_argument("--media-index-path", default=None, help="Optional path to media-index.json")

    args = parser.parse_args()

    if args.command in {"index", "crawl-index"}:
        entries = json.loads(Path(args.json_input).read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            entries = [entries]
        idx_path = Path(getattr(args, "index_path", None)) if getattr(args, "index_path", None) else None
        res = cmd_index(entries, idx_path)
        print(f"Indexed {len(res.get('items', []))} total items in Aura catalog.")
        return 0

    if args.command == "import-selected":
        raw = Path(args.code_file).read_text(encoding="utf-8")
        idx_path = Path(args.index_path) if args.index_path else None
        imp_dir = Path(args.import_dir) if args.import_dir else None
        ok, msg = cmd_import_selected(args.id, raw, idx_path, imp_dir)
        print(msg)
        return 0 if ok else 1

    if args.command == "inspect-bundled-media":
        entries = json.loads(Path(args.json_input).read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            entries = [entries]
        m_idx_path = Path(args.media_index_path) if args.media_index_path else None
        res = cmd_inspect_bundled_media(entries, m_idx_path)
        print(f"Inspected and recorded metadata for {len(res.get('items', []))} media items in media-index.json.")
        return 0

    if args.command == "vendor-selected-media":
        out_dir = Path(args.output_dir)
        m_file = Path(args.media_file) if args.media_file else None
        p_file = Path(args.poster_file) if args.poster_file else None
        m_idx_path = Path(args.media_index_path) if args.media_index_path else None
        ok, msg = cmd_vendor_selected_media(args.template_id, out_dir, m_file, p_file, m_idx_path)
        print(msg)
        return 0 if ok else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
