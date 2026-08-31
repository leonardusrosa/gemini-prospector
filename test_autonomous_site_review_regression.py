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
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
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


def make_design(skill_path: Path, *, include_read=True, sha_override: str | None = None, gr_state="NO_USABLE_REVIEWS") -> str:
    sha = sha_override or hashlib.sha256(skill_path.read_bytes()).hexdigest()
    lines = []
    if include_read:
        lines.append("GPT_TASTE_READ: PASS")
    lines.extend(
        [
            f"GPT_TASTE_PATH: {skill_path}",
            f"GPT_TASTE_SHA256: {sha}",
            "GOOGLE_REVIEWS_CHECK: PASS",
            f"GOOGLE_REVIEWS_STATE: {gr_state}",
            "SECONDARY_REVIEW_SEARCH: PASS",
            "- **Factual Verified Services**: Atendimento clínico geral",
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
        design = make_design(skill_path, gr_state=gr_state)
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
        "usableTextReviews": 1,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
        "reviews": [
            {
                "id": "gr-1",
                "author": "Carlos",
                "text": "Excelente atendimento",
                "verified": True,
            }
        ],
    }
    html = PASS_HTML.replace('</body>', '<section data-role="reviews" data-review-mode="text-reviews"><div data-role="review-card" data-review-evidence-id="gr-1"><p>Excelente atendimento</p><span>Carlos</span></div></section></body>')
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


def test_multi_source_verified_text_review_allows_card_when_google_is_aggregate_only():
    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["googleReviews"] = {
        "checked": True,
        "verifiedGoogleProfile": True,
        "state": "VERIFIED_STRONG",
        "aggregateRating": 5.0,
        "ratingCount": 12,
        "usableTextReviews": 0,
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
    }
    manifest["reviewEvidence"] = {
        "checked": True,
        "sources": [
            {
                "platform": "doctoralia",
                "profileIdentityMatched": True,
                "profileUrl": "https://www.doctoralia.com.br/aline-iost/ortodontista/rio-claro",
                "reviews": [
                    {
                        "id": "doctoralia-daniel-2022-05-04",
                        "author": "Daniel",
                        "date": "2022-05-04",
                        "text": "Excelente profissional. Cuidadosa, pontual. Faz um trabalho de muita qualidade.",
                        "verification": "verified_opinion",
                        "verified": True,
                    }
                ],
            }
        ],
    }
    # HTML with verified text card
    html = PASS_HTML.replace(
        '</body>',
        '<section data-role="reviews" data-review-mode="verified-text" data-review-rating="5.0" data-review-count="12"><div class="container"><article data-role="review-card" data-review-evidence-id="doctoralia-daniel-2022-05-04"><p>Excelente profissional. Cuidadosa, pontual. Faz um trabalho de muita qualidade.</p><span>Daniel</span></article></div></section></body>',
    )
    code, payload = run_case(html=html, manifest=manifest)
    assert code == 0, f"Expected PASS but got failure: {payload}"


if __name__ == "__main__":
    tests = [name for name in globals() if name.startswith("test_")]
    for name in sorted(tests):
        globals()[name]()
        print(f"[PASS] {name}")
    print(f"\n{len(tests)}/{len(tests)} autonomous site-review regression cases passed")
