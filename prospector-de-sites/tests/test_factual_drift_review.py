import sys
import tempfile
from pathlib import Path
import pytest

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from factual_drift_review import check_factual_drift, is_presentation_patch

BASE_MANIFEST_BEFORE = {
    "businessName": "IOST Ortodontia",
    "doctorName": "Dra. Aline Iost",
    "credentials": "CRO-SP 104164",
    "factualEvidence": {
        "verifiedServices": [
            {"claim": "Avaliação ortodôntica", "verified": True},
            {"claim": "Manutenção de aparelho fixo", "verified": True},
        ]
    },
    "phone": "5519996571896",
    "address": "Av 9, 411",
    "cnpj": "12345678000199",
    "googleReviews": {
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "placeId": "ChIJ123",
        "cid": "999999",
    },
}


def test_regression_a_css_services_change_commit_chore_no_refresh_fails():
    """A. CSS + services change, commit message = 'chore: cleanup', no factual-refresh => FAIL."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["factualEvidence"]["verifiedServices"].append({"claim": "Alinhadores Invisíveis"})

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=after,
        commit_message="chore: cleanup",
        changed_files=["styles.css", "review-manifest.json"],
        factual_refresh_data=None,
    )
    assert res.passed is False
    assert any("factualEvidence.verifiedServices" in f for f in res.failures)


def test_regression_b_css_services_change_random_note_fails():
    """B. CSS + services change, research/random-note.txt added => FAIL."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["factualEvidence"]["verifiedServices"].append({"claim": "Aparelhos Autoligados"})

    # random-note.txt is not a canonical factual-refresh.json
    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=after,
        commit_message="fix: mobile navbar",
        changed_files=["styles.css", "research/random-note.txt", "review-manifest.json"],
        factual_refresh_data=None,
    )
    assert res.passed is False
    assert any("without explicit authorization in factual-refresh.json" in f for f in res.failures)


def test_regression_c_css_services_change_address_refresh_only_fails(tmp_path):
    """C. CSS + services change, factual-refresh.json only declares address evidence => FAIL."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["factualEvidence"]["verifiedServices"].append({"claim": "Ortodontia Preventiva"})

    # Create dummy proof for address
    proof = tmp_path / "research" / "address-proof.txt"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("proof content", encoding="utf-8")

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "address refresh only",
        "changedFields": [{"path": "address", "evidenceIds": ["src-addr"]}],
        "sources": [
            {
                "id": "src-addr",
                "type": "official_record",
                "artifactPath": "research/address-proof.txt",
            }
        ],
    }

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=after,
        commit_message="fix: layout adjustments",
        changed_files=["index.html", "review-manifest.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
    )
    assert res.passed is False
    assert any("factualEvidence.verifiedServices" in f for f in res.failures)


def test_regression_d_css_services_change_with_valid_services_refresh_passes(tmp_path):
    """D. CSS + services change, factual-refresh.json explicitly binds services, valid preserved source artifact exists => PASS."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["factualEvidence"]["verifiedServices"].append({"claim": "Ortodontia Preventiva"})

    proof = tmp_path / "research" / "services-proof.txt"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("official record evidence", encoding="utf-8")

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "services update",
        "changedFields": [
            {"path": "factualEvidence.verifiedServices", "evidenceIds": ["src-srv"]}
        ],
        "sources": [
            {
                "id": "src-srv",
                "type": "official_record",
                "artifactPath": "research/services-proof.txt",
            }
        ],
    }

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=after,
        commit_message="fix: compact navbar and update verified services",
        changed_files=["styles.css", "review-manifest.json", "research/services-proof.txt"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
    )
    assert res.passed is True
    assert len(res.failures) == 0


def test_regression_e_css_only_passes():
    """E. CSS only => PASS."""
    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=BASE_MANIFEST_BEFORE,
        commit_message="fix: header responsive css",
        changed_files=["styles.css"],
        factual_refresh_data=None,
    )
    assert res.passed is True
    assert len(res.failures) == 0


def test_regression_f_factual_refresh_only_with_valid_evidence_passes(tmp_path):
    """F. factual refresh only with valid evidence => PASS."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["phone"] = "5519999999999"

    proof = tmp_path / "research" / "phone-proof.txt"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("direct maps profile phone screenshot proof", encoding="utf-8")

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "phone change",
        "changedFields": [{"path": "phone", "evidenceIds": ["src-phone"]}],
        "sources": [
            {
                "id": "src-phone",
                "type": "direct_maps",
                "artifactPath": "research/phone-proof.txt",
            }
        ],
    }

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=after,
        commit_message="factual-refresh: update phone from direct maps",
        changed_files=["review-manifest.json", "research/phone-proof.txt"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
    )
    assert res.passed is True
    assert len(res.failures) == 0


def test_regression_g_two_fields_changed_refresh_authorizes_only_one_fails(tmp_path):
    """G. two protected fields changed but refresh authorizes only one => FAIL."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["phone"] = "5519999999999"
    after["cnpj"] = "99999999000199"

    proof = tmp_path / "research" / "phone-proof.txt"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("phone proof", encoding="utf-8")

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "phone update only",
        "changedFields": [{"path": "phone", "evidenceIds": ["src-phone"]}],
        "sources": [
            {
                "id": "src-phone",
                "type": "direct_maps",
                "artifactPath": "research/phone-proof.txt",
            }
        ],
    }

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=after,
        commit_message="fix: layout and contacts",
        changed_files=["index.html", "review-manifest.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
    )
    assert res.passed is False
    assert any("cnpj" in f for f in res.failures)
    assert not any("'phone'" in f for f in res.failures)


def test_regression_h_factual_refresh_references_nonexistent_artifact(tmp_path):
    """H. factual-refresh references nonexistent artifact => FAIL."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["phone"] = "5519999999999"

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "phone update",
        "changedFields": [{"path": "phone", "evidenceIds": ["src-phone"]}],
        "sources": [
            {
                "id": "src-phone",
                "type": "direct_maps",
                "artifactPath": "research/does-not-exist.png",
            }
        ],
    }

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=after,
        commit_message="chore: update phone",
        changed_files=["review-manifest.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
    )
    assert res.passed is False
    assert any("does not exist: research/does-not-exist.png" in f for f in res.failures)


def json_clone(obj):
    import json
    return json.loads(json.dumps(obj))
