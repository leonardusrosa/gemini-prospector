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

## 7. Design-runtime rule

OpenDesign is a creative-direction MCP layer, not a production authority. A runtime may use OpenDesign through any compatible MCP client.

For expert/expert-placeholder heroes, `expert-hero-full-bleed` remains a hard invariant regardless of the agent, OpenDesign direction, design model, or runtime.

The design judge must apply the canonical Prospector design criteria. If an external `gpt-taste` skill is available, use the current installed version as the preferred critic. Its absence must never cause an agent to silently fabricate a `GPT_TASTE_READ: PASS` marker.

## 8. Outreach and irreversible actions

No agent/runtime may send outreach, contact a prospect, execute an irreversible client action, or mark a deal closed without the same approval required by the canonical skills.

Changing CLI/agent does not weaken human-approval requirements.

## 9. QA is runtime-independent

A different agent is not a reason to skip gates.

When applicable, run the repository-owned validators and the publish repository's build gates. A self-authored report is never sufficient evidence of PASS.

At minimum, a site production decision must distinguish:

```text
STATIC / DETERMINISTIC QA
BROWSER / VISUAL QA
FACTUAL EVIDENCE QA
DEPLOY QA
```

If the runtime cannot execute one layer, report it as unavailable and stop before claiming a full production PASS.

## 10. Mandatory pre-publish reviews: /impeccable and /copywriting-marketing

Before any lead is considered publish-ready, every prospect site and proposal must pass two mandatory skill reviews using the installed Antigravity/Codex skills by their slash-command names:

1. `/impeccable`: visual craft, typography, spacing, hierarchy, layout rhythm, responsive presentation on rendered desktop and mobile views, and proposal layout. Distinguishes CRITICAL, REAL IMPROVEMENT, and OPTIONAL/TASTE.
2. `/copywriting-marketing`: reviews all user-facing copy on site, proposal, CTAs, navigation, review headings, disclaimers, and assistant prompts. Eliminates robotic internal/audit jargon while strictly constrained to **IMPROVE THE EXPRESSION OF SUPPORTED PROPOSITIONS ONLY**.

### Copywriting constraint: No newly-created unsupported propositions

The copywriter MUST NOT create a new business, medical, operational, or relational proposition merely because it sounds better or more natural.

Risky newly-created propositions that fail without explicit evidence:
- Quality adjectives: *acolhedor*, *personalizado*, *especializado*, *premium*, *cuidadoso*
- Operational claims: *agendamento*, *horários reservados*, *atendimento individualizado*
- Medical/process claims: *diagnóstico*, *prevenção*, *tratamento*, *avaliação clínica*
- Facility claims: *confortável*, *moderno*, *equipado*, *planejado*
- Relationship claims: *pacientes*, *clientes da clínica*, *nossa equipe*

### Review identity and relationship semantics

The following semantic inferences are strictly prohibited without evidence:
- Public review author != automatically verified patient/client/customer (do not refer to reviewers as "nossos pacientes" or "clientes da clínica").
- Business has WhatsApp != automatically accepts appointments or bookings via WhatsApp.
- Business category "Odontologia" != detailed diagnostic/preventive/treatment catalog.
- Business category "Estética" != facial procedures/harmonization/personalized facial care.
- Address in a specific neighborhood != "centro da cidade".

### Fail-closed semantics

Allowed review states:
- `PASS`
- `PASS_AFTER_CHANGES`
- `BLOCKED_SKILL_UNAVAILABLE`

If either skill is unavailable, the agent MUST NOT silently substitute generic LLM taste or claim equivalent PASS. The blocker must be reported explicitly, and the lead cannot advance to publish readiness.

### Upgraded Factual Recheck & Semantic Claim Audit

"Protected fields unchanged" is **NOT sufficient** for `FACTUAL_RECHECK: PASS`.

`FACTUAL_RECHECK` must include a semantic claim audit after copy edits:
1. Compute user-facing copy diff.
2. Extract every added or materially strengthened assertion.
3. Classify each assertion as:
   - `SUPPORTED`: grounded in verified factual evidence (record source/reference).
   - `NONFACTUAL_UI_COPY`: neutral navigation/layout phrasing that asserts no factual capabilities.
   - `UNSUPPORTED`: any claim exceeding evidence.
4. Any `UNSUPPORTED` claim causes immediate `FACTUAL_RECHECK: FAIL` and `SEMANTIC_CLAIM_AUDIT: FAIL`.

### Canonical publish sequence

1. evidence verified
2. design workflow complete
3. implementation complete
4. browser QA desktop/mobile
5. `/impeccable` review
6. impeccable corrections
7. `/copywriting-marketing` review (under supported propositions constraint)
8. copy corrections
9. factual re-check + semantic claim audit (extract claims, classify, require 0 unsupported)
10. deterministic site/review/hero/conversion gates
11. proposal QA
12. Vercel build
13. deploy
14. live browser verification
15. local CRM promotion to `publicado`

A lead cannot advance to `publicado` before steps 1–14 are complete.

## 11. New runtime support

To support another CLI:

1. use `generic` first;
2. verify capability probes;
3. only add a dedicated adapter when the runtime needs special setup;
4. never fork or copy canonical skills merely to fit the new CLI;
5. keep runtime-specific files under `prospector-de-sites/adapters/` or ignored local config.

The target architecture is one Prospector Core, many thin runtime adapters.
