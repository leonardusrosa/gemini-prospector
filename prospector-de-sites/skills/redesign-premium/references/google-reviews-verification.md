# Google Reviews Verification Protocol

Use this protocol for every redesign or new local-business site when a plausible Google Business Profile / Google Maps listing exists.

The objective is to prevent ambiguous profile matches, stale aggregate values, incomplete traversal, fabricated review metadata, and public review UI that cannot be traced back to source evidence.

The canonical rule is `../../google-reviews-verification/SKILL.md`. This reference expands the implementation procedure and must not weaken that skill.

## 1. Identify the exact profile first

Before accepting any rating, count, author, date, or review text, verify the correct listing using as many anchors as available:

- public business/professional name;
- city and address;
- phone and official site;
- direct Google Maps URL;
- Place ID and/or CID.

Do not mix branches, professionals, old profiles, or homonymous businesses.

If identity remains uncertain, use `PROFILE_CONFLICT` and stop.

## 2. Current direct Maps evidence wins

For public rendering, the current direct Maps observation takes precedence over:

- CRM values;
- search snippets;
- old screenshots;
- local caches;
- prior JSON;
- prior successful QA reports.

Always record `collectedAt`.

An operator-supplied current Maps observation is a conflict trigger when it disagrees with stored evidence. Recollect before PASS.

## 3. Aggregate collection

From the exact profile, preserve:

- `aggregateRating`;
- `ratingCount`;
- profile identity;
- direct Maps URL;
- timestamp;
- raw visible header rating/count strings.

After opening the reviews panel, preserve the independently visible panel count as a second observation.

Both count observations must reconcile with the structured count.

## 4. Full panel traversal

For small profiles, traverse the complete available review/rating set.

Do not infer that total ratings equals textual reviews. Track every observed entry separately in `observedEntries[]`.

The collector should preserve the native `data-review-id` or equivalent source identifier whenever available.

Use unique source identities rather than DOM positions because Google Maps may virtualize/recycle list nodes.

## 5. Per-entry factual provenance

For every observed entry, preserve only values that were actually visible or available from Maps.

Preferred fields:

```json
{
  "nativeReviewId": "<actual source id or null>",
  "author": "<actual author or null>",
  "rating": 5,
  "dateLabel": "<actual label or null>",
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

If Maps does not expose a value, use `null`.

Never create a value to satisfy schema validation or visual composition.

Forbidden synthetic metadata includes patterns such as:

- `Paciente Verificado #1`;
- `Reviewer #2`;
- `Cliente #3`;
- `Anonymous #4`;
- invented relative dates;
- invented reviewer type/status.

A cryptographic hash does not establish provenance. It only verifies that the stored inputs have not changed.

## 6. Text reviews

For each textual review:

- expand `More` / `Mais` before capture when necessary;
- preserve author verbatim when visible;
- preserve individual star rating;
- preserve text verbatim;
- preserve date/date label exactly when visible;
- preserve native review ID when available;
- bind the review to the same Place ID/CID.

Do not rewrite, summarize, merge, or reconstruct missing review text.

## 7. Star-only ratings

A star-only rating is not a missing testimonial to be filled in.

For a star-only entry:

- `hasText=false`;
- `textEvidenceId=null`;
- public UI may show the observed stars and observed author/date;
- if author/date are unavailable, omit them;
- a neutral UI label such as `Avaliação sem comentário` is allowed;
- never invent reviewer identity, date, sentiment, treatment, recommendation, or patient status.

## 8. Canonical derived counts

After traversal, derive rather than independently author:

```text
observedRatingEntries = observedEntries.length
observedTextReviewEntries = count(hasText=true)
starOnlyRatingCount = count(hasText=false)
capturedTextReviewCount = valid same-place text evidence count
```

All declared counts must reconcile with the derived values.

## 9. Verification states

### `VERIFIED_STRONG`

Complete traversal plus at least 3 verified same-profile Google text reviews.

### `VERIFIED_TEXT_LIMITED`

Complete traversal plus exactly 1 or 2 verified same-profile Google text reviews.

### `VERIFIED_AGGREGATE_ONLY`

Complete traversal plus zero Google text reviews and a verified aggregate.

### `COLLECTION_INCOMPLETE`

Traversal, provenance, text capture, count reconciliation, or binding is incomplete. Publication is blocked.

### `PROFILE_CONFLICT`

Profile identity/provenance is unresolved. Publication is blocked.

### `NO_USABLE_REVIEWS`

The correctly identified profile has zero ratings/reviews.

Secondary review platforms are separate evidence and must never upgrade the Google-specific state.

## 10. Fingerprinting

Prefer fingerprints derived from:

1. Place ID + native Google review ID;
2. fallback observed fields only when no native ID is available.

Fallback fingerprint inputs may include observed author, rating, date label, and text hash. Never insert generated placeholders into fingerprint inputs.

Validate separately:

- source provenance;
- fingerprint integrity;
- traversal completeness;
- public binding.

## 11. Public presentation

Use source-neutral review-section copy. The section should look native to the client's website rather than like a copied Google widget.

Do not use branded labels such as:

- `Google Reviews`;
- `Avaliações no Google`;
- `12 avaliações Google`.

Neutral aggregate copy such as `5,0 · 12 avaliações` is appropriate.

A small provenance icon may be used when consistent with current design rules.

Never call reviewers `patients`, `clients`, or another relationship category unless explicit evidence supports that status.

## 12. All-reviews carousel

When the chosen UX represents all observed rating/review entries:

- `data-review-total-items` must equal `observedEntries.length`;
- every slide must bind to exactly one observed-entry fingerprint;
- every text slide must also bind to its exact `textEvidenceId`;
- no duplicate fingerprints;
- no orphan slides;
- no fabricated metadata to make star-only cards look more complete.

Use user-controlled navigation only. No forced auto-rotation.

## 13. Build gate

Before deploy, require explicit PASS for:

```text
REVIEW SOURCE PROVENANCE
REVIEW FINGERPRINT INTEGRITY
REVIEW TRAVERSAL COMPLETENESS
REVIEW PUBLIC BINDING
SYNTHETIC REVIEW METADATA = 0
```

Any uncertainty is a BLOCK, not a reason to generate plausible data.

## 14. Required regressions

At minimum regress:

- stale aggregate count;
- mismatched profile header/panel count;
- declared traversal count greater than entry inventory;
- duplicate native review ID or fingerprint;
- text entry without exact text evidence binding;
- star-only entry with generated review text;
- synthetic author such as `Paciente Verificado #1` with an otherwise valid SHA-256 fingerprint;
- non-null author/date marked as not observed;
- null author/date with real native review ID accepted;
- public `patient/client` attribution without explicit source support.

Do not weaken regressions to make a tenant pass.

## 15. Outreach separation

Verified review evidence for the public page does not automatically authorize using ratings, counts, or quotes in cold outreach. Outreach rules remain independent.
