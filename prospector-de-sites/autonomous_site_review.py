#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic pre-browser review for Prospector public websites.

Usage:
    python prospector-de-sites/autonomous_site_review.py \
        --html sites/<slug>/<slug>.html \
        --design-read sites/<slug>/design-read.md \
        --manifest sites/<slug>/review-manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

try:
    from autonomous_site_review_helpers import (
        Review,
        contains_real_motion,
        disabled_social_tag_is_safe,
        extract_attr,
        extract_design_value,
        extract_motion_score,
        find_canonical_template_manifest,
        first_map_iframe,
        load_json,
        normalize_digits,
        read_text,
        section,
        social_tag,
        HERO_IMAGE_PATTERN,
        HERO_SECTION_PATTERN,
        INSTAGRAM_ACTIVE_PATTERN,
        REVIEWS_SECTION_PATTERN,
        REVIEWS_TAG_PATTERN,
        WA_LINK_PATTERN,
    )
except ImportError:
    from .autonomous_site_review_helpers import (
        Review,
        contains_real_motion,
        disabled_social_tag_is_safe,
        extract_attr,
        extract_design_value,
        extract_motion_score,
        find_canonical_template_manifest,
        first_map_iframe,
        load_json,
        normalize_digits,
        read_text,
        section,
        social_tag,
        HERO_IMAGE_PATTERN,
        HERO_SECTION_PATTERN,
        INSTAGRAM_ACTIVE_PATTERN,
        REVIEWS_SECTION_PATTERN,
        REVIEWS_TAG_PATTERN,
        WA_LINK_PATTERN,
    )


def check_gpt_taste(manifest: dict, design_read: str, review: Review) -> None:
    gpt_cfg = section(manifest, "gptTaste")
    if not gpt_cfg.get("required", True):
        return
    gpt_pass = bool(re.search(r"(?im)^\s*GPT_TASTE_READ\s*:\s*PASS\s*$", design_read))
    gpt_path_raw = extract_design_value(design_read, "GPT_TASTE_PATH")
    path_ok = bool(gpt_path_raw and "<" not in gpt_path_raw and ">" not in gpt_path_raw)
    review.check("gpt_taste_read", gpt_pass, "design-read must contain GPT_TASTE_READ: PASS")
    review.check("gpt_taste_path", path_ok, "design-read must record the real gpt-taste SKILL.md path")

    if gpt_cfg.get("skillSha256Required", True) and path_ok:
        gpt_sha = (extract_design_value(design_read, "GPT_TASTE_SHA256") or "").lower()
        sha_format_ok = bool(re.fullmatch(r"[0-9a-f]{64}", gpt_sha))
        review.check("gpt_taste_sha_format", sha_format_ok, "design-read must contain GPT_TASTE_SHA256 64-char hex")
        actual_path = Path(str(gpt_path_raw)).expanduser()
        actual_exists = actual_path.is_file()
        review.check("gpt_taste_skill_exists", actual_exists, f"Recorded gpt-taste skill must exist: {actual_path}")
        if actual_exists and sha_format_ok:
            actual_sha = hashlib.sha256(actual_path.read_bytes()).hexdigest()
            review.check("gpt_taste_sha_matches", actual_sha == gpt_sha, "Recorded GPT_TASTE_SHA256 must match current file")


def check_hero_visual(manifest: dict, html: str, design_read: str, review: Review, base_dir: Path | None = None) -> None:
    hero_cfg = section(manifest, "heroVisual")
    if not hero_cfg.get("required", True):
        return

    hero_section = HERO_SECTION_PATTERN.search(html)
    review.check("hero_section_hook", hero_section is not None, "Hero requires <section data-role=\"hero\">")

    hero_image_tag = None
    if hero_section:
        image_match = HERO_IMAGE_PATTERN.search(hero_section.group(1))
        hero_image_tag = image_match.group(0) if image_match else None

    review.check("hero_image_present", hero_image_tag is not None, "Hero requires <img data-role=\"hero-image\">")
    if not hero_image_tag or not hero_section:
        return

    src = (extract_attr(hero_image_tag, "src") or "").strip()
    alt = (extract_attr(hero_image_tag, "alt") or "").strip()
    loading = (extract_attr(hero_image_tag, "loading") or "").strip().lower()
    image_context = (extract_attr(hero_image_tag, "data-image-context") or "").strip().lower()

    review.check("hero_image_src", bool(src), "Hero image src must be non-empty")
    review.check("hero_image_alt", bool(alt), "Hero image alt must be non-empty and factual")
    review.check("hero_image_not_lazy", loading != "lazy", "Critical hero image must not use loading=lazy")

    kind = str(hero_cfg.get("kind") or "").strip().lower()
    source_type = str(hero_cfg.get("sourceType") or "").strip().lower()
    rep_business = bool(hero_cfg.get("representsActualBusiness", False))
    rep_expert = bool(hero_cfg.get("representsActualExpert", False))
    disclosure_required = bool(hero_cfg.get("illustrativeDisclosureRequired", True))

    valid_kinds = {"expert", "expert-placeholder", "facility", "contextual", "product", "other"}
    valid_sources = {"first_party", "user_provided", "stock", "generated", "generated-template"}
    review.check("hero_image_kind_manifest", kind in valid_kinds, f"heroVisual.kind must be in {sorted(valid_kinds)}")
    review.check("hero_image_source_manifest", source_type in valid_sources, f"heroVisual.sourceType must be in {sorted(valid_sources)}")

    if source_type in {"stock", "generated", "generated-template"}:
        review.check(
            "hero_image_no_false_business_representation",
            not rep_business,
            "Template/stock/generated hero imagery cannot claim representsActualBusiness=true",
        )
        review.check(
            "hero_image_no_false_expert_representation",
            not rep_expert,
            "Template/stock/generated hero imagery cannot claim representsActualExpert=true",
        )
        if disclosure_required and not rep_business:
            review.check(
                "hero_image_illustrative_context",
                image_context == "illustrative",
                "Illustrative hero requires data-image-context=\"illustrative\"",
            )

    if kind == "expert-placeholder":
        template_id = str(hero_cfg.get("templateId") or "").strip()
        review.check("hero_template_id_present", bool(template_id), "kind=expert-placeholder requires templateId")
        review.check("hero_template_source_type", source_type == "generated-template", "kind=expert-placeholder requires sourceType=generated-template")
        review.check("hero_template_no_actual_expert", not rep_expert, "Template placeholder cannot claim representsActualExpert=true")
        review.check("hero_template_no_actual_business", not rep_business, "Template placeholder cannot claim representsActualBusiness=true")
        review.check("hero_template_illustrative_context", image_context == "illustrative", "Template requires data-image-context=\"illustrative\"")

        hero_tag_match = re.search(r"<section\b[^>]*data-role\s*=\s*['\"]hero['\"][^>]*>", html, re.IGNORECASE)
        hero_tag_str = hero_tag_match.group(0) if hero_tag_match else ""
        layout_mode = extract_attr(hero_tag_str, "data-hero-layout")
        review.check("hero_template_layout_mode", layout_mode == "full-bleed-background", "Hero template requires data-hero-layout=\"full-bleed-background\"")

        has_picture = bool(re.search(r"<picture\b", hero_section.group(1), re.IGNORECASE))
        review.check("hero_template_picture_present", has_picture, "Hero template requires <picture> wrapper for responsive assets")

        has_mobile_source = bool(re.search(r"<source\b[^>]*media\s*=\s*['\"][^'\"]*max-width[^'\"]*['\"][^>]*srcset\s*=", hero_section.group(1), re.IGNORECASE))
        review.check("hero_template_mobile_source_present", has_mobile_source, "Hero template requires mobile <source media=\"(max-width: ...)\">")

        cat_path, cat_data = find_canonical_template_manifest(base_dir)
        review.check("hero_template_catalog_exists", cat_data is not None, f"Canonical hero-expert catalog not found (checked {cat_path})")
        if cat_data and template_id:
            templates_list = cat_data.get("templates", [])
            matched = [t for t in templates_list if t.get("id") == template_id]
            review.check("hero_template_id_in_catalog", bool(matched), f"templateId '{template_id}' not found in canonical manifest")
            if matched and cat_path:
                t_entry = matched[0]
                t_root = cat_path.parent
                d_file = t_root / t_entry.get("desktop", "")
                m_file = t_root / t_entry.get("mobile", "")
                review.check("hero_template_desktop_file_exists", d_file.is_file(), f"Desktop template file missing: {d_file}")
                review.check("hero_template_mobile_file_exists", m_file.is_file(), f"Mobile template file missing: {m_file}")


def check_google_reviews(manifest: dict, html: str, design_read: str, review: Review) -> None:
    gr_cfg = section(manifest, "googleReviews")
    if not gr_cfg:
        return
    checked = bool(gr_cfg.get("checked", False))
    review.check("google_reviews_checked", checked, "Google reviews check must be performed for first-version concepts")
    state = str(gr_cfg.get("state") or "").upper().strip()
    valid_states = {
        "VERIFIED_STRONG",
        "VERIFIED_AGGREGATE_ONLY",
        "NO_USABLE_REVIEWS",
        "NO_USABLE_REVIEWS_WITH_VERIFIED_AGGREGATE",
        "PROFILE_CONFLICT",
    }
    review.check("google_reviews_state_valid", state in valid_states, f"googleReviews.state must be in {sorted(valid_states)}")
    review.check("google_reviews_no_conflict", state != "PROFILE_CONFLICT", "PROFILE_CONFLICT blocks Core QA PASS")

    dr_check = bool(re.search(r"(?im)^\s*GOOGLE_REVIEWS_CHECK\s*:\s*PASS\s*$", design_read))
    review.check("google_reviews_design_read_check", dr_check, "design-read must record GOOGLE_REVIEWS_CHECK: PASS")

    rating_count = gr_cfg.get("ratingCount")
    if rating_count is None:
        rating_count = gr_cfg.get("reviewCount")

    has_ratings = isinstance(rating_count, (int, float)) and rating_count > 0
    verified_profile = bool(gr_cfg.get("verifiedGoogleProfile", True))

    section_required = bool(gr_cfg.get("reviewSectionRequired", False))
    section_rendered = bool(gr_cfg.get("reviewSectionRendered", False))

    requires_section = (
        state in {"VERIFIED_STRONG", "VERIFIED_AGGREGATE_ONLY", "NO_USABLE_REVIEWS_WITH_VERIFIED_AGGREGATE"}
        or (verified_profile and has_ratings and state != "PROFILE_CONFLICT")
    )

    if requires_section:
        review.check("google_reviews_section_required", section_required, f"State {state} with ratings requires reviewSectionRequired=true")
        review.check("google_reviews_section_rendered", section_rendered, f"State {state} with ratings requires reviewSectionRendered=true")
        has_reviews_html = bool(
            re.search(r"data-role=['\"]reviews['\"]|data-role=['\"]testimonials['\"]|id=['\"]avaliacoes['\"]|class=['\"][^'\"]*(?:review|testimonial|avaliacao|depoimento)", html, re.IGNORECASE)
        )
        review.check("google_reviews_html_rendered", has_reviews_html, f"State {state} requires rendered review section in HTML")

        tag_match = REVIEWS_TAG_PATTERN.search(html)
        section_match = REVIEWS_SECTION_PATTERN.search(html)
        tag_str = tag_match.group(0) if tag_match else ""
        section_inner = section_match.group(1) if section_match else ""

        if state in {"VERIFIED_AGGREGATE_ONLY", "NO_USABLE_REVIEWS_WITH_VERIFIED_AGGREGATE"}:
            review_mode = extract_attr(tag_str, "data-review-mode")
            review.check("google_reviews_mode_aggregate", review_mode == "aggregate-only", "Aggregate-only review section requires data-review-mode=\"aggregate-only\"")

            rating_attr = extract_attr(tag_str, "data-review-rating")
            expected_rating = gr_cfg.get("aggregateRating")
            rating_ok = False
            if rating_attr is not None and expected_rating is not None:
                try:
                    rating_ok = abs(float(str(rating_attr).replace(",", ".")) - float(str(expected_rating).replace(",", "."))) < 0.01
                except ValueError:
                    rating_ok = False
            review.check("google_reviews_rating_hook", rating_ok, f"data-review-rating={rating_attr!r} must match evidence rating {expected_rating!r}")

            count_attr = extract_attr(tag_str, "data-review-count")
            expected_count = gr_cfg.get("ratingCount")
            if expected_count is None:
                expected_count = gr_cfg.get("reviewCount")
            count_ok = False
            if count_attr is not None and expected_count is not None:
                try:
                    count_ok = int(count_attr) == int(expected_count)
                except ValueError:
                    count_ok = False
            review.check("google_reviews_count_hook", count_ok, f"data-review-count={count_attr!r} must match evidence count {expected_count!r}")

            has_fake_cards = bool(re.search(r"data-role=['\"]review-card['\"]|<blockquote\b", section_inner, re.IGNORECASE))
            review.check("google_reviews_no_fake_cards", not has_fake_cards, "Aggregate-only state cannot contain testimonial cards or blockquotes")

            has_unsupported_patient = bool(re.search(r"\b(?:paciente|pacientes|atendido|atendidos|pessoa que realizou tratamento)\b", section_inner, re.IGNORECASE))
            review.check("google_reviews_no_unsupported_patient_attribution", not has_unsupported_patient, "Review section cannot infer patient/client attribution without verified review text evidence")
        elif state == "VERIFIED_STRONG":
            review_mode = extract_attr(tag_str, "data-review-mode")
            review.check("google_reviews_mode_text", review_mode == "text-reviews", "VERIFIED_STRONG reviews require data-review-mode=\"text-reviews\"")
            has_cards = bool(re.search(r"data-role=['\"]review-card['\"]", section_inner, re.IGNORECASE))
            review.check("google_reviews_cards_present", has_cards, "VERIFIED_STRONG state requires verified review cards with data-role=\"review-card\"")


def check_factual_traceability(manifest: dict, design_read: str, html: str, review: Review) -> None:
    verified_services_cfg = manifest.get("factualServices") or manifest.get("verifiedServices")
    if verified_services_cfg is None:
        factual_evidence = section(manifest, "factualEvidence")
        verified_services_cfg = factual_evidence.get("verifiedServices")

    # Extract claims from design_read
    claimed_services = []
    for line in design_read.splitlines():
        if re.search(r"factual verified services|serviços verificados", line, re.IGNORECASE):
            claimed_services.append(line)

    unsupported_terms = [
        "invisalign",
        "alinhador",
        "ortopedia facial",
        "interceptativa",
        "contenção",
        "adultos e crianças",
    ]

    if verified_services_cfg is not None and isinstance(verified_services_cfg, list):
        norm_verified = " ".join(str(s).lower() for s in verified_services_cfg)
        for term in unsupported_terms:
            for claim_line in claimed_services:
                if term in claim_line.lower() and term not in norm_verified:
                    review.check(
                        "factual_traceability_verified_services",
                        False,
                        f"design-read claims verified service '{term}' not traced to factual evidence inventory",
                    )
                    return
    review.check("factual_traceability_verified_services", True, "All claimed verified services trace to factual evidence inventory")


def check_motion_and_map(manifest: dict, html: str, design_read: str, review: Review) -> None:
    motion_cfg = section(manifest, "motion")
    if bool(motion_cfg.get("required", True)):
        motion_score = extract_motion_score(design_read)
        review.check("motion_score", motion_score is not None and motion_score > 0, f"Motion dial must be > 0; found {motion_score!r}")
        review.check("motion_runtime", contains_real_motion(html), "Page needs real scroll/reveal behavior")
        review.check("reduced_motion_css", "prefers-reduced-motion" in html, "prefers-reduced-motion handling required")
        min_reveals = int(motion_cfg.get("minimumRevealGroups", 2) or 0)
        if min_reveals > 0:
            count = len(re.findall(r"data-motion\s*=\s*['\"]reveal['\"]", html, re.IGNORECASE))
            review.check("motion_reveal_hooks", count >= min_reveals, f"Expected >={min_reveals} reveal groups; found {count}")
        if motion_cfg.get("headerScrollStateRequired", False):
            review.check("header_scroll_hook", bool(re.search(r"data-role\s*=\s*['\"]site-header['\"]", html, re.IGNORECASE)), "Header needs data-role=site-header")

    address_cfg = section(manifest, "address")
    if bool(address_cfg.get("verified") and address_cfg.get("public", True) and address_cfg.get("mapEmbedRequired", True)):
        iframe = first_map_iframe(html)
        review.check("map_embed", iframe is not None, "Verified public address requires embedded Google Maps")
        if iframe:
            review.check("map_lazy", "loading=\"lazy\"" in iframe.lower() or "loading='lazy'" in iframe.lower(), "Map iframe should lazy-load")
            review.check("map_title", bool(re.search(r"\btitle\s*=", iframe, re.IGNORECASE)), "Map iframe requires title")
            review.check("map_referrerpolicy", "referrerpolicy=" in iframe.lower(), "Map iframe requires referrerpolicy")


def check_socials_and_extras(manifest: dict, html: str, review: Review) -> None:
    wa_cfg = section(manifest, "whatsapp")
    if wa_cfg.get("verified"):
        expected = normalize_digits(wa_cfg.get("number"))
        links = WA_LINK_PATTERN.findall(html)
        normalized = [normalize_digits(item) for item in links]
        matches = [item for item in normalized if item == expected] if expected else normalized
        review.check("whatsapp_verified_destination", bool(matches), f"Expected wa.me link to {expected or '[configured]'}")
        wrong = sorted({item for item in normalized if expected and item != expected})
        review.check("whatsapp_no_wrong_numbers", not wrong, "Unexpected WhatsApp: " + (", ".join(wrong) if wrong else "none"))
        if wa_cfg.get("contactActionRequired", True):
            review.check("whatsapp_multiple_conversion_points", len(matches) >= 2, f"Expected >=2 wa.me links, found {len(matches)}")
        if wa_cfg.get("floatingRequired", True):
            review.check("floating_whatsapp_hook", bool(re.search(r"data-role\s*=\s*['\"]floating-whatsapp['\"]", html, re.IGNORECASE)), "Floating WhatsApp required")
    elif wa_cfg.get("mockAffordanceRequired", False):
        tag = social_tag(html, "whatsapp")
        review.check("whatsapp_mock_present", bool(tag), "Unverified WhatsApp requires mockup affordance")
        if tag:
            safe, detail = disabled_social_tag_is_safe(tag)
            review.check("whatsapp_mock_disabled_no_navigation", safe, detail)

    ig_cfg = section(manifest, "instagram")
    ig_state = str(ig_cfg.get("state") or "not_applicable").strip().lower()
    if ig_state == "verified":
        review.check("instagram_active", bool(INSTAGRAM_ACTIVE_PATTERN.search(html)), "Verified Instagram requires active link")
        expected_url = str(ig_cfg.get("expectedUrl") or "").strip().rstrip("/").lower()
        if expected_url:
            review.check("instagram_verified_url", expected_url in html.lower(), "Instagram href must match verified profile")
    elif ig_state == "unverified" and ig_cfg.get("mockAffordanceRequired", True):
        tag = social_tag(html, "instagram")
        review.check("instagram_mock_present", bool(tag), "Unverified Instagram requires visible mockup affordance")
        if tag:
            safe, detail = disabled_social_tag_is_safe(tag)
            review.check("instagram_mock_disabled_no_navigation", safe, "Unverified Instagram must be disabled. " + detail)

    assistant_cfg = section(manifest, "assistant")
    if assistant_cfg.get("present") and assistant_cfg.get("collisionCheckRequired", True):
        launcher = bool(re.search(r"data-role\s*=\s*['\"]assistant-launcher['\"]", html, re.IGNORECASE))
        floating = bool(re.search(r"data-role\s*=\s*['\"]floating-whatsapp['\"]", html, re.IGNORECASE))
        review.check("assistant_launcher_hook", launcher, "Assistant requires data-role=assistant-launcher")
        review.check("assistant_whatsapp_geometry_hooks", launcher and floating, "Assistant + WhatsApp need geometry hooks")

    if manifest.get("preview") is True:
        noindex = bool(re.search(r"<meta\b[^>]*name\s*=\s*['\"]robots['\"][^>]*content\s*=\s*['\"][^'\"]*noindex[^'\"]*nofollow[^'\"]*['\"]", html, re.IGNORECASE | re.DOTALL))
        review.check("preview_noindex", noindex, "Preview must be noindex,nofollow")

    review.check("fake_online_state", not bool(re.search(r">\s*Online\s*<|>\s*Estamos online\s*<", html, re.IGNORECASE)), "Do not simulate human/online state")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prospector deterministic autonomous site review")
    parser.add_argument("--html", required=True)
    parser.add_argument("--design-read", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    html_path = Path(args.html)
    design_path = Path(args.design_read)
    manifest_path = Path(args.manifest)

    html = read_text(html_path, "HTML")
    design_read = read_text(design_path, "design-read")
    manifest = load_json(manifest_path)
    review = Review()

    base_dir = manifest_path.parent

    check_gpt_taste(manifest, design_read, review)
    check_hero_visual(manifest, html, design_read, review, base_dir=base_dir)
    check_google_reviews(manifest, html, design_read, review)
    check_factual_traceability(manifest, design_read, html, review)
    check_motion_and_map(manifest, html, design_read, review)
    check_socials_and_extras(manifest, html, review)

    return review.emit()


if __name__ == "__main__":
    sys.exit(main())
