"""Canonical geographical and qualification policy for NEW Prospector discoveries.

The country is an ISO 3166-1 alpha-2 value independently verified by research.
This module deliberately does not infer countries from language, telephone,
city-name guesses, or the operator's location. Its scores never authorize contact.
"""
from __future__ import annotations

from typing import Any
import math
import re
import unicodedata

EUROPE_COUNTRIES = frozenset(
    """AD AL AT BA BE BG BY CH CY CZ DE DK EE ES FI FR GB GR HR HU IE IS
       IT LI LT LU LV MC MD ME MK MT NL NO PL PT RO RS SE SI SK SM UA VA""".split()
)
NORTH_AMERICA_COUNTRIES = frozenset({"US", "CA"})
NEW_DISCOVERY_COUNTRIES = EUROPE_COUNTRIES | NORTH_AMERICA_COUNTRIES

# Markets for an initial high-signal cohort; the remaining European countries
# are in scope for discovery but need local-language/compliance research.
PRIORITY_COUNTRIES = frozenset(
    {"US", "CA", "GB", "IE", "NL", "DE", "CH", "AT", "DK", "SE", "NO", "FR", "ES", "PT"}
)

# Initial owner-selected niches are advisory, never exclusive.
# Keep targeting terms language-aware for USA/Canada/Europe research.
_NICHE_PHRASES = (
    ("pizzeria", ("pizzeria", "pizzaria", "pizza restaurant", "pizza shop", "pizza place", "pizza takeout", "pizza")),
    ("cafe", ("cafe", "coffee shop", "coffeehouse", "cafeteria", "salon de the", "cafetería", "cafeteria", "caffetteria")),
    ("restaurant", ("restaurant", "restaurante", "ristorante", "gastronomia", "bistro", "brasserie", "eatery")),
    ("dentistry", ("dentist", "dentistry", "dental", "odontologia", "odontologica", "odontologo", "ortodontia", "orthodontic", "zahnarzt", "tandarts", "dentaire", "dentiste", "dentista", "clinica dentaria", "clinica dental")),
    ("clinic", ("clinic", "clinica", "clinique", "klinik", "kliniek", "medical practice", "medical office", "health clinic")),
)


def priority_niche(niche: Any) -> str | None:
    if not isinstance(niche, str):
        return None
    normalized = unicodedata.normalize("NFKD", niche.lower())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    if not normalized:
        return None
    for target, phrases in _NICHE_PHRASES:
        if any(re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", normalized)
               for phrase in phrases):
            return target
    return None


def normalize_country(country: Any) -> str:
    if not isinstance(country, str):
        return ""
    code = country.strip().upper()
    return code if len(code) == 2 and code.isascii() and code.isalpha() else ""

def scope_issue(country: Any) -> str | None:
    code = normalize_country(country)
    if not code:
        return "New lead discovery requires an independently verified ISO country code."
    if code not in NEW_DISCOVERY_COUNTRIES:
        return "New lead discovery is restricted to the USA, Canada, and Europe."
    return None

def region(country: Any) -> str | None:
    code = normalize_country(country)
    if code in NORTH_AMERICA_COUNTRIES:
        return "NORTH_AMERICA"
    if code in EUROPE_COUNTRIES:
        return "EUROPE"
    return None

def _number(value: Any) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else 0
    except (TypeError, ValueError):
        return 0

def assess_research_candidate(lead: dict[str, Any]) -> dict[str, Any]:
    """Deterministic research-ranking score, not a lead-contact permission."""
    country = normalize_country(lead.get("country"))
    issue = scope_issue(country)
    niche = priority_niche(lead.get("nicho", lead.get("niche", "")))
    if issue:
        return {"scope": "BLOCK", "region": None, "score": 0,
                "action": "HOLD", "reasons": [issue],
                "priorityNiche": niche,
                "regulatedClinicalClaimsReview": niche in {"clinic", "dentistry"},
                "outreachAuthorized": False, "callbackAuthorized": False}

    rating = _number(lead.get("nota", lead.get("rating")))
    reviews = int(max(0, _number(lead.get("avaliacoes", lead.get("reviewCount")))))
    site = str(lead.get("websiteStatus") or "").strip().lower()
    evidence = lead.get("classificationEvidence")
    website_verified = bool(evidence) and str(evidence).strip().lower() not in ("{}", "[]", "unknown")
    photo_sources = lead.get("verifiedPhotoSources") or []
    verified_photos = bool(photo_sources) if isinstance(photo_sources, list) else False
    services_verified = bool(lead.get("verifiedServices"))
    identity_verified = bool(lead.get("identityVerified"))
    contact_evidence = bool(lead.get("verifiedContactEvidence"))
    social_evidence = bool(lead.get("verifiedSocialProfiles"))
    reasons: list[str] = []
    points = 0

    if rating >= 4.7:
        points += 18
    elif rating >= 4.5:
        points += 9
    else:
        reasons.append("Business reputation below initial cohort threshold or unverified.")

    if reviews >= 60:
        points += 14
    elif reviews >= 40:
        points += 8
    else:
        reasons.append("Review volume below initial cohort threshold or unverified.")

    if site in ("none", "existing_weak") and website_verified:
        points += 24
    else:
        reasons.append("Website opportunity lacks verified classification evidence.")

    if verified_photos:
        points += 12
    else:
        reasons.append("Verify genuine business media before creative design.")

    if services_verified:
        points += 10
    else:
        reasons.append("Verify business services using source-backed evidence.")

    if identity_verified:
        points += 10
    else:
        reasons.append("Confirm exact business identity before research promotion.")

    if contact_evidence:
        points += 8
    else:
        reasons.append("Contact coordinates are not verified; do not treat as reachable.")

    if social_evidence:
        points += 4
    else:
        reasons.append("No verified official social profile yet.")

    if country not in PRIORITY_COUNTRIES:
        reasons.append("In scope, but local language and local-market research needed.")

    action = "RESEARCH_NEXT" if points >= 70 and identity_verified and website_verified else "HOLD_FOR_EVIDENCE"
    if not niche:
        reasons.append("Lower-priority niche; still geographically eligible.")
    if niche in {"clinic", "dentistry"}:
        reasons.append("Clinical claims, patient imagery and advertising require jurisdiction review.")
    return {"scope": "ALLOW", "country": country, "region": region(country),
            "priorityMarket": country in PRIORITY_COUNTRIES,
            "priorityNiche": niche,
            "regulatedClinicalClaimsReview": niche in {"clinic", "dentistry"},
            "score": points, "action": action, "reasons": reasons,
            "outreachAuthorized": False, "callbackAuthorized": False}
