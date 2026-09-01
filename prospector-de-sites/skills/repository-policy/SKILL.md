---
name: repository-policy
instruction_language: en
description: Canonical repository-wide policy for Prospector rules, skills, QA gates, and implementation guidance. Read before adding or changing any rule or quality gate.
---

# Repository Policy

## 1. Rule authoring language

All new or modified repository rules, skill documentation, QA gate documentation, regression descriptions, and agent-facing implementation instructions MUST be written in English.

This applies to:

- `prospector-de-sites/skills/**/SKILL.md`
- rule and policy markdown files
- QA gate descriptions and failure messages added or modified in code
- regression-test names and explanatory comments added or modified in code
- agent-facing reference documents

Client-facing copy keeps the target market language. Existing legacy rule files written in another language may be migrated incrementally, but any section materially edited must be converted to English rather than extended in another language.

## 2. Fail-closed quality rules

Permanent UX, factual, safety, and conversion requirements must not exist only as prose. When the requirement can be checked deterministically, add a static/build gate and a regression that reproduces the failure that motivated the rule.

A self-authored agent report is not evidence of PASS.

## 3. Fixed conversion-control exclusivity

A public site may expose several conversion destinations in normal page content, but it must not show multiple competing fixed bottom-corner conversion launchers.

### Assistant present

When an AI assistant launcher is present:

- the assistant is the ONLY persistent fixed bottom conversion launcher;
- a floating WhatsApp button is forbidden;
- WhatsApp must remain available through normal page CTAs such as the hero, header, contact section, footer, and assistant escalation/handoff;
- cookie/privacy controls may coexist only if they are legally/functionally necessary and do not behave as a competing conversion CTA.

Required hook:

```html
<div data-role="assistant-launcher">...</div>
```

Forbidden in the same page when the assistant is present:

```html
<a data-role="floating-whatsapp">...</a>
```

### Assistant absent

When no assistant is present and verified WhatsApp is a primary conversion channel, the existing floating WhatsApp rule applies: show the floating WhatsApp only after the primary hero CTA leaves the viewport.

### Rationale

The assistant already acts as the persistent help/conversion entry point and can escalate to WhatsApp. Showing both fixed launchers creates duplicate attention targets, consumes mobile viewport space, and makes the page feel mechanically assembled.

## 4. Fixed-control enforcement

Autonomous review, browser QA, and the Vercel predeploy gate must treat these states as follows:

- assistant + floating WhatsApp => BLOCK
- assistant + no floating WhatsApp + normal WhatsApp CTAs => PASS
- no assistant + verified WhatsApp + required floating WhatsApp missing => BLOCK
- no assistant + verified WhatsApp + synchronized floating WhatsApp => PASS

Do not weaken this rule to solve a tenant-specific layout problem. Fix the tenant instead.

## 5. Google Maps review evidence integrity

Every local-business first version, review refresh, or materially revised public site that uses Google rating/review data MUST read and obey `../google-reviews-verification/SKILL.md` and MUST validate its evidence with `prospector-de-sites/google_reviews_evidence.py`.

Direct Google Maps is the canonical source. Cached snippets, CRM values, search summaries, old screenshots, and previously accepted evidence never override the current exact Maps place profile.

Publishable evidence requires:

1. the exact listing identity;
2. the visible place-profile header aggregate/count;
3. the count visible after opening the reviews panel;
4. complete traversal evidence for the current rating/review set when the public site represents individual entries;
5. evidence-to-DOM binding for every rendered review/rating item.

The two live count observations must match the structured count and the same Place ID/CID. A mismatch is a hard BLOCK.

Do not infer text-review completeness from the aggregate count. A profile may have star-only ratings. Classification must be based on a completed traversal and the number of actual observed text entries.

## 6. Review metadata provenance is mandatory

Review/rating metadata is factual business evidence. It is subject to the same non-fabrication rule as names, phone numbers, addresses, credentials, services, testimonials, and prices.

For every observed review/rating entry:

- preserve the native Google review ID when exposed;
- preserve the exact author only when observed;
- preserve the exact date/date label only when observed;
- preserve the exact rating only when observed;
- preserve exact review text only when observed and linked to verified same-place evidence;
- if author or date is unavailable, store `null` rather than inventing a replacement;
- never generate surrogate identities such as `Paciente Verificado #1`, `Reviewer #2`, `Cliente #3`, `Anonymous #4`, or analogous placeholders;
- never generate a plausible date merely to satisfy a schema or visual layout;
- never label a reviewer as a patient/client unless the source explicitly verifies that status.

A cryptographic fingerprint proves integrity of supplied values, not provenance. A valid SHA-256 over fabricated metadata is still fabricated metadata and MUST BLOCK.

Source provenance, fingerprint integrity, traversal completeness, and public binding are four separate checks. All four must PASS.

## 7. Canonical traversal semantics

When a direct Maps profile is fully traversed, `observedEntries[]` is the canonical evidence inventory.

Derived values must come from that inventory rather than being trusted as independently authored numbers:

- `observedRatingEntries = observedEntries.length`
- `observedTextReviewEntries = count(hasText === true)`
- `starOnlyRatingCount = count(hasText === false)`
- `capturedTextReviewCount = count(valid same-place text evidence records)`

Every derived/declared count must reconcile. Duplicate fingerprints or duplicate native review IDs BLOCK.

For an entry with `hasText=true`, its `textEvidenceId` must resolve to an exact verified same-place Google review. For `hasText=false`, `textEvidenceId` must be `null`.

## 8. Review classification

After complete traversal:

- `VERIFIED_STRONG`: 3 or more verified same-place Google text reviews;
- `VERIFIED_TEXT_LIMITED`: exactly 1 or 2 verified same-place Google text reviews;
- `VERIFIED_AGGREGATE_ONLY`: zero text reviews after complete traversal, with a verified aggregate;
- `COLLECTION_INCOMPLETE`: traversal or evidence reconciliation is incomplete;
- `PROFILE_CONFLICT`: identity/provenance conflict;
- `NO_USABLE_REVIEWS`: correctly identified profile has zero ratings/reviews.

Secondary platforms may add separate evidence, but they must never upgrade the Google-specific state.

## 9. Operator conflict rule

If the operator supplies a newer direct Maps observation that conflicts with stored evidence, the stored evidence becomes stale immediately and publication is blocked until recollection reconciles the values.

The autonomous adversarial review must always ask whether the live direct Maps profile currently shows a different rating/count than the active evidence and visible page. If yes or uncertain, BLOCK.

## 10. Review evidence regression requirements

Repository CI must include deterministic regressions proving at least these states fail:

- indirect/search-snippet aggregate used as publishable evidence;
- structured review count differs from the direct Maps profile-header text;
- structured review count differs from the independently observed reviews-panel count;
- newer operator direct-Maps observation conflicts with stored evidence;
- declared traversal count exceeds `observedEntries.length`;
- `capturedTextReviewCount` differs from actual text evidence;
- captured review belongs to another Place ID/CID;
- duplicate fingerprint or duplicate native review ID;
- synthetic review author such as `Paciente Verificado #1`, even when its fingerprint is valid;
- non-null author/date marked as not observed;
- generated placeholder reviewer identity or generated date used instead of `null`;
- public review UI renders an item that has no evidence binding;
- public review copy claims `patient/client` status without explicit source support;
- public review copy presents branded count labels such as `1 avaliação Google`.

Do not remove or weaken these regressions to make a tenant pass.

## 11. OpenDesign creative-direction policy

For **new first-version public websites and landing pages created under review-manifest schema v2 or later**, read and obey `../open-design-direction/SKILL.md` before production HTML is written.

OpenDesign is an art-direction layer only. It does not become a factual source, production authority, or deploy authority.

The required order is:

```text
Prospector factual research/evidence
-> OpenDesign direction pass
-> gpt-taste critique/selection
-> Prospector implementation
-> autonomous/browser/deploy QA
```

When the local `open-design` MCP is available, generate two genuinely distinct structural directions and persist the selected/refined `open-design/DESIGN.md` before implementation.

Do not use OpenDesign's bundled web/landing templates as the production source. Do not inherit a default OpenDesign house style merely because a template, seed, font rule, or section skeleton is available.

`gpt-taste` remains the final creative critic/selector. Prospector factual evidence and Website Core Rules always outrank both OpenDesign and gpt-taste.

If the MCP cannot be reached, record `OPEN_DESIGN_DIRECTION: UNAVAILABLE`, the actual probe failure, and `OPEN_DESIGN_FALLBACK: GPT_TASTE_ONLY`. Never claim OpenDesign PASS when another model or an ordinary prompt produced the direction.

An explicit operator skip must be recorded as `SKIPPED_BY_OPERATOR`; it must not be silently treated as a successful OpenDesign pass.

### Schema v2 enforcement

New first-version schema v2+ manifests must include `openDesignDirection` with truthful MCP status. The deterministic autonomous reviewer must verify the manifest/design-read contract without changing legacy schema v1 sites.

This integration is intended to improve first-pass art direction while preserving the existing fail-closed factual and production pipeline.