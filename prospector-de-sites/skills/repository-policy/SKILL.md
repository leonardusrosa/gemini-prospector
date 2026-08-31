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

Direct Google Maps is the canonical aggregate source. Cached snippets, CRM values, search summaries, old screenshots, and previously accepted evidence never override the current exact Maps place profile.

Publishable evidence requires two independent direct-Maps count observations from the same collection pass:

1. the visible place-profile header count;
2. the count visible after opening the reviews panel.

Both must match the structured `reviewCount` and the same Place ID/CID. A mismatch is a hard BLOCK.

If the direct profile reports 3 or more ratings/reviews but fewer than 3 verified same-profile text reviews were captured, the state is `COLLECTION_INCOMPLETE`, not aggregate-only PASS. The collector must continue or request human evidence.

If the operator supplies a newer direct Maps observation that conflicts with stored evidence, the stored evidence becomes stale immediately and publication is blocked until recollection reconciles the values.

The autonomous adversarial review must always ask whether the live direct Maps profile currently shows a different rating/count than the active evidence and visible page. If yes or uncertain, BLOCK.

## 6. Review evidence regression requirements

The repository CI must include deterministic regressions proving at least these states fail:

- indirect/search-snippet aggregate used as publishable evidence;
- structured review count differs from the direct Maps profile-header text;
- structured review count differs from the independently observed reviews-panel count;
- newer operator direct-Maps observation conflicts with stored evidence;
- same profile reports 3+ ratings/reviews but text-review collection is incomplete;
- captured review belongs to another Place ID/CID;
- public review copy presents branded count labels such as `1 avaliação Google`.

Do not remove or weaken these regressions to make a tenant pass.
