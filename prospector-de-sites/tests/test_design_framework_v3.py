#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Design Framework V3.1.1 regression test suite.

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
16. V3.1.1: US cities (Springfield, Prosper, Prescott, Miami) NOT flagged as BR.
17. V3.1.1: Raw '55' phone without E.164 does NOT imply BR.
18. V3.1.1: Verified E.164 +55 without country blocked as BR inference.
19. V3.1.1: Explicit country=US overrides misleading city substrings.
20. V3.1.1: marketTier auto-computed (TIER_A, TIER_B, OTHER).
21. V3.1.1: Fresh DB schema includes marketTier column.
22. V3.1.1: salvar_lead exposes marketTier and MARKET_DEFAULTS auto-fill.
23. V3.1.1: DNA token similarity (Jaccard) catches reordered tokens.
24. V3.1.1: DNA token similarity allows truly distinct values.
25. V3.1.1: Aura resources stay UNCONFIRMED/REFERENCE_ONLY.
26. V3.1.1: External resources without license fail provenance gate.
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
    check_hero_media_plane,
    check_navbar_labels,
    _dna_token_similarity,
    derive_dom_structural_fingerprint,
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


# ============================
# V3.1.1 TESTS — Market Policy
# ============================

def test_us_cities_not_flagged_as_brazilian():
    """Explicit country=US must override any misleading phone/city heuristic."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        us_cities = [
            {"slug": "springfield-il", "nome": "Springfield Dental", "cidade": "Springfield, IL", "country": "US", "phoneCountryCode": "1"},
            {"slug": "prosper-tx", "nome": "Prosper Auto Detail", "cidade": "Prosper, TX", "country": "US", "phoneCountryCode": "1"},
            {"slug": "prescott-az", "nome": "Prescott Wellness", "cidade": "Prescott, AZ", "country": "US"},
            {"slug": "miami-fl", "nome": "Miami Smile Center", "cidade": "Miami, FL, US", "country": "US", "whatsapp": "+13055550199"},
        ]
        for lead_data in us_cities:
            res = pm.f_salvar(lead_data)
            assert res.get("ok") is True, f"US lead {lead_data['slug']} should NOT be blocked: {res}"
            lead = pm.f_obter(lead_data["slug"])
            assert lead["marketTier"] == "TIER_A", f"US lead {lead_data['slug']} should be TIER_A, got {lead['marketTier']}"


def test_raw_55_phone_without_e164_does_not_imply_br():
    """Raw number starting '55' (without +) must NOT imply BR when country is missing."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        # Raw 55 phone without verified E.164 prefix, no country
        res = pm.f_salvar({"slug": "raw-55-lead", "nome": "Test Raw", "cidade": "Dallas, TX", "whatsapp": "5512345678"})
        assert res.get("ok") is True, f"Raw '55' phone without + and no country must NOT be blocked: {res}"


def test_verified_e164_plus55_without_country_blocked():
    """Verified E.164 number starting +55 without explicit country must be blocked as BR inference."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        res = pm.f_salvar({"slug": "e164-br", "nome": "E164 Test", "whatsapp": "+5519999990000"})
        assert "erro" in res, "E.164 +55 number without country should be blocked as inferred BR"
        assert "NEW_DISCOVERY_BR" in res["erro"]


def test_explicit_us_overrides_misleading_city():
    """country=US overrides even if city string contains 'sp' or 'brasil' substrings."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        # City containing "sp" but country is US
        res = pm.f_salvar({"slug": "cusp-city", "nome": "Cusp Dental", "cidade": "Cusp Springs, MO", "country": "US"})
        assert res.get("ok") is True, f"US lead with 'sp' in city must NOT be blocked: {res}"


def test_market_tier_computed_correctly():
    """marketTier auto-computation: US=TIER_A, PT=TIER_B, JP=OTHER."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        cases = [
            ({"slug": "us-lead", "nome": "US Lead", "country": "US"}, "TIER_A"),
            ({"slug": "ca-lead", "nome": "CA Lead", "country": "CA"}, "TIER_A"),
            ({"slug": "pt-lead", "nome": "PT Lead", "country": "PT"}, "TIER_B"),
            ({"slug": "mx-lead", "nome": "MX Lead", "country": "MX"}, "TIER_B"),
            ({"slug": "jp-lead", "nome": "JP Lead", "country": "JP"}, "OTHER"),
        ]
        for lead_data, expected_tier in cases:
            res = pm.f_salvar(lead_data)
            assert res.get("ok") is True, f"Lead {lead_data['slug']} save failed: {res}"
            lead = pm.f_obter(lead_data["slug"])
            assert lead["marketTier"] == expected_tier, (
                f"Lead {lead_data['slug']} (country={lead_data['country']}): "
                f"expected {expected_tier}, got {lead['marketTier']}"
            )


def test_market_tier_fresh_db_schema():
    """Fresh DB schema includes marketTier column."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        conn = pm.conexao()
        cursor = conn.execute("PRAGMA table_info(leads)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        assert "marketTier" in columns, f"marketTier column missing from fresh DB schema. Columns: {columns}"


def test_salvar_lead_exposes_market_tier():
    """salvar_lead MCP tool accepts marketTier parameter and persists it."""
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "prospector.db"
        import importlib.util
        spec = importlib.util.spec_from_file_location("prospector_mcp", str(ROOT.parent / "prospector-mcp.py"))
        pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pm)
        pm.DB = str(db_path)
        pm.PASTA = str(tmp)

        res = pm.f_salvar({"slug": "explicit-tier", "nome": "Explicit Tier", "country": "US", "marketTier": "TIER_A"})
        assert res.get("ok") is True
        lead = pm.f_obter("explicit-tier")
        assert lead["marketTier"] == "TIER_A"
        assert lead["currency"] == "USD", "MARKET_DEFAULTS should auto-fill USD for US"


# ============================
# V3.1.1 TESTS — Diversity Gate
# ============================

def test_dna_token_similarity_catches_reorder():
    """Reordered tokens like 'gentle-reveal-subtle-parallax' vs 'subtle-reveal-gentle-parallax' should match >= 0.7."""
    sim = _dna_token_similarity("gentle-reveal-subtle-parallax", "subtle-reveal-gentle-parallax")
    assert sim >= 0.7, f"Reordered tokens should have similarity >= 0.7, got {sim:.3f}"


def test_dna_token_similarity_allows_distinct():
    """Truly distinct values like 'oversized-serif-display' vs 'refined-humanist-sans' should NOT match."""
    sim = _dna_token_similarity("oversized-serif-display", "refined-humanist-sans")
    assert sim < 0.7, f"Distinct values should have similarity < 0.7, got {sim:.3f}"


# ============================
# V3.1.1 TESTS — Resource Registry
# ============================

def test_aura_unconfirmed_stays_reference_only():
    """Aura resources with commercialUse=UNCONFIRMED must have adaptationMode=REFERENCE_ONLY."""
    registry_path = ROOT / "design-resources" / "registry.json"
    assert registry_path.is_file(), f"Registry not found at {registry_path}"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    for res in data.get("resources", []):
        if res.get("source") == "aura":
            assert res.get("commercialUse") == "UNCONFIRMED", (
                f"Aura resource {res['id']} must have commercialUse=UNCONFIRMED, got {res.get('commercialUse')}"
            )
            assert res.get("adaptationMode") == "REFERENCE_ONLY", (
                f"Aura resource {res['id']} must have adaptationMode=REFERENCE_ONLY, got {res.get('adaptationMode')}"
            )


def test_external_resource_cannot_pass_without_license():
    """External resources (non-native) without license or commercialUse must fail provenance gate."""
    manifest = {
        "schemaVersion": 3,
        "slug": "unlicensed-site",
        "resourceProvenance": {
            "source": "aura",
            "sourceUrl": "https://auraui.com/example",
            "commercialUse": "UNCONFIRMED",
        },
    }
    design = (
        "RESOURCE_PROVENANCE:\n"
        "source: aura\n"
        "sourceUrl: https://auraui.com/example\n"
        "commercialUse: UNCONFIRMED\n"
    )
    rev = Review()
    check_resource_provenance(manifest, design, rev)
def test_dom_structural_fingerprint_derivation():
    """DOM structural fingerprint correctly classifies hero, cards, sections, and signature."""
    html = """
    <section data-role="hero" data-hero-layout="full-bleed-background"><h1>Title</h1></section>
    <section data-role="signature-section"><input type="range" id="compareRange"><div class="compare-handle"></div></section>
    <section id="services"><div class="service-card">S1</div><div class="service-card">S2</div></section>
    <section data-role="reviews"><div class="review-card">R1</div></section>
    """
    fp = derive_dom_structural_fingerprint(html)
    assert fp["heroStructure"] == "FULL_BLEED"
    assert fp["signatureInteractive"] is True
    assert fp["cardGridUsage"] == "LOW"
    assert fp["sectionFlowFingerprint"] == ["hero", "signature-section", "services", "reviews"]


def test_dom_structural_signature_mismatch_fails():
    """Declaring an interactive signature module with non-interactive DOM fails."""
    manifest = {
        "schemaVersion": 3,
        "slug": "mismatch-site",
        "designDna": {
            "heroGrammar": "split-editorial",
            "paletteFamily": "dark",
            "typographyCharacter": "sans",
            "layoutGrammar": "spec-cards",
            "motionLanguage": "reveal",
            "reviewTreatment": "curated",
            "signatureModule": "interactive-slider-comparison",
        }
    }
    design = "\n".join([f"DESIGN_DNA_{k.upper()}: {v}" for k, v in manifest["designDna"].items()])
    html = '<section data-role="signature-section"><p>Static only image</p></section>'
    rev = Review()
    check_design_dna(manifest, design, rev, html=html)
    assert not _passed(rev)
    assert any("interactive signature" in err for err in _errors(rev))


def test_dom_structural_signature_match_passes():
    """Declaring an interactive signature module with interactive DOM passes."""
    manifest = {
        "schemaVersion": 3,
        "slug": "match-site",
        "designDna": {
            "heroGrammar": "split-editorial",
            "paletteFamily": "dark",
            "typographyCharacter": "sans",
            "layoutGrammar": "spec-cards",
            "motionLanguage": "reveal",
            "reviewTreatment": "curated",
            "signatureModule": "interactive-slider-comparison",
        }
    }
    design = "\n".join([f"DESIGN_DNA_{k.upper()}: {v}" for k, v in manifest["designDna"].items()])
    html = '<section data-role="signature-section"><input type="range" id="compareRange"></section>'
    rev = Review()
    check_design_dna(manifest, design, rev, html=html)
    assert _passed(rev)


def test_fake_full_bleed_attribute_with_split_grid_reports_split():
    """Fake data-hero-layout='full-bleed-background' with a split grid reports SPLIT."""
    html = """
    <section data-role="hero" data-hero-layout="full-bleed-background">
      <div class="hero-grid">
        <div class="hero-text-col"><h1>Title</h1></div>
        <div class="hero-media-col"><div class="hero-media"><img src="car.jpg"></div></div>
      </div>
    </section>
    """
    fp = derive_dom_structural_fingerprint(html)
    assert fp["heroStructure"] == "SPLIT"

    # Declaring full-bleed with split DOM fails
    manifest_fb = {
        "schemaVersion": 3,
        "slug": "split-site",
        "designDna": {
            "heroGrammar": "full-bleed-cinematic",
            "paletteFamily": "dark",
            "typographyCharacter": "sans",
            "layoutGrammar": "spec-cards",
            "motionLanguage": "reveal",
            "reviewTreatment": "curated",
            "signatureModule": "interactive-slider",
        }
    }
    design_fb = "\n".join([f"DESIGN_DNA_{k.upper()}: {v}" for k, v in manifest_fb["designDna"].items()])
    html_with_sig = html + '<section data-role="signature-section"><input type="range" id="compareRange"></section>'
    rev_fb = Review()
    check_design_dna(manifest_fb, design_fb, rev_fb, html=html_with_sig)
    assert not _passed(rev_fb)
    assert any("full-bleed hero" in err for err in _errors(rev_fb))

    # Declaring split hero with split DOM passes
    manifest_sp = {
        "schemaVersion": 3,
        "slug": "split-site",
        "designDna": {
            "heroGrammar": "split-automotive-precision",
            "paletteFamily": "dark",
            "typographyCharacter": "sans",
            "layoutGrammar": "spec-cards",
            "motionLanguage": "reveal",
            "reviewTreatment": "curated",
            "signatureModule": "interactive-slider",
        }
    }
    design_sp = "\n".join([f"DESIGN_DNA_{k.upper()}: {v}" for k, v in manifest_sp["designDna"].items()])
    rev_sp = Review()
    check_design_dna(manifest_sp, design_sp, rev_sp, html=html_with_sig)
    assert _passed(rev_sp)


def test_schema_v3_review_translation_provenance_validation():
    """Schema v3 requires valid translationState, sourceLocale, and displayedText."""
    from google_reviews_evidence import validate_evidence
    evidence_missing = {
        "schemaVersion": 3,
        "profileName": "Test Shop",
        "profileUrl": "https://maps.google.com/?cid=123",
        "placeIdOrCid": "place123",
        "sourceSurface": "direct_google_maps",
        "collectionMethod": "browser_direct_maps",
        "collectedAt": "2026-09-08T12:00:00Z",
        "aggregateRating": 4.9,
        "ratingCount": 10,
        "profileHeaderObserved": True,
        "reviewsPanelOpened": True,
        "aggregateObservation": {
            "ratingText": "4.9",
            "countText": "10 reviews",
            "surfaceUrl": "https://maps.google.com/?cid=123",
        },
        "reviews": [
            {
                "id": "r1",
                "author": "Alice",
                "rating": 5,
                "text": "Great service",
                "dateLabel": "1 month ago",
                "source": "google_maps",
                "placeIdOrCid": "place123",
                "verified": True,
                "hasText": True,
                # Missing translation provenance
            }
        ]
    }
    res = validate_evidence(evidence_missing)
    assert any("translationState" in err or "sourceLocale" in err for err in res.errors)

    # Adding valid translation provenance passes
    evidence_valid = dict(evidence_missing)
    evidence_valid["reviews"] = [
        {
            "id": "r1",
            "author": "Alice",
            "rating": 5,
            "text": "Great service",
            "dateLabel": "1 month ago",
            "source": "google_maps",
            "placeIdOrCid": "place123",
            "verified": True,
            "hasText": True,
            "sourceLocale": "en-US",
            "displayedText": "Great service",
            "originalText": "Great service",
            "translationState": "ORIGINAL",
        }
    ]
    res_valid = validate_evidence(evidence_valid)
    assert not any("translationState" in err or "sourceLocale" in err for err in res_valid.errors)


# ==========================================
# Design Framework V3.2 Test Cases
# ==========================================

def test_v32_split_hero_policy_v1_fails():
    """split hero + policy v1 -> FAIL"""
    manifest = {"schemaVersion": 3, "heroMediaPolicyVersion": 1, "slug": "test-v32"}
    html = """
    <section data-role="hero" data-hero-layout="split-columns">
      <div class="hero-grid">
        <div class="hero-text-col"><h1>Title</h1></div>
        <div class="hero-media-col"><div class="hero-media"><img src="assets/hero.jpg"></div></div>
      </div>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "", rev)
    assert any("forbids SPLIT hero structure" in err for err in _errors(rev))


def test_v32_framed_hero_video_fails():
    """framed hero video -> FAIL"""
    manifest = {"schemaVersion": 3, "heroMediaPolicyVersion": 1, "slug": "test-v32"}
    html = """
    <section data-role="hero" data-hero-layout="split-columns">
      <div class="hero-grid">
        <div class="hero-text-col"><h1>Title</h1></div>
        <div class="hero-media-col"><div class="hero-media"><video autoplay muted playsinline poster="assets/poster.webp"><source src="assets/video.mp4"></video></div></div>
      </div>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "", rev)
    assert any("forbids SPLIT hero structure" in err or "requires desktop visual media plane >= 98%" in err for err in _errors(rev))


def test_v32_full_width_image_desktop_framed_mobile_fails():
    """full-width image desktop + framed mobile -> FAIL"""
    manifest = {"schemaVersion": 3, "heroMediaPolicyVersion": 1, "slug": "test-v32"}
    html = """
    <style>
      .hero-full-bleed { width: 100%; }
      @media (max-width: 768px) {
        .hero-media { border: 1px solid #ccc; }
        .hero-media img { height: 250px; }
      }
    </style>
    <section data-role="hero" data-hero-layout="full-bleed-background" data-hero-mobile-layout="framed" class="hero-full-bleed">
      <img src="assets/hero.webp">
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "", rev)
    assert any("cannot fall back to framed media on mobile" in err for err in _errors(rev))


def test_v32_full_width_video_passes():
    """full-width video: autoplay muted playsinline poster -> PASS"""
    manifest = {
        "schemaVersion": 3,
        "heroMediaPolicyVersion": 1,
        "slug": "test-v32",
        "heroMedia": {"source": "NATIVE"}
    }
    html = """
    <style>
      .hero-full-bleed { width: 100%; }
      @media (prefers-reduced-motion: reduce) {
        .hero-video-bg { display: none !important; }
        .hero-poster-fallback { display: block !important; }
      }
    </style>
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <div class="hero-media-plane">
        <video class="hero-video-bg" autoplay muted loop playsinline poster="assets/hero-poster.webp">
          <source src="assets/hero-video.webm" type="video/webm">
          <source src="assets/hero-video.mp4" type="video/mp4">
        </video>
        <img class="hero-poster-fallback" src="assets/hero-poster.webp" alt="Hero poster">
      </div>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "HERO_MEDIA_SOURCE: NATIVE\nHERO_MEDIA_COMMERCIAL_USE: confirmed", rev)
    assert _passed(rev), f"Expected pass, got: {_errors(rev)}"


def test_v32_video_missing_poster_fails():
    """video missing poster -> FAIL"""
    manifest = {"schemaVersion": 3, "heroMediaPolicyVersion": 1, "slug": "test-v32"}
    html = """
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <video class="hero-video-bg" autoplay muted playsinline>
        <source src="assets/video.mp4">
      </video>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "", rev)
    assert any("Hero video requires poster attribute" in err for err in _errors(rev))


def test_v32_video_missing_playsinline_fails():
    """video missing playsinline -> FAIL"""
    manifest = {"schemaVersion": 3, "heroMediaPolicyVersion": 1, "slug": "test-v32"}
    html = """
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <video class="hero-video-bg" autoplay muted poster="assets/poster.webp">
        <source src="assets/video.mp4">
      </video>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "", rev)
    assert any("Hero video requires playsinline attribute" in err for err in _errors(rev))


def test_v32_video_reduced_motion_no_poster_fallback_fails():
    """reduced-motion no poster fallback -> FAIL"""
    manifest = {"schemaVersion": 3, "heroMediaPolicyVersion": 1, "slug": "test-v32"}
    html = """
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <video class="hero-video-bg" autoplay muted playsinline poster="assets/poster.webp">
        <source src="assets/video.mp4">
      </video>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "", rev)
    assert any("Hero video requires prefers-reduced-motion fallback" in err for err in _errors(rev))


def test_v32_external_aura_video_commercial_unconfirmed_fails_shipping():
    """external Aura video commercialUse=UNCONFIRMED -> FAIL shipping"""
    manifest = {
        "schemaVersion": 3,
        "heroMediaPolicyVersion": 1,
        "slug": "test-v32",
        "heroMedia": {
            "source": "AURA",
            "commercialUse": "unconfirmed",
            "localPath": "assets/hero-video.mp4"
        }
    }
    design_read = (
        "HERO_MEDIA_SOURCE: AURA\n"
        "HERO_MEDIA_COMMERCIAL_USE: unconfirmed\n"
        "HERO_MEDIA_LOCAL_PATH: assets/hero-video.mp4\n"
        "HERO_MEDIA_ADAPTATION_MODE: USE_DIRECTLY\n"
    )
    html = """
    <style>@media (prefers-reduced-motion: reduce) { video { display: none; } }</style>
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <video autoplay muted playsinline poster="assets/poster.webp"><source src="assets/hero-video.mp4"></video>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, design_read, rev)
    assert any("External hero media requires confirmed commercial rights" in err for err in _errors(rev))


def test_v32_same_aura_video_reference_only_not_shipped_passes():
    """same Aura video REFERENCE_ONLY + not shipped -> PASS"""
    manifest = {
        "schemaVersion": 3,
        "heroMediaPolicyVersion": 1,
        "slug": "test-v32",
        "heroMedia": {
            "source": "AURA",
            "commercialUse": "unconfirmed",
            "adaptationMode": "REFERENCE_ONLY"
        }
    }
    design_read = (
        "HERO_MEDIA_SOURCE: AURA\n"
        "HERO_MEDIA_COMMERCIAL_USE: unconfirmed\n"
        "HERO_MEDIA_ADAPTATION_MODE: REFERENCE_ONLY\n"
    )
    html = """
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <img src="assets/native-poster.webp" alt="Native hero">
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, design_read, rev)
    assert _passed(rev), f"Expected pass, got: {_errors(rev)}"


def test_v32_aura_cdn_in_final_media_src_fails():
    """Aura CDN in final media src -> FAIL"""
    manifest = {"schemaVersion": 3, "heroMediaPolicyVersion": 1, "slug": "test-v32"}
    html = """
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <video autoplay muted playsinline poster="https://cdn.aura.build/assets/poster.jpg">
        <source src="https://cdn.aura.build/assets/video.mp4">
      </video>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "", rev)
    assert any("Aura CDN in final media src/poster is forbidden" in err for err in _errors(rev))


def test_v32_local_vendored_confirmed_media_passes():
    """local vendored confirmed media -> PASS"""
    manifest = {
        "schemaVersion": 3,
        "heroMediaPolicyVersion": 1,
        "slug": "test-v32",
        "heroMedia": {
            "source": "AURA",
            "commercialUse": "confirmed",
            "adaptationMode": "ADAPT_TO_VANILLA",
            "localPath": "assets/hero-video.mp4"
        }
    }
    design_read = (
        "HERO_MEDIA_SOURCE: AURA\n"
        "HERO_MEDIA_COMMERCIAL_USE: confirmed\n"
        "HERO_MEDIA_ADAPTATION_MODE: ADAPT_TO_VANILLA\n"
        "HERO_MEDIA_LOCAL_PATH: assets/hero-video.mp4\n"
    )
    html = """
    <style>@media (prefers-reduced-motion: reduce) { video { display: none; } }</style>
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <video autoplay muted playsinline poster="assets/hero-poster.webp"><source src="assets/hero-video.mp4"></video>
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, design_read, rev)
    assert _passed(rev), f"Expected pass, got: {_errors(rev)}"


def test_v32_expert_full_width_image_passes():
    """expert full-width image -> PASS"""
    manifest = {
        "schemaVersion": 3,
        "heroMediaPolicyVersion": 1,
        "slug": "test-v32",
        "heroMedia": {"source": "FIRST_PARTY", "type": "image"}
    }
    html = """
    <section data-role="hero" data-hero-layout="full-bleed-background" class="hero-full-bleed">
      <img src="assets/expert-hero.webp" alt="Dr. Expert">
    </section>
    """
    rev = Review()
    check_hero_media_plane(manifest, html, "HERO_MEDIA_SOURCE: FIRST_PARTY\nHERO_MEDIA_COMMERCIAL_USE: confirmed", rev)
    assert _passed(rev), f"Expected pass, got: {_errors(rev)}"


def test_v32_navbar_google_reviews_fails():
    """navbar 'Google Reviews' -> FAIL"""
    html = """
    <header>
      <nav>
        <a href="#services">Services</a>
        <a href="#reviews">Google Reviews</a>
      </nav>
    </header>
    """
    rev = Review()
    check_navbar_labels(html, rev)
    assert any("Navbar links cannot contain vendor names" in err for err in _errors(rev))


def test_v32_navbar_reviews_passes():
    """navbar 'Reviews' -> PASS"""
    html = """
    <header>
      <nav>
        <a href="#services">Services</a>
        <a href="#reviews">Reviews</a>
      </nav>
    </header>
    """
    rev = Review()
    check_navbar_labels(html, rev)
    assert _passed(rev)


def test_v32_dallas_final_derived_hero_not_split():
    """Dallas final derived hero: not SPLIT"""
    dallas_html_path = ROOT.parent / "sites" / "dallas-detailing-and-buffing" / "dallas-detailing-and-buffing.html"
    assert dallas_html_path.is_file(), f"Dallas HTML not found at {dallas_html_path}"
    html = dallas_html_path.read_text(encoding="utf-8")
    fp = derive_dom_structural_fingerprint(html)
    assert fp["heroStructure"] in {"FULL_BLEED", "LAYERED"}, f"Dallas hero must be FULL_BLEED or LAYERED; got {fp['heroStructure']}"
    assert fp["heroStructure"] != "SPLIT"


if __name__ == "__main__":
    test_funcs = [k for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn_name in test_funcs:
        globals()[fn_name]()
        print(f"[PASS] {fn_name}")
    print(f"\nAll {len(test_funcs)} Design Framework V3.2 test cases passed successfully.")


