# Prospector Agent Contract

This repository is agent-agnostic. The canonical Prospector rules, evidence model, QA gates, CRM, deploy flow, and site-generation behavior live in the repository and must not depend on one vendor-specific agent runtime.

Any capable CLI/IDE agent may operate Prospector when it can read/write files, execute commands, and satisfy the required runtime capabilities for the requested task.

## 1. Canonical entry order

Before changing a site, workflow, rule, or gate, read:

1. `prospector-de-sites/skills/repository-policy/SKILL.md`
2. `prospector-de-sites/skills/agent-runtime/SKILL.md`
3. the task-specific skills under `prospector-de-sites/skills/`
4. the current runtime adapter under `prospector-de-sites/adapters/`

Do not duplicate canonical rules inside an agent-specific configuration file. Adapters only explain how a runtime exposes filesystem, shell, MCP, browser, image, GitHub, Vercel, and other capabilities.

## 2. Capability negotiation is mandatory

At the beginning of a new runtime/session, run:

```bash
python prospector.py doctor --agent <agent>
```

Supported labels are convenience hints only:

```text
generic
antigravity
codex
claude-code
opencode
hermes
```

An unlisted CLI uses the `generic` adapter.

The static doctor does not prove live connectivity. The active agent must separately probe runtime-only capabilities before relying on them.

Probe when relevant:

- Prospector CRM MCP
- browser / Playwright
- OpenDesign MCP
- image generation or editing
- GitHub authentication
- Vercel authentication
- Gmail / Calendar / other connected services

Never report PASS merely because a binary, config file, or MCP definition exists.

## 3. Portable MCP handoff

Generate a local absolute-path MCP handoff with:

```bash
python prospector.py setup --agent <agent> --workspace <workspace>
```

This creates ignored local files:

```text
.prospector/runtime.json
.prospector/mcp.generated.json
```

The active CLI imports `mcp.generated.json` using its own native MCP configuration mechanism.

The repository must not hard-code one user's home directory, IDE install path, daemon path, API key, or workspace path into canonical rules.

## 4. Core vs adapter responsibilities

### Prospector Core owns

- factual research policy
- evidence and provenance rules
- Google review integrity
- OpenDesign direction contract
- expert hero invariants
- conversion rules
- outreach approval rules
- CRM semantics
- static/autonomous QA
- browser QA requirements
- deployment gates
- client CMS/editor rules

### Runtime adapters own only

- how the current agent discovers skills/instructions
- how it imports MCP servers
- how it invokes browser tooling
- how it accesses image generation
- how it accesses GitHub/Vercel or other credentials
- runtime-specific command syntax

If an adapter conflicts with a canonical skill, the canonical skill wins.

## 5. Required baseline capabilities

A runtime can operate Prospector Core when it has:

```text
filesystem read/write
shell/command execution
Python 3
```

For the normal full workflow, also prefer:

```text
Node.js + npx
Git
MCP client
browser/Playwright
GitHub access
Vercel access
```

Optional capabilities have fail-closed or documented fallbacks.

Examples:

- no native image generation -> use verified existing assets or canonical hero templates; do not invent a real expert/facility image
- no OpenDesign MCP -> record the explicit unavailable state and use the documented design fallback
- no browser -> do not claim Browser QA PASS
- no GitHub/Vercel credentials -> prepare artifacts locally but do not claim deployment

## 6. Agent-neutral execution rules

Do not assume:

- `~/.gemini/`
- `.claude/`
- Codex-specific paths
- Antigravity plugins
- one specific MCP config location
- one specific image model/provider
- one specific browser implementation

Vendor-specific integrations may exist, but they are adapters, not repository truth.

When a task can be completed by a repository script or deterministic gate, prefer that over an agent's prose judgment.

## 7. Frontend Design Governance — GPT-Taste as Creative Director

### 7.1 Design Authority: GPT-Taste = Creative Director / Frontend Design Owner

`gpt-taste` is the sole creative director and art director of prospect-site frontend design.

GPT-Taste owns:
- 3 structural concepts generated before any code (differing in structure/layout, not just color/copy)
- selection of 1 chosen concept
- visual direction, composition, layout architecture, hierarchy, typography, density/whitespace
- signature module selection and review-section presentation
- visual personality, cinematic pacing, anti-template/anti-AI-slop judgment

Pre-code requirement:
No code may be written before a recorded decision:
```text
GPT_TASTE_DESIGN_DECISION: PASS | PASS_AFTER_DIRECTION_CHANGE | BLOCKED_SKILL_UNAVAILABLE
```

Post-browser-QA requirement:
After implementation and browser QA, GPT-Taste inspects the actual build:
```text
GPT_TASTE_IMPLEMENTATION_REVIEW: PASS | PASS_AFTER_CHANGES | BLOCKED_SKILL_UNAVAILABLE
```

If GPT-Taste is unavailable: STOP. Never fabricate a fallback PASS.

### 7.2 OpenDesign Status: Legacy Only

OpenDesign is no longer part of the production site-generation workflow for schema v3+ sites.
Retained only for backwards compatibility with legacy schema v2 manifests. Future sites do not generate `DESIGN.md` or OpenDesign artifacts.

### 7.3 Cinematic & Distinctive Design Objective

Target:
- Distinctive, cinematic when useful, conversion-clear, mobile-safe, fast, anti-template.
- Good patterns: full-bleed visual fields, oversized editorial type, asymmetric grids, layered depth, editorial pacing, split-screen sections, rich galleries, interactive spaces.
- Avoid default cookie-cutter repetition: hero -> intro -> 3 service cards -> reviews -> map -> contact.
- Motion rules: no motion for motion's sake; respect `prefers-reduced-motion`, accessibility, and zero layout shift.

### 7.4 Design DNA & Diversity Enforcement

Every new site records 7 design DNA fields:
1. `heroGrammar`
2. `paletteFamily`
3. `typographyCharacter`
4. `layoutGrammar`
5. `motionLanguage`
6. `reviewTreatment`
7. `signatureModule`

Before build, compare new DNA against the last 3-5 published sites:
```text
DESIGN_DIVERSITY: PASS | NEEDS_DIRECTION_CHANGE
```
If a repeat look is detected, GPT-Taste must alter structural direction.

### 7.5 Signature Module Requirement

Every new site version must implement at least one interactive or high-impact signature module:
```text
SIGNATURE_SECTION: PASS | FAIL
type: [slider | visual-compare | service-finder | calculator | map-explorer | gallery-explorer | timeline | visualizer | interactive-matrix | interactive-story]
purpose: [user value explanation]
evidenceSafety: [confirmed safe / no unsupported claims]
```
Required HTML hook:
```html
<section data-role="signature-section" ...>
```
Healthcare safety invariant: no fabricated medical outcomes or clinical guarantees. Visualizers must be marked illustrative unless directly backed by source evidence.

### 7.6 Design Resource Registry & Provenance

External UI assets (Aura compositions, 21st.dev components, Preline primitives) are raw material, never the design owner.
External libraries cannot set site direction.
Priority: Native build -> Aura reference -> 21st interaction -> Preline primitive -> other.
Every reused resource must log provenance with verified commercial use:
```text
RESOURCE_PROVENANCE:
source: [aura | 21st | preline | custom]
sourceUrl: [url]
license: [license name]
commercialUse: CONFIRMED
attribution: [text or null]
adaptationMode: [ADAPT_TO_VANILLA | USE_DIRECTLY | REFERENCE_ONLY]
```
If purely custom/native: `RESOURCE_PROVENANCE: NATIVE`. Unconfirmed commercial use BLOCKS.

### 7.7 Conflict Resolution Hierarchy

When skills or perspectives conflict, authority resolves strictly in this order:
```text
FACTUAL/EVIDENCE SAFETY > GPT-TASTE DESIGN DIRECTION > /COPYWRITING-MARKETING > /IMPECCABLE
```
Evidence remains sovereign over all creative and copy choices.

## 8. Global Market Acquisition Policy

- Target Markets: United States, Canada, Europe, Latin America (LATAM).
- **Brazil Discovery**: `NEW_DISCOVERY_BR = DISABLED`. Reject all new Brazilian leads.
- Existing Brazilian leads remain valid for updates, funnel advancement, follow-up, and closure.
- Market Tiers:
  - Tier A: US, CA, GB, IE, NL, CH, DE, AT, DK, SE, NO
  - Tier B: ES, CL, MX, PA, CR, UY, PT
  - Other countries permitted only on explicit user request.
- Stored market metadata: `country`, `locale`, `currency`, `phoneCountryCode`, `marketTier`. Locale is derived from country evidence, not language alone.

## 9. Outreach and Irreversible Actions

Zero outreach without explicit user authorization. No messages or calls may be sent automatically.
Changing CLI/agent does not weaken human-approval requirements.

## 10. Mandatory Specialist Reviews: /impeccable and /copywriting-marketing

### 10.1 `/impeccable`: Bounded Execution QA

Reviews craft after implementation: spacing bugs, overflow, crop, contrast, focus/hover states, tap targets, alignment, and responsive craft.
Does NOT art-direct or redesign. If design direction is fundamentally broken: `ESCALATE_TO_GPT_TASTE`.

### 10.2 `/copywriting-marketing`: Bounded Message & Conversion Review

Reviews customer-facing copy, headline hierarchy, CTA wording, persuasion, and jargon removal.
MUST NOT invent new unsupported business, medical, operational, or relational propositions.

### 10.3 Factual Re-Check & Semantic Claim Audit

`FACTUAL_RECHECK` executes a semantic claim audit after copy edits:
1. Extract all added or modified assertions.
2. Classify as `SUPPORTED`, `NONFACTUAL_UI_COPY`, or `UNSUPPORTED`.
3. Any `UNSUPPORTED` claim causes immediate `FACTUAL_RECHECK: FAIL` and `SEMANTIC_CLAIM_AUDIT: FAIL`.

## 11. Canonical 19-Step Publish Sequence

No lead may advance to `publicado` in CRM before all steps pass:
1. Evidence collection & verification
2. GPT-Taste: 3 diverse structural concepts
3. GPT-Taste: concept selection & rationale
4. Design DNA recording + diversity check
5. Signature module selection & safety check
6. Resource registry lookup (if applicable)
7. Implementation / build
8. Browser QA
9. GPT-Taste implementation review
10. GPT-Taste corrections (if required)
11. `/impeccable` execution review
12. Impeccable corrections (if required)
13. `/copywriting-marketing` review
14. Copywriting corrections (if required)
15. Semantic + factual recheck
16. Deterministic gates + proposal QA
17. Vercel build + deploy
18. Live QA
19. Local CRM promotion to `publicado`

## 12. Pipeline Reporting Format

```text
FRAMEWORK:
OpenDesign production dependency: LEGACY_ONLY
GPT-Taste owner: PASS
Cinematic rule: PASS
Design DNA: PASS (7 fields recorded)
Signature module: PASS (data-role="signature-section")

RESOURCES:
Aura: [referenced/native]
21st: [adapted/none]
Preline: [primitive/none]
Pagedone: DISABLED
Resource provenance gate: PASS

MARKET:
New BR discovery: DISABLED
Existing BR leads: VALID
Tier A/B: [Tier]

TESTS:
core: PASS
sites: PASS
doctor: PASS
self-test: PASS

GIT:
commit: [hash]
worktree: CLEAN

OUTREACH:
messages: 0
```

## 13. New runtime support

To support another CLI:

1. use `generic` first;
2. verify capability probes;
3. only add a dedicated adapter when the runtime needs special setup;
4. never fork or copy canonical skills merely to fit the new CLI;
5. keep runtime-specific files under `prospector-de-sites/adapters/` or ignored local config.

The target architecture is one Prospector Core, many thin runtime adapters.
