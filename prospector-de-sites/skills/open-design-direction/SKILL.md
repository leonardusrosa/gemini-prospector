---
name: open-design-direction
instruction_language: en
description: Mandatory creative-direction pass for new Prospector website/landing-page first versions when the local OpenDesign MCP is available. Uses OpenDesign to generate distinct art directions and a business-specific DESIGN.md, while Prospector remains authoritative for facts, implementation, QA, and deployment.
---

# OpenDesign Direction Pass

Use this skill for every new first-version public website or landing page created by Prospector under review-manifest schema v2 or later.

OpenDesign is a **creative-direction tool**, not the factual source, production renderer, or final QA authority.

The intended stack is:

```text
Prospector research/evidence
    -> OpenDesign: 2 distinct art directions + DESIGN.md
    -> gpt-taste: critique/select/refine
    -> Prospector: production HTML/CSS/JS implementation
    -> autonomous/browser/deploy QA
```

## 1. Authority and precedence

The following always outrank OpenDesign output:

1. verified factual evidence and source truth;
2. `repository-policy` and `website-core-rules`;
3. verified real assets and user requirements;
4. current `gpt-taste` guidance;
5. OpenDesign art direction;
6. implementation convenience.

OpenDesign may propose composition, typography, rhythm, image treatment, motion, spacing, component grammar, and visual hierarchy. It may not establish or modify factual claims.

Never allow OpenDesign to invent or silently change:

- business identity;
- services/specialties;
- credentials;
- prices;
- metrics;
- reviews/testimonials;
- phone/WhatsApp/email;
- address/hours;
- guarantees/results;
- expert/facility identity;
- social accounts;
- image provenance.

If OpenDesign output conflicts with verified evidence, discard the conflicting part rather than adapting the evidence.

## 2. MCP expectation

The Antigravity MCP server alias is:

```text
open-design
```

The operator configures the local OpenDesign MCP outside the repository. Do not commit machine-specific user paths, secrets, API keys, daemon IPC paths, or local app data paths into Prospector.

At the start of the pass:

1. probe the `open-design` MCP;
2. dynamically inspect the available OpenDesign capabilities instead of assuming stale tool names;
3. prefer local design-system / project-file / design-artifact capabilities;
4. do not route to OpenDesign Cloud or a paid hosted model unless the operator explicitly authorized it;
5. if the MCP is unavailable, record the failure truthfully and continue with the documented gpt-taste fallback rather than pretending OpenDesign ran.

## 3. Direction-only rule

Do **not** use OpenDesign's default landing-page/web-prototype seed as the production website source.

OpenDesign may create exploratory HTML or visual prototypes when useful, but they are reference artifacts only. Prospector must implement the selected direction inside its own static architecture and retain its own factual, conversion, accessibility, performance, CMS/editor, assistant, and deploy rules.

This prevents replacing generic AI slop with a recognizable OpenDesign house style.

Do not inherit template-specific assumptions merely because OpenDesign ships them, including:

- default serif display typography;
- fixed section skeletons;
- generic SaaS rhythms;
- predefined accent budgets;
- template card anatomy;
- stock startup composition.

A template convention may be used only when it is independently justified by this business and survives gpt-taste critique.

## 4. Prepare a factual creative brief

Before calling OpenDesign, create:

```text
sites/[slug]/open-design/brief.md
```

It must contain only verified or explicitly marked illustrative information:

```text
Business identity
Site mode
Audience/context
Verified services/offer
Verified contact/conversion destination
Verified location
Available real assets
Hero asset state
Review evidence summary
User requirements
Forbidden factual claims
Forbidden visual tropes
Technical constraints
Mobile priority
```

Do not feed speculative marketing claims to OpenDesign and later treat its output as evidence.

## 5. Generate two genuinely distinct directions

Ask OpenDesign for exactly **two primary art directions** by default.

They must differ structurally, not merely by palette/font.

Each direction must define:

```text
Direction name
One-sentence thesis
Why it fits this specific business
Hero composition
Page/section rhythm
Typography strategy
Color strategy
Photography/image treatment
Spacing/density
Component grammar
Motion/behavior
Mobile art direction
Conversion treatment
One decisive visual flourish
Business-specific decisions
Anti-slop risks
Explicitly rejected tropes
```

A direction is invalid if changing only logo, name, colors, and copy would make it suitable for dozens of unrelated businesses.

Examples of meaningful structural contrast:

- expert-led full-frame editorial composition vs architecture-led asymmetric split;
- restrained clinical publication rhythm vs image-first spatial narrative;
- typographic identity hero vs photographic negative-space hero.

Examples that do **not** count as separate directions:

- blue version vs green version;
- serif version vs sans version with the same layout;
- rounded cards vs slightly less rounded cards;
- the same hero with a different gradient.

## 6. Required OpenDesign outputs

Persist the design work under:

```text
sites/[slug]/open-design/
```

Required files when the MCP pass succeeds:

```text
brief.md
directions.md
DESIGN.md
```

`directions.md` contains both directions and their rationale.

`DESIGN.md` is the selected/refined visual contract, not a generic OpenDesign template. It should cover at minimum:

```text
Design thesis
Color tokens
Typography
Layout/grid
Spacing/rhythm
Hero composition
Section grammar
Image treatment
Component rules
Motion
Mobile behavior
Accessibility-sensitive visual choices
Anti-slop exclusions
```

Do not put factual business claims in `DESIGN.md` unless they are separately traceable to Prospector evidence.

## 7. gpt-taste is the selector/editor

After OpenDesign produces the two directions, read the current installed `gpt-taste/SKILL.md` and critique both directions.

Score qualitatively against:

- business specificity;
- visual originality without novelty-for-novelty's-sake;
- hierarchy;
- hero quality;
- section rhythm;
- typography;
- image use;
- mobile composition;
- conversion clarity;
- accessibility/performance feasibility;
- AI-slop/trope risk;
- implementation maintainability.

Select one direction or synthesize a clearly documented hybrid.

Do not let OpenDesign self-select and self-approve its own output.

## 8. Required design-read evidence

For schema v2+ first versions, `sites/[slug]/design-read.md` must contain one of the following truthful states.

Successful pass:

```text
OPEN_DESIGN_DIRECTION: PASS
OPEN_DESIGN_MCP: open-design
OPEN_DESIGN_MCP_PROBE: PASS
OPEN_DESIGN_DIRECTIONS_GENERATED: 2
OPEN_DESIGN_SELECTED_DIRECTION: <name>
OPEN_DESIGN_DESIGN_MD: open-design/DESIGN.md
OPEN_DESIGN_IMPLEMENTATION_ROLE: DIRECTION_ONLY
OPEN_DESIGN_GPT_TASTE_REVIEW: PASS
```

Unavailable MCP fallback:

```text
OPEN_DESIGN_DIRECTION: UNAVAILABLE
OPEN_DESIGN_MCP: open-design
OPEN_DESIGN_MCP_PROBE: FAIL
OPEN_DESIGN_UNAVAILABLE_REASON: <actual error/condition>
OPEN_DESIGN_FALLBACK: GPT_TASTE_ONLY
```

Explicit operator skip:

```text
OPEN_DESIGN_DIRECTION: SKIPPED_BY_OPERATOR
OPEN_DESIGN_OPERATOR_OVERRIDE: true
```

Never write `PASS` merely because a design was produced by another model or because OpenDesign is installed on the machine.

## 9. Review-manifest contract

New first-version manifests use schema v2+ and include:

```json
{
  "openDesignDirection": {
    "required": true,
    "mcpServerName": "open-design",
    "mcpProbeAttempted": true,
    "status": "used",
    "directionsGenerated": 2,
    "selectedDirection": "<name>",
    "designMdPath": "open-design/DESIGN.md",
    "gptTasteSelectionReviewed": true
  }
}
```

Allowed statuses:

- `used`
- `unavailable`
- `skipped_by_operator`

For `unavailable`, include a non-empty `unavailableReason`.

For `skipped_by_operator`, include `operatorOverride: true`.

## 10. Anti-house-style adversarial check

Before production implementation, explicitly ask:

> Did OpenDesign create a direction that is specific to this business, or did it merely apply an OpenDesign/template aesthetic?

Reject or revise when any of these dominate without business-specific justification:

- generic SaaS hero;
- interchangeable three-card feature row;
- decorative metric strip;
- arbitrary serif-luxury treatment;
- startup gradients/glow;
- bento layout as default;
- glassmorphism;
- cards around every content unit;
- repeated eyebrow + heading + paragraph + three cards rhythm;
- default OpenDesign template typography/layout copied wholesale.

One strong specific visual decision is preferable to several fashionable treatments.

## 11. Production handoff

The selected `DESIGN.md` is a visual specification only.

Prospector production still owns:

- factual allowlists and review evidence;
- hero provenance;
- real/illustrative image distinction;
- HTML/CSS/JS structure;
- conversion destinations;
- responsive behavior;
- CMS/editor compatibility;
- assistant integration;
- accessibility;
- performance;
- SEO/noindex behavior;
- browser QA;
- Vercel gates.

Never copy an OpenDesign prototype into production without reconciling it against all Prospector rules.

## 12. First-version completion rule

For schema v2+ first versions, the direction pass is considered complete only when:

```text
OPEN DESIGN MCP PROBED
2 DIRECTIONS PRODUCED OR A TRUTHFUL FALLBACK RECORDED
GPT-TASTE REVIEW RECORDED WHEN USED
SELECTED DESIGN.md PERSISTED WHEN USED
PRODUCTION IMPLEMENTATION REMAINS PROSPECTOR-OWNED
```

The purpose of this pass is not more design output. It is to force a deliberate art-direction decision before code so the first version is less generic, more business-specific, and easier to critique.