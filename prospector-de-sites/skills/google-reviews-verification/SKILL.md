---
name: google-reviews-verification
instruction_language: en
description: Mandatory fail-closed Google Reviews evidence gate for every Prospector local-business site, redesign, concept, or public QA when a Google Business Profile / Google Maps listing exists or may exist.
---

# Google Reviews Verification

This skill is mandatory together with `repository-policy`, `website-core-rules`, `redesign-premium`, and `autonomous-site-review` whenever the lead has or may have a Google Business Profile.

Read the detailed protocol in:

`../redesign-premium/references/google-reviews-verification.md`

Validate evidence with:

```bash
python prospector-de-sites/google_reviews_evidence.py <evidence.json> --html <site.html>
```

A written agent report is not evidence. Direct Maps observations, source provenance, deterministic validation, and browser verification are authoritative.

## 1. Canonical source precedence

For aggregate rating, count, and individual review/rating entries, source precedence is:

1. the exact live Google Maps place profile;
2. the live profile header and opened reviews panel for that same profile;
3. other Google surfaces only as corroboration.

CRM values, cached snippets, search summaries, old screenshots, stale JSON, and prior PASS reports never override the current exact Maps profile.

If direct Maps disagrees with cached or secondary evidence, mark the cached evidence stale and BLOCK publication until recollection reconciles it.

## 2. Exact profile identity

Before trusting any rating, count, author, date, or review text, establish the exact listing using multiple anchors where available:

- business/professional name;
- city and address;
- canonical phone;
- official site;
- Place ID and/or CID.

Never mix reviews from different units, professionals, old profiles, or homonymous listings.

## 3. Required direct-Maps evidence

Publishable evidence must record the current direct Maps collection pass, including:

```json
{
  "profileName": "...",
  "profileUrl": "https://www.google.../maps/place/...",
  "placeId": "...",
  "cid": "...",
  "aggregateRating": 5.0,
  "ratingCount": 12,
  "collectedAt": "<ISO-8601>",
  "sourceSurface": "direct_google_maps",
  "collectionMethod": "playwright_direct_maps",
  "profileHeaderObserved": true,
  "reviewsPanelOpened": true,
  "reviewsPanelFullyTraversed": true,
  "textReviewCollectionAttempted": true,
  "aggregateObservation": {
    "ratingText": "5,0",
    "countText": "12 avaliações",
    "surfaceUrl": "https://www.google.../maps/place/..."
  },
  "reviewsPanelObservation": {
    "countText": "12 avaliações",
    "surfaceUrl": "https://www.google.../maps/place/..."
  },
  "reviews": [],
  "observedEntries": []
}
```

`collectionMethod` may be `playwright_direct_maps`, `browser_direct_maps`, or `manual_direct_maps` only when it truthfully describes the collection.

The header count and opened-panel count must independently match the structured rating count and the same Place ID/CID.

## 4. Complete traversal is evidence, not a declaration

When the site represents individual Google rating/review entries, `observedEntries[]` is the canonical traversal inventory.

Do not trust a standalone declaration such as `observedRatingEntries: 12` without 12 corresponding observed-entry records.

Derived values are:

```text
observedRatingEntries = observedEntries.length
observedTextReviewEntries = count(hasText == true)
starOnlyRatingCount = count(hasText == false)
capturedTextReviewCount = count(valid same-place googleReviews.reviews)
```

All declared values must equal the derived values. Duplicate fingerprints or duplicate native review IDs are a hard FAIL.

## 5. Source-observed metadata only

Every factual field in an observed entry must come directly from the source or be `null`.

Preferred record:

```json
{
  "fingerprint": "...",
  "fingerprintVersion": "maps-native-id-v1",
  "nativeReviewId": "<actual Maps review id or null>",
  "author": "<exact observed author or null>",
  "rating": 5,
  "dateLabel": "<exact observed date label or null>",
  "hasText": false,
  "textEvidenceId": null,
  "sourceSurface": "direct_google_maps",
  "collectedAt": "<ISO-8601>",
  "provenance": {
    "authorObserved": true,
    "ratingObserved": true,
    "dateLabelObserved": true
  }
}
```

Hard rules:

- preserve `nativeReviewId` whenever Maps exposes it;
- preserve author verbatim only when observed;
- preserve date/date label verbatim only when observed;
- preserve rating only when observed;
- preserve review text verbatim only when observed;
- if author is unavailable, use `null`;
- if date is unavailable, use `null`;
- never invent a surrogate author to satisfy schema/layout;
- never invent a plausible date;
- never replace unavailable evidence with synthetic labels.

Forbidden examples include, but are not limited to:

- `Paciente Verificado #1`
- `Paciente Verificado #7`
- `Reviewer #2`
- `Cliente #3`
- `Anonymous #4`
- `Paciente 1`

A valid cryptographic fingerprint over fabricated metadata is still fabricated metadata and MUST BLOCK.

## 6. Fingerprint integrity is not provenance

Fingerprints protect integrity after collection; they do not establish that the input values were actually observed.

Validation must report four independent dimensions:

```text
REVIEW SOURCE PROVENANCE
REVIEW FINGERPRINT INTEGRITY
REVIEW TRAVERSAL COMPLETENESS
REVIEW PUBLIC BINDING
```

All four must PASS.

When `nativeReviewId` is available, prefer a fingerprint derived from the same Place ID plus the native review ID. Fallback fingerprints may use observed fields only. Never hash generated placeholders.

## 7. Text-evidence binding

For every `observedEntries[]` item with `hasText=true`:

- `textEvidenceId` is mandatory;
- it must resolve to a verified same-place item in `googleReviews.reviews[]`;
- author, rating, date label, and text must match the observed/source evidence where present.

For `hasText=false`:

- `textEvidenceId` must be `null`;
- no quote, summary, sentiment, treatment, or recommendation text may be generated.

## 8. Canonical states

State depends on complete traversal, not aggregate count alone.

### `VERIFIED_STRONG`

Complete direct-Maps traversal and at least 3 verified same-profile text reviews.

### `VERIFIED_TEXT_LIMITED`

Complete direct-Maps traversal and exactly 1 or 2 verified same-profile text reviews.

### `VERIFIED_AGGREGATE_ONLY`

Complete direct-Maps traversal and zero text reviews, with a verified aggregate.

### `COLLECTION_INCOMPLETE`

Any required traversal, provenance, count reconciliation, text capture, or evidence binding is incomplete. BLOCK.

### `PROFILE_CONFLICT`

Identity/provenance conflict. BLOCK.

### `NO_USABLE_REVIEWS`

The correctly identified profile has zero ratings/reviews.

Secondary sources may be retained separately but must never upgrade the Google-specific state.

## 9. Operator conflict rule

If the operator supplies a current direct Maps URL, screenshot, rating, count, or other observation that conflicts with stored evidence:

- mark stored evidence stale;
- recollect the exact profile;
- BLOCK until reconciled.

Never dismiss a newer direct observation because older evidence previously passed.

## 10. Evidence-to-DOM binding

Public output must match active evidence exactly.

At minimum:

```html
<section
  data-role="reviews"
  data-review-rating="5.0"
  data-review-count="12"
>
```

If an all-reviews carousel is used:

```html
<div data-role="reviews-carousel" data-review-total-items="12">
  <article
    data-role="review-carousel-item"
    data-review-entry-fingerprint="..."
  >...</article>
</div>
```

Every carousel item must bind to one `observedEntries[]` record. Text items must additionally bind to their exact `textEvidenceId`.

A page that renders 2 items from 12 observed entries while claiming an all-reviews carousel is a FAIL.

## 11. Public wording and reviewer status

Google is provenance, not the main public message.

Do not use branded count labels such as `12 avaliações Google` in the review section. Neutral copy such as `Avaliações`, `5,0`, and `12 avaliações` is preferred.

Do not call reviewers `patients`, `clients`, or equivalent merely because they left a Google review. Reviewer status is a separate factual claim and requires explicit source support.

For a star-only entry with no observed author/date, omit those fields in the public card. Do not display generated placeholders.

## 12. Public rendering

For text reviews, render exact verified text only. Do not invent, merge, paraphrase-as-verbatim, or mix profiles.

For star-only ratings, render only observed factual metadata plus a neutral label such as `Avaliação sem comentário` when appropriate. The neutral label describes the absence of review text; it must not imply patient verification.

Carousel, grid, or masonry may be chosen based on the verified content and UX, but no visual requirement may justify inventing missing factual metadata.

## 13. Mandatory adversarial check

Before final PASS, ask:

> Could any review author, date, rating, text, reviewer status, or count have been generated to make the schema, layout, or gate pass rather than observed from the source?

If yes or uncertain: BLOCK.

Also check:

- wrong listing/CID;
- stale count;
- count captured from an individual review element;
- reviews panel never opened;
- traversal count declared without entry inventory;
- duplicate native review ID/fingerprint;
- missing native review IDs that the collector actually observed;
- synthetic author/date placeholders;
- valid hash over fabricated metadata;
- public reviewer/patient attribution unsupported by evidence;
- visible public values disagreeing with evidence.

## 14. Required report

```text
GOOGLE PROFILE IDENTIFIED: PASS/FAIL
DIRECT MAPS SOURCE: PASS/FAIL
PROFILE HEADER OBSERVED: PASS/FAIL
REVIEWS PANEL OPENED: PASS/FAIL
REVIEWS PANEL FULLY TRAVERSED: PASS/FAIL
AGGREGATE RATING: <value>
RATING COUNT: <value>
OBSERVED ENTRIES: <n>
UNIQUE NATIVE REVIEW IDS: <n>
VERIFIED TEXT REVIEWS: <n>
STAR-ONLY RATINGS: <n>
ENTRIES WITH AUTHOR=NULL: <n>
ENTRIES WITH DATE=NULL: <n>
SYNTHETIC REVIEW METADATA: 0/<n>
REVIEW SOURCE PROVENANCE: PASS/FAIL
REVIEW FINGERPRINT INTEGRITY: PASS/FAIL
REVIEW TRAVERSAL COMPLETENESS: PASS/FAIL
REVIEW PUBLIC BINDING: PASS/FAIL
GOOGLE REVIEWS STATUS: VERIFIED_STRONG / VERIFIED_TEXT_LIMITED / VERIFIED_AGGREGATE_ONLY / COLLECTION_INCOMPLETE / PROFILE_CONFLICT / NO_USABLE_REVIEWS
GOOGLE REVIEWS QA: PASS/BLOCKED
```

No deploy, proposal, or outreach PASS may rely on review evidence that fails this contract.
