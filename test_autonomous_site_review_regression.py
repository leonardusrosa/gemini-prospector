#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression coverage for the autonomous site-review gate.

Each failure case mirrors a class of omission that previously escaped an agent's
self-reported Core QA pass: no gpt-taste evidence, missing hero imagery,
motionless page, map placeholder, omitted social affordance, navigable fake
social, missing floating WhatsApp, and missing assistant collision hooks.
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
        "illustrativeDisclosureRequired": True,
    },
    "motion": {
        "required": True,
        "minimumRevealGroups": 2,
        "headerScrollStateRequired": True,
        "floatingCtaSyncRequired": True,
    },
    "address": {"verified": True, "public": True, "mapEmbedRequired": True},
    "whatsapp": {
        "verified": True,
        "number": "5511999999999",
        "floatingRequired": True,
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
<a href="https://wa.me/5511999999999" data-role="floating-whatsapp">WhatsApp</a>
<button data-role="assistant-launcher">Assistente</button>
<iframe src="https://maps.google.com/maps?q=Rua+1&z=16&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="Mapa de localização"></iframe>
<script>
const obs = new IntersectionObserver(()=>{});
window.addEventListener('scroll',()=>document.querySelector('header').classList.toggle('scrolled',scrollY>10));
</script>
</body></html>'''


def make_design(skill_path: Path, *, include_read=True, sha_override: str | None = None) -> str:
    sha = sha_override or hashlib.sha256(skill_path.read_bytes()).hexdigest()
    lines = []
    if include_read:
        lines.append("GPT_TASTE_READ: PASS")
    lines.extend(
        [
            f"GPT_TASTE_PATH: {skill_path}",
            f"GPT_TASTE_SHA256: {sha}",
            "Design Variance: 5",
            "Motion: 3",
            "Density: 4",
        ]
    )
    return "\n".join(lines) + "\n"


def run_case(html: str = PASS_HTML, design_transform=None, manifest=None):
    manifest = manifest or BASE_MANIFEST
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        html_path = p / "index.html"
        design_path = p / "design-read.md"
        manifest_path = p / "review-manifest.json"
        skill_path = p / "gpt-taste-SKILL.md"
        skill_path.write_text("# Synthetic current gpt-taste skill\nrule: use deliberate composition\n", encoding="utf-8")
        design = make_design(skill_path)
        if design_transform:
            design = design_transform(design, skill_path)
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
    html = PASS_HTML.replace(
        '<a href="https://wa.me/5511999999999" data-role="floating-whatsapp">WhatsApp</a>',
        '<a href="https://wa.me/5511999999999">WhatsApp</a>',
    )
    code, payload = run_case(html=html)
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


if __name__ == "__main__":
    tests = [name for name in globals() if name.startswith("test_")]
    for name in sorted(tests):
        globals()[name]()
        print(f"[PASS] {name}")
    print(f"\n{len(tests)}/{len(tests)} autonomous site-review regression cases passed")
