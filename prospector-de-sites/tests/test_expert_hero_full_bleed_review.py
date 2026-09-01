import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "expert_hero_full_bleed_review.py"
spec = importlib.util.spec_from_file_location("expert_hero_full_bleed_review", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
validate = module.validate

PASS_MARKERS = """
EXPERT_HERO_FULL_BLEED: PASS
EXPERT_HERO_DESKTOP_FULL_WIDTH: PASS
EXPERT_HERO_MOBILE_FULL_WIDTH: PASS
EXPERT_HERO_GPT_TASTE_JUDGED: PASS
"""

BASE_MANIFEST = {
    "heroVisual": {
        "kind": "expert-placeholder",
        "expertBackgroundRequired": True,
        "desktopFullWidthRequired": True,
        "mobileFullWidthRequired": True,
    }
}

VALID_HTML = """
<section data-role="hero" data-hero-layout="full-bleed-background"
 data-hero-expert-presentation="background" data-hero-mobile-layout="full-width-background">
  <picture>
    <source media="(max-width: 640px)" srcset="hero-mobile.webp">
    <img data-role="hero-image" src="hero-desktop.webp" alt="Illustrative expert context">
  </picture>
</section>
"""


def test_non_expert_not_applicable():
    manifest = {"heroVisual": {"kind": "facility"}}
    assert validate(manifest, "<section data-role='hero'></section>", "") == []


def test_right_side_framed_expert_fails():
    html = VALID_HTML.replace('data-hero-expert-presentation="background"', 'data-hero-expert-presentation="framed"')
    errors = validate(BASE_MANIFEST, html, PASS_MARKERS)
    assert errors
    assert any("background" in error or "framed" in error for error in errors)


def test_split_column_expert_fails():
    html = VALID_HTML.replace('data-hero-layout="full-bleed-background"', 'data-hero-layout="editorial-split"')
    errors = validate(BASE_MANIFEST, html, PASS_MARKERS)
    assert any("full-bleed-background" in error for error in errors)


def test_desktop_full_bleed_mobile_without_responsive_source_fails():
    html = VALID_HTML.replace('<source media="(max-width: 640px)" srcset="hero-mobile.webp">', "")
    errors = validate(BASE_MANIFEST, html, PASS_MARKERS)
    assert any("mobile <source" in error for error in errors)


def test_missing_gpt_taste_judge_marker_fails():
    markers = PASS_MARKERS.replace("EXPERT_HERO_GPT_TASTE_JUDGED: PASS", "")
    errors = validate(BASE_MANIFEST, VALID_HTML, markers)
    assert any("EXPERT_HERO_GPT_TASTE_JUDGED" in error for error in errors)


def test_valid_full_bleed_desktop_and_mobile_passes():
    assert validate(BASE_MANIFEST, VALID_HTML, PASS_MARKERS) == []
