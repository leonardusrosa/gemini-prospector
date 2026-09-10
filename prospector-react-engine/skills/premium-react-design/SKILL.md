---
name: premium-react-design
description: Creative direction, component architecture, motion tokens, and design governance for Engine B (Next.js App Router + Motion + Tailwind).
---

# Premium React Design System (Engine B)

Engine B provides a high-fidelity, component-driven React architecture using Next.js App Router, Tailwind CSS, and Motion (`motion/react`), outputting pure static artifacts (`output: 'export'`).

---

## 1. Design Authority & Creative Direction (GPT-Taste)

`gpt-taste` is the creative director for prospect frontend design.
Before writing component code, 3 structural layout concepts must be defined:

1. **Editorial Architecture**: High typographic hierarchy, asymmetric layouts, expansive negative space.
2. **Layered Cinematic Depth**: Media-plane immersion, overlapping visual panels, subtle parallax depth.
3. **Structured Bento Showcase**: Information density balance, tactile interactive cards, high-contrast accenting.

Pre-code requirement:
- Select 1 structural concept and log selection rationale.
- Record `GPT_TASTE_DESIGN_DECISION: PASS`.

---

## 2. Design DNA (7 Canonical Fields)

Every site generated with Engine B records:
1. `heroGrammar`: Full-bleed visual plane, overlaid copy, asymmetric split.
2. `paletteFamily`: Contextual, high-contrast, accessible HSL palette tokens.
3. `typographyCharacter`: Modern sans/editorial pair, balanced line lengths.
4. `layoutGrammar`: Section rhythms, alternating density, fluid container constraints.
5. `motionLanguage`: Smooth spring dynamics, scroll reveals, tactile hover feedback.
6. `reviewTreatment`: Source-neutral badges, verified text integrity, tactile cards.
7. `signatureModule`: Dedicated interactive micro-app (e.g. before/after slider).

---

## 3. Spacing System (8px Baseline Rhythm)

All spacing, padding, and layout margins strictly adhere to an 8px grid:
- `space-1` = 4px (micro adjustment)
- `space-2` = 8px (minimum inner padding)
- `space-3` = 12px (badge padding)
- `space-4` = 16px (card interior padding)
- `space-6` = 24px (card gaps, mobile section spacing)
- `space-8` = 32px (component separation)
- `space-12` = 48px (section sub-rhythms)
- `space-16` = 64px (major section padding)
- `space-24` = 96px (desktop section gutters)
- `space-32` = 128px (hero vertical breathing room)

---

## 4. Standard Motion Tokens & Physics

Motion in Engine B uses `motion/react` with unified physics constants:

```typescript
export const MOTION_TOKENS = {
  duration: {
    instant: 0.15,
    fast: 0.25,
    normal: 0.45,
    slow: 0.8,
    cinematic: 1.2,
  },
  ease: {
    standard: [0.25, 0.1, 0.25, 1.0],      // cubic-bezier standard
    outQuart: [0.165, 0.84, 0.44, 1.0],    // smooth decelerate
    inOutCubic: [0.645, 0.045, 0.355, 1],  // balanced transition
  },
  viewport: {
    once: true,
    amount: 0.2,
    margin: "0px 0px -50px 0px",
  },
} as const;
```

### Reduced-Motion Fallback Invariant
Every animated element must respect `prefers-reduced-motion`:
- Animations disable translations and scales (`opacity: 1`, `transform: none`).
- Video backgrounds switch to static poster fallback.
- Next.js and Motion `useReducedMotion()` hook or CSS media query `motion-reduce:transition-none` must be applied.

---

## 5. Component Resource Priority

When sourcing or assembling UI patterns:
1. **Custom Motion (`motion/react`)**: Bespoke interactive components built directly for the prospect domain.
2. **21st.dev Adapted Patterns**: High-taste community primitives adapted to strict vanilla Tailwind + Motion.
3. **Tailwind Primitives**: Unstyled accessible atomic building blocks.

*Pagedone or bloated third-party CSS libraries are strictly disabled.*

---

## 6. Evidence-Safety & Claim Granularity Invariants

Engine B enforces the identical factual guardrails as Engine A:
- **Broad Category vs Claim Expansion**:
  `verified broad category != verified procedure != verified equipment != verified materials != verified outcome`
  Descriptions must remain conservative unless explicitly verified by primary evidence.
- **Source-Neutral Reviews**:
  No visible third-party vendor labels (`Google`, `Google Maps`, `Yelp`, etc.) on public badges or headings.
- **Public Label Ban**:
  Forbidden visible labels: `Private Website Concept`, `Demo Site`, `Mockup`, `Prototype`, etc.
- **Punctuation Cleanliness**:
  No em-dashes (`—`/`–`) in public badge copy (e.g. use `Corrected Surface: Illustrative`).
