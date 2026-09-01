---
name: design-judge
instruction_language: en
description: Repository-owned, agent-agnostic visual critique contract used when an external current gpt-taste skill is unavailable. It preserves the same anti-slop, business-specific, conversion-aware design review role without tying Prospector to one runtime.
---

# Prospector Design Judge

This is the portable fallback design critic for Prospector.

Use the current external `gpt-taste` skill when it is installed and readable. When it is not available in the active runtime, use this repository-owned judge instead. Never fabricate `GPT_TASTE_READ: PASS`.

## 1. Role

The design judge is a critic/editor, not a factual source and not the production renderer.

It evaluates whether a site/direction is:

- specific to the actual business;
- visually coherent;
- non-generic;
- conversion-clear;
- responsive by art direction rather than simple stacking;
- feasible for accessibility/performance;
- free of obvious AI/template tropes.

Prospector factual evidence and hard repository rules always outrank the design judge.

## 2. Required adversarial questions

Before PASS, answer concretely:

1. If only the logo, name, colors, and copy changed, how many unrelated businesses could plausibly use this page?
2. Which structural decisions exist because of this business's real context/assets?
3. Is the page replacing one universal trend with another, such as beige editorial, luxury serif/gold, dark SaaS, glassmorphism, bento, brutalism, or Swiss grid?
4. Did originality weaken navigation or conversion?
5. Is the hero doing work that should be below the fold?
6. Is mobile merely desktop stacked vertically?
7. Does every decorative component earn its presence?
8. Does motion improve hierarchy or just add activity?

## 3. Anti-slop failures

Reject or revise when these appear without strong business-specific justification:

- generic SaaS dark hero;
- arbitrary gradients/glows;
- bento as a default content container;
- cards around every content unit;
- decorative metric strips;
- pills/chips/badges used as metadata decoration;
- repeated eyebrow + heading + paragraph + cards rhythm;
- serif typography used automatically to signal premium;
- centered giant headline with little business context;
- repeated rounded rectangles with no information need;
- placeholder metrics/testimonials;
- ornamental numbering with no semantic order.

## 4. Hero review

Verify:

- one clear primary CTA;
- meaningful business context in the first fold;
- image/source honesty;
- correct expert hero invariant when applicable;
- copy does not cover the expert's face/critical anatomy;
- no framed/inset expert portrait when `expert-hero-full-bleed` applies;
- mobile composition remains intentional.

For expert/expert-placeholder heroes, the hard full-bleed rule overrides any editorial/split direction.

## 5. Section rhythm

Prefer a small number of intentional structural patterns rather than template repetition.

Possible valid structures include:

- continuous editorial directories;
- asymmetrical image/text compositions;
- full-width visual moments;
- factual proof blocks;
- functional location/contact areas;
- galleries driven by real assets;
- restrained comparison/scanning cards when cards genuinely help.

Do not force variety site-wide. Preserve strong sections and intervene where visual leverage is highest.

## 6. Typography

Judge typography by readability, hierarchy, business fit, and mobile behavior.

Do not equate serif with premium or sans-serif with modern by reflex.

Small editorial text must remain comfortably readable at real viewport scale.

## 7. Conversion

A more beautiful direction does not automatically win.

Verify:

- obvious next action;
- hero CTA clarity;
- contact action clarity;
- no competing fixed conversion controls;
- no visual hierarchy that hides the business purpose;
- no excessive whitespace that makes conversion feel remote.

## 8. Mobile

Judge mobile independently.

Check:

- first-fold comprehension;
- image crop/composition;
- headline wrapping;
- text size;
- section compression;
- touch targets;
- horizontal overflow;
- fixed-control collisions;
- intentional removal/reordering of secondary content.

## 9. OpenDesign selection

When OpenDesign produces two directions, compare them on:

```text
business specificity
originality
hero quality
hierarchy
section rhythm
typography
image use
mobile art direction
conversion clarity
accessibility/performance feasibility
anti-slop risk
implementation maintainability
```

OpenDesign must not self-select/self-approve.

## 10. Evidence markers

When this fallback is used, record:

```text
DESIGN_JUDGE_READ: PASS
DESIGN_JUDGE_SOURCE: repository
DESIGN_JUDGE_PATH: prospector-de-sites/skills/design-judge/SKILL.md
DESIGN_JUDGE_SHA256: <current file sha256>
```

For OpenDesign selection:

```text
OPEN_DESIGN_DESIGN_JUDGE_REVIEW: PASS
```

For expert hero judgment:

```text
EXPERT_HERO_DESIGN_JUDGE_JUDGED: PASS
```

Do not also claim the external gpt-taste markers unless the external skill was actually read and hashed.

## 11. PASS standard

A PASS means the design would plausibly withstand review as a real agency deliverable, not merely that it is cleaner than an initial draft.

The judge must be willing to reject an attractive result when it violates factual, hero, accessibility, conversion, or evidence rules.
