#!/usr/bin/env python3
"""One-way Prospector SQLite -> Supabase preview-copy migration.

Dry-run is the default. Apply requires both --apply and --confirm.
The script never modifies SQLite.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


LEAD_COLUMNS = [
    "slug", "nome", "nicho", "cidade", "nota", "avaliacoes", "email", "telefone", "whatsapp",
    "siteAntigo", "motivo", "status", "urlNova", "dataProposta", "valor", "obs", "contratoStatus",
    "contratoEm", "manutencao", "pago", "docCliente", "endCliente", "atualizado", "placeId",
    "opportunityType", "opportunityScore", "classificationEvidence", "mainRisk", "factualContent",
    "imageryLevel", "socialUrls", "mapsUrl", "runId", "criadoEm", "country", "locale", "language",
    "phoneCountryCode", "websiteStatus", "siteMode", "currency", "marketTier",
]
OUTREACH_COLUMNS = [
    "id", "slug", "canal", "destino", "tipo", "mensagem", "urlProposta", "mensagemId", "status", "criadoEm",
]
NUMERIC_FIELDS = {"nota", "avaliacoes", "valor", "manutencao", "pago", "opportunityScore", "runId", "id"}
TIMESTAMP_FIELDS = {"dataProposta", "contratoEm", "atualizado", "criadoEm"}
CHECK_FIELDS = {
    "slug", "country", "locale", "currency", "marketTier", "siteAntigo", "urlNova", "mapsUrl", "obs",
    "contratoStatus", "contratoEm", "valor", "manutencao", "pago", "dataProposta", "atualizado", "criadoEm",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", action="store_true", help="Required with --apply")
    parser.add_argument("--sqlite", default=os.environ.get("PROSPECTOR_SQLITE_PATH"))
    parser.add_argument("--report", default=str(Path(__file__).resolve().parents[1] / "migration-parity-report.json"))
    return parser.parse_args()


def sqlite_path(arg: str | None) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "prospector.db").resolve()


def rows(db: sqlite3.Connection, table: str, columns: list[str]) -> list[dict[str, Any]]:
    db.row_factory = sqlite3.Row
    quoted = ", ".join(f'"{column}"' for column in columns)
    return [dict(row) for row in db.execute(f'SELECT {quoted} FROM "{table}" ORDER BY 1')]


def schema_columns(db: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in db.execute(f'PRAGMA table_info("{table}")')]


def compare_projection(source: list[dict[str, Any]], projected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    by_slug = {str(item.get("slug")): item for item in projected}
    for original in source:
        slug = str(original.get("slug"))
        target = by_slug.get(slug)
        if target is None:
            mismatches.append({"slug": slug, "field": "slug", "reason": "missing projected row"})
            continue
        for field, value in original.items():
            if target.get(field) != value:
                mismatches.append({"slug": slug, "field": field, "source": value, "projected": target.get(field)})
    return mismatches


def field_audit(records: list[dict[str, Any]]) -> dict[str, Any]:
    nulls = {field: sum(1 for row in records if row.get(field) is None) for field in records[0].keys()} if records else {}
    numeric_type_errors = [
        {"slug": row.get("slug"), "field": field, "valueType": type(row.get(field)).__name__}
        for row in records for field in NUMERIC_FIELDS
        if field in row and row.get(field) is not None and not isinstance(row.get(field), (int, float))
    ]
    timestamp_type_errors = [
        {"slug": row.get("slug"), "field": field, "valueType": type(row.get(field)).__name__}
        for row in records for field in TIMESTAMP_FIELDS
        if field in row and row.get(field) is not None and not isinstance(row.get(field), str)
    ]
    checked_values = {
        str(row.get("slug")): {field: row.get(field) for field in CHECK_FIELDS if field in row}
        for row in records
    }
    return {"nullCounts": nulls, "numericTypeErrors": numeric_type_errors, "timestampTypeErrors": timestamp_type_errors, "checkedValues": checked_values}


def supabase_request(table: str, method: str = "GET", payload: Any = None, query: str = "") -> Any:
    base = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not base or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for --apply")
    url = f"{base.rstrip('/')}/rest/v1/{table}{query}"
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("apikey", key)
    request.add_header("Authorization", f"Bearer {key}")
    request.add_header("Content-Type", "application/json")
    if method in {"POST", "PATCH"}:
        request.add_header("Prefer", "resolution=merge-duplicates,return=minimal")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Supabase request failed ({exc.code}): {detail}") from exc


def fetch_remote(table: str, order: str) -> list[dict[str, Any]]:
    encoded = urllib.parse.quote(order, safe=".,")
    result = supabase_request(table, query=f"?select=*&order={encoded}")
    return result or []


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    applying = bool(args.apply)
    if applying and not args.confirm:
        print("REFUSED: --apply requires --confirm", file=sys.stderr)
        return 2

    db_path = sqlite_path(args.sqlite)
    uri = f"file:{db_path.as_posix()}?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    lead_schema = schema_columns(db, "leads")
    outreach_schema = schema_columns(db, "outreach_history")
    source_leads = rows(db, "leads", LEAD_COLUMNS)
    source_outreach = rows(db, "outreach_history", OUTREACH_COLUMNS)
    db.close()

    schema_mismatches = {
        "leadsMissingExpected": [field for field in LEAD_COLUMNS if field not in lead_schema],
        "outreachMissingExpected": [field for field in OUTREACH_COLUMNS if field not in outreach_schema],
    }
    planned_leads = [dict(row) for row in source_leads]
    planned_outreach = [dict(row) for row in source_outreach]
    projection_mismatches = compare_projection(source_leads, planned_leads) + compare_projection(source_outreach, planned_outreach)
    audit = field_audit(source_leads)
    duplicate_slugs = sorted({slug for slug in [row["slug"] for row in source_leads] if sum(1 for row in source_leads if row["slug"] == slug) > 1})

    dry_pass = not any(schema_mismatches.values()) and not projection_mismatches and not audit["numericTypeErrors"] and not audit["timestampTypeErrors"] and not duplicate_slugs
    report: dict[str, Any] = {
        "mode": "apply" if applying else "dry-run",
        "crmMode": "PREVIEW_COPY",
        "canonicalCrm": "LOCAL_SQLITE",
        "source": {"path": str(db_path), "leads": len(source_leads), "outreach": len(source_outreach)},
        "dryRun": {
            "status": "PASS" if dry_pass else "FAIL",
            "schemaMismatches": schema_mismatches,
            "projectionFieldMismatches": projection_mismatches,
            "duplicateSlugs": duplicate_slugs,
            "audit": audit,
        },
        "postCopy": None,
    }
    report_path = Path(args.report).resolve()
    write_report(report_path, report)
    if not dry_pass:
        print(f"DRY_RUN=FAIL report={report_path}")
        return 1
    print(f"DRY_RUN=PASS SOURCE_LEADS={len(source_leads)} SOURCE_OUTREACH={len(source_outreach)} report={report_path}")
    if not applying:
        return 0

    if source_leads:
        supabase_request("leads?on_conflict=slug", method="POST", payload=source_leads)
    if source_outreach:
        supabase_request("outreach_history?on_conflict=id", method="POST", payload=source_outreach)
    remote_leads = fetch_remote("leads", "slug.asc")
    remote_outreach = fetch_remote("outreach_history", "id.asc")
    source_by_slug = {row["slug"]: row for row in source_leads}
    remote_by_slug = {row["slug"]: row for row in remote_leads}
    missing_slugs = sorted(set(source_by_slug) - set(remote_by_slug))
    extra_slugs = sorted(set(remote_by_slug) - set(source_by_slug))
    remote_duplicates = sorted({slug for slug in [row["slug"] for row in remote_leads] if sum(1 for row in remote_leads if row["slug"] == slug) > 1})
    field_mismatches = compare_projection(source_leads, remote_leads)
    parity = (
        len(remote_leads) == len(source_leads)
        and len(remote_outreach) == len(source_outreach)
        and not missing_slugs and not extra_slugs and not remote_duplicates and not field_mismatches
    )
    report["postCopy"] = {
        "status": "PASS" if parity else "FAIL",
        "remoteLeads": len(remote_leads),
        "remoteOutreach": len(remote_outreach),
        "missingSlugs": missing_slugs,
        "extraSlugs": extra_slugs,
        "duplicateSlugs": remote_duplicates,
        "fieldMismatches": field_mismatches,
    }
    write_report(report_path, report)
    print(f"COPY_PARITY={'PASS' if parity else 'FAIL'} REMOTE_LEADS={len(remote_leads)} REMOTE_OUTREACH={len(remote_outreach)}")
    return 0 if parity else 1


if __name__ == "__main__":
    raise SystemExit(main())
