#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Design Framework V3.1 regression test suite.

Validates:
1. Schema v3 future leads do not require OpenDesign.
2. GPT-Taste design decision is required before code (PASS / PASS_AFTER_DIRECTION_CHANGE).
3. GPT-Taste implementation review is required post-browser-QA (PASS / PASS_AFTER_CHANGES).
4. All 7 Design DNA fields are strictly required.
5. Repeat DNA against recent published sites triggers NEEDS_DIRECTION_CHANGE.
6. Signature section is mandatory in design-read and requires data-role="signature-section" in HTML.
7. Healthcare visualizer / evidence safety blocks fabricated clinical guarantees.
8. Missing 21st.dev MCP does not block publication.
9. Missing Aura index does not block publication.
10. Missing Preline does not block publication.
11. External resources without confirmed commercial use FAIL.
12. Native build passes without external resource provenance.
13. New Brazilian discovery is blocked (NEW_DISCOVERY_BR = DISABLED).
14. Existing Brazilian leads can be updated and closed.
15. Factual re-check & semantic claim audit fail on unsupported claims.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))

from autonomous_site_review_core import (
    Review,
    check_gpt_taste,
    check_design_dna,
    check_design_diversity,
    check_signature_section,
    check_resource_provenance,
    check_21st_dev,
    check_aura,
    check_preline,
    check_mandatory_prepublish_reviews,
    check_semantic_claims,
)
from open_design_direction_review import validate_open_design_direction


def _valid_dna_dict() -> dict:
    return {
        "heroGrammar": "split-editorial",
        "paletteFamily": "warm-sand-bronze",
        "typographyCharacter": "oversized-serif-display",
        "layoutGrammar": "asymmetric-staggered",
        "motionLanguage": "gentle-reveal-subtle-parallax",
        "reviewTreatment": "curated-quotes-with-metrics",
        "signatureModule": "interactive-treatment-timeline",
    }


def _valid_dna_design_read() -> str:
    return "\n".join([
        "DESIGN_DNA_HERO_GRAMMAR: split-editorial",
        "DESIGN_DNA_PALETTE_FAMILY: warm-sand-bronze",
        "DESIGN_DNA_TYPOGRAPHY_CHARACTER: oversized-serif-display",
        "DESIGN_DNA_LAYOUT_GRAMMAR: asymmetric-staggered",
        "DESIGN_DNA_MOTION_LANGUAGE: gentle-reveal-subtle-parallax",
        "DESIGN_DNA_REVIEW_TREATMENT: curated-quotes-with-metrics",
        "DESIGN_DNA_SIGNATURE_MODULE: interactive-treatment-timeline",
    ])


def _passed(rev: Review) -> bool:
    return len(rev.failed) == 0


def _errors(rev: Review) -> list[str]:
    return [item["detail"] for item in rev.failed]


def test_future_lead_no_open_design():
    """Schema v3 future leads must not require OpenDesign configuration or DESIGN.md."""
    manifest = {
        "schemaVersion": 3,
        "siteMode": "new_site_concept",
        "slug": "future-aesthetic-clinic",
    }
    errors = validate_open_design_direction(manifest, "", None)
    assert errors == [], f"Expected 0 errors for schema v3 without OpenDesign, got {errors}"


def test_gpt_taste_decision_required():
    """Schema v3+ requires GPT_TASTE_DESIGN_DECISION before code."""
    manifest = {
        "schemaVersion": 3,
        "siteMode": "new_site_concept",
        "slug": "studio-nova",
        "gptTaste": {"required": True, "pathRequired": False},
    }
    # Missing decision fails
    rev = Review()
    check_gpt_taste(manifest, "GPT_TASTE_READ: PASS\n", rev)
    assert not _passed(rev), "Expected failure when GPT_TASTE_DESIGN_DECISION is missing"
    assert any("GPT_TASTE_DESIGN_DECISION" in err for err in _errors(rev))

    # Blocked decision fails
    rev = Review()
    check_gpt_taste(manifest, "GPT_TASTE_READ: PASS\nGPT_TASTE_DESIGN_DECISION: BLOCKED_SKILL_UNAVAILABLE\n", rev)
    assert not _passed(rev), "Expected failure when GPT_TASTE_DESIGN_DECISION is BLOCKED"

    # Valid PASS passes
    rev = Review()
    design = (
        "GPT_TASTE_READ: PASS\n"
        "GPT_TASTE_DESIGN_DECISION: PASS\n"
        "GPT_TASTE_IMPLEMENTATION_REVIEW: PASS\n"
    )
    check_gpt_taste(manifest, design, rev)
    assert _passed(rev), f"Expected pass, got {_errors(rev)}"


def test_gpt_taste_implementation_review_required():
    """Schema v3+ requires GPT_TASTE_IMPLEMENTATION_REVIEW after browser QA."""
    manifest = {
        "schemaVersion": 3,
        "siteMode": "new_site_concept",
        "slug": "studio-nova",
        "gptTaste": {"required": True, "pathRequired": False},
    }
    design_without_impl = (
        "GPT_TASTE_READ: PASS\n"
        "GPT_TASTE_DESIGN_DECISION: PASS\n"
    )
    rev = Review()
    check_gpt_taste(manifest, design_without_impl, rev)
    assert not _passed(rev), "Expected failure when GPT_TASTE_IMPLEMENTATION_REVIEW is missing on schema v3"
    assert any("GPT_TASTE_IMPLEMENTATION_REVIEW" in err for err in _errors(rev))

    design_with_impl = design_without_impl + "GPT_TASTE_IMPLEMENTATION_REVIEW: PASS_AFTER_CHANGES\n"
    rev = Review()
    check_gpt_taste(manifest, design_with_impl, rev)
    assert _passed(rev), f"Expected pass for PASS_AFTER_CHANGES, got {_errors(rev)}"


def test_all_seven_design_dna_fields_required():
    """All 7 design DNA fields must be present and non-empty."""
    manifest = {
        "schemaVersion": 3,
        "siteMode": "new_site_concept",
        "slug": "studio-nova",
        "designDna": _valid_dna_dict(),
    }
    rev = Review()
    check_design_dna(manifest, _valid_dna_design_read(), rev)
    assert _passed(rev), f"Expected pass with 7 DNA fields, got {_errors(rev)}"

    # Missing one in manifest
    bad_manifest = dict(manifest)
    bad_manifest["designDna"] = dict(_valid_dna_dict())
    del bad_manifest["designDna"]["signatureModule"]
    rev = Review()
    check_design_dna(bad_manifest, _valid_dna_design_read(), rev)
    assert not _passed(rev), "Expected failure when signatureModule missing from manifest"
    assert any("signatureModule" in err for err in _errors(rev))


def test_repeat_dna_can_force_direction_change():
    """When a new site duplicates recent DNA, diversity check reports NEEDS_DIRECTION_CHANGE."""
    with tempfile.TemporaryDirectory() as tmp:
        base_dir = Path(tmp)
        # Create published-sites.json with matching DNA
        resources_dir = base_dir / "design-resources" / "design-dna"
        resources_dir.mkdir(parents=True, exist_ok=True)
        published = [
            {
                "slug": "recent-site-1",
                "publishedAt": "2026-09-01",
                "dna": _valid_dna_dict(),
            }
        ]
        (resources_dir / "published-sites.json").write_text(json.dumps(published), encoding="utf-8")

        manifest = {
            "schemaVersion": 3,
            "siteMode": "new_site_concept",
            "slug": "repeat-look-clinic",
            "designDna": _valid_dna_dict(),
        }
        # Claiming PASS when too similar should fail
        design_claiming_pass = _valid_dna_design_read() + "\nDESIGN_DIVERSITY: PASS\n"
        rev = Review()
        check_design_diversity(manifest, design_claiming_pass, rev, base_dir=base_dir)
        assert not _passed(rev), "Expected failure when repeat DNA is claimed as PASS"
        assert any("NEEDS_DIRECTION_CHANGE" in err for err in _errors(rev))

        # Altering direction resolves diversity check
        altered_dna = dict(_valid_dna_dict())
        altered_dna["heroGrammar"] = "full-bleed-video-ambient"
        altered_dna["paletteFamily"] = "dark-noir-sapphire"
        altered_dna["layoutGrammar"] = "horizontal-scroll-gallery"
        altered_dna["typographyCharacter"] = "brutalist-mono-slab"

        altered_manifest = {
            "schemaVersion": 3,
            "siteMode": "new_site_concept",
            "slug": "distinct-clinic",
            "designDna": altered_dna,
        }
        altered_design = "\n".join(f"DESIGN_DNA_{k.upper()}: {v}" for k, v in altered_dna.items()) + "\nDESIGN_DIVERSITY: PASS\n"
        rev = Review()
        check_design_diversity(altered_manifest, altered_design, rev, base_dir=base_dir)
        assert _passed(rev), f"Expected pass for altered DNA, got {_errors(rev)}"


def test_signature_section_required():
    """Every new schema v3 site requires SIGNATURE_SECTION: PASS and data-role='signature-section' in HTML."""
    manifest = {
        "schemaVersion": 3,
        "siteMode": "new_site_concept",
        "slug": "signature-clinic",
        "signatureSection": {
            "type": "interactive-timeline",
            "purpose": "Show step-by-step patient journey",
            "evidenceSafety": "illustrative journey only, no clinical guarantee",
        },
    }
    valid_html = '<section data-role="signature-section" id="journey"><h2>Jornada</h2></section>'
    valid_design = (
        "SIGNATURE_SECTION: PASS\n"
        "SIGNATURE_SECTION_TYPE: interactive-timeline\n"
        "SIGNATURE_SECTION_PURPOSE: Show step-by-step patient journey\n"
        "SIGNATURE_SECTION_EVIDENCE_SAFETY: illustrative journey only, no clinical guarantee\n"
    )

    rev = Review()
    check_signature_section(manifest, valid_html, valid_design, rev)
    assert _passed(rev), f"Expected pass, got {_errors(rev)}"

    # Missing HTML hook
    rev = Review()
    check_signature_section(manifest, "<section id='journey'></section>", valid_design, rev)
    assert not _passed(rev), "Expected failure when data-role='signature-section' is missing in HTML"
    assert any("signature-section" in err for err in _errors(rev))

    # Missing design-read PASS
    rev = Review()
    check_signature_section(manifest, valid_html, "SIGNATURE_SECTION: FAIL\n", rev)
    assert not _passed(rev), "Expected failure when SIGNATURE_SECTION is FAIL"


def test_healthcare_visualizer_safety():
    """Fabricated clinical guarantees or unauthorized patient before/after must fail."""
    manifest = {
        "schemaVersion": 3,
        "siteMode": "new_site_concept",
        "slug": "unsafe-clinic",
        "signatureSection": {
            "type": "results-guarantee",
            "purpose": "Promise 100% cure rate",
            "evidenceSafety": "resultado garantido de 100% de cura para todos os pacientes",
        },
    }
    html = '<section data-role="signature-section">Garantimos resultado de 100% de cura</section>'
    design = (
        "SIGNATURE_SECTION: PASS\n"
        "SIGNATURE_SECTION_TYPE: results-guarantee\n"
        "SIGNATURE_SECTION_EVIDENCE_SAFETY: resultado médico garantido sem ressalvas\n"
    )
    rev = Review()
    check_signature_section(manifest, html, design, rev)
    assert not _passed(rev), "Expected failure for unsafe medical guarantee in signature section"
    assert any("guarantee" in err.lower() or "cura" in err.lower() or "segurança" in err.lower() or "safety" in err.lower() for err in _errors(rev))


def test_21st_missing_does_not_block():
    """Optional resource 21st.dev unavailable does not block schema v3 review."""
    manifest = {"schemaVersion": 3, "slug": "test-site"}
    design = "TWENTY_FIRST_DEV: UNAVAILABLE\n"
    rev = Review()
    check_21st_dev(manifest, design, rev)
    assert _passed(rev), f"Expected pass when 21st.dev is unavailable, got {_errors(rev)}"


def test_aura_missing_does_not_block():
    """Optional resource Aura unavailable does not block schema v3 review."""
    manifest = {"schemaVersion": 3, "slug": "test-site"}
    design = "AURA_RESOURCE: UNAVAILABLE\n"
    rev = Review()
    check_aura(manifest, design, rev)
    assert _passed(rev), f"Expected pass when Aura is unavailable, got {_errors(rev)}"


def test_preline_missing_does_not_block():
    """Optional resource Preline unavailable does not block schema v3 review."""
    manifest = {"schemaVersion": 3, "slug": "test-site"}
    design = "PRELINE_RESOURCE: UNAVAILABLE\n"
    rev = Review()
    check_preline(manifest, design, rev)
    assert _passed(rev), f"Expected pass when Preline is unavailable, got {_errors(rev)}"


def test_external_resource_without_commercial_use_fails():
    """Reusing an external asset without confirmed commercial use must fail."""
    manifest = {
        "schemaVersion": 3,
        "slug": "resource-site",
        "resourceProvenance": {
            "source": "aura",
            "sourceUrl": "https://example.com/component",
            "license": "Non-Commercial",
            "commercialUse": "UNKNOWN",
        },
    }
    design = (
        "RESOURCE_PROVENANCE: AURA\n"
        "RESOURCE_SOURCE_URL: https://example.com/component\n"
        "RESOURCE_LICENSE: Non-Commercial\n"
        "RESOURCE_COMMERCIAL_USE: UNKNOWN\n"
    )
    rev = Review()
    check_resource_provenance(manifest, design, rev)
    assert not _passed(rev), "Expected failure when commercialUse is UNKNOWN"
    assert any("commercial" in err.lower() for err in _errors(rev))


def test_native_build_passes_without_external_provenance():
    """Native/custom build without external resources passes provenance cleanly."""
    manifest = {
        "schemaVersion": 3,
        "slug": "native-site",
        "resourceProvenance": {"source": "native"},
    }
    design = "RESOURCE_PROVENANCE: NATIVE\n"
    rev = Review()
    check_resource_provenance(manifest, design, rev)
    assert _passed(rev), f"Expected pass for native resource provenance, got {_errors(rev)}"


def test_new_br_lead_rejected_in_crm():
    """CRM must reject new Brazilian leads under Market Policy V3 (NEW_DISCOVERY_BR = DISABLED)."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        # We invoke prospector-mcp logic pointing PASTA to tmp
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        # Attempt to save a new Brazilian lead
        new_br_lead = {
            "slug": "dentista-novo-br",
            "nome": "Clínica Nova Brasil",
            "nicho": "Odontologia",
            "cidade": "Rio Claro, SP, Brasil",
            "country": "BR",
            "locale": "pt-BR",
            "phoneCountryCode": "55",
            "whatsapp": "5519999990000",
        }
        res = pm.f_salvar(new_br_lead)
        assert "erro" in res, "Expected error when saving new BR lead"
        assert "NEW_DISCOVERY_BR is DISABLED" in res["erro"], f"Expected disabled message, got {res}"

        # Attempt to save a new European / Tier A lead should succeed
        new_us_lead = {
            "slug": "miami-dental-care",
            "nome": "Miami Dental Care",
            "nicho": "Dentistry",
            "cidade": "Miami, FL, US",
            "country": "US",
            "locale": "en-US",
            "phoneCountryCode": "1",
            "currency": "USD",
            "whatsapp": "13055550199",
        }
        res_us = pm.f_salvar(new_us_lead)
        assert res_us.get("ok") is True, f"Expected success for US lead, got {res_us}"


def test_existing_br_lead_can_update_in_crm():
    """Existing Brazilian leads remain valid and can advance in the funnel, update, and close."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        # Seed an existing BR lead directly in the database
        conn = pm.conexao()
        conn.execute(
            "INSERT INTO leads (slug, nome, cidade, country, locale, phoneCountryCode, status, valor, atualizado) "
            "VALUES ('clinica-legada-br', 'Clínica Legada', 'Rio Claro SP', 'BR', 'pt-BR', '55', 'novo', 0, '2026-09-01 10:00')"
        )
        conn.commit()
        conn.close()

        # Update the existing BR lead via f_salvar
        update_data = {
            "slug": "clinica-legada-br",
            "obs": "Cliente respondeu interesse no conceito",
            "status": "respondeu",
        }
        res = pm.f_salvar(update_data)
        assert res.get("ok") is True, f"Expected existing BR lead to update successfully, got {res}"

        # Advance status via f_status
        res_st = pm.f_status("clinica-legada-br", "fechado")
        assert res_st.get("ok") is True, f"Expected status change to succeed, got {res_st}"

        # Close via f_fechar
        res_close = pm.f_fechar("clinica-legada-br", valor=3500.0, manutencao=350.0)
        assert res_close.get("ok") is True, f"Expected close to succeed, got {res_close}"

        lead = pm.f_obter("clinica-legada-br")
        assert lead["status"] == "fechado"
        assert lead["valor"] == 3500.0


def test_semantic_factual_gates_still_block_bad_claims():
    """Unsupported medical or operational claims fail semantic and prepublish reviews."""
    manifest = {
        "schemaVersion": 3,
        "siteMode": "new_site_concept",
        "slug": "clinic-bad-claims",
        "prepublishReviews": {
            "factualRecheck": "FAIL",
            "semanticClaimAudit": "FAIL",
        },
    }
    design = (
        "IMPECCABLE_REVIEW: PASS\n"
        "COPYWRITING_MARKETING_REVIEW: PASS\n"
        "FACTUAL_RECHECK: FAIL\n"
        "SEMANTIC_CLAIM_AUDIT: FAIL\n"
    )
    rev = Review()
    check_mandatory_prepublish_reviews(manifest, design, rev)
    assert not _passed(rev), "Expected prepublish review failure when factual recheck and semantic claim audit FAIL"
    assert any("FACTUAL_RECHECK" in err for err in _errors(rev))
    assert any("SEMANTIC_CLAIM_AUDIT" in err for err in _errors(rev))


if __name__ == "__main__":
    test_funcs = [k for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn_name in test_funcs:
        globals()[fn_name]()
        print(f"[PASS] {fn_name}")
    print(f"\nAll {len(test_funcs)} Design Framework V3.1 test cases passed successfully.")
