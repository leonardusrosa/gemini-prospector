"""Fail-closed first-party/social media evidence for Prospector site concepts.

This module plans research and audits media provenance without scraping,
downloading, republishing, initiating contact, or changing the CRM. The browser
executor must independently verify official identity and usage rights.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from market_scope import normalize_country, scope_issue, assess_research_candidate

SOCIAL_HOSTS = {
    "instagram": ("instagram.com",),
    "facebook": ("facebook.com", "fb.com"),
    "tiktok": ("tiktok.com",),
    "youtube": ("youtube.com", "youtu.be"),
    "linkedin": ("linkedin.com",),
}
RIGHTS = {"CONFIRMED", "UNCONFIRMED", "DENIED"}
SOURCES = {"official_site", "instagram", "facebook", "tiktok",
           "youtube", "linkedin", "google_maps", "user_provided",
           "licensed_library", "generated"}
TYPES = {"image", "video"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        try:
            ipaddress.ip_address(host)
            return False
        except ValueError:
            pass
        return (parsed.scheme == "https" and bool(host) and not parsed.username
                and not parsed.password and not host.endswith(".local")
                and host not in {"localhost"})
    except ValueError:
        return False


def official_social(url: str, platform: str) -> bool:
    if platform not in SOCIAL_HOSTS or not https_url(url):
        return False
    host = (urlsplit(url).hostname or "").lower()
    return any(host == base or host.endswith("." + base)
               for base in SOCIAL_HOSTS[platform])


def extract_profile_candidates(value: Any) -> list[dict]:
    """Only extract literal verified-source candidates; never guess handles."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            value = re.findall(r"https://[^\s,;\"'<>]+", value)
    if isinstance(value, list):
        urls = [u for u in value if isinstance(u, str)]
    elif isinstance(value, dict):
        urls = [u for u in value.values() if isinstance(u, str)]
    else:
        urls = []
    profiles = []
    seen: set[tuple[str, str]] = set()
    for url in urls:
        for platform in SOCIAL_HOSTS:
            if official_social(url, platform) and (platform, url) not in seen:
                seen.add((platform, url))
                profiles.append({
                    "platform": platform, "url": url,
                    "identityVerified": False, "identityEvidence": None,
                    "checkedAt": None, "linkActive": False,
                    "researchOnly": True
                })
    return profiles


def research_plan(lead: dict[str, Any]) -> dict:
    """Create a browser-research handoff; never label unsighted profiles verified."""
    slug = str(lead.get("slug") or "")
    if not SLUG.fullmatch(slug):
        raise ValueError("Invalid lead slug")
    assessment = assess_research_candidate(lead)
    if assessment["scope"] != "ALLOW":
        raise ValueError("Lead is outside new prospecting region or country unknown")
    site = lead.get("siteAntigo")
    official = site if https_url(site) else None
    return {
        "schemaVersion": 1, "leadSlug": slug,
        "country": normalize_country(lead.get("country")),
        "mode": "READ_ONLY_RESEARCH", "noOutbound": True,
        "assessment": assessment,
        "officialWebsite": {"url": official,
                            "identityVerified": False,
                            "identityEvidence": None,
                            "inspectionStatus": "NOT_STARTED"},
        "pageCategories": [
            "home", "about_team", "services", "gallery_facilities",
            "contact_hours", "first_party_media"
        ],
        "crawl": {"maxDepth": 3, "sameDomainOnly": True,
                  "noCredentialAccess": True, "noBulkDownloads": True},
        "socialProfiles": extract_profile_candidates(lead.get("socialUrls")),
        "assets": [],
        "recommendedStack": "static-html-css-js-with-autocora-client-cms",
        "clientCmsRequirements": {
            "mustProvideAdmin": True,
            "adminPathPattern": "/clientes/{slug}/admin/",
            "publishedPagePattern": "/clientes/{slug}/site/",
            "tenantLocaleFromLead": True,
            "clientLoginEditDraftPublishRollbackE2ERequired": True,
        },
        "researchChecks": {
            "businessIdentityVerified": False,
            "websiteClassificationVerified": False,
            "socialProfileIdentityVerified": False,
            "mediaRightsReviewed": False,
            "factualSourceManifestComplete": False,
        },
        "reviewPlan": [
            "FACTS_AND_IDENTITIES", "MEDIA_RIGHTS_AND_RELEVANCE",
            "ENGINE_C_CANDIDATES", "INDEPENDENT_DESIGN_DIRECTION",
            "IMPLEMENTATION_AND_RESPONSIVE", "CLIENT_CMS_COMPATIBILITY",
            "BROWSER_VISUAL_AND_INTERACTIONS", "FACTUAL_AND_CONVERSION_RECHECK",
            "HUMAN_PREVIEW_APPROVAL",
        ],
    }


def audit_research_manifest(manifest: dict) -> dict:
    """Block real publication paths from unverified social identities/rights."""
    findings: list[str] = []
    warnings: list[str] = []
    if manifest.get("schemaVersion") != 1:
        findings.append("Invalid research manifest schemaVersion")
    if not SLUG.fullmatch(str(manifest.get("leadSlug") or "")):
        findings.append("Invalid lead slug")
    if scope_issue(manifest.get("country")):
        findings.append("Manifest country is outside USA/Canada/Europe or unverified")
    profiles = manifest.get("socialProfiles") or []
    if not isinstance(profiles, list):
        findings.append("socialProfiles must be a list")
        profiles = []
    for i, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            findings.append(f"socialProfiles[{i}] must be an object")
            continue
        plat = profile.get("platform")
        url = profile.get("url")
        if not official_social(url, plat):
            findings.append(f"socialProfiles[{i}] invalid platform/URL")
        if profile.get("linkActive") is True and not (
            profile.get("identityVerified") is True and
            https_url(profile.get("identityEvidence")) and
            isinstance(profile.get("checkedAt"), str) and profile.get("checkedAt")
        ):
            findings.append(f"socialProfiles[{i}] public link lacks verified identity evidence")
    verified_profile_urls = {
        (profile.get("platform"), profile.get("url"))
        for profile in profiles
        if isinstance(profile, dict)
        and official_social(profile.get("url"), profile.get("platform"))
        and profile.get("identityVerified") is True
        and https_url(profile.get("identityEvidence"))
        and bool(profile.get("checkedAt"))
    }
    assets = manifest.get("assets") or []
    if not isinstance(assets, list):
        findings.append("assets must be a list")
        assets = []
    ids: set[str] = set()
    approved = 0
    reference_only = 0
    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            findings.append(f"assets[{i}] must be an object")
            continue
        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,80}", asset_id):
            findings.append(f"assets[{i}] invalid asset identifier")
        elif asset_id in ids:
            findings.append(f"assets[{i}] duplicate identifier")
        ids.add(str(asset_id))
        origin = asset.get("origin")
        if origin not in SOURCES:
            findings.append(f"assets[{i}] invalid media origin")
        if asset.get("mediaType") not in TYPES:
            findings.append(f"assets[{i}] mediaType must be image or video")
        if not https_url(asset.get("sourceUrl")) or not https_url(asset.get("sourcePage")):
            findings.append(f"assets[{i}] source/page must be exact HTTPS URLs")
        rights = asset.get("rightsStatus", "UNCONFIRMED")
        if rights not in RIGHTS:
            findings.append(f"assets[{i}] invalid rights status")
        allowed = (rights == "CONFIRMED" and
                   asset.get("identityVerified") is True and
                   https_url(asset.get("permissionEvidence")) and
                   isinstance(asset.get("rightsVerifiedBy"), str) and
                   len(asset["rightsVerifiedBy"].strip()) >= 3 and
                   origin in SOURCES)
        local_path = asset.get("localPath")
        if local_path and (
            not isinstance(local_path, str)
            or not local_path.startswith("assets/")
            or not re.fullmatch(r"assets/[A-Za-z0-9._/-]+", local_path)
            or any(segment in ("", ".", "..") for segment in local_path.split("/"))
        ):
            findings.append(f"assets[{i}] localPath must stay inside the site's assets directory")
        used = asset.get("usedInSite") is True or bool(local_path)
        if used and origin in SOCIAL_HOSTS and (
            origin, asset.get("profileUrl")
        ) not in verified_profile_urls:
            allowed = False
            findings.append(
                f"assets[{i}] social media must bind to a separately verified official profile")
        if used and not allowed:
            findings.append(f"assets[{i}] cannot be copied or displayed without documented rights and identity")
        if origin == "google_maps" and used and not allowed:
            findings.append(f"assets[{i}] Google Maps images are reference-only absent separate permission")
        if used and allowed:
            approved += 1
        else:
            reference_only += 1
    if not assets:
        warnings.append("No media candidates assessed; use honest fallback imagery if needed")
    checks = manifest.get("researchChecks") or {}
    if not isinstance(checks, dict):
        findings.append("researchChecks must be an object")
        checks = {}
    complete = all(checks.get(k) is True for k in (
        "businessIdentityVerified", "websiteClassificationVerified",
        "mediaRightsReviewed", "factualSourceManifestComplete"
    ))
    if not complete:
        warnings.append("Research incomplete; design handoff is not approved")
    # Structural audit is not independent verification of media rights or
    # business identity. A human/browser evidence review must authorize design.
    return {"result": "BLOCK" if findings else
            ("REVIEW_REQUIRED" if not complete else "STRUCTURE_PASS"),
            "readyForDesign": False,
            "independentEvidenceReviewRequired": True,
            "validatorScope": "STRUCTURAL_ONLY",
            "approvedSiteMedia": approved,
            "referenceOnlyMedia": reference_only,
            "findings": findings, "warnings": warnings,
            "outreachAuthorized": False, "callbackAuthorized": False}


def audit_protected_owner_preview(
    manifest: dict, access_evidence: dict | None = None
) -> dict:
    """Evaluate brand imagery for an access-protected, recipient-only draft.

    Reuse permission is NOT a prerequisite to this *internal preview review*
    path. This does not license images or allow anonymous delivery,
    search indexing, public publication, or final client handoff.

    Flags/document references alone do NOT prove a preview is protected:
    an independent access-control/HTTP probe and browser review are needed.
    """
    failures: list[str] = []
    warnings: list[str] = []
    identity_checks = manifest.get("researchChecks") or {}
    if scope_issue(manifest.get("country")):
        failures.append("Lead must be located in the permitted target markets")
    if not identity_checks.get("businessIdentityVerified"):
        failures.append("Business identity requires source-backed verification")
    if not identity_checks.get("factualSourceManifestComplete"):
        failures.append("Private preview still requires verified factual sources")
    policy = manifest.get("ownerPreviewPolicy") or {}
    for key in ("accessProtected", "ownerOnlyAudience",
                "noSearchIndexing", "noPublicRelease"):
        if policy.get(key) is not True:
            failures.append("Private owner preview missing mandatory protection: " + key)
    if policy.get("previewPurpose") != "BUSINESS_OWNER_REVIEW":
        failures.append("Preview purpose must be explicit business-owner review")

    profiles = manifest.get("socialProfiles") or []
    verified_social = set()
    for profile in profiles:
        if (isinstance(profile, dict) and
                official_social(profile.get("url"), profile.get("platform")) and
                profile.get("identityVerified") is True and
                https_url(profile.get("identityEvidence"))):
            verified_social.add((profile["platform"], profile["url"]))

    approved_for_internal_staging = 0
    unconfirmed_rights = 0
    for i, asset in enumerate(manifest.get("assets") or []):
        if not isinstance(asset, dict) or asset.get("useInProtectedOwnerPreview") is not True:
            continue
        origin = asset.get("origin")
        if origin not in {"official_site", "instagram", "facebook",
                          "youtube", "tiktok", "linkedin"}:
            failures.append(f"assets[{i}] preview source must be a verified official brand source")
            continue
        if not https_url(asset.get("sourceUrl")) or not https_url(asset.get("sourcePage")):
            failures.append(f"assets[{i}] preview has no verifiable original asset/page URLs")
            continue
        if asset.get("identityVerified") is not True:
            failures.append(f"assets[{i}] business-media identity isn't verified")
            continue
        if origin in SOCIAL_HOSTS and (
                origin, asset.get("profileUrl")) not in verified_social:
            failures.append(f"assets[{i}] brand social account is not independently verified")
            continue
        if asset.get("usedInSite") is True or bool(asset.get("localPath")):
            failures.append(f"assets[{i}] must not enter a public site's assets directory")
            continue
        preview_path = asset.get("previewPath")
        if not isinstance(preview_path, str) or not preview_path.startswith(".prospector/"):
            failures.append(f"assets[{i}] private preview asset must remain under ignored .prospector/")
            continue
        if any(part in ("", ".", "..") for part in preview_path.split("/")):
            failures.append(f"assets[{i}] private preview path escapes its isolated workspace")
            continue
        approved_for_internal_staging += 1
        if asset.get("rightsStatus") != "CONFIRMED":
            unconfirmed_rights += 1

    if unconfirmed_rights:
        warnings.append("Private owner preview references media with unconfirmed reuse rights; public use is blocked.")
    if not approved_for_internal_staging:
        warnings.append("No verified brand media staged for protected owner preview.")

    # A self-reported auth flag is not proof that a Vercel/HTTP preview is protected.
    evidence = access_evidence if access_evidence is not None else (policy.get("independentAccessProbe") or {})
    http_proven = (
        evidence.get("unauthenticatedAccessDenied") is True and
        evidence.get("noIndexHeadersVerified") is True and
        evidence.get("recipientRestricted") is True and
        isinstance(evidence.get("reviewedBy"), str) and
        len(evidence["reviewedBy"].strip()) > 2 and
        isinstance(evidence.get("probeAt"), str) and
        bool(evidence["probeAt"])
    )
    if not http_proven:
        warnings.append("Actual host privacy/noindex must be verified by an independent HTTP/browser probe.")

    return {
        "mode": "PROTECTED_OWNER_PREVIEW_ONLY",
        "result": ("BLOCK" if failures else
                   "PREVIEW_ACCESS_REVIEW_REQUIRED" if not http_proven else
                   "STRUCTURE_READY_FOR_PRIVATE_PREVIEW"),
        "brandAssetsUsableInInternalPreview": approved_for_internal_staging,
        "rightsUnconfirmedCount": unconfirmed_rights,
        "rightsAuditRequiredBeforeInternalPreview": False,
        "publicReleaseAuthorized": False,
        "productionReleaseAuthorized": False,
        "independentAccessReviewRequired": True,
        "findings": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Local evidence research: no outbound calls or scraping")
    command = parser.add_subparsers(dest="command", required=True)
    plan = command.add_parser("plan")
    plan.add_argument("--lead-json", type=Path, required=True)
    plan.add_argument("--output", type=Path, required=True)
    audit = command.add_parser("audit")
    audit.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "plan":
        lead = json.loads(args.lead_json.read_text(encoding="utf-8"))
        payload = research_plan(lead)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"created": True, "scope": payload["assessment"]["scope"],
                          "profileCandidates": len(payload["socialProfiles"]),
                          "mode": "READ_ONLY_RESEARCH", "outreach": False}))
        return 0
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = audit_research_manifest(manifest)
    print(json.dumps(result))
    return 0 if result["result"] == "STRUCTURE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
