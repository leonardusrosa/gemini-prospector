#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for Hero Copy Density & De-Duplication Invariant (V3.3.3).

Tests the 4 canonical cases specified in the gate contract:
1. Eyebrow location repeated in supporting copy => FAIL
2. Rating & review count in trust repeated in supporting copy => FAIL
3. Phone in CTA repeated in supporting copy => FAIL
4. Clean 5-layer hero with zero duplication => PASS
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autonomous_site_review_core import check_hero_copy_density
from autonomous_site_review_helpers import Review


def test_case_1_duplicate_location_fails():
    """Case 1: Eyebrow has location, supporting copy repeats location => FAIL"""
    html = """
    <section data-role="hero">
        <div class="hero-eyebrow" data-role="hero-eyebrow">
            Auto Detailing • Addison, Texas
        </div>
        <h1>Automotive Detailing & Paint Refinement</h1>
        <p class="hero-desc" data-role="hero-desc">
            Auto detailing in Addison, Texas.
        </p>
        <a href="tel:2144007287" class="hero-cta" data-role="hero-cta">Call (214) 400-7287</a>
        <div class="hero-trust" data-role="hero-trust">★ 4.9 / 268 Reviews</div>
    </section>
    """
    manifest = {
        "city": "Addison",
        "rating": 4.9,
        "reviewCount": 268,
        "phone": "(214) 400-7287",
    }
    review = Review()
    check_hero_copy_density(html, manifest, review)
    check_dict = {c["key"]: c["status"] == "PASS" for c in review.checks}
    assert check_dict.get("hero_copy_no_duplicate_location") is False, f"Expected duplicate location FAIL, got {check_dict}"
    assert check_dict.get("hero_copy_density_pass") is False, "Expected hero_copy_density_pass FAIL"
    print("[PASS] Case 1: Duplicate location fails as expected.")


def test_case_2_duplicate_rating_and_review_count_fails():
    """Case 2: Supporting copy repeats rating & review count from trust => FAIL"""
    html = """
    <section data-role="hero">
        <div class="hero-eyebrow" data-role="hero-eyebrow">
            Auto Detailing • Addison, Texas
        </div>
        <h1>Automotive Detailing & Paint Refinement</h1>
        <p class="hero-desc" data-role="hero-desc">
            Backed by a 4.9 rating across 268 reviews.
        </p>
        <a href="tel:2144007287" class="hero-cta" data-role="hero-cta">Call (214) 400-7287</a>
        <div class="hero-trust" data-role="hero-trust">★ 4.9 / 268 Reviews</div>
    </section>
    """
    manifest = {
        "city": "Addison",
        "rating": 4.9,
        "reviewCount": 268,
        "phone": "(214) 400-7287",
    }
    review = Review()
    check_hero_copy_density(html, manifest, review)
    check_dict = {c["key"]: c["status"] == "PASS" for c in review.checks}
    assert check_dict.get("hero_copy_no_duplicate_rating") is False, f"Expected duplicate rating FAIL, got {check_dict}"
    assert check_dict.get("hero_copy_no_duplicate_review_count") is False, f"Expected duplicate review count FAIL, got {check_dict}"
    assert check_dict.get("hero_copy_density_pass") is False, "Expected hero_copy_density_pass FAIL"
    print("[PASS] Case 2: Duplicate rating and review count fails as expected.")


def test_case_3_duplicate_phone_fails():
    """Case 3: Supporting copy repeats phone from CTA => FAIL"""
    html = """
    <section data-role="hero">
        <div class="hero-eyebrow" data-role="hero-eyebrow">
            Auto Detailing • Addison, Texas
        </div>
        <h1>Automotive Detailing & Paint Refinement</h1>
        <p class="hero-desc" data-role="hero-desc">
            Call us at (214) 400-7287.
        </p>
        <a href="tel:2144007287" class="hero-cta" data-role="hero-cta">Call (214) 400-7287</a>
        <div class="hero-trust" data-role="hero-trust">★ 4.9 / 268 Reviews</div>
    </section>
    """
    manifest = {
        "city": "Addison",
        "rating": 4.9,
        "reviewCount": 268,
        "phone": "(214) 400-7287",
    }
    review = Review()
    check_hero_copy_density(html, manifest, review)
    check_dict = {c["key"]: c["status"] == "PASS" for c in review.checks}
    assert check_dict.get("hero_copy_no_duplicate_phone") is False, f"Expected duplicate phone FAIL, got {check_dict}"
    assert check_dict.get("hero_copy_density_pass") is False, "Expected hero_copy_density_pass FAIL"
    print("[PASS] Case 3: Duplicate phone fails as expected.")


def test_case_4_clean_hero_passes():
    """Case 4: Clean 5-layer hero with zero duplicate facts => PASS"""
    html = """
    <section data-role="hero">
        <div class="hero-eyebrow" data-role="hero-eyebrow">
            Auto Detailing • Addison, Texas
        </div>
        <h1>Automotive Detailing & Paint Refinement</h1>
        <p class="hero-desc" data-role="hero-desc">
            Auto detailing, paint correction, and buffing.
        </p>
        <a href="tel:2144007287" class="hero-cta" data-role="hero-cta">Call (214) 400-7287</a>
        <div class="hero-trust" data-role="hero-trust">★ 4.9 / 268 Reviews</div>
    </section>
    """
    manifest = {
        "city": "Addison",
        "rating": 4.9,
        "reviewCount": 268,
        "phone": "(214) 400-7287",
    }
    review = Review()
    check_hero_copy_density(html, manifest, review)
    check_dict = {c["key"]: c["status"] == "PASS" for c in review.checks}
    assert check_dict.get("hero_copy_no_duplicate_location") is True, f"Expected location PASS, got {check_dict}"
    assert check_dict.get("hero_copy_no_duplicate_rating") is True, f"Expected rating PASS, got {check_dict}"
    assert check_dict.get("hero_copy_no_duplicate_review_count") is True, f"Expected review count PASS, got {check_dict}"
    assert check_dict.get("hero_copy_no_duplicate_phone") is True, f"Expected phone PASS, got {check_dict}"
    assert check_dict.get("hero_copy_density_pass") is True, f"Expected hero_copy_density_pass PASS, got {check_dict}"
    print("[PASS] Case 4: Clean 5-layer hero passes all checks.")


if __name__ == "__main__":
    test_case_1_duplicate_location_fails()
    test_case_2_duplicate_rating_and_review_count_fails()
    test_case_3_duplicate_phone_fails()
    test_case_4_clean_hero_passes()
    print("\nAll 4 Hero Copy Density test cases passed successfully!")
