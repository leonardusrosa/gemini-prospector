---
name: google-reviews-verification
instruction_language: en
description: Mandatory fail-closed Google Reviews evidence gate for every Prospector local-business site, redesign, concept, or public QA when a Google Business Profile / Google Maps listing exists or may exist.
---

# Google Reviews Verification

This skill is mandatory together with `website-core-rules`, `redesign-premium`, and `autonomous-site-review` whenever the lead has or may have a Google Business Profile.

Read the detailed protocol in:

`../redesign-premium/references/google-reviews-verification.md`

Validate the evidence record with:

```bash
python prospector-de-sites/google_reviews_evidence.py <evidence.json> --html <site.html>
```

A written agent report is not evidence. The current direct Maps observation, deterministic validator, and browser verification are authoritative.

## 1. Canonical source precedence

For aggregate rating and public rating/review count, source precedence is:

1. the exact live Google Maps place profile;
2. the live place header and live reviews panel for that same profile;
3. other Google surfaces only as corroboration.

Never let CRM data, cached snippets, search-result summaries, old screenshots, stale JSON, or the number of captured text reviews override the direct Maps place profile.

If direct Maps disagrees with any cached or secondary observation, the cached observation becomes stale and publication is blocked until the active evidence is recollected.

## 2. Required direct-Maps evidence contract

Active publishable evidence must include all of the following:

```json
{
  "profileName": "...",
  "profileUrl": "https://www.google.../maps/place/...",
  "placeIdOrCid": "...",
  "aggregateRating": 5.0,
  "reviewCount": 12,
  "collectedAt": "<ISO-8601>",
  "sourceSurface": "direct_google_maps",
  "collectionMethod": "playwright_direct_maps",
  "profileHeaderObserved": true,
  "reviewsPanelOpened": true,
  "textReviewCollectionAttempted": true,
  "aggregateObservation": {
    "ratingText": "5,0",
    "countText": "12 avaliações",
    "surfaceUrl": "https://www.google.../maps/place/..."
  },
  "reviews": []
}
```

`collectionMethod` may also be `browser_direct_maps` or `manual_direct_maps` when that truthfully describes the collection pass.

The raw header strings are mandatory because they create a second independent check against structured values. The validator must reject `reviewCount=1` when the preserved direct Maps header says `12 avaliações`.

## 3. Exact profile identity

Before trusting rating, count, or review text, establish the exact listing using multiple identity anchors where available:

- business/professional name;
- city and address;
- canonical phone;
- official site if present;
- Place ID and/or CID.

A review captured from another listing must never count toward the minimum review threshold.

Every captured review must preserve:

```json
{
  "author": "...",
  "rating": 5,
  "text": "...",
  "dateLabel": "...",
  "source": "google_maps",
  "placeIdOrCid": "<same active profile id>"
}
```

## 4. Mandatory reviews-panel collection

When `reviewCount > 0`:

- open the actual reviews panel;
- attempt text-review collection;
- expand truncated review text before capturing it;
- scroll/load sufficiently to obtain the usable review set;
- keep star-only ratings separate from text reviews.

Do not infer that `reviewCount` equals the number of usable text reviews.

## 5. Fail-closed classification

### `VERIFIED_STRONG`

The exact direct Maps profile is verified, aggregate/count are current, and at least 3 same-profile text reviews are captured and verified.

Result:

```text
REVIEW DISPLAY REQUIRED: YES
GOOGLE REVIEWS QA: PASS
```

Use 4 to 6 verified review cards when available; minimum 3.

### `VERIFIED_AGGREGATE_ONLY`

This state is allowed only when the direct Maps profile itself reports fewer than 3 total ratings/reviews and there are not enough usable text reviews to reach the display minimum.

Render only what is verified. Never fabricate text.

### `COLLECTION_INCOMPLETE`

If direct Maps reports 3 or more ratings/reviews but fewer than 3 verified text reviews were captured, this is a collection failure, not a valid aggregate-only PASS.

Result:

```text
GOOGLE REVIEWS QA: BLOCKED
```

Continue collection or request human evidence. Never downgrade to aggregate-only merely because scraping/browser collection failed.

### `PROFILE_CONFLICT`

Any unresolved identity/provenance/count/rating conflict blocks publication.

### `NO_USABLE_REVIEWS`

Only valid when the correctly identified direct Maps profile has zero ratings/reviews.

Never use this state as a fallback for failed collection.

## 6. Operator-supplied direct Maps observations

If the operator supplies a current direct Maps URL, screenshot, rating, or review count that conflicts with stored evidence, treat that as a conflict trigger.

Record it as `operatorObservation` with an observation timestamp. If it is newer than or equal to the active evidence and the rating/count differs:

- mark the active evidence stale;
- recollect the exact direct Maps profile;
- block PASS until the conflict is reconciled.

Do not dismiss the operator observation because older cached evidence previously passed QA.

## 7. Freshness and stale-state rule

Google review count is mutable public data.

A previous successful collection does not freeze the value indefinitely. For first-version generation, review refreshes, or when a current conflicting observation is supplied, collect the live direct Maps state again.

Historical evidence may be retained only if explicitly marked stale/superseded. Contradictory active evidence is forbidden.

## 8. Evidence to DOM binding

The rendered site must match the active evidence exactly.

At minimum the review section must expose deterministic hooks such as:

```html
<section
  data-role="reviews"
  data-review-rating="5.0"
  data-review-count="12"
>
```

Browser QA must verify both the attributes and the visible user-facing values.

It is not sufficient for `data-review-count="12"` to be correct while visible copy still says `1 avaliação`.

Any visible count that disagrees with the active direct Maps evidence is a hard FAIL.

## 9. Public source-neutral presentation

Google is provenance, not the main public message.

In the public reviews UI:

- do not use `Google Reviews`, `Avaliações no Google`, `O que dizem no Google`, `Veja nossas avaliações no Google`, or equivalent branded headings/labels;
- do not display labels such as `1 avaliação Google` or `12 avaliações Google`;
- use natural neutral copy such as `Avaliações`, `5,0`, `12 avaliações`;
- a small Google logo/icon may be used discretely for provenance;
- do not simulate official Google widget chrome;
- keep full provenance in the internal evidence record.

## 10. Review-card rendering

For `VERIFIED_STRONG`, every public review card must map to an exact evidence object. Do not invent, merge, paraphrase-as-verbatim, or mix reviews from different profiles.

When review lengths vary significantly, prefer an accessible masonry/Pinterest-style layout:

- 3 columns desktop;
- 2 columns tablet;
- 1 column mobile;
- intrinsic card heights;
- consistent gaps;
- DOM order remains the reading order;
- no fixed equal-height cards;
- no clipping/truncation merely to equalize cards;
- resize/font loading/expansion must recalculate cleanly.

A carousel remains allowed when review lengths are similar and horizontal browsing is genuinely useful.

## 11. Mandatory adversarial check

Before final PASS, explicitly ask:

> Does the exact live Google Maps place profile currently show a different aggregate rating or review count than the evidence and public page?

If yes or uncertain: BLOCK.

Also check:

- wrong listing/CID;
- stale cached count;
- count accidentally taken from an individual review element;
- profile header not fully loaded;
- reviews panel never opened;
- locale-dependent selector error;
- captured text reviews from another listing;
- visible site count differing from evidence attributes.

## 12. Required report

```text
GOOGLE PROFILE IDENTIFIED: PASS/FAIL
DIRECT MAPS SOURCE: PASS/FAIL
PROFILE HEADER OBSERVED: PASS/FAIL
REVIEWS PANEL OPENED: PASS/FAIL
TEXT REVIEW COLLECTION ATTEMPTED: PASS/FAIL
AGGREGATE CURRENTLY VERIFIED: PASS/FAIL
AGGREGATE RATING: <value>
REVIEW COUNT: <value>
VERIFIED TEXT REVIEWS: <n>
GOOGLE REVIEWS STATUS: VERIFIED_STRONG / VERIFIED_AGGREGATE_ONLY / COLLECTION_INCOMPLETE / PROFILE_CONFLICT / NO_USABLE_REVIEWS
VISIBLE SITE COUNT MATCHES EVIDENCE: PASS/FAIL
GOOGLE REVIEWS QA: PASS/BLOCKED
```

No deploy, proposal, or outreach PASS may rely on review evidence that fails this contract.
