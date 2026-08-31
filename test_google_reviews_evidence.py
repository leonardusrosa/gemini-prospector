#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = ROOT / "prospector-de-sites" / "google_reviews_evidence.py"
SPEC = importlib.util.spec_from_file_location("google_reviews_evidence", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["google_reviews_evidence"] = mod
SPEC.loader.exec_module(mod)


class GoogleReviewsEvidenceTest(unittest.TestCase):
    def base(self, count=36, rating=5.0):
        return {
            "profileName": "Negócio Teste",
            "profileUrl": "https://www.google.com/maps/place/teste",
            "placeIdOrCid": "cid:test",
            "aggregateRating": rating,
            "reviewCount": count,
            "collectedAt": "2026-08-31T17:00:00-03:00",
            "sourceSurface": "direct_google_maps",
            "collectionMethod": "playwright_direct_maps",
            "profileHeaderObserved": True,
            "reviewsPanelOpened": count > 0,
            "textReviewCollectionAttempted": count > 0,
            "aggregateObservation": {
                "ratingText": str(rating).replace(".", ","),
                "countText": f"{count} avaliações" if count != 1 else "1 avaliação",
                "surfaceUrl": "https://www.google.com/maps/place/teste",
            },
            "reviews": [],
        }

    def review(self, n):
        return {
            "author": f"Pessoa {n}",
            "rating": 5,
            "text": f"Avaliação real de teste {n}",
            "dateLabel": "há um mês",
            "source": "google_maps",
            "placeIdOrCid": "cid:test",
        }

    def test_three_verified_reviews_require_display(self):
        data = self.base()
        data["reviews"] = [self.review(1), self.review(2), self.review(3)]
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.VERIFIED_STRONG)
        self.assertTrue(result.carousel_required)
        self.assertTrue(result.pass_for_carousel)
        self.assertTrue(result.pass_for_publish)

    def test_many_ratings_but_too_few_text_reviews_blocks_publish(self):
        data = self.base(count=12)
        data["reviews"] = [self.review(1)]
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.COLLECTION_INCOMPLETE)
        self.assertFalse(result.pass_for_publish)
        self.assertTrue(any("Collection is incomplete" in x for x in result.errors))

    def test_one_rating_can_be_aggregate_only(self):
        data = self.base(count=1)
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.VERIFIED_AGGREGATE_ONLY)
        self.assertTrue(result.pass_for_publish)

    def test_direct_maps_surface_is_mandatory(self):
        data = self.base(count=1)
        data["sourceSurface"] = "google_search_snippet"
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.PROFILE_CONFLICT)
        self.assertFalse(result.pass_for_publish)
        self.assertTrue(any("direct_google_maps" in x for x in result.errors))

    def test_profile_header_raw_count_must_match_structured_count(self):
        data = self.base(count=1)
        data["aggregateObservation"]["countText"] = "12 avaliações"
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.PROFILE_CONFLICT)
        self.assertFalse(result.pass_for_publish)
        self.assertTrue(any("does not match direct Maps header" in x for x in result.errors))

    def test_newer_operator_direct_maps_observation_forces_recollection(self):
        data = self.base(count=1)
        data["operatorObservation"] = {
            "sourceSurface": "direct_google_maps",
            "aggregateRating": 5.0,
            "reviewCount": 12,
            "observedAt": "2026-08-31T17:30:00-03:00",
            "profileUrl": "https://www.google.com/maps/place/teste",
        }
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.PROFILE_CONFLICT)
        self.assertFalse(result.pass_for_publish)
        self.assertTrue(any("reports reviewCount=12" in x for x in result.errors))

    def test_older_operator_observation_does_not_override_newer_collection(self):
        data = self.base(count=12)
        data["reviews"] = [self.review(1), self.review(2), self.review(3)]
        data["operatorObservation"] = {
            "sourceSurface": "direct_google_maps",
            "aggregateRating": 5.0,
            "reviewCount": 1,
            "observedAt": "2026-08-30T12:00:00-03:00",
        }
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.VERIFIED_STRONG)
        self.assertTrue(result.pass_for_publish)

    def test_reviews_panel_must_be_opened_when_count_positive(self):
        data = self.base(count=12)
        data["reviewsPanelOpened"] = False
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.PROFILE_CONFLICT)
        self.assertFalse(result.pass_for_publish)

    def test_review_from_wrong_profile_is_not_counted(self):
        data = self.base(count=12)
        wrong = self.review(1)
        wrong["placeIdOrCid"] = "cid:other"
        data["reviews"] = [wrong, self.review(2), self.review(3)]
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.COLLECTION_INCOMPLETE)
        self.assertEqual(result.verified_review_count, 2)

    def test_duplicate_reviews_do_not_satisfy_minimum(self):
        data = self.base(count=12)
        r = self.review(1)
        data["reviews"] = [r, dict(r), self.review(2)]
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.COLLECTION_INCOMPLETE)
        self.assertEqual(result.verified_review_count, 2)

    def test_public_copy_neutrality_passes_clean_html(self):
        clean_html = """
        <nav><a href="#avaliacoes">Avaliações</a></nav>
        <section class="reviews-section" id="avaliacoes" aria-label="Avaliações">
            <h2>Avaliações</h2>
            <div class="aggregate-score">5,0</div>
            <div><strong>36 avaliações</strong></div>
            <div class="review-card">
                <p>"Ótimo atendimento!"</p>
                <div class="review-provenance" aria-label="Origem da avaliação">
                    <svg viewBox="0 0 24 24"><path fill="#4285F4" d="M12 2..."></path></svg>
                </div>
            </div>
        </section>
        """
        self.assertEqual(mod.validate_reviews_public_copy(clean_html), [])

    def test_public_copy_neutrality_rejects_branded_phrases_and_count_labels(self):
        bad_samples = [
            '<section id="avaliacoes"><h2>Avaliações no Google</h2></section>',
            '<section id="avaliacoes"><h2>Google Reviews</h2></section>',
            '<section id="avaliacoes"><div>36 avaliações no Google Meu Negócio</div></section>',
            '<section id="avaliacoes"><h2>O que dizem no Google</h2></section>',
            '<section id="avaliacoes"><div>1 avaliação Google</div></section>',
            '<nav><a href="#avaliacoes">Avaliações no Google</a></nav><section id="avaliacoes"><h2>Depoimentos</h2></section>',
        ]
        for bad in bad_samples:
            self.assertTrue(mod.validate_reviews_public_copy(bad), f"Expected violation for: {bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
