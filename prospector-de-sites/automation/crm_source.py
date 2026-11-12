"""Read-only canonical CRM adapter and fail-closed preview eligibility checks."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BUILDABLE_STAGES = {"qualified", "qualificado", "redesigned", "redesenhado"}
VERIFIED_METHODS = {
    "email", "instagram_dm", "facebook_messenger",
    "whatsapp", "phone_call", "contact_form",
}


def read_lead(crm_path: Path, slug: str) -> dict | None:
    """Never create or mutate the canonical local SQLite CRM."""
    crm_path = Path(crm_path).resolve()
    if not crm_path.is_file():
        raise FileNotFoundError(f"Canonical CRM not found: {crm_path}")
    if not SLUG_RE.fullmatch(slug):
        raise ValueError("Invalid canonical lead slug")
    db = sqlite3.connect(crm_path.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        row = db.execute("SELECT * FROM leads WHERE slug=?", (slug,)).fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def _has_research_contact_evidence(sites_repo: Path, slug: str) -> bool:
    """Verify non-SMS contact evidence from the lead's research artifacts."""
    if not SLUG_RE.fullmatch(slug):
        return False
    sites_repo = Path(sites_repo).resolve()
    for folder in ("clientes", "sites"):
        rdir = sites_repo / folder / slug / "research"
        if not rdir.is_dir():
            continue
        wpp_file = rdir / "whatsapp-profile-evidence.json"
        if wpp_file.is_file():
            try:
                data = json.loads(wpp_file.read_text(encoding="utf-8"))
                target = str(data.get("whatsapp") or data.get("number") or "").strip()
                tstamp = data.get("verifiedAt") or data.get("collectedAt")
                source = data.get("sourceUrl") or data.get("sourceSurface") or data.get("url") or data.get("source")
                if data.get("verified") is True and target and tstamp and source:
                    return True
            except Exception:
                pass
        id_file = rdir / "business-identity-evidence.json"
        if id_file.is_file():
            try:
                data = json.loads(id_file.read_text(encoding="utf-8"))
                wpp = data.get("whatsapp")
                if isinstance(wpp, dict) and wpp.get("verified") is True:
                    target = str(wpp.get("number") or wpp.get("formatted") or "").strip()
                    tstamp = data.get("collectedAt") or wpp.get("verifiedAt")
                    source = wpp.get("source") or data.get("sources")
                    if target and tstamp and source:
                        return True
            except Exception:
                pass
    return False


def eligibility_issues(lead: dict | None, sites_repo: Path | None = None) -> list[str]:
    if lead is None:
        return ["Lead is missing from the canonical CRM"]
    issues = []
    status = str(lead.get("status") or "").strip().lower()
    if status not in BUILDABLE_STAGES:
        issues.append("Lead is not in a qualified or redesigned stage")
    methods = lead.get("verified_contact_methods")
    if isinstance(methods, str):
        try:
            methods = json.loads(methods)
        except (ValueError, TypeError):
            methods = []
    if not isinstance(methods, list):
        methods = []
    verified = any(
        isinstance(item, dict)
        and str(item.get("method") or "").lower() in VERIFIED_METHODS
        and str(item.get("status") or "").lower() == "verified"
        and item.get("actionable_now") is True
        and bool(str(item.get("target") or "").strip())
        and bool(item.get("verified_at"))
        and bool(item.get("verification_source") or item.get("source"))
        for item in methods
    )
    # Keep the canonical email-specific evidence as an alternative to method JSON.
    email_verified = (
        bool(lead.get("email"))
        and str(lead.get("email_verification_status") or "").lower() == "verified"
        and bool(lead.get("email_verified_at"))
        and bool(lead.get("email_verification_source"))
    )
    if not (verified or email_verified):
        if sites_repo and lead.get("slug"):
            if _has_research_contact_evidence(Path(sites_repo), lead["slug"]):
                verified = True
    if not (verified or email_verified):
        issues.append("No verified actionable non-SMS contact evidence with source and timestamp")
    return issues


def artifact_issues(sites_repo: Path, slug: str) -> list[str]:
    """Check only local prerequisites; this never substitutes for rendered QA."""
    if not SLUG_RE.fullmatch(slug):
        return ["Invalid canonical lead slug"]
    sites_repo = Path(sites_repo).resolve()
    folder_name = "clientes"
    for candidate in ("clientes", "sites"):
        if (sites_repo / candidate / slug).is_dir():
            folder_name = candidate
            break
    client_root = (sites_repo / folder_name).resolve()
    client_path = (client_root / slug).resolve()
    if client_root not in client_path.parents:
        return ["Lead directory escapes the sites repository"]
    if not (sites_repo / "package.json").is_file():
        return ["Missing prospector-sites package.json"]
    required = ("index.html", "proposta.html", "review-manifest.json")
    return [f"Missing {folder_name}/{slug}/{name}" for name in required
            if not (client_path / name).is_file()]
