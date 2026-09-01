#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression coverage for the autonomous site-review gate.

Each failure case mirrors a class of omission that previously escaped an agent's
self-reported Core QA pass: no gpt-taste evidence, missing hero imagery,
motionless page, map placeholder, omitted social affordance, navigable fake
social, missing floating WhatsApp, missing assistant collision hooks,
invalid hero templates, and omitted Google Reviews.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "prospector-de-sites"))
REVIEWER = ROOT / "prospector-de-sites" / "autonomous_site_review.py"

BASE_MANIFEST = {
    "schemaVersion": 1,
    "slug": "synthetic-review-fixture",
    "siteMode": "new_site_concept",
    "preview": True,
    "gptTaste": {"required": True, "skillSha256Required": True},
    "heroVisual": {
        "required": True,
        "kind": "contextual",
        "sourceType": "generated",
        "representsActualBusiness": False,
        "representsActualExpert": False,
        "illustrativeDisclosureRequired": True,
    },
    "googleReviews": {
        "checked": True,
        "state": "NO_USABLE_REVIEWS",
        "usableTextReviews": 0,
        "reviewSectionRequired": False,
        "reviewSectionRendered": False,
    },
    "motion": {
        "required": True,
        "minimumRevealGroups": 2,
        "headerScrollStateRequired": True,
        "floatingCtaSyncRequired": False,
    },
    "factualEvidence": {
        "verifiedServices": [
            {"claim": "Atendimento clínico geral", "verified": True, "source": "official_record"}
        ]
    },
    "address": {"verified": True, "public": True, "mapEmbedRequired": True},
    "whatsapp": {
        "verified": True,
        "number": "5511999999999",
        "floatingRequired": False,
        "contactActionRequired": True,
    },
    "instagram": {"state": "unverified", "mockAffordanceRequired": True},
    "assistant": {"present": True, "collisionCheckRequired": True},
    "qa": {"noJsRequired": True, "reducedMotionRequired": True},
}

PASS_HTML = r'''<!doctype html>
<html lang="pt-BR"><head>
<meta name="robots" content="noindex, nofollow">
<style>@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important}}</style>
</head><body>
<header data-role="site-header">Header</header>
<section data-role="hero"><h1>Site teste</h1><a href="https://wa.me/5511999999999">Agendar</a><img data-role="hero-image" data-image-context="illustrative" src="/hero.webp" alt="Imagem ilustrativa de consultório" width="1200" height="800"></section>
<section data-motion="reveal">A</section>
<section data-motion="reveal">B</section>
<span data-social="instagram" aria-disabled="true" tabindex="-1">Instagram</span>
<a href="https://wa.me/5511999999999">Contato WhatsApp</a>
<button data-role="assistant-launcher">Assistente</button>
<iframe src="https://maps.google.com/maps?q=Rua+1&z=16&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Mapa de localização"></iframe>
<script>
const obs = new IntersectionObserver(()=>{});
window.addEventListener('scroll',()=>document.querySelector('header').classList.toggle('scrolled',scrollY>10));
</script>
</body></html>'''


def make_design(skill_path: Path, *, include_read=True, sha_override: str | None = None, gr_state="NO_USABLE_REVIEWS", manifest=None) -> str:
    sha = sha_override or hashlib.sha256(skill_path.read_bytes()).hexdigest()
    lines = []
    if include_read:
        lines.append("GPT_TASTE_READ: PASS")

    verified_services = "Atendimento clínico geral"
    if manifest and "factualEvidence" in manifest:
        services = [s.get("claim") for s in manifest["factualEvidence"].get("verifiedServices", []) if s.get("claim")]
        if services:
            verified_services = ", ".join(services)

    lines.extend(
        [
            f"GPT_TASTE_PATH: {skill_path}",
            f"GPT_TASTE_SHA256: {sha}",
            "GOOGLE_REVIEWS_CHECK: PASS",
            f"GOOGLE_REVIEWS_STATE: {gr_state}",
            "SECONDARY_REVIEW_SEARCH: PASS",
            f"- **Factual Verified Services**: {verified_services}",
            "Design Variance: 5",
            "Motion: 3",
            "Density: 4",
        ]
    )
    return "\n".join(lines) + "\n"


def run_case(html: str = PASS_HTML, design_transform=None, manifest=None, custom_setup=None):
    manifest = manifest or BASE_MANIFEST
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        html_path = p / "index.html"
        design_path = p / "design-read.md"
        manifest_path = p / "review-manifest.json"
        skill_path = p / "gpt-taste-SKILL.md"
        skill_path.write_text("# Synthetic current gpt-taste skill\nrule: use deliberate composition\n", encoding="utf-8")
        
        gr_state = manifest.get("googleReviews", {}).get("state", "NO_USABLE_REVIEWS")
        design = make_design(skill_path, gr_state=gr_state, manifest=manifest)
        if design_transform:
            design = design_transform(design, skill_path)
            
        if custom_setup:
            custom_setup(p)

        html_path.write_text(html, encoding="utf-8")
        design_path.write_text(design, encoding="utf-8")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                str(REVIEWER),
                "--html",
                str(html_path),
                "--design-read",
                str(design_path),
                "--manifest",
                str(manifest_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(proc.stdout)
        return proc.returncode, payload


def failed_keys(payload):
    return {item["key"] for item in payload["checks"] if item["status"] == "FAIL"}


def test_clean_fixture_passes():
    code, payload = run_case()
    assert code == 0
    assert payload["autonomousReviewPass"] is True


def test_missing_gpt_taste_is_blocked():
    code, payload = run_case(design_transform=lambda d, _: d.replace("GPT_TASTE_READ: PASS\n", ""))
    assert code == 1
    assert "gpt_taste_read" in failed_keys(payload)


def test_stale_or_fake_gpt_taste_hash_is_blocked():
    code, payload = run_case(
        design_transform=lambda d, _: d.replace(
            next(line for line in d.splitlines() if line.startswith("GPT_TASTE_SHA256:")),
            "GPT_TASTE_SHA256: " + ("0" * 64),
        )
    )
    assert code == 1
    assert "gpt_taste_sha_matches" in failed_keys(payload)


def test_missing_hero_image_is_blocked():
    html = PASS_HTML.replace('<img data-role="hero-image" data-image-context="illustrative" src="/hero.webp" alt="Imagem ilustrativa de consultório" width="1200" height="800">', "")
    code, payload = run_case(html=html)
    assert code == 1
    assert "hero_image_present" in failed_keys(payload)


def test_hero_image_outside_hero_is_blocked():
    hero_image = '<img data-role="hero-image" data-image-context="illustrative" src="/hero.webp" alt="Imagem ilustrativa de consultório" width="1200" height="800">'
    html = PASS_HTML.replace(hero_image, "").replace("</body>", hero_image + "</body>")
    code, payload = run_case(html=html)
    assert code == 1
    assert "hero_image_present" in failed_keys(payload)


def test_generated_hero_cannot_claim_real_business_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"]["representsActualBusiness"] = True
    code, payload = run_case(manifest=manifest)
    assert code == 1
    assert "hero_image_no_false_business_representation" in failed_keys(payload)


def test_generated_hero_requires_illustrative_context_hook():
    html = PASS_HTML.replace(' data-image-context="illustrative"', "")
    code, payload = run_case(html=html)
    assert code == 1
    assert "hero_image_illustrative_context" in failed_keys(payload)


def test_lazy_loaded_hero_is_blocked():
    html = PASS_HTML.replace('src="/hero.webp"', 'src="/hero.webp" loading="lazy"')
    code, payload = run_case(html=html)
    assert code == 1
    assert "hero_image_not_lazy" in failed_keys(payload)


# --- Template Specific Regressions ---

def test_nonexistent_template_id_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "nonexistent-niche-template",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
    }
    code, payload = run_case(manifest=manifest)
    assert code == 1
    assert "hero_template_id_in_catalog" in failed_keys(payload)


def test_template_claims_actual_expert_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-female",
        "sourceType": "generated-template",
        "representsActualExpert": True,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
    }
    code, payload = run_case(manifest=manifest)
    assert code == 1
    assert "hero_template_no_actual_expert" in failed_keys(payload)


def test_template_claims_actual_business_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-male",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": True,
        "illustrativeDisclosureRequired": True,
    }
    code, payload = run_case(manifest=manifest)
    assert code == 1
    assert "hero_template_no_actual_business" in failed_keys(payload)


def test_template_missing_illustrative_context_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-female",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
    }
    html = PASS_HTML.replace(' data-image-context="illustrative"', "")
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "hero_template_illustrative_context" in failed_keys(payload)


def test_template_missing_file_on_disk_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "broken-template",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
    }
    def setup_broken_catalog(p: Path):
        tpl_dir = p / "templates" / "hero-expert"
        tpl_dir.mkdir(parents=True)
        cat = {
            "schemaVersion": 1,
            "templates": [
                {
                    "id": "broken-template",
                    "desktop": "missing/desktop.webp",
                    "mobile": "missing/mobile.webp"
                }
            ]
        }
        (tpl_dir / "manifest.json").write_text(json.dumps(cat), encoding="utf-8")
        
    code, payload = run_case(manifest=manifest, custom_setup=setup_broken_catalog)
    assert code == 1
    assert "hero_template_desktop_file_exists" in failed_keys(payload)


def test_valid_dentistry_female_template_passes():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-female",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
        "desktopAssetRequired": True,
        "mobileAssetRequired": True,
    }
    html = PASS_HTML.replace(
        '<section data-role="hero">',
        '<section data-role="hero" data-hero-layout="full-bleed-background" data-hero-frame-policy="preserve-complete-frame"><picture><source media="(max-width: 767px)" srcset="assets/mobile.webp" width="941" height="1672"><img data-role="hero-image" data-image-context="illustrative" src="/hero.webp" alt="Consultorio" width="1983" height="793">',
    ).replace('</section>', '</picture></section>', 1)
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 0
    assert payload["autonomousReviewPass"] is True


def test_valid_dentistry_male_template_passes():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-male",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
        "desktopAssetRequired": True,
        "mobileAssetRequired": True,
    }
    html = PASS_HTML.replace(
        '<section data-role="hero">',
        '<section data-role="hero" data-hero-layout="full-bleed-background" data-hero-frame-policy="preserve-complete-frame"><picture><source media="(max-width: 767px)" srcset="assets/mobile.webp" width="941" height="1672"><img data-role="hero-image" data-image-context="illustrative" src="/hero.webp" alt="Consultorio" width="1983" height="793">',
    ).replace('</section>', '</picture></section>', 1)
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 0
    assert payload["autonomousReviewPass"] is True


# --- Google Reviews Regressions ---

def test_google_reviews_profile_conflict_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "state": "PROFILE_CONFLICT",
        "reviewSectionRequired": False,
        "reviewSectionRendered": False,
    }
    code, payload = run_case(manifest=manifest)
    assert code == 1
    assert "google_reviews_no_conflict" in failed_keys(payload)


def test_google_reviews_verified_strong_without_rendered_section_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "state": "VERIFIED_STRONG",
        "reviewSectionRequired": True,
        "reviewSectionRendered": False,
    }
    code, payload = run_case(manifest=manifest)
    assert code == 1
    assert "google_reviews_section_rendered" in failed_keys(payload)


def test_google_reviews_verified_strong_with_rendered_section_passes():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "state": "VERIFIED_STRONG",
        "usableTextReviews": 3,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
        "reviews": [
            {"id": "gr-1", "author": "Carlos", "text": "Excelente atendimento", "verified": True},
            {"id": "gr-2", "author": "Ana", "text": "Muito atenciosa e pontual", "verified": True},
            {"id": "gr-3", "author": "Bruno", "text": "Ambiente limpo e seguro", "verified": True},
        ],
    }
    html = PASS_HTML.replace(
        '</body>',
        '''<section data-role="reviews" data-review-mode="text-reviews">
          <div data-role="review-card" data-review-evidence-id="gr-1"><p>Excelente atendimento</p><span>Carlos</span></div>
          <div data-role="review-card" data-review-evidence-id="gr-2"><p>Muito atenciosa e pontual</p><span>Ana</span></div>
          <div data-role="review-card" data-review-evidence-id="gr-3"><p>Ambiente limpo e seguro</p><span>Bruno</span></div>
        </section></body>'''
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 0
    assert payload["autonomousReviewPass"] is True


def test_google_reviews_aggregate_only_with_rating_count_1_without_section_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_AGGREGATE_ONLY",
        "aggregateRating": 5.0,
        "ratingCount": 1,
        "usableTextReviews": 0,
        "reviewSectionRequired": True,
        "reviewSectionRendered": False,
    }
    code, payload = run_case(manifest=manifest)
    assert code == 1
    assert "google_reviews_section_rendered" in failed_keys(payload)


def test_google_reviews_aggregate_only_with_rating_count_1_with_section_passes():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_AGGREGATE_ONLY",
        "aggregateRating": 5.0,
        "ratingCount": 1,
        "usableTextReviews": 0,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
    }
    html = PASS_HTML.replace('</body>', '<section data-role="reviews" data-review-mode="aggregate-only" data-review-presentation="compact-summary" data-review-rating="5.0" data-review-count="1"><h2>Avaliações</h2><div data-role="reviews-summary">5,0 de 5 | 1 avaliação</div></section></body>')
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 0
    assert payload["autonomousReviewPass"] is True


def test_google_reviews_zero_ratings_and_zero_reviews_omission_passes():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "verifiedGoogleProfile": True,
        "state": "NO_USABLE_REVIEWS",
        "aggregateRating": 0.0,
        "ratingCount": 0,
        "usableTextReviews": 0,
        "reviewSectionRequired": False,
        "reviewSectionRendered": False,
    }
    code, payload = run_case(manifest=manifest)
    assert code == 0
    assert payload["autonomousReviewPass"] is True


# --- General Regressions ---

def test_motionless_page_is_blocked():
    html = PASS_HTML.replace("const obs = new IntersectionObserver(()=>{});", "")
    html = html.replace("window.addEventListener('scroll',()=>document.querySelector('header').classList.toggle('scrolled',scrollY>10));", "")
    code, payload = run_case(html=html)
    assert code == 1
    assert "motion_runtime" in failed_keys(payload)


def test_map_placeholder_without_iframe_is_blocked():
    html = PASS_HTML.replace(
        '<iframe src="https://maps.google.com/maps?q=Rua+1&z=16&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Mapa de localização"></iframe>',
        '<div class="map-placeholder">Mapa</div>',
    )
    code, payload = run_case(html=html)
    assert code == 1
    assert "map_embed" in failed_keys(payload)


def test_missing_instagram_mock_is_blocked():
    html = PASS_HTML.replace('<span data-social="instagram" aria-disabled="true" tabindex="-1">Instagram</span>', "")
    code, payload = run_case(html=html)
    assert code == 1
    assert "instagram_mock_present" in failed_keys(payload)


def test_disabled_instagram_with_javascript_href_is_blocked():
    html = PASS_HTML.replace(
        '<span data-social="instagram" aria-disabled="true" tabindex="-1">Instagram</span>',
        '<a data-social="instagram" aria-disabled="true" tabindex="-1" href="javascript:void(0)">Instagram</a>',
    )
    code, payload = run_case(html=html)
    assert code == 1
    assert "instagram_mock_disabled_no_navigation" in failed_keys(payload)


def test_fake_instagram_destination_is_blocked():
    html = PASS_HTML.replace(
        '<span data-social="instagram" aria-disabled="true" tabindex="-1">Instagram</span>',
        '<a data-social="instagram" aria-disabled="true" href="https://instagram.com/fake-handle">Instagram</a>',
    )
    code, payload = run_case(html=html)
    assert code == 1
    assert "instagram_mock_disabled_no_navigation" in failed_keys(payload)


def test_missing_floating_whatsapp_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["assistant"]["present"] = False
    manifest["whatsapp"]["floatingRequired"] = True
    html = PASS_HTML.replace('<button data-role="assistant-launcher">Assistente</button>', '')
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "floating_whatsapp_hook" in failed_keys(payload)


def test_assistant_without_collision_hook_is_blocked():
    html = PASS_HTML.replace('data-role="assistant-launcher"', 'class="assistant-launcher"')
    code, payload = run_case(html=html)
    assert code == 1
    assert "assistant_launcher_hook" in failed_keys(payload)


def test_wrong_whatsapp_number_is_blocked():
    html = PASS_HTML.replace("5511999999999", "5511888888888")
    code, payload = run_case(html=html)
    assert code == 1
    assert "whatsapp_verified_destination" in failed_keys(payload)


def test_missing_reduced_motion_is_blocked():
    html = PASS_HTML.replace("@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important}}", "")
    code, payload = run_case(html=html)
    assert code == 1
    assert "reduced_motion_css" in failed_keys(payload)


def test_hero_template_in_card_without_full_bleed_layout_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-female",
        "sourceType": "generated-template",
        "representsActualBusiness": False,
        "representsActualExpert": False,
        "illustrativeDisclosureRequired": True,
    }
    # HTML uses right-side card without data-hero-layout="full-bleed-background"
    html = PASS_HTML.replace(
        '<section data-role="hero">',
        '<section data-role="hero"><div class="hero-grid"><div class="hero-card"><img data-role="hero-image" data-image-context="illustrative" src="assets/hero.webp" alt="Consultorio"></div></div>',
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "hero_template_layout_mode" in failed_keys(payload)


def test_google_reviews_aggregate_only_with_fabricated_quotes_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_AGGREGATE_ONLY",
        "aggregateRating": 5.0,
        "ratingCount": 1,
        "usableTextReviews": 0,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
    }
    # Section has fabricated quotation text
    html = PASS_HTML.replace(
        '</body>',
        '<section data-role="reviews" data-review-mode="aggregate-only" data-review-rating="5.0" data-review-count="1"><div class="aggregate">5,0 de 5</div><p>“Atendimento maravilhoso, a melhor dentista de Rio Claro!”</p></section></body>',
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "google_reviews_no_fabricated_text" in failed_keys(payload)


def test_google_reviews_aggregate_only_with_fake_cards_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_AGGREGATE_ONLY",
        "aggregateRating": 5.0,
        "ratingCount": 1,
        "usableTextReviews": 0,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
    }
    html = PASS_HTML.replace(
        '</body>',
        '<section data-role="reviews" data-review-mode="aggregate-only" data-review-rating="5.0" data-review-count="1"><div data-role="review-card">Fake Review</div></section></body>',
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "google_reviews_no_fake_cards" in failed_keys(payload)


def test_placeholder_hero_missing_frame_policy_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-female",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
    }
    # Has layout mode but missing data-hero-frame-policy="preserve-complete-frame"
    html = PASS_HTML.replace(
        '<section data-role="hero">',
        '<section data-role="hero" data-hero-layout="full-bleed-background"><picture><source media="(max-width: 767px)" srcset="assets/mobile.webp" width="941" height="1672"><img data-role="hero-image" data-image-context="illustrative" src="/hero.webp" alt="Consultorio" width="1983" height="793">',
    ).replace('</section>', '</picture></section>', 1)
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "hero_template_frame_policy" in failed_keys(payload)


def test_placeholder_hero_wrong_declared_dimensions_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-female",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
    }
    # Has wrong dimensions (e.g. 1920x1080 instead of 1983x793)
    html = PASS_HTML.replace(
        '<section data-role="hero">',
        '<section data-role="hero" data-hero-layout="full-bleed-background" data-hero-frame-policy="preserve-complete-frame"><picture><source media="(max-width: 767px)" srcset="assets/mobile.webp" width="941" height="1672"><img data-role="hero-image" data-image-context="illustrative" src="/hero.webp" alt="Consultorio" width="1920" height="1080">',
    ).replace('</section>', '</picture></section>', 1)
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "hero_template_declared_dimensions" in failed_keys(payload)


def test_placeholder_hero_with_cover_css_is_blocked():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["heroVisual"] = {
        "required": True,
        "kind": "expert-placeholder",
        "templateId": "dentistry-female",
        "sourceType": "generated-template",
        "representsActualExpert": False,
        "representsActualBusiness": False,
        "illustrativeDisclosureRequired": True,
    }
    # HTML includes object-fit: cover for hero image
    html = PASS_HTML.replace(
        '</style>',
        '.hero-bg-img { object-fit: cover; }</style>',
    ).replace(
        '<section data-role="hero">',
        '<section data-role="hero" data-hero-layout="full-bleed-background" data-hero-frame-policy="preserve-complete-frame"><picture><source media="(max-width: 767px)" srcset="assets/mobile.webp" width="941" height="1672"><img data-role="hero-image" data-image-context="illustrative" src="/hero.webp" alt="Consultorio" width="1983" height="793" class="hero-bg-img">',
    ).replace('</section>', '</picture></section>', 1)
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "hero_template_no_cover" in failed_keys(payload)


def test_aggregate_only_reviews_must_be_compact():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_AGGREGATE_ONLY",
        "aggregateRating": 5.0,
        "ratingCount": 1,
        "usableTextReviews": 0,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
    }
    # Section missing compact-summary presentation
    html = PASS_HTML.replace(
        '</body>',
        '<section data-role="reviews" data-review-mode="aggregate-only" data-review-rating="5.0" data-review-count="1"><div class="reviews-aggregate-card">5,0 de 5</div></section></body>',
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "google_reviews_presentation_compact" in failed_keys(payload)


def test_factual_traceability_generic_allowlist_blocks_unsupported_service():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["factualEvidence"] = {
        "verifiedServices": [
            {"claim": "Avaliação ortodôntica", "verified": True, "source": "official_record"}
        ]
    }
    # design-read claims a completely new unsupported service (e.g. Implantes dentários or Sedação consciente)
    code, payload = run_case(
        design_transform=lambda d, s: d + "\n- **Factual Verified Services**: Avaliação ortodôntica, Implantes dentários, Sedação consciente\n",
        manifest=manifest,
    )
    assert code == 1
    assert "factual_traceability_verified_services" in failed_keys(payload)


def test_direct_maps_count_overrides_stale_cached_count():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "sourceSurface": "direct_google_maps",
        "placeId": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
        "cid": "8080486820542360312",
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_STRONG",
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "usableTextReviews": 0,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
    }
    # HTML erroneously still has old count 1
    html = PASS_HTML.replace(
        '</body>',
        '<section data-role="reviews" data-review-mode="aggregate-only" data-review-presentation="compact-summary" data-review-rating="5.0" data-review-count="1"><div data-role="reviews-summary">5,0 · 1 avaliação</div></section></body>',
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "google_reviews_count_hook" in failed_keys(payload)


def test_banned_stale_count_text_fails_when_count_differs():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "sourceSurface": "direct_google_maps",
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_STRONG",
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "usableTextReviews": 0,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
    }
    # HTML has data-review-count="12" but text still says "1 avaliação"
    html = PASS_HTML.replace(
        '</body>',
        '<section data-role="reviews" data-review-mode="aggregate-only" data-review-presentation="compact-summary" data-review-rating="5.0" data-review-count="12"><div data-role="reviews-summary">5,0 · 1 avaliação</div></section></body>',
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 1
    assert "google_reviews_no_stale_count_text" in failed_keys(payload)


def test_case_a_incomplete_traversal_blocks():
    from google_reviews_evidence import validate_evidence, COLLECTION_INCOMPLETE
    data = {
        "profileName": "Odontologia Dra. Aline Iost",
        "profileUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
        "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
        "sourceSurface": "direct_google_maps",
        "collectionMethod": "playwright_direct_maps",
        "profileHeaderObserved": True,
        "reviewsPanelOpened": True,
        "reviewsPanelFullyTraversed": False,
        "textReviewCollectionAttempted": True,
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "observedRatingEntries": 5,
        "observedTextReviewEntries": 1,
        "capturedTextReviewCount": 1,
        "aggregateObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "ratingText": "5,0",
            "countText": "12 avaliações"
        },
        "reviewsPanelObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "countText": "12 avaliações"
        },
        "collectedAt": "2026-08-31T20:55:00Z",
        "reviews": [
            {
                "author": "Arthur Di Donato",
                "rating": 5,
                "dateLabel": "um ano atrás",
                "text": "Gostaria de expressar minha profunda gratidão.",
                "source": "google_maps",
                "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A"
            }
        ]
    }
    res = validate_evidence(data)
    assert res.status == COLLECTION_INCOMPLETE
    assert not res.pass_for_publish


def test_case_b_aggregate_only_complete_traversal_passes():
    from google_reviews_evidence import validate_evidence, VERIFIED_AGGREGATE_ONLY
    data = {
        "profileName": "Odontologia Dra. Aline Iost",
        "profileUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
        "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
        "sourceSurface": "direct_google_maps",
        "collectionMethod": "playwright_direct_maps",
        "profileHeaderObserved": True,
        "reviewsPanelOpened": True,
        "reviewsPanelFullyTraversed": True,
        "textReviewCollectionAttempted": True,
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "observedRatingEntries": 12,
        "observedTextReviewEntries": 0,
        "capturedTextReviewCount": 0,
        "aggregateObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "ratingText": "5,0",
            "countText": "12 avaliações"
        },
        "reviewsPanelObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "countText": "12 avaliações"
        },
        "collectedAt": "2026-08-31T20:55:00Z",
        "reviews": []
    }
    res = validate_evidence(data)
    assert res.status == VERIFIED_AGGREGATE_ONLY
    assert res.pass_for_publish


def test_case_c_verified_text_limited_passes():
    from google_reviews_evidence import validate_evidence, VERIFIED_TEXT_LIMITED
    data = {
        "profileName": "Odontologia Dra. Aline Iost",
        "profileUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
        "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
        "sourceSurface": "direct_google_maps",
        "collectionMethod": "playwright_direct_maps",
        "profileHeaderObserved": True,
        "reviewsPanelOpened": True,
        "reviewsPanelFullyTraversed": True,
        "textReviewCollectionAttempted": True,
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "observedRatingEntries": 12,
        "observedTextReviewEntries": 2,
        "capturedTextReviewCount": 2,
        "aggregateObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "ratingText": "5,0",
            "countText": "12 avaliações"
        },
        "reviewsPanelObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "countText": "12 avaliações"
        },
        "collectedAt": "2026-08-31T20:55:00Z",
        "reviews": [
            {
                "author": "Arthur Di Donato",
                "rating": 5,
                "dateLabel": "um ano atrás",
                "text": "Gostaria de expressar minha profunda gratidão pelo excelente trabalho.",
                "source": "google_maps",
                "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A"
            },
            {
                "author": "João Victor Velasco",
                "rating": 5,
                "dateLabel": "5 anos atrás",
                "text": "A Dra. Aline me atendeu com muita competência e profissionalismo.",
                "source": "google_maps",
                "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A"
            }
        ]
    }
    res = validate_evidence(data)
    assert res.status == VERIFIED_TEXT_LIMITED
    assert res.pass_for_publish
    assert res.verified_review_count == 2


def test_case_d_verified_strong_passes():
    from google_reviews_evidence import validate_evidence, VERIFIED_STRONG
    data = {
        "profileName": "Odontologia Dra. Aline Iost",
        "profileUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
        "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
        "sourceSurface": "direct_google_maps",
        "collectionMethod": "playwright_direct_maps",
        "profileHeaderObserved": True,
        "reviewsPanelOpened": True,
        "reviewsPanelFullyTraversed": True,
        "textReviewCollectionAttempted": True,
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "observedRatingEntries": 12,
        "observedTextReviewEntries": 5,
        "capturedTextReviewCount": 5,
        "aggregateObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "ratingText": "5,0",
            "countText": "12 avaliações"
        },
        "reviewsPanelObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "countText": "12 avaliações"
        },
        "collectedAt": "2026-08-31T20:55:00Z",
        "reviews": [
            {"author": f"User {i}", "rating": 5, "dateLabel": "1 ano atrás", "text": f"Review {i} text here", "source": "google_maps", "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A"}
            for i in range(1, 6)
        ]
    }
    res = validate_evidence(data)
    assert res.status == VERIFIED_STRONG
    assert res.pass_for_publish
    assert res.verified_review_count == 5


def test_case_e_uncaptured_text_reviews_blocks():
    from google_reviews_evidence import validate_evidence, COLLECTION_INCOMPLETE
    data = {
        "profileName": "Odontologia Dra. Aline Iost",
        "profileUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
        "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
        "sourceSurface": "direct_google_maps",
        "collectionMethod": "playwright_direct_maps",
        "profileHeaderObserved": True,
        "reviewsPanelOpened": True,
        "reviewsPanelFullyTraversed": True,
        "textReviewCollectionAttempted": True,
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "observedRatingEntries": 12,
        "observedTextReviewEntries": 5,
        "capturedTextReviewCount": 3,
        "aggregateObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "ratingText": "5,0",
            "countText": "12 avaliações"
        },
        "reviewsPanelObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "countText": "12 avaliações"
        },
        "collectedAt": "2026-08-31T20:55:00Z",
        "reviews": [
            {"author": f"User {i}", "rating": 5, "dateLabel": "1 ano atrás", "text": f"Review {i} text here", "source": "google_maps", "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A"}
            for i in range(1, 4)
        ]
    }
    res = validate_evidence(data)
    assert res.status == COLLECTION_INCOMPLETE
    assert not res.pass_for_publish


def test_case_f_secondary_reviews_do_not_upgrade_google_state():
    from google_reviews_evidence import validate_evidence, VERIFIED_AGGREGATE_ONLY
    data = {
        "profileName": "Odontologia Dra. Aline Iost",
        "profileUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
        "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
        "sourceSurface": "direct_google_maps",
        "collectionMethod": "playwright_direct_maps",
        "profileHeaderObserved": True,
        "reviewsPanelOpened": True,
        "reviewsPanelFullyTraversed": True,
        "textReviewCollectionAttempted": True,
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "observedRatingEntries": 12,
        "observedTextReviewEntries": 0,
        "capturedTextReviewCount": 0,
        "aggregateObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "ratingText": "5,0",
            "countText": "12 avaliações"
        },
        "reviewsPanelObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "countText": "12 avaliações"
        },
        "collectedAt": "2026-08-31T20:55:00Z",
        "reviews": []
    }
    res = validate_evidence(data)
    assert res.status == VERIFIED_AGGREGATE_ONLY
    assert res.pass_for_publish


def test_iost_verified_text_limited_two_real_cards_passes():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "sourceSurface": "direct_google_maps",
        "collectionMethod": "playwright_direct_maps",
        "placeId": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
        "cid": "8080486820542360312",
        "profileName": "Odontologia Dra. Aline Iost",
        "profileUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_TEXT_LIMITED",
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "observedRatingEntries": 12,
        "observedTextReviewEntries": 2,
        "capturedTextReviewCount": 2,
        "starOnlyRatingCount": 10,
        "profileHeaderObserved": True,
        "reviewsPanelOpened": True,
        "reviewsPanelFullyTraversed": True,
        "textReviewCollectionAttempted": True,
        "aggregateObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "ratingText": "5,0",
            "countText": "12 avaliações"
        },
        "reviewsPanelObservation": {
            "surfaceUrl": "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu",
            "countText": "12 avaliações"
        },
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
        "reviews": [
            {
                "id": "google-review-arthur-di-donato",
                "author": "Arthur Di Donato",
                "rating": 5,
                "dateLabel": "um ano atrás",
                "hasText": True,
                "text": "Gostaria de expressar minha profunda gratidão pelo excelente trabalho realizado pela Dra. Aline. Desde a minha primeira consulta, fui recebido com profissionalismo e atenção. A Dra. explicou cada procedimento de forma clara, o que me deixou muito seguro durante todo o processo.",
                "source": "google_maps",
                "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
                "verified": True
            },
            {
                "id": "google-review-joao-victor-velasco",
                "author": "João Victor Velasco",
                "rating": 5,
                "dateLabel": "5 anos atrás",
                "hasText": True,
                "text": "A Dra. Aline me atendeu com muita competência e profissionalismo, seguindo rigidamente todos os protocolos de higiene e prevenção por conta da pandemia. Adorei o resultado do tratamento que fiz com ela. Excelente profissional!",
                "source": "google_maps",
                "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
                "verified": True
            }
        ]
    }
    # HTML with 2 real review cards
    html = PASS_HTML.replace(
        '</body>',
        '''<section data-role="reviews" data-review-mode="verified-text" data-review-rating="5.0" data-review-count="12">
          <div class="container">
            <article data-role="review-card" data-review-evidence-id="google-review-arthur-di-donato">
              <p>Gostaria de expressar minha profunda gratidão pelo excelente trabalho realizado pela Dra. Aline. Desde a minha primeira consulta, fui recebido com profissionalismo e atenção. A Dra. explicou cada procedimento de forma clara, o que me deixou muito seguro durante todo o processo.</p>
              <span>Arthur Di Donato</span>
            </article>
            <article data-role="review-card" data-review-evidence-id="google-review-joao-victor-velasco">
              <p>A Dra. Aline me atendeu com muita competência e profissionalismo, seguindo rigidamente todos os protocolos de higiene e prevenção por conta da pandemia. Adorei o resultado do tratamento que fiz com ela. Excelente profissional!</p>
              <span>João Victor Velasco</span>
            </article>
          </div>
        </section></body>''',
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 0, f"Expected PASS for IOST VERIFIED_TEXT_LIMITED: {payload}"


def test_observed_entries_fingerprint_mismatch_fails():
    from google_reviews_evidence import validate_evidence
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"]["sourceSurface"] = "direct_google_maps"
    manifest["googleReviews"]["collectionMethod"] = "playwright_direct_maps"
    manifest["googleReviews"]["profileHeaderObserved"] = True
    manifest["googleReviews"]["reviewsPanelOpened"] = True
    manifest["googleReviews"]["reviewsPanelFullyTraversed"] = True
    manifest["googleReviews"]["textReviewCollectionAttempted"] = True
    manifest["googleReviews"]["profileName"] = "Odontologia Dra. Aline Iost"
    manifest["googleReviews"]["profileUrl"] = "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu"
    manifest["googleReviews"]["placeIdOrCid"] = "ChIJ5-3JUhHbx5QR-KoFM6msI3A"
    manifest["googleReviews"]["collectedAt"] = "2026-08-31T20:55:00Z"
    manifest["googleReviews"]["aggregateRating"] = 5.0
    manifest["googleReviews"]["ratingCount"] = 1
    manifest["googleReviews"]["observedRatingEntries"] = 1
    manifest["googleReviews"]["observedTextReviewEntries"] = 1
    manifest["googleReviews"]["capturedTextReviewCount"] = 1
    manifest["googleReviews"]["starOnlyRatingCount"] = 0
    manifest["googleReviews"]["observedEntries"] = [
        {
            "fingerprint": "bad_fingerprint_hash",
            "author": "Arthur Di Donato",
            "rating": 5,
            "dateLabel": "um ano atrás",
            "hasText": True,
            "textEvidenceId": "google-review-arthur-di-donato"
        }
    ]
    manifest["googleReviews"]["reviews"] = [
        {
            "id": "google-review-arthur-di-donato",
            "author": "Arthur Di Donato",
            "rating": 5,
            "dateLabel": "um ano atrás",
            "hasText": True,
            "text": "Excelente atendimento",
            "source": "google_maps",
            "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
            "verified": True
        }
    ]
    res = validate_evidence(manifest["googleReviews"])
    assert not res.pass_for_publish
    assert any("fingerprint mismatch" in e for e in res.errors)


def test_observed_entries_count_mismatch_fails():
    from google_reviews_evidence import validate_evidence
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"]["sourceSurface"] = "direct_google_maps"
    manifest["googleReviews"]["collectionMethod"] = "playwright_direct_maps"
    manifest["googleReviews"]["profileHeaderObserved"] = True
    manifest["googleReviews"]["reviewsPanelOpened"] = True
    manifest["googleReviews"]["reviewsPanelFullyTraversed"] = True
    manifest["googleReviews"]["textReviewCollectionAttempted"] = True
    manifest["googleReviews"]["profileName"] = "Odontologia Dra. Aline Iost"
    manifest["googleReviews"]["profileUrl"] = "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu"
    manifest["googleReviews"]["placeIdOrCid"] = "ChIJ5-3JUhHbx5QR-KoFM6msI3A"
    manifest["googleReviews"]["collectedAt"] = "2026-08-31T20:55:00Z"
    manifest["googleReviews"]["aggregateRating"] = 5.0
    manifest["googleReviews"]["ratingCount"] = 12
    manifest["googleReviews"]["observedRatingEntries"] = 12
    manifest["googleReviews"]["observedEntries"] = []
    res = validate_evidence(manifest["googleReviews"])
    assert not res.pass_for_publish
    assert any("observedRatingEntries" in e for e in res.errors)


def test_reviews_carousel_slide_count_mismatch_fails():
    with open("sites/iost-ortodontia-aline-iost-rio-claro/review-manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open("sites/iost-ortodontia-aline-iost-rio-claro/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Tamper HTML to only have 1 slide instead of 12
    articles = re.findall(r"<article[^>]*data-role=[\"']review-carousel-item[\"'][^>]*>.*?</article>", html, re.DOTALL)
    html_single_slide = html
    for art in articles[1:]:
        html_single_slide = html_single_slide.replace(art, "")

    def setup_template(p: Path):
        tpl_dir = p / "assets" / "templates"
        tpl_dir.mkdir(parents=True, exist_ok=True)
        (tpl_dir / "dentistry-female.webp").write_bytes(b"RIFF....WEBPVP8 ...")
    def iost_design(design_text, skill_path):
        lines = [
            design_text.strip(),
            "- **Factual Verified Services**: Ortodontia Preventiva e Interceptativa, Aparelhos Autoligados, Alinhadores Invisíveis, Ortodontia para Adultos e Crianças",
        ]
        return "\n".join(lines) + "\n"

    code, payload = run_case(html=html_single_slide, manifest=manifest, design_transform=iost_design, custom_setup=setup_template)
    assert code == 1
    assert any(c.get("key") == "carousel_items_count" and c.get("status") == "FAIL" for c in payload.get("checks", []))


def test_reviews_carousel_12_items_passes():
    with open("sites/iost-ortodontia-aline-iost-rio-claro/review-manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open("sites/iost-ortodontia-aline-iost-rio-claro/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    def iost_design(design_text, skill_path):
        lines = [
            design_text.strip(),
            "- **Factual Verified Services**: Avaliação ortodôntica, manutenção de aparelho fixo, clareamento dental, procedimentos clínicos gerais",
        ]
        return "\n".join(lines) + "\n"

    def setup_template(p: Path):
        tpl_dir = p / "assets" / "templates"
        tpl_dir.mkdir(parents=True, exist_ok=True)
        (tpl_dir / "dentistry-female.webp").write_bytes(b"RIFF....WEBPVP8 ...")
        (tpl_dir / "dentistry-female-mobile.webp").write_bytes(b"RIFF....WEBPVP8 ...")

    code, payload = run_case(html=html, manifest=manifest, design_transform=iost_design, custom_setup=setup_template)
    assert code == 0, f"Expected PASS for full 12-item carousel: {payload}"


def test_synthetic_review_author_in_manifest_fails():
    from google_reviews_evidence import validate_evidence
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"]["sourceSurface"] = "direct_google_maps"
    manifest["googleReviews"]["collectionMethod"] = "playwright_direct_maps"
    manifest["googleReviews"]["profileHeaderObserved"] = True
    manifest["googleReviews"]["reviewsPanelOpened"] = True
    manifest["googleReviews"]["reviewsPanelFullyTraversed"] = True
    manifest["googleReviews"]["textReviewCollectionAttempted"] = True
    manifest["googleReviews"]["profileName"] = "Odontologia Dra. Aline Iost"
    manifest["googleReviews"]["profileUrl"] = "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu"
    manifest["googleReviews"]["placeIdOrCid"] = "ChIJ5-3JUhHbx5QR-KoFM6msI3A"
    manifest["googleReviews"]["collectedAt"] = "2026-08-31T20:55:00Z"
    manifest["googleReviews"]["aggregateRating"] = 5.0
    manifest["googleReviews"]["ratingCount"] = 1
    manifest["googleReviews"]["observedRatingEntries"] = 1
    manifest["googleReviews"]["observedTextReviewEntries"] = 1
    manifest["googleReviews"]["capturedTextReviewCount"] = 1
    manifest["googleReviews"]["starOnlyRatingCount"] = 0
    manifest["googleReviews"]["observedEntries"] = [
        {
            "fingerprint": "123",
            "author": "Paciente Verificado #1",
            "rating": 5,
            "dateLabel": "2 anos atrás",
            "hasText": True,
            "textEvidenceId": "g1"
        }
    ]
    manifest["googleReviews"]["reviews"] = [
        {
            "id": "g1",
            "author": "Paciente Verificado #1",
            "rating": 5,
            "dateLabel": "2 anos atrás",
            "hasText": True,
            "text": "Excelente",
            "source": "google_maps",
            "placeIdOrCid": "ChIJ5-3JUhHbx5QR-KoFM6msI3A",
            "verified": True
        }
    ]
    res = validate_evidence(manifest["googleReviews"])
    assert not res.pass_for_publish
    assert any("synthetic author placeholder" in e for e in res.errors)


def test_star_only_without_unique_source_witness_cannot_be_individual_carousel_item():
    from google_reviews_evidence import compute_entry_fingerprint, validate_evidence
    # Two entries without nativeReviewId or sourceWitness have identical raw fingerprints (no entryIndex fake differentiator)
    fp1 = compute_entry_fingerprint("ChIJ5-3JUhHbx5QR-KoFM6msI3A", None, 5, None, "", None)
    fp2 = compute_entry_fingerprint("ChIJ5-3JUhHbx5QR-KoFM6msI3A", None, 5, None, "", None)
    assert fp1 == fp2, "Fingerprints without source witness must not use entryIndex as fake discriminator"

    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"]["sourceSurface"] = "direct_google_maps"
    manifest["googleReviews"]["collectionMethod"] = "playwright_direct_maps"
    manifest["googleReviews"]["profileHeaderObserved"] = True
    manifest["googleReviews"]["reviewsPanelOpened"] = True
    manifest["googleReviews"]["reviewsPanelFullyTraversed"] = True
    manifest["googleReviews"]["textReviewCollectionAttempted"] = True
    manifest["googleReviews"]["profileName"] = "Odontologia Dra. Aline Iost"
    manifest["googleReviews"]["profileUrl"] = "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu"
    manifest["googleReviews"]["placeIdOrCid"] = "ChIJ5-3JUhHbx5QR-KoFM6msI3A"
    manifest["googleReviews"]["collectedAt"] = "2026-08-31T20:55:00Z"
    manifest["googleReviews"]["aggregateRating"] = 5.0
    manifest["googleReviews"]["ratingCount"] = 2
    manifest["googleReviews"]["observedRatingEntries"] = 2
    manifest["googleReviews"]["observedTextReviewEntries"] = 0
    manifest["googleReviews"]["capturedTextReviewCount"] = 0
    manifest["googleReviews"]["starOnlyRatingCount"] = 2
    manifest["googleReviews"]["usableTextReviews"] = 0
    manifest["googleReviews"]["state"] = "VERIFIED_AGGREGATE_ONLY"
    manifest["googleReviews"]["aggregateObservation"] = {
        "ratingText": "5,0",
        "countText": "2 avaliações",
        "surfaceUrl": "https://maps.google.com",
    }
    manifest["googleReviews"]["reviewsPanelObservation"] = {
        "countText": "2 avaliações",
        "surfaceUrl": "https://maps.google.com",
    }
    manifest["googleReviews"]["observedEntries"] = [
        {
            "fingerprint": fp1,
            "fingerprintVersion": "observed-fields-v1",
            "nativeReviewId": None,
            "author": None,
            "rating": 5,
            "dateLabel": None,
            "hasText": False,
            "textEvidenceId": None,
            "sourceSurface": "direct_google_maps",
            "collectedAt": "2026-09-01T01:00:00Z",
            "provenance": {
                "ratingObserved": True,
                "authorObserved": False,
                "dateLabelObserved": False,
                "nativeReviewIdObserved": False,
                "textObserved": False,
            },
        },
        {
            "fingerprint": fp2,
            "fingerprintVersion": "observed-fields-v1",
            "nativeReviewId": None,
            "author": None,
            "rating": 5,
            "dateLabel": None,
            "hasText": False,
            "textEvidenceId": None,
            "sourceSurface": "direct_google_maps",
            "collectedAt": "2026-09-01T01:00:00Z",
            "provenance": {
                "ratingObserved": True,
                "authorObserved": False,
                "dateLabelObserved": False,
                "nativeReviewIdObserved": False,
                "textObserved": False,
            },
        },
    ]
    res = validate_evidence(manifest["googleReviews"])
    assert res.status == "VERIFIED_AGGREGATE_ONLY"
    assert not res.errors


def test_star_only_with_source_witness_passes():
    from google_reviews_evidence import compute_entry_fingerprint, validate_evidence
    fp1 = compute_entry_fingerprint("ChIJ5-3JUhHbx5QR-KoFM6msI3A", None, 5, None, "", None, {"type": "maps_card_hash", "value": "card-hash-1"})
    fp2 = compute_entry_fingerprint("ChIJ5-3JUhHbx5QR-KoFM6msI3A", None, 5, None, "", None, {"type": "maps_card_hash", "value": "card-hash-2"})
    assert fp1 != fp2, "Entries with distinct source witnesses must produce distinct fingerprints"

    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"]["sourceSurface"] = "direct_google_maps"
    manifest["googleReviews"]["collectionMethod"] = "playwright_direct_maps"
    manifest["googleReviews"]["profileHeaderObserved"] = True
    manifest["googleReviews"]["reviewsPanelOpened"] = True
    manifest["googleReviews"]["reviewsPanelFullyTraversed"] = True
    manifest["googleReviews"]["textReviewCollectionAttempted"] = True
    manifest["googleReviews"]["profileName"] = "Odontologia Dra. Aline Iost"
    manifest["googleReviews"]["profileUrl"] = "https://www.google.com.br/maps/place/Odontologia+Dra.+Aline+Iost/@-22.4138359,-47.5626633,17z/data=!3m1!4b1!4m6!3m5!1s0x94c7db1152c9ede7:0x7023aca93305aaf8!8m2!3d-22.4138409!4d-47.5600884!16s%2Fg%2F11qyn05pnk!5m1!1e1?entry=ttu"
    manifest["googleReviews"]["placeIdOrCid"] = "ChIJ5-3JUhHbx5QR-KoFM6msI3A"
    manifest["googleReviews"]["collectedAt"] = "2026-08-31T20:55:00Z"
    manifest["googleReviews"]["aggregateRating"] = 5.0
    manifest["googleReviews"]["ratingCount"] = 2
    manifest["googleReviews"]["observedRatingEntries"] = 2
    manifest["googleReviews"]["observedTextReviewEntries"] = 0
    manifest["googleReviews"]["capturedTextReviewCount"] = 0
    manifest["googleReviews"]["starOnlyRatingCount"] = 2
    manifest["googleReviews"]["usableTextReviews"] = 0
    manifest["googleReviews"]["state"] = "VERIFIED_AGGREGATE_ONLY"
    manifest["googleReviews"]["aggregateObservation"] = {
        "ratingText": "5,0",
        "countText": "2 avaliações",
        "surfaceUrl": "https://maps.google.com",
    }
    manifest["googleReviews"]["reviewsPanelObservation"] = {
        "countText": "2 avaliações",
        "surfaceUrl": "https://maps.google.com",
    }
    manifest["googleReviews"]["observedEntries"] = [
        {
            "fingerprint": fp1,
            "fingerprintVersion": "maps-witness-v1",
            "nativeReviewId": None,
            "sourceWitness": {"type": "maps_card_hash", "value": "card-hash-1"},
            "author": None,
            "rating": 5,
            "dateLabel": None,
            "hasText": False,
            "textEvidenceId": None,
            "sourceSurface": "direct_google_maps",
            "collectedAt": "2026-09-01T01:00:00Z",
            "provenance": {
                "ratingObserved": True,
                "authorObserved": False,
                "dateLabelObserved": False,
                "nativeReviewIdObserved": False,
                "textObserved": False,
            },
        },
        {
            "fingerprint": fp2,
            "fingerprintVersion": "maps-witness-v1",
            "nativeReviewId": None,
            "sourceWitness": {"type": "maps_card_hash", "value": "card-hash-2"},
            "author": None,
            "rating": 5,
            "dateLabel": None,
            "hasText": False,
            "textEvidenceId": None,
            "sourceSurface": "direct_google_maps",
            "collectedAt": "2026-09-01T01:00:00Z",
            "provenance": {
                "ratingObserved": True,
                "authorObserved": False,
                "dateLabelObserved": False,
                "nativeReviewIdObserved": False,
                "textObserved": False,
            },
        },
    ]
    res = validate_evidence(manifest["googleReviews"])
    assert res.status == "VERIFIED_AGGREGATE_ONLY"
    assert not res.errors


if __name__ == "__main__":
    tests = [name for name in globals() if name.startswith("test_")]
    for name in sorted(tests):
        globals()[name]()
        print(f"[PASS] {name}")
    print(f"\n{len(tests)}/{len(tests)} autonomous site-review regression cases passed")



