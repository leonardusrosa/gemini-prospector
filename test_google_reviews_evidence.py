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
    def base(self):
        return {
            "profileName": "Negócio Teste",
            "profileUrl": "https://www.google.com/maps/place/teste",
            "placeIdOrCid": "cid:test",
            "aggregateRating": 5.0,
            "reviewCount": 36,
            "collectedAt": "2026-08-30T15:00:00-03:00",
            "reviews": [],
        }

    def review(self, n):
        return {
            "author": f"Pessoa {n}",
            "rating": 5,
            "text": f"Avaliação real de teste {n}",
            "dateLabel": "há um mês",
        }

    def test_three_verified_reviews_require_carousel(self):
        data = self.base()
        data["reviews"] = [self.review(1), self.review(2), self.review(3)]
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.VERIFIED_STRONG)
        self.assertTrue(result.carousel_required)
        self.assertTrue(result.pass_for_carousel)

    def test_aggregate_only_is_blocker_not_silent_omit(self):
        data = self.base()
        data["reviews"] = [self.review(1)]
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.VERIFIED_AGGREGATE_ONLY)
        self.assertFalse(result.carousel_required)
        self.assertFalse(result.pass_for_carousel)
        self.assertTrue(any("Do not silently omit" in x for x in result.warnings))

    def test_profile_identity_is_required(self):
        data = self.base()
        data["profileUrl"] = ""
        data["placeIdOrCid"] = ""
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.PROFILE_CONFLICT)
        self.assertTrue(result.errors)

    def test_conflict_fails_closed(self):
        data = self.base()
        data["profileConflict"] = True
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.PROFILE_CONFLICT)
        self.assertFalse(result.carousel_required)

    def test_duplicate_reviews_do_not_satisfy_minimum(self):
        data = self.base()
        r = self.review(1)
        data["reviews"] = [r, dict(r), self.review(2)]
        result = mod.validate_evidence(data)
        self.assertEqual(result.status, mod.VERIFIED_AGGREGATE_ONLY)
        self.assertEqual(result.verified_review_count, 2)

    def test_public_copy_neutrality_passes_clean_html(self):
        clean_html = """
        <nav><a href="#avaliacoes">Avaliações</a></nav>
        <section class="reviews-section" id="avaliacoes" aria-label="Avaliações de pacientes">
            <h2>O que nossos pacientes dizem</h2>
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
        violations = mod.validate_reviews_public_copy(clean_html)
        self.assertEqual(violations, [])

    def test_public_copy_neutrality_rejects_forbidden_phrases(self):
        bad_samples = [
            '<section id="avaliacoes"><h2>Avaliações no Google</h2></section>',
            '<section id="avaliacoes"><h2>Google Reviews</h2></section>',
            '<section id="avaliacoes"><div>36 avaliações no Google Meu Negócio</div></section>',
            '<section id="avaliacoes"><h2>O que dizem no Google</h2></section>',
            '<nav><a href="#avaliacoes">Avaliações no Google</a></nav><section id="avaliacoes"><h2>Depoimentos</h2></section>',
        ]
        for bad in bad_samples:
            violations = mod.validate_reviews_public_copy(bad)
            self.assertTrue(len(violations) > 0, f"Expected violation for: {bad}")

    def test_public_copy_neutrality_allows_svg_and_internal_classes(self):
        html_with_internals = """
        <!-- Google Reviews Carousel Section -->
        <section class="reviews-section review-google-badge" id="avaliacoes" aria-label="Avaliações de pacientes">
            <h2>Depoimentos de pacientes</h2>
            <div class="review-card">
                <p>Excelente</p>
                <div class="review-google-badge">
                    <svg><path d="M..."></path></svg>
                </div>
            </div>
        </section>
        """
        violations = mod.validate_reviews_public_copy(html_with_internals)
        self.assertEqual(violations, [])

    def test_instituto_ferreira_public_html_passes_neutrality_gate(self):
        instituto_html_path = ROOT / "sites" / "instituto-ferreira-odontologia-rio-claro" / "instituto-ferreira-odontologia-rio-claro.html"
        if instituto_html_path.is_file():
            violations = mod.validate_reviews_public_copy(instituto_html_path.read_text(encoding="utf-8"))
            self.assertEqual(violations, [], f"Violations found in Instituto HTML: {violations}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
