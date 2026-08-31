---
name: repository-policy
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

## 4. Enforcement

Autonomous review, browser QA, and the Vercel predeploy gate must treat these states as follows:

- assistant + floating WhatsApp => BLOCK
- assistant + no floating WhatsApp + normal WhatsApp CTAs => PASS
- no assistant + verified WhatsApp + required floating WhatsApp missing => BLOCK
- no assistant + verified WhatsApp + synchronized floating WhatsApp => PASS

Do not weaken this rule to solve a tenant-specific layout problem. Fix the tenant instead.
