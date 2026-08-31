---
name: autonomous-site-review
description: Mandatory fail-closed quality gate after creating or changing any Prospector site, concept, or redesign and before screenshot approval, deploy, proposal, or outreach. It must independently detect missing gpt-taste usage, hero visual defects, motion/scroll omissions, WhatsApp/social/map issues, fixed-control conflicts, reduced-motion/no-JS failures, factual regressions, and visual regressions.
---

# Autonomous Site Review

This skill is a hard quality barrier, not an optional checklist. A site cannot be marked Core QA PASS merely because the implementing agent reports that it passed.

## Repository policy and precedence

Read and obey, in order:

1. `../repository-policy/SKILL.md`
2. `../website-core-rules/SKILL.md`
3. `../redesign-premium/SKILL.md`
4. `../hero-visual-rule/SKILL.md`
5. the current installed `gpt-taste/SKILL.md`

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

Recommended QA hooks:

```html
<header data-role="site-header">...</header>
<section data-role="hero">...</section>
<div data-motion="reveal">...</div>
```

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

WhatsApp must still remain available through normal page CTAs and through assistant escalation/handoff. The rule removes only the competing fixed floating WhatsApp launcher.

Deterministic outcomes:

- assistant + floating WhatsApp => BLOCK
- assistant + normal WhatsApp CTAs + no floating WhatsApp => PASS
- no assistant + verified WhatsApp + missing required floating WhatsApp => BLOCK

Cookie/privacy controls may coexist only when functionally required and must not become competing conversion launchers.

## 5. HARD GATE: Instagram/social affordance in prospect mockups

For noindex prospect concepts, represent Instagram UI even when an official profile is not verified.

Verified profile:

- active real link;
- `data-social="instagram"`;
- verified destination only.

Unverified profile:

- visual affordance present;
- `data-social="instagram"`;
- `aria-disabled="true"`;
- no `href`, including no `#` and no `javascript:void(0)`;
- no invented URL or handle;
- non-navigable (`tabindex="-1"` or equivalent).

## 6. HARD GATE: embedded map

A verified public customer-facing physical address requires an embedded map preview by default.

A decorative location card without an embedded map does not satisfy the gate.

A map may be omitted only for a private/non-public address, an explicit operator decision, or a documented technical restriction.

## 7. HARD GATE: Google Reviews evidence and rendering

Every first-version local-business concept must explicitly check the correct Google Business Profile.

Canonical states:

- `VERIFIED_STRONG`: verified aggregate plus enough verified text reviews; review section required with only verified review text.
- `VERIFIED_AGGREGATE_ONLY`: verified aggregate exists but text evidence is insufficient; compact aggregate-only section required, with no testimonial cards or invented reviewer language.
- `NO_USABLE_REVIEWS` with verified `ratingCount > 0`: aggregate-only section required.
- verified profile with exactly 0 ratings/reviews: section may be omitted, but the state must be recorded.
- `PROFILE_CONFLICT`: BLOCK.

Evidence values must flow into DOM hooks rather than being manually retyped without verification.

Never infer that a public reviewer is a patient/client unless verified text evidence supports that statement.

## 8. HARD GATE: factual traceability

Public claims, verified-service lists, design-read claims, and assistant knowledge must derive from a verified factual allowlist/evidence inventory.

Do not rely on a blacklist of previously observed hallucinations. A new unsupported service or claim must fail even if its wording has never appeared before.

## 9. Two-layer review

### Layer A: deterministic/static

Run both static gates:

```bash
python prospector-de-sites/autonomous_site_review.py \
  --html sites/[slug]/[slug].html \
  --design-read sites/[slug]/design-read.md \
  --manifest sites/[slug]/review-manifest.json

python prospector-de-sites/fixed_conversion_controls_review.py \
  --html sites/[slug]/[slug].html
```

Both commands must exit with code 0. Any non-zero result blocks Static Review PASS.

### Layer B: browser/visual

Run:

```bash
python prospector-de-sites/autonomous_site_review_browser.py \
  --url <URL> \
  --manifest sites/[slug]/review-manifest.json
```

If Playwright/browser QA was not actually executed, Browser Review is `NOT VERIFIED`, never PASS.

Test at least:

- desktop 1440x900;
- tablet 800x1024;
- mobile 390x844;
- any additional viewport required by the current hero frame policy.

If an assistant is present, browser QA must also verify that no `data-role="floating-whatsapp"` launcher exists at any tested viewport.

## 10. Required review manifest

Create `sites/[slug]/review-manifest.json` from the canonical example.

The manifest records QA/evidence state, not convenient values chosen to make tests pass. Relevant sections include:

- hero visual and provenance;
- address/map state;
- verified WhatsApp destination;
- Instagram state;
- assistant presence;
- fixed conversion-control policy;
- motion expectations;
- Google Reviews evidence;
- factual evidence/verified claims;
- preview/noindex state.

## 11. Mandatory adversarial review

After the first PASS, perform a second review whose purpose is to fail the page.

Ask:

> If I were trying to reject this page, what permanent requirement could the implementing agent have skipped while still producing something that looks plausible?

Inspect especially:

- stale or fake gpt-taste proof;
- missing/incorrect hero image or crop/frame behavior;
- generated/stock imagery presented as the real person/facility;
- motion declared but not implemented;
- missing embedded map;
- missing/false Instagram state;
- wrong WhatsApp destination;
- assistant and floating WhatsApp both present;
- fixed controls covering content on mobile;
- reduced-motion/no-JS failures;
- Google review numbers/copy not matching evidence;
- fabricated reviewer/patient attribution;
- unsupported factual claims reintroduced after hardening;
- console/network failures.

## 12. No self-approval by written checklist

A report written by the implementing agent is not sufficient evidence.

PASS requires observable proof such as:

- DOM/HTML inspection;
- deterministic validator execution;
- current gpt-taste hash verification;
- factual evidence traceability;
- browser QA;
- geometry/screenshot checks where relevant;
- console/network checks;
- deploy gate execution.

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
