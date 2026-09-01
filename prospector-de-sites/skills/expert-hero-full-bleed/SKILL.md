---
name: expert-hero-full-bleed
instruction_language: en
description: Canonical hard rule for any Prospector hero whose primary visual is a real expert or canonical expert placeholder. The expert media must be a full-width background composition on both desktop and mobile, regardless of OpenDesign direction, gpt-taste preference, or template aesthetics.
---

# Expert Hero Full-Bleed Rule

This rule is mandatory whenever `heroVisual.kind` is `expert` or `expert-placeholder`.

It outranks OpenDesign art direction, gpt-taste stylistic preference, `redesign-premium` hero mode suggestions, template defaults, and implementation convenience.

## 1. Non-negotiable visual invariant

An expert-led hero must use the expert image as the hero's **full-width background media layer** on both desktop and mobile.

The expert image must never be presented as:

- a right-side framed portrait;
- an architectural image frame;
- a card, tile, panel, or component box;
- a split-layout image column that stops short of the hero edges;
- a floating portrait over a plain background;
- a thumbnail beside the headline.

OpenDesign may change typography, spacing, copy placement, palette, section rhythm, motion, and the exact negative-space strategy. It may not change this expert-background invariant.

## 2. Desktop requirement

For desktop expert heroes:

- the hero media plane spans the full hero width;
- the expert is composed into the background, normally occupying a strong visual territory without being covered by copy;
- copy uses intentional negative space in the same full-bleed composition;
- there is exactly one primary hero CTA;
- no component border, rounded frame, card shadow, or inset image container may visually separate the expert from the hero background.

Required hero hooks:

```html
<section
  data-role="hero"
  data-hero-layout="full-bleed-background"
  data-hero-expert-presentation="background"
  data-hero-mobile-layout="full-width-background"
>
```

## 3. Mobile requirement

Mobile must also keep the expert media **full width**.

A valid mobile composition may place the expert primarily in the upper part of the hero and copy below, but the expert image still belongs to the hero background/media plane and must span the viewport width. It must not become a framed portrait card.

Preferred implementation uses a dedicated mobile composition rather than shrinking/cropping the desktop asset blindly.

Required responsive structure:

```html
<picture>
  <source media="(max-width: 640px)" srcset="assets/hero-mobile.webp">
  <img data-role="hero-image" src="assets/hero-desktop.webp" alt="...">
</picture>
```

For canonical placeholder templates, preserve the template's factual/illustrative disclosure and frame-preservation requirements while still making the media layer full width.

## 4. gpt-taste judge responsibility

The gpt-taste review is not allowed to trade this rule away for a visually attractive OpenDesign direction.

When evaluating OpenDesign directions, gpt-taste MUST reject or revise any direction that uses an expert/expert-placeholder hero as a framed, split-column, carded, tiled, or inset image.

A direction cannot receive `OPEN_DESIGN_GPT_TASTE_REVIEW: PASS` for an expert-led hero until all of these are true:

```text
EXPERT_HERO_FULL_BLEED: PASS
EXPERT_HERO_DESKTOP_FULL_WIDTH: PASS
EXPERT_HERO_MOBILE_FULL_WIDTH: PASS
EXPERT_HERO_GPT_TASTE_JUDGED: PASS
```

This remains true even when the rejected framed/split solution scores better on originality or editorial aesthetics.

## 5. OpenDesign constraints

Every OpenDesign brief for an expert-led prospect must explicitly state:

```text
HARD HERO CONSTRAINT:
The expert image is a full-width hero background on desktop and mobile.
Do not propose framed portraits, side image cards, split-column portrait panels,
or inset expert photography.
```

If one of the two generated directions violates this constraint, it does not count as a valid direction and must be regenerated or revised before gpt-taste compares the options.

## 6. Manifest contract

For schema v2+ first versions with `heroVisual.kind` equal to `expert` or `expert-placeholder`, require:

```json
{
  "heroVisual": {
    "kind": "expert-placeholder",
    "expertBackgroundRequired": true,
    "desktopFullWidthRequired": true,
    "mobileFullWidthRequired": true
  }
}
```

These booleans are declarative requirements, not proof of compliance.

## 7. Static QA

Static QA must BLOCK an expert hero when any of the following is true:

- `data-hero-layout` is not `full-bleed-background`;
- `data-hero-expert-presentation` is not `background`;
- `data-hero-mobile-layout` is not `full-width-background`;
- there is no responsive `<picture>` / mobile `<source>`;
- the manifest does not require desktop and mobile full-width expert presentation;
- design-read lacks the four expert-hero PASS markers.

## 8. Browser QA geometry

Static hooks are necessary but not sufficient.

At minimum verify at 1440x900 and 390x844:

- the expert hero media plane width is at least 98% of the hero/viewport width;
- the expert is not contained inside an inset card/frame;
- the image remains visually meaningful and recognizable;
- copy does not cover the expert's face or critical anatomy;
- no horizontal overflow is introduced;
- mobile does not fall back to a framed portrait.

Browser failure overrides static PASS.

## 9. Asset strategy

Use separate desktop/mobile assets when needed:

```text
assets/hero-desktop.webp
assets/hero-mobile.webp
```

For real experts, preserve real identity. Outpainting may extend environment/negative space, but must not regenerate the subject into a different person.

For canonical placeholders, keep `data-image-context="illustrative"` and never imply the template depicts the actual expert or facility.

## 10. Regression requirement

Repository regression coverage must include at least:

- expert hero in a right-side framed portrait => FAIL;
- expert hero in a split image column => FAIL;
- desktop full-bleed but mobile framed => FAIL;
- full-bleed desktop + full-width mobile with responsive source => PASS;
- non-expert hero => this rule is not applicable.

Do not weaken this rule to preserve an OpenDesign direction. Revise the direction instead.
