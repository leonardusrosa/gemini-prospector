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

        frame_policy = extract_attr(hero_tag_str, "data-hero-frame-policy")
        review.check("hero_template_frame_policy", frame_policy == "preserve-complete-frame", "Hero template requires data-hero-frame-policy=\"preserve-complete-frame\"")

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

                # Check declared dimensions match template dimensions
                d_dims = t_entry.get("desktopDimensions", {})
                exp_w = d_dims.get("width")
                exp_h = d_dims.get("height")
                img_w = extract_attr(hero_image_tag, "width")
                img_h = extract_attr(hero_image_tag, "height")
                dims_ok = (str(img_w) == str(exp_w) and str(img_h) == str(exp_h)) if (exp_w and exp_h) else True
                review.check("hero_template_declared_dimensions", dims_ok, f"Hero desktop image declared dimensions ({img_w}x{img_h}) must match template dimensions ({exp_w}x{exp_h})")

        # Check no object-fit: cover for preserve-complete-frame
        has_cover_css = bool(re.search(r"(?:\.hero-bg-img|img\[data-role=['\"]hero-image['\"])[^{}]*\{[^}]*object-fit\s*:\s*cover", html, re.IGNORECASE))
        review.check("hero_template_no_cover", not has_cover_css, "preserve-complete-frame template cannot use object-fit: cover (use object-fit: contain or width: 100%; height: auto)")


def check_google_reviews(manifest: dict, html: str, design_read: str, review: Review) -> None:
    gr_cfg = section(manifest, "googleReviews")
    if not gr_cfg:
        return
    checked = bool(gr_cfg.get("checked", False))
    review.check("google_reviews_checked", checked, "Google reviews check must be performed for first-version concepts")
    state = str(gr_cfg.get("state") or "").upper().strip()
    valid_states = {
        "VERIFIED_STRONG",
        "VERIFIED_TEXT_LIMITED",
        "VERIFIED_AGGREGATE_ONLY",
        "NO_USABLE_REVIEWS",
        "NO_USABLE_REVIEWS_WITH_VERIFIED_AGGREGATE",
        "COLLECTION_INCOMPLETE",
        "PROFILE_CONFLICT",
    }
    review.check("google_reviews_state_valid", state in valid_states, f"googleReviews.state must be in {sorted(valid_states)}")
    review.check("google_reviews_no_conflict", state != "PROFILE_CONFLICT", "PROFILE_CONFLICT blocks Core QA PASS")
    review.check("google_reviews_no_incomplete", state != "COLLECTION_INCOMPLETE", "COLLECTION_INCOMPLETE blocks Core QA PASS")

    dr_check = bool(re.search(r"(?im)^\s*GOOGLE_REVIEWS_CHECK\s*:\s*PASS\s*$", design_read))
    review.check("google_reviews_design_read_check", dr_check, "design-read must record GOOGLE_REVIEWS_CHECK: PASS")

    usable_google_text = int(gr_cfg.get("usableTextReviews", 0) or 0)
    if usable_google_text < 3:
        sec_search = bool(re.search(r"(?im)^\s*SECONDARY_REVIEW_SEARCH\s*:\s*PASS\s*$", design_read))
        review.check("secondary_review_search_check", sec_search, "When Google usable text reviews < 3, design-read must record SECONDARY_REVIEW_SEARCH: PASS")

    rating_count = gr_cfg.get("ratingCount")
    if rating_count is None:
        rating_count = gr_cfg.get("reviewCount")

    has_ratings = isinstance(rating_count, (int, float)) and rating_count > 0
    verified_profile = bool(gr_cfg.get("verifiedGoogleProfile", True))

    section_required = bool(gr_cfg.get("reviewSectionRequired", False))
    section_rendered = bool(gr_cfg.get("reviewSectionRendered", False))

    # Build inventory of verified text reviews from googleReviews
    google_verified_reviews: dict[str, dict] = {}
    for r in gr_cfg.get("reviews", []):
        r_id = r.get("id")
        if r_id and r.get("verified") and r.get("hasText", True) and r.get("text"):
            google_verified_reviews[r_id] = r

    # Panel completeness validation
    observed_rating_entries = gr_cfg.get("observedRatingEntries")
    observed_text_entries = gr_cfg.get("observedTextReviewEntries")
    captured_text_count = gr_cfg.get("capturedTextReviewCount")

    if isinstance(rating_count, int) and rating_count > 0:
        if observed_rating_entries is not None:
            review.check(
                "google_reviews_panel_traversal_complete",
                observed_rating_entries == rating_count,
                f"observedRatingEntries ({observed_rating_entries}) must equal ratingCount ({rating_count})",
            )
        if observed_text_entries is not None:
            review.check(
                "google_reviews_text_capture_complete",
                len(google_verified_reviews) == observed_text_entries,
                f"captured text reviews ({len(google_verified_reviews)}) must equal observedTextReviewEntries ({observed_text_entries})",
            )
        if captured_text_count is not None:
            review.check(
                "google_reviews_captured_count_match",
                captured_text_count == len(google_verified_reviews),
                f"capturedTextReviewCount ({captured_text_count}) must equal captured text reviews ({len(google_verified_reviews)})",
            )

    requires_section = (
        len(google_verified_reviews) > 0
        or state in {"VERIFIED_STRONG", "VERIFIED_TEXT_LIMITED", "VERIFIED_AGGREGATE_ONLY", "NO_USABLE_REVIEWS_WITH_VERIFIED_AGGREGATE"}
        or (verified_profile and has_ratings and state != "PROFILE_CONFLICT")
    )

    if requires_section:
        review.check("google_reviews_section_required", section_required, f"State {state} with ratings/evidence requires reviewSectionRequired=true")
        review.check("google_reviews_section_rendered", section_rendered, f"State {state} with ratings/evidence requires reviewSectionRendered=true")
        has_reviews_html = bool(
            re.search(r"data-role=['\"]reviews['\"]|data-role=['\"]testimonials['\"]|id=['\"]avaliacoes['\"]|class=['\"][^'\"]*(?:review|testimonial|avaliacao|depoimento)", html, re.IGNORECASE)
        )
        review.check("google_reviews_html_rendered", has_reviews_html, f"State {state} requires rendered review section in HTML")

        tag_match = REVIEWS_TAG_PATTERN.search(html)
        section_match = REVIEWS_SECTION_PATTERN.search(html)
        tag_str = tag_match.group(0) if tag_match else ""
        section_inner = section_match.group(1) if section_match else ""

        # Rating and Count attributes
        rating_attr = extract_attr(tag_str, "data-review-rating")
        expected_rating = gr_cfg.get("aggregateRating")
        if expected_rating is not None:
            rating_ok = False
            if rating_attr is not None:
                try:
                    rating_ok = abs(float(str(rating_attr).replace(",", ".")) - float(str(expected_rating).replace(",", "."))) < 0.01
                except ValueError:
                    rating_ok = False
            review.check("google_reviews_rating_hook", rating_ok, f"data-review-rating={rating_attr!r} must match evidence rating {expected_rating!r}")

        count_attr = extract_attr(tag_str, "data-review-count")
        expected_count = gr_cfg.get("ratingCount")
        if expected_count is None:
            expected_count = gr_cfg.get("reviewCount")
        if expected_count is not None:
            count_ok = False
            if count_attr is not None:
                try:
                    count_ok = int(count_attr) == int(expected_count)
                except ValueError:
                    count_ok = False
            review.check("google_reviews_count_hook", count_ok, f"data-review-count={count_attr!r} must match evidence count {expected_count!r}")

        # Ban stale "1 avaliação" if expected_count != 1
        text_only = re.sub(r"<[^>]+>", " ", section_inner)
        if expected_count is not None and int(expected_count) != 1:
            has_stale_1 = bool(re.search(r"\b1\s+avalia[cç][aã]o\b", text_only, re.IGNORECASE))
            review.check("google_reviews_no_stale_count_text", not has_stale_1, f"Review section cannot display '1 avaliação' when ratingCount is {expected_count}")

        # Ban synthetic reviewer placeholders (e.g. Paciente Verificado #1)
        has_synthetic = bool(re.search(r"(?i)\b(?:paciente\s+verificado|reviewer|cliente|an[oô]nimo|paciente)\s*#?\s*\d+\b", text_only))
        review.check("google_reviews_no_synthetic_metadata", not has_synthetic, "Public review section cannot contain synthetic reviewer placeholders (e.g. Paciente Verificado #1)")

        # Ban unsupported patient status claim in review subtitle
        has_patient_claim = bool(re.search(r"(?i)\bopini(?:ão|ões)\s+de\s+pacientes\b", text_only))
        review.check("google_reviews_no_unsupported_patient_claim", not has_patient_claim, "Public review section subtitle cannot claim verified patient status ('Opiniões de pacientes') without source verification. Use 'Avaliações públicas sobre o atendimento' instead.")

        if state in {"VERIFIED_STRONG", "VERIFIED_TEXT_LIMITED"}:
            review_mode = extract_attr(tag_str, "data-review-mode")
            review.check(
                "google_reviews_mode_text",
                review_mode in {"verified-text", "multi-source", "text-reviews"},
                f"Verified text reviews present ({len(google_verified_reviews)}) require data-review-mode in ['verified-text', 'multi-source', 'text-reviews']",
            )

        if state in {"VERIFIED_STRONG", "VERIFIED_TEXT_LIMITED"}:
            review_mode = extract_attr(tag_str, "data-review-mode")
            review.check(
                "google_reviews_mode_text",
                review_mode in {"verified-text", "multi-source", "text-reviews"},
                f"Verified text reviews present ({len(google_verified_reviews)}) require data-review-mode in ['verified-text', 'multi-source', 'text-reviews']",
            )

            observed_entries = gr_cfg.get("observedEntries")
            has_carousel = bool(re.search(r"data-role=['\"]reviews-carousel['\"]", section_inner, re.IGNORECASE))

            if observed_entries and isinstance(observed_entries, list) and has_carousel:
                # Validate carousel presentation
                carousel_match = re.search(r"<[^>]*data-role=['\"]reviews-carousel['\"][^>]*>", section_inner, re.IGNORECASE)
                carousel_tag = carousel_match.group(0) if carousel_match else ""
                carousel_total = extract_attr(carousel_tag, "data-review-total-items")
                
                review.check(
                    "carousel_total_items_attr",
                    carousel_total is not None and int(carousel_total) == len(observed_entries),
                    f"Carousel data-review-total-items={carousel_total!r} must match observedEntries length {len(observed_entries)}",
                )

                carousel_items = list(re.finditer(r"<(?P<tag>article|div)\b(?P<attrs>[^>]*)data-role=['\"]review-carousel-item['\"](?P<rest>[^>]*)>(?P<content>.*?)</(?P=tag)>", section_inner, re.DOTALL | re.IGNORECASE))
                review.check(
                    "carousel_items_count",
                    len(carousel_items) == len(observed_entries),
                    f"Carousel must render all {len(observed_entries)} observed entries, found {len(carousel_items)} items",
                )

                observed_by_fp = {e.get("fingerprint"): e for e in observed_entries if e.get("fingerprint")}

                for item in carousel_items:
                    full_item_tag = item.group("attrs") + " " + item.group("rest")
                    item_content = item.group("content")
                    item_fp = extract_attr(full_item_tag, "data-review-entry-fingerprint")
                    item_has_text = extract_attr(full_item_tag, "data-review-has-text")

                    review.check(
                        "carousel_item_fingerprint_valid",
                        bool(item_fp and item_fp in observed_by_fp),
                        f"Carousel item fingerprint {item_fp!r} must exist in googleReviews.observedEntries",
                    )

                    if item_fp and item_fp in observed_by_fp:
                        obs_entry = observed_by_fp[item_fp]
                        item_plain_text = re.sub(r"<[^>]+>", " ", item_content).strip()
                        obs_author = str(obs_entry.get("author") or "").strip().lower()

                        if obs_entry.get("hasText"):
                            ev_id = extract_attr(full_item_tag, "data-review-evidence-id")
                            expected_ev_id = obs_entry.get("textEvidenceId")
                            review.check(
                                "carousel_text_item_evidence_id",
                                ev_id == expected_ev_id and ev_id in google_verified_reviews,
                                f"Text carousel item must bind data-review-evidence-id={expected_ev_id!r}",
                            )
                            if ev_id in google_verified_reviews:
                                ev_item = google_verified_reviews[ev_id]
                                ev_text = ev_item.get("text", "").strip()
                                ev_text_clean = " ".join(ev_text.split()[:8])
                                review.check(
                                    "carousel_text_item_match",
                                    ev_text_clean.lower() in item_plain_text.lower(),
                                    f"Text carousel item must contain snippet '{ev_text_clean}'",
                                )
                        else:
                            # Star-only rating card
                            has_fake_quote = bool(re.search(r"[\"“][^\"”\n]{15,}[\"”]", item_plain_text))
                            review.check(
                                "carousel_rating_only_no_fake_quotes",
                                not has_fake_quote,
                                f"Rating-only carousel item for {obs_author} cannot contain fabricated review quote",
                            )

                # Check carousel navigation hooks
                has_prev = bool(re.search(r"data-role=['\"]carousel-prev['\"]", section_inner, re.IGNORECASE))
                has_next = bool(re.search(r"data-role=['\"]carousel-next['\"]", section_inner, re.IGNORECASE))
                has_counter = bool(re.search(r"data-role=['\"]carousel-counter['\"]", section_inner, re.IGNORECASE))
                review.check("carousel_prev_button", has_prev, "Carousel requires [data-role=\"carousel-prev\"] button")
                review.check("carousel_next_button", has_next, "Carousel requires [data-role=\"carousel-next\"] button")
                review.check("carousel_counter", has_counter, "Carousel requires [data-role=\"carousel-counter\"] element")
            else:
                # Find standard review cards
                card_matches = list(re.finditer(r"<(?P<tag>article|div)\b(?P<attrs>[^>]*)data-role=['\"]review-card['\"](?P<rest>[^>]*)>(?P<content>.*?)</(?P=tag)>", section_inner, re.DOTALL | re.IGNORECASE))
                
                if state == "VERIFIED_STRONG":
                    review.check("google_reviews_cards_present", len(card_matches) >= 3, f"VERIFIED_STRONG state requires >= 3 review cards, found {len(card_matches)}")
                elif state == "VERIFIED_TEXT_LIMITED":
                    review.check("google_reviews_cards_present", len(card_matches) in {1, 2}, f"VERIFIED_TEXT_LIMITED state requires 1-2 review cards, found {len(card_matches)}")

                for card in card_matches:
                    full_card_tag = card.group("attrs") + " " + card.group("rest")
                    card_content = card.group("content")
                    ev_id = extract_attr(full_card_tag, "data-review-evidence-id")
                    
                    review.check(
                        "review_card_evidence_id_valid",
                        bool(ev_id and ev_id in google_verified_reviews),
                        f"Review card data-review-evidence-id={ev_id!r} must exist in googleReviews.reviews evidence inventory",
                    )

                    if ev_id and ev_id in google_verified_reviews:
                        ev_item = google_verified_reviews[ev_id]
                        ev_author = ev_item.get("author", "").strip().lower()
                        ev_text = ev_item.get("text", "").strip()
                        card_plain_text = re.sub(r"<[^>]+>", " ", card_content).strip()

                        review.check(
                            "review_card_author_match",
                            ev_author in card_plain_text.lower(),
                            f"Review card {ev_id} must contain author '{ev_item.get('author')}'",
                        )
                        
                        ev_text_clean = " ".join(ev_text.split()[:8])
                        review.check(
                            "review_card_text_match",
                            ev_text_clean.lower() in card_plain_text.lower(),
                            f"Review card {ev_id} text must match evidence snippet '{ev_text_clean}'",
                        )
        elif state in {"VERIFIED_AGGREGATE_ONLY", "NO_USABLE_REVIEWS_WITH_VERIFIED_AGGREGATE"}:
            # Aggregate-only mode
            review_mode = extract_attr(tag_str, "data-review-mode")
            review.check("google_reviews_mode_aggregate", review_mode == "aggregate-only", "Aggregate-only review section requires data-review-mode=\"aggregate-only\"")

            presentation = extract_attr(tag_str, "data-review-presentation")
            review.check("google_reviews_presentation_compact", presentation == "compact-summary", "Aggregate-only review section requires data-review-presentation=\"compact-summary\"")

            has_summary_hook = bool(re.search(r"data-role=['\"]reviews-summary['\"]", section_inner, re.IGNORECASE))
            review.check("google_reviews_summary_hook", has_summary_hook, "Aggregate-only review section requires [data-role=\"reviews-summary\"] element")

            has_fake_cards = bool(re.search(r"data-role=['\"]review-card['\"]|<blockquote\b", section_inner, re.IGNORECASE))
            review.check("google_reviews_no_fake_cards", not has_fake_cards, "Aggregate-only state cannot contain testimonial cards or blockquotes")

            has_fake_quotes = bool(re.search(r"[\"“][^\"”\n]{15,}[\"”]", text_only))
            review.check("google_reviews_no_fabricated_text", not has_fake_quotes, "Aggregate-only state cannot contain fabricated review quotes or reviewer authors")


def check_factual_traceability(manifest: dict, design_read: str, html: str, review: Review) -> None:
    import unicodedata

    def strip_accents(s: str) -> str:
        return unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII").lower()

    verified_services_cfg = manifest.get("factualServices") or manifest.get("verifiedServices")
    if verified_services_cfg is None:
        factual_evidence = section(manifest, "factualEvidence")
        verified_services_cfg = factual_evidence.get("verifiedServices")

    # Normalize allowlist items
    allowlist_claims = []
    if isinstance(verified_services_cfg, list):
        for item in verified_services_cfg:
            if isinstance(item, dict):
                allowlist_claims.append(strip_accents(str(item.get("claim", "")).strip()))
            elif isinstance(item, str):
                allowlist_claims.append(strip_accents(item.strip()))

    if not allowlist_claims:
        review.check("factual_traceability_verified_services", False, "factualEvidence.verifiedServices allowlist is empty or missing")
        return

    # Extract claims from design_read
    claimed_services = []
    for line in design_read.splitlines():
        if re.search(r"factual verified services|serviços verificados", line, re.IGNORECASE):
            parts = line.split(":", 1)
            if len(parts) > 1:
                claimed_blob = parts[1]
                for item in re.split(r"[,;•\n]", claimed_blob):
                    cleaned = re.sub(r"^\s*[-*0-9.]+\s*", "", item).strip()
                    if cleaned and len(cleaned) > 2:
                        claimed_services.append(cleaned)

    # Verify that every claimed service maps to the allowlist
    for claim in claimed_services:
        norm_claim = strip_accents(claim)
        claim_words = [w for w in re.findall(r"\b\w{4,}\b", norm_claim) if w not in {"para", "com", "sem", "sobre", "gerais", "geral", "procedimentos", "tratamentos"}]
        is_supported = False
        if any(norm_claim in a or a in norm_claim for a in allowlist_claims):
            is_supported = True
        elif claim_words:
            for a in allowlist_claims:
                if all(w in a for w in claim_words):
                    is_supported = True
                    break

        review.check(
            "factual_traceability_verified_services",
            is_supported,
            f"Claimed service '{claim}' is not supported by factualEvidence.verifiedServices allowlist",
        )
        if not is_supported:
            return

    review.check(
        "factual_traceability_verified_services",
        True,
        "All claimed verified services trace to factual evidence inventory allowlist",
    )


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
    assistant_cfg = section(manifest, "assistant")
    assistant_present = bool(assistant_cfg.get("present") or re.search(r"data-role\s*=\s*['\"]assistant-launcher['\"]", html, re.IGNORECASE))

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

        has_floating_wpp = bool(re.search(r"data-role\s*=\s*['\"]floating-whatsapp['\"]", html, re.IGNORECASE))
        if assistant_present:
            review.check("fixed_conversion_control_exclusivity", not has_floating_wpp, "Assistant is present, so floating WhatsApp is forbidden")
        elif wa_cfg.get("floatingRequired", True):
            review.check("floating_whatsapp_hook", has_floating_wpp, "Floating WhatsApp required when no assistant is present")
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

    if assistant_cfg.get("present"):
        launcher = bool(re.search(r"data-role\s*=\s*['\"]assistant-launcher['\"]", html, re.IGNORECASE))
        review.check("assistant_launcher_hook", launcher, "Assistant requires data-role=assistant-launcher")

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
