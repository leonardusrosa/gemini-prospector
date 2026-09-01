---
name: autonomous-site-review
instruction_language: en
description: Mandatory fail-closed quality gate after creating or changing any Prospector site, concept, or redesign and before screenshot approval, deploy, proposal, or outreach. It must independently detect missing gpt-taste usage, hero visual defects, motion/scroll omissions, WhatsApp/social/map issues, fixed-control conflicts, reduced-motion/no-JS failures, factual regressions, review-provenance failures, and visual regressions.
---

# Autonomous Site Review

This skill is a hard quality barrier, not an optional checklist. A site cannot be marked Core QA PASS merely because the implementing agent reports that it passed.

## Repository policy and precedence

Read and obey, in order:

1. `../repository-policy/SKILL.md`
2. `../website-core-rules/SKILL.md`
3. `../redesign-premium/SKILL.md`
4. `../hero-visual-rule/SKILL.md`
5. `../google-reviews-verification/SKILL.md` when a Google Business Profile exists or may exist
6. the current installed `gpt-taste/SKILL.md`

All new or materially modified repository rules, gate descriptions, regression names/comments, and agent-facing rule documentation must be written in English. Client-facing copy remains in the target market language.

## 1. HARD GATE: prove current gpt-taste usage

Before any visual creation, redesign, or rework:

- read the current `gpt-taste/SKILL.md` from disk;
- do not work from memory;
- record its real path and SHA-256 in `sites/[slug]/design-read.md`;
- record the current design dials.

Minimum evidence:

```text
GPT_TASTE_READ: PASS
GPT_TASTE_PATH: <real path>
GPT_TASTE_SHA256: <sha256 of the file read>
Design Variance: <0-10>
Motion: <0-10>
Density: <0-10>
```

The validator must compare the recorded hash with the current file. A textual `PASS` alone is insufficient.

`scroll-behavior: smooth` does not count as a Motion & Behavior Pass.

## 2. HARD GATE: meaningful hero visual

Every first-version site, concept, and redesign requires a meaningful hero image unless the operator explicitly requests a text-only exception.

Selection order:

1. verified real expert photo;
2. verified first-party business/context image;
3. user-provided image;
4. canonical niche expert-placeholder template;
5. honest contextual illustrative image.

Required structural hook:

```html
<section data-role="hero">
  <img data-role="hero-image" ...>
</section>
```

Rules:

- non-empty factual `src` and `alt`;
- critical hero image is not lazy-loaded;
- illustrative/stock/generated imagery uses honest provenance and must not pretend to show the real expert or facility;
- canonical expert-placeholder templates must follow the current hero-template manifest and frame policy;
- missing expert photography is never a reason to omit the hero visual.

## 3. HARD GATE: motion and behavior

Prospect/redesign sites default to `Motion > 0` unless an explicit documented exception exists.

Verify actual behavior:

- header state changes on scroll when appropriate;
- short hero entry/reveal when motion is enabled;
- at least two meaningful reveal/behavior groups when the page has enough content;
- functional microinteractions;
- no-JS content remains visible;
- `prefers-reduced-motion` is respected;
- no scroll-jacking, gratuitous loops, or ornamental motion overload.

## 4. HARD GATE: WhatsApp conversion points

When verified WhatsApp is an appropriate contact channel:

- keep a functional primary CTA;
- keep a functional contact-area action;
- use only the verified destination;
- never invent a second number or alternate destination.

### Assistant absent

If no persistent assistant exists, a synchronized floating WhatsApp action is required by default after the primary hero CTA leaves the viewport:

```html
<a data-role="floating-whatsapp" ...>...</a>
```

Do not show the floating WhatsApp while the hero CTA is already visible.

### Assistant present: fixed-control exclusivity

If an AI assistant launcher is present, the assistant becomes the ONLY persistent fixed bottom conversion launcher.

Required:

```html
<div data-role="assistant-launcher">...</div>
```

Forbidden on the same page:

```html
<a data-role="floating-whatsapp">...</a>
```

WhatsApp must still remain available through normal page CTAs and assistant escalation/handoff.

## 5. HARD GATE: Instagram/social affordance in prospect mockups

For noindex prospect concepts, represent Instagram UI even when an official profile is not verified.

Verified profile: active verified link only.

Unverified profile: visual affordance only, `aria-disabled="true"`, no `href`, no invented URL/handle, non-navigable.

## 6. HARD GATE: embedded map

A verified public customer-facing physical address requires an embedded map preview by default. A decorative location card alone does not satisfy the gate.

## 7. HARD GATE: Google Reviews provenance, completeness, and rendering

Every first-version local-business concept must explicitly verify the correct Google Business Profile and obey `google-reviews-verification`.

Review QA has four independent dimensions:

```text
REVIEW SOURCE PROVENANCE
REVIEW FINGERPRINT INTEGRITY
REVIEW TRAVERSAL COMPLETENESS
REVIEW PUBLIC BINDING
```

All four must PASS.

A cryptographic fingerprint is not source provenance. A valid SHA-256 over fabricated author/date metadata remains a hard FAIL.

### Source-observed metadata rule

Every factual review/rating field must be directly observed from the source or be `null`.

Never create surrogate values to satisfy schema/layout, including:

- `Paciente Verificado #1` or numbered variants;
- `Reviewer #1`;
- `Cliente #1`;
- `Anonymous #1`;
- invented date/date labels;
- inferred patient/client status.

If Google Maps does not expose an author or date, use `null` and omit it publicly.

Preserve native Google review IDs whenever available. Missing source IDs must not be replaced with generated identities.

### Canonical states

- `VERIFIED_STRONG`: complete traversal + at least 3 verified same-place Google text reviews.
- `VERIFIED_TEXT_LIMITED`: complete traversal + exactly 1 or 2 verified same-place Google text reviews.
- `VERIFIED_AGGREGATE_ONLY`: complete traversal + zero Google text reviews and a verified aggregate.
- `COLLECTION_INCOMPLETE`: incomplete traversal/provenance/reconciliation/binding => BLOCK.
- `PROFILE_CONFLICT`: BLOCK.
- verified profile with exactly 0 ratings/reviews: section may be omitted when recorded truthfully.

Do not infer text-review count from aggregate rating count.

When an all-reviews carousel is used, every carousel item must bind to one canonical `observedEntries[]` record. Text items must additionally bind to exact verified text evidence. Star-only items must not receive invented quotes, authors, dates, or reviewer status.

Public copy must not call reviewers patients/clients unless that relationship is explicitly verified by source evidence.

## 8. HARD GATE: factual traceability

Public claims, verified-service lists, design-read claims, and assistant knowledge must derive from a verified factual allowlist/evidence inventory.

Do not rely on a blacklist of previously observed hallucinations. A new unsupported service or claim must fail even if its wording has never appeared before.

## 9. Two-layer review

### Layer A: deterministic/static

Run all applicable static gates, including:

```bash
python prospector-de-sites/autonomous_site_review.py \
  --html sites/[slug]/[slug].html \
  --design-read sites/[slug]/design-read.md \
  --manifest sites/[slug]/review-manifest.json

python prospector-de-sites/fixed_conversion_controls_review.py \
  --html sites/[slug]/[slug].html

python prospector-de-sites/google_reviews_evidence.py \
  sites/[slug]/review-manifest.json \
  --html sites/[slug]/[slug].html
```

Any non-zero result blocks Static Review PASS.

### Layer B: browser/visual

Run the browser QA and test at least desktop 1440x900, tablet 800x1024, mobile 390x844, plus any hero-specific viewport.

If an assistant is present, verify no floating WhatsApp launcher exists.

If reviews are rendered, browser QA must verify visible aggregate/count, actual review item count, evidence bindings, zero synthetic reviewer metadata, and zero unsupported reviewer-status attribution.

## 10. Required review manifest

The manifest records observed QA/evidence state, not convenient values chosen to make tests pass.

For review evidence, `observedEntries[]` must be a real source inventory. Declared counts without corresponding entries are not proof of traversal.

## 11. Mandatory adversarial review

After the first PASS, perform a second review whose purpose is to fail the page.

Ask:

> If I were trying to reject this page, what permanent requirement could the implementing agent have skipped while still producing something that looks plausible?

Inspect especially:

- stale or fake gpt-taste proof;
- incorrect hero/frame behavior;
- generated imagery presented as factual;
- assistant and floating WhatsApp both present;
- reduced-motion/no-JS failures;
- Google review numbers/copy not matching evidence;
- traversal counts declared without source entries;
- fabricated reviewer names/dates hidden behind valid hashes;
- synthetic placeholder identities;
- unsupported patient/client attribution;
- missing native review IDs that were available during collection;
- unsupported factual claims;
- console/network failures.

## 12. No self-approval by written checklist

A report written by the implementing agent is not sufficient evidence. PASS requires observable proof from deterministic gates, source evidence, browser QA, and deployment checks.

## 13. Final gate report

Use this output block:

```text
AUTONOMOUS SITE REVIEW
GPT_TASTE_READ: PASS/FAIL
GPT_TASTE_SHA_MATCH: PASS/FAIL
STATIC REVIEW: PASS/FAIL
BROWSER REVIEW: PASS/FAIL
ADVERSARIAL REVIEW: PASS/FAIL
HERO IMAGE: PASS/FAIL
HERO FRAME/CROP: PASS/FAIL/N/A
MOTION: PASS/FAIL
WHATSAPP: PASS/FAIL/N/A
ASSISTANT: PASS/FAIL/N/A
FIXED CONTROL EXCLUSIVITY: PASS/FAIL/N/A
INSTAGRAM UI: PASS/FAIL/N/A
MAP EMBED: PASS/FAIL/N/A
GOOGLE REVIEWS: PASS/FAIL/N/A
REVIEW SOURCE PROVENANCE: PASS/FAIL/N/A
REVIEW FINGERPRINT INTEGRITY: PASS/FAIL/N/A
REVIEW TRAVERSAL COMPLETENESS: PASS/FAIL/N/A
REVIEW PUBLIC BINDING: PASS/FAIL/N/A
SYNTHETIC REVIEW METADATA: 0/<n>
FACTUAL TRACEABILITY: PASS/FAIL
REDUCED MOTION: PASS/FAIL
NO-JS: PASS/FAIL
DESKTOP: PASS/FAIL
TABLET: PASS/FAIL
MOBILE: PASS/FAIL
CONSOLE/NETWORK: PASS/FAIL

AUTONOMOUS_REVIEW_PASS: YES/NO
```

Deploy, proposal, or outreach may proceed only when `AUTONOMOUS_REVIEW_PASS: YES`.
