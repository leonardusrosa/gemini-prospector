#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = ROOT / "prospector-de-sites" / "google_reviews_evidence.py"
SPEC = importlib.util.spec_from_file_location("google_reviews_evidence", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
