import sys
from pathlib import Path
import pytest

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from factual_drift_review import check_factual_drift, is_layout_responsive_intent

def test_layout_intent_detection():
    assert is_layout_responsive_intent("fix(iost): compact mobile header") is True
    assert is_layout_responsive_intent("responsive navbar fix") is True
    assert is_layout_responsive_intent("style: adjust section padding") is True
    assert is_layout_responsive_intent("feat: add new client concept") is False
    assert is_layout_responsive_intent("factual-refresh: update cnpj and services") is False

def test_verified_services_drift_blocked_on_layout_patch():
    before = {
        "factualEvidence": {
            "verifiedServices": [
                {"claim": "Avaliação ortodôntica", "verified": True},
                {"claim": "Manutenção de aparelho fixo", "verified": True},
            ]
        }
    }
    after = {
        "factualEvidence": {
            "verifiedServices": [
                {"claim": "Ortodontia Preventiva", "verified": True},
                {"claim": "Aparelhos Autoligados", "verified": True},
            ]
        }
    }
    # No evidence artifact on layout patch -> BLOCKED
    res = check_factual_drift(before, after, "fix(iost): compact mobile header navbar", evidence_artifacts=[])
    assert res.passed is False
    assert any("verifiedServices mutated" in f for f in res.failures)

def test_verified_services_identical_passes_on_layout_patch():
    before = {
        "factualEvidence": {
            "verifiedServices": [
                {"claim": "Avaliação ortodôntica", "verified": True},
                {"claim": "Manutenção de aparelho fixo", "verified": True},
            ]
        }
    }
    after = {
        "factualEvidence": {
            "verifiedServices": [
                {"claim": "Avaliação ortodôntica", "verified": True},
                {"claim": "Manutenção de aparelho fixo", "verified": True},
            ]
        }
    }
    res = check_factual_drift(before, after, "fix(iost): compact mobile header navbar")
    assert res.passed is True
    assert len(res.failures) == 0

def test_phone_address_credentials_drift_blocked_on_layout_patch():
    before = {
        "phone": "5519996571896",
        "address": "Av 9, 411",
        "credentials": "CRO-SP 104164",
        "cnpj": "12345678000199",
    }
    after = {
        "phone": "5519999999999",
        "address": "Av 10, 500",
        "credentials": "CRO-SP 999999",
        "cnpj": "99999999000199",
    }
    res = check_factual_drift(before, after, "responsive css update", evidence_artifacts=[])
    assert res.passed is False
    assert len(res.failures) == 4

def test_google_reviews_mutation_blocked_on_layout_patch():
    before = {
        "googleReviews": {"aggregateRating": 5.0, "ratingCount": 12, "placeId": "ChIJ123"}
    }
    after = {
        "googleReviews": {"aggregateRating": 4.8, "ratingCount": 15, "placeId": "ChIJ123"}
    }
    res = check_factual_drift(before, after, "mobile spacing fix", evidence_artifacts=[])
    assert res.passed is False
    assert any("googleReviews.aggregateRating mutated" in f for f in res.failures)

def test_factual_mutation_allowed_with_explicit_evidence_artifact():
    before = {
        "factualEvidence": {
            "verifiedServices": [
                {"claim": "Avaliação ortodôntica", "verified": True}
            ]
        }
    }
    after = {
        "factualEvidence": {
            "verifiedServices": [
                {"claim": "Avaliação ortodôntica", "verified": True},
                {"claim": "Ortodontia Preventiva", "verified": True}
            ]
        }
    }
    res = check_factual_drift(
        before,
        after,
        "factual-refresh: update services from official registry",
        evidence_artifacts=["research/official-record-proof.json"],
        explicit_refresh_provenance=True,
    )
    assert res.passed is True
