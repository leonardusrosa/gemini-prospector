import json
import sys
import tempfile
from pathlib import Path
import pytest

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from factual_drift_review import (
    check_factual_drift,
    is_presentation_patch,
    ensure_git_commit_available,
    calculate_baseline_sha256,
)

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
        changed_files=["index.html", "review-manifest.json", "research/factual-refresh.json"],
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
        changed_files=["styles.css", "review-manifest.json", "research/factual-refresh.json"],
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
        changed_files=["review-manifest.json", "research/factual-refresh.json"],
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
        changed_files=["index.html", "review-manifest.json", "research/factual-refresh.json"],
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
        changed_files=["review-manifest.json", "research/factual-refresh.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
    )
    assert res.passed is False
    assert any("does not exist: research/does-not-exist.png" in f for f in res.failures)


def test_regression_i_stale_unchanged_factual_refresh_reused_fails(tmp_path):
    """I. stale unchanged factual-refresh reused => FAIL."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["phone"] = "5519999999999"

    proof = tmp_path / "research" / "phone-proof.txt"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("phone proof", encoding="utf-8")

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "old phone update",
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
        commit_message="update phone",
        changed_files=["review-manifest.json"],
        factual_refresh_data=refresh_data,
        factual_refresh_modified=False,
        base_dir=tmp_path,
    )
    assert res.passed is False
    assert any("stale refresh" in f for f in res.failures)


def test_regression_j_factual_only_partial_authorization_fails(tmp_path):
    """J. factual-only partial authorization => FAIL unauthorized field (no HTML/CSS touched)."""
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
        commit_message="factual-refresh: update records",
        changed_files=["review-manifest.json", "research/factual-refresh.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
    )
    assert res.passed is False
    assert any("cnpj" in f for f in res.failures)


def test_regression_k_no_trustworthy_baseline_fails():
    """K. no trustworthy baseline => FAIL (reports FACTUAL_DRIFT_BASELINE_UNRESOLVED)."""
    res = check_factual_drift(
        before_manifest=None,
        after_manifest=BASE_MANIFEST_BEFORE,
        commit_message="deploy: initial site",
        changed_files=["index.html"],
    )
    assert res.passed is False
    assert any("FACTUAL_DRIFT_BASELINE_UNRESOLVED" in f for f in res.failures)


def test_regression_l_multi_commit_push_with_drift_in_intermediate_commit():
    """L. multi-commit push with drift in intermediate commit: comparing baseline A to HEAD C detects drift."""
    manifest_a = json_clone(BASE_MANIFEST_BEFORE)

    manifest_b = json_clone(manifest_a)
    manifest_b["factualEvidence"]["verifiedServices"].append({"claim": "Alinhadores"})

    manifest_c = json_clone(manifest_b)

    res = check_factual_drift(
        before_manifest=manifest_a,
        after_manifest=manifest_c,
        commit_message="fix: layout spacing",
        changed_files=["styles.css", "review-manifest.json"],
        factual_refresh_data=None,
    )
    assert res.passed is False
    assert any("factualEvidence.verifiedServices" in f for f in res.failures)


def test_regression_m_internal_json_labels_itself_official_record_fails(tmp_path):
    """M. internal JSON labels itself official_record with no underlying source => FAIL."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["factualEvidence"]["verifiedServices"].append({"claim": "Nova Especialidade"})

    internal_summary = tmp_path / "research" / "internal-notes.json"
    internal_summary.parent.mkdir(parents=True, exist_ok=True)
    internal_summary.write_text(
        json.dumps({"internal": True, "justification": "Accepted conservative baseline record"}),
        encoding="utf-8",
    )

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "internal baseline note",
        "changedFields": [{"path": "factualEvidence.verifiedServices", "evidenceIds": ["src-note"]}],
        "sources": [
            {
                "id": "src-note",
                "type": "official_record",
                "artifactPath": "research/internal-notes.json",
            }
        ],
    }

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=after,
        commit_message="update services",
        changed_files=["review-manifest.json", "research/factual-refresh.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
    )
    assert res.passed is False
    assert any("cannot declare itself 'official_record'" in f for f in res.failures)


def test_regression_n_exact_accepted_baseline_restoration_passes(tmp_path):
    """N. exact accepted-baseline restoration pointing to real previous commit/value => PASS."""
    current_manifest = json_clone(BASE_MANIFEST_BEFORE)
    current_manifest["factualEvidence"]["verifiedServices"] = [
        {"claim": "Ortodontia Preventiva", "verified": True}
    ]

    target_restored = json_clone(BASE_MANIFEST_BEFORE)

    trusted_baseline_file = {
        "acceptedBaselineHistory": {
            "abc1234": {
                "iost": {
                    "factualEvidence.verifiedServices": [
                        "Avaliação ortodôntica",
                        "Manutenção de aparelho fixo",
                    ]
                }
            }
        }
    }

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "restore accepted baseline",
        "changedFields": [{"path": "factualEvidence.verifiedServices", "evidenceIds": ["src-base"]}],
        "sources": [
            {
                "id": "src-base",
                "type": "accepted_baseline",
                "repository": "prospector-sites",
                "commitSha": "abc1234",
                "manifestPath": "clientes/iost/review-manifest.json",
                "protectedPath": "factualEvidence.verifiedServices",
                "expectedValue": [
                    "Avaliação ortodôntica",
                    "Manutenção de aparelho fixo",
                ],
            }
        ],
    }

    res = check_factual_drift(
        before_manifest=current_manifest,
        after_manifest=target_restored,
        commit_message="restore conservative verifiedServices",
        changed_files=["review-manifest.json", "research/factual-refresh.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
        repo_dir=None,
        trusted_persisted_baseline=trusted_baseline_file,
    )
    assert res.passed is True
    assert len(res.failures) == 0


def test_regression_o_head_edits_baseline_and_manifest_fails():
    """O. current HEAD edits baseline + manifest to same fake value => MUST NOT hide drift => FAIL."""
    trusted_baseline_manifest = json_clone(BASE_MANIFEST_BEFORE)

    head_manifest = json_clone(BASE_MANIFEST_BEFORE)
    head_manifest["phone"] = "5519888888888"

    res = check_factual_drift(
        before_manifest=trusted_baseline_manifest,
        after_manifest=head_manifest,
        commit_message="chore: update phone and baseline together",
        changed_files=["review-manifest.json", "factual-baseline.json"],
        factual_refresh_data=None,
    )
    assert res.passed is False
    assert any("phone" in f for f in res.failures)


def test_regression_p_shallow_clone_head_adds_matching_history_fails(tmp_path):
    """P. shallow clone, historical accepted_baseline unavailable in git, HEAD adds matching acceptedBaselineHistory => FAIL."""
    current_manifest = json_clone(BASE_MANIFEST_BEFORE)
    current_manifest["phone"] = "5519888888888"

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "unauthorized baseline restore",
        "changedFields": [{"path": "phone", "evidenceIds": ["src-fake"]}],
        "sources": [
            {
                "id": "src-fake",
                "type": "accepted_baseline",
                "repository": "prospector-sites",
                "commitSha": "fake-sha-not-in-history",
                "manifestPath": "clientes/iost/review-manifest.json",
                "protectedPath": "phone",
                "expectedValue": "5519888888888",
            }
        ],
    }

    trusted_baseline_file = {
        "acceptedBaselineHistory": {}
    }

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=current_manifest,
        commit_message="restore fake phone",
        changed_files=["review-manifest.json", "research/factual-refresh.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
        repo_dir=None,
        trusted_persisted_baseline=trusted_baseline_file,
    )
    assert res.passed is False
    assert any("could not be verified in git history or trusted prior baseline" in f for f in res.failures)


def test_regression_q_trusted_previous_production_contains_history_passes(tmp_path):
    """Q. trusted previous production contains acceptedBaselineHistory => PASS."""
    target_manifest = json_clone(BASE_MANIFEST_BEFORE)
    current_manifest = json_clone(BASE_MANIFEST_BEFORE)
    current_manifest["phone"] = "5519111111111"

    refresh_data = {
        "schemaVersion": 1,
        "collectedAt": "2026-09-01T12:00:00Z",
        "reason": "restore accepted baseline",
        "changedFields": [{"path": "phone", "evidenceIds": ["src-base"]}],
        "sources": [
            {
                "id": "src-base",
                "type": "accepted_baseline",
                "repository": "prospector-sites",
                "commitSha": "historic-prod-sha",
                "manifestPath": "clientes/iost/review-manifest.json",
                "protectedPath": "phone",
                "expectedValue": "5519996571896",
            }
        ],
    }

    trusted_baseline_file = {
        "acceptedBaselineHistory": {
            "historic-prod-sha": {
                "iost": {
                    "phone": "5519996571896"
                }
            }
        }
    }

    res = check_factual_drift(
        before_manifest=current_manifest,
        after_manifest=target_manifest,
        commit_message="restore phone from accepted baseline",
        changed_files=["review-manifest.json", "research/factual-refresh.json"],
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
        repo_dir=None,
        trusted_persisted_baseline=trusted_baseline_file,
    )
    assert res.passed is True
    assert len(res.failures) == 0


def test_regression_r_production_no_head_tilde_1_fallback():
    """R. production baseline ref unavailable but HEAD~1 exists => FAIL, no production HEAD~1 fallback."""
    res = check_factual_drift(
        before_manifest=None,
        after_manifest=BASE_MANIFEST_BEFORE,
        commit_message="chore: update",
        is_ci=True,
    )
    assert res.passed is False
    assert any("FACTUAL_DRIFT_BASELINE_UNRESOLVED" in f for f in res.failures)


def test_regression_s_trusted_sha_missing_locally_targeted_fetch_succeeds(monkeypatch):
    """S. trusted SHA missing locally, targeted git fetch succeeds => PASS."""
    def mock_ensure(ref, repo_dir=None, is_ci=False):
        if ref == "remote-sha-123":
            return "remote-sha-123"
        return None

    resolved = mock_ensure("remote-sha-123", is_ci=True)
    assert resolved == "remote-sha-123"

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=BASE_MANIFEST_BEFORE,
        commit_message="fix: layout",
        changed_files=["styles.css"],
        baseline_mode="EXPLICIT_REF",
        baseline_sha="remote-sha-123",
    )
    assert res.passed is True
    assert res.baseline_mode == "EXPLICIT_REF"
    assert res.baseline_sha == "remote-sha-123"


def test_regression_t_trusted_sha_missing_locally_targeted_fetch_fails():
    """T. trusted SHA missing locally, targeted fetch fails, no valid baseline hash => FAIL."""
    def mock_ensure(ref, repo_dir=None, is_ci=False):
        return None

    resolved = mock_ensure("unreachable-sha", is_ci=True)
    assert resolved is None

    res = check_factual_drift(
        before_manifest=None,
        after_manifest=BASE_MANIFEST_BEFORE,
        commit_message="chore: deploy",
        is_ci=True,
    )
    assert res.passed is False
    assert any("FACTUAL_DRIFT_BASELINE_UNRESOLVED" in f for f in res.failures)


def test_regression_u_shallow_clone_hash_matches_external_env_anchor():
    """U. shallow clone, current factual-baseline.json hash matches external env anchor => PASS."""
    content = json.dumps({"schemaVersion": 1, "clients": {"iost": BASE_MANIFEST_BEFORE}}).encode("utf-8")
    expected_hash = calculate_baseline_sha256(content)

    computed_hash = calculate_baseline_sha256(content)
    assert computed_hash == expected_hash

    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=BASE_MANIFEST_BEFORE,
        commit_message="fix: style",
        changed_files=["styles.css"],
        baseline_mode="EXTERNAL_SHA256",
        baseline_sha=expected_hash,
    )
    assert res.passed is True
    assert res.baseline_mode == "EXTERNAL_SHA256"


def test_regression_v_candidate_edits_baseline_hash_mismatch_fails():
    """V. candidate edits factual-baseline.json, external env hash still points to prior accepted bytes => FAIL."""
    original_content = json.dumps({"schemaVersion": 1, "phone": "111"}).encode("utf-8")
    env_hash = calculate_baseline_sha256(original_content)

    tampered_content = json.dumps({"schemaVersion": 1, "phone": "999"}).encode("utf-8")
    tampered_hash = calculate_baseline_sha256(tampered_content)

    assert tampered_hash != env_hash

    res = check_factual_drift(
        before_manifest=None,
        after_manifest=BASE_MANIFEST_BEFORE,
        commit_message="tampered baseline",
        is_ci=True,
    )
    assert res.passed is False
    assert any("FACTUAL_DRIFT_BASELINE_UNRESOLVED" in f for f in res.failures)


def test_regression_w_candidate_edits_baseline_and_manifest_same_fake_value():
    """W. candidate edits baseline + manifest to same fake value => FAIL."""
    trusted_manifest = json_clone(BASE_MANIFEST_BEFORE)
    fake_manifest = json_clone(BASE_MANIFEST_BEFORE)
    fake_manifest["phone"] = "5519777777777"

    res = check_factual_drift(
        before_manifest=trusted_manifest,
        after_manifest=fake_manifest,
        commit_message="tamper phone in both",
        changed_files=["review-manifest.json", "factual-baseline.json"],
    )
    assert res.passed is False
    assert any("phone" in f for f in res.failures)


def test_regression_x_production_no_trusted_ref_no_hash_head_tilde_1_exists():
    """X. production no trusted ref, no valid external hash, HEAD~1 exists => FAIL."""
    res = check_factual_drift(
        before_manifest=None,
        after_manifest=BASE_MANIFEST_BEFORE,
        is_ci=True,
    )
    assert res.passed is False
    assert any("FACTUAL_DRIFT_BASELINE_UNRESOLVED" in f for f in res.failures)


def test_regression_y_external_sha256_valid_commit_unavailable_no_mutation_passes():
    """Y. EXTERNAL_SHA256 valid, historical commit unavailable, HEAD~1 exists, no factual mutation => PASS without HEAD~1."""
    res = check_factual_drift(
        before_manifest=BASE_MANIFEST_BEFORE,
        after_manifest=BASE_MANIFEST_BEFORE,
        commit_message="fix: responsive css",
        changed_files=None,  # diff unavailable
        history_available=False,
        baseline_mode="EXTERNAL_SHA256",
        baseline_sha="3c34dd26",
    )
    assert res.passed is True
    assert len(res.failures) == 0


def test_regression_z_external_sha256_valid_commit_unavailable_mutation_fails_closed(tmp_path):
    """Z. EXTERNAL_SHA256 valid, historical commit unavailable, protected mutation exists even with refresh => FAIL FACTUAL_DRIFT_HISTORY_REQUIRED_FOR_MUTATION."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["phone"] = "5519999999999"

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
        commit_message="update phone",
        changed_files=None,  # diff unavailable
        history_available=False,
        factual_refresh_data=refresh_data,
        baseline_mode="EXTERNAL_SHA256",
        baseline_sha="3c34dd26",
    )
    assert res.passed is False
    assert any("FACTUAL_DRIFT_HISTORY_REQUIRED_FOR_MUTATION" in f for f in res.failures)


def test_regression_aa_external_sha256_valid_commit_fetched_valid_refresh_passes(tmp_path):
    """AA. EXTERNAL_SHA256 valid, historical commit successfully targeted-fetched, valid new factual refresh => PASS normal full-history path."""
    after = json_clone(BASE_MANIFEST_BEFORE)
    after["phone"] = "5519999999999"

    proof = tmp_path / "research" / "phone-proof.txt"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("proof text", encoding="utf-8")

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
        commit_message="factual-refresh: update phone",
        changed_files=["review-manifest.json", "research/factual-refresh.json"],
        history_available=True,  # commit fetched!
        factual_refresh_data=refresh_data,
        base_dir=tmp_path,
        baseline_mode="EXTERNAL_SHA256",
        baseline_sha="3c34dd26",
    )
    assert res.passed is True
    assert len(res.failures) == 0


def json_clone(obj):
    return json.loads(json.dumps(obj))
