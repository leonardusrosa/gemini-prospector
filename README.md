# Prospector

Agent-agnostic prospecting, evidence, redesign, QA, CRM, publishing, and outreach workflow for local-business websites.

Prospector Core is not tied to Antigravity, Claude, Codex, OpenCode, Hermes, or any other single agent runtime. The repository owns the canonical rules and deterministic gates; each agent runtime supplies capabilities through a thin adapter.

## Architecture

```text
Prospector Core
├── AGENTS.md                         canonical runtime entry contract
├── prospector.py                     runtime doctor + portable MCP handoff
└── prospector-de-sites/
    ├── skills/                       canonical factual/design/QA/outreach rules
    ├── adapters/                     thin runtime-specific setup only
    ├── prospector-mcp.py             CRM MCP over the local SQLite database
    ├── dashboard/                    CRM dashboard
    ├── editor / CMS tooling
    ├── review evidence / QA gates
    ├── OpenDesign integration
    └── deploy tooling
```

The target model is:

```text
one Prospector Core
        +
many thin agent adapters
```

No adapter is allowed to fork or weaken canonical rules.

## Supported agent runtimes

The bootstrap recognizes any runtime label. Known convenience adapters currently include:

```text
generic
antigravity
codex
claude-code
opencode
hermes
```

Any unlisted CLI automatically uses the `generic` adapter.

A runtime does not need a dedicated adapter if it can:

- read/write repository files;
- run shell commands;
- run Python 3.

For the full workflow, MCP, browser automation, Git, GitHub, Vercel, Node/npx, and image generation are useful additional capabilities.

## Quick start

Clone/open the repository, then:

```bash
python prospector.py doctor --agent generic
python prospector.py setup --agent generic --workspace .
```

Any CLI name is accepted:

```bash
python prospector.py doctor --agent my-new-cli
python prospector.py setup --agent my-new-cli --workspace .
```

Unknown labels fall back to `prospector-de-sites/adapters/generic.md`.

Setup writes local ignored handoff files:

```text
.prospector/runtime.json
.prospector/mcp.generated.json
```

Make the active agent read:

```text
AGENTS.md
prospector-de-sites/skills/repository-policy/SKILL.md
prospector-de-sites/skills/agent-runtime/SKILL.md
```

Then import `.prospector/mcp.generated.json` through that runtime's native MCP configuration mechanism.

## Runtime doctor

```bash
python prospector.py doctor --agent generic
```

The doctor reports static/local discovery such as:

- Python;
- Node / npx;
- Git;
- Prospector CRM MCP script;
- canonical skills;
- likely OpenDesign installation;
- whether Playwright MCP is launchable.

It deliberately does **not** pretend that a discovered binary/config proves live connectivity.

The active agent must still probe runtime-only capabilities:

```text
MCP connectivity
browser
OpenDesign daemon
image generation
GitHub authentication
Vercel authentication
other connected services
```

## Portable MCP

Print a portable local MCP definition:

```bash
python prospector.py mcp-config --workspace .
```

The generated CRM server uses an absolute local path to:

```text
prospector-de-sites/prospector-mcp.py
```

and the selected workspace/database.

The CRM MCP itself is stdio and is not tied to an agent vendor.

Optional Playwright MCP is also included when the runtime wants browser automation.

A placeholder example is available at:

```text
prospector-de-sites/mcp_config.example.json
```

Do not treat the historical Antigravity `mcp_config.json` as canonical portable configuration.

## Canonical skills

All factual, UX, evidence, safety, conversion, QA, and outreach requirements live under:

```text
prospector-de-sites/skills/
```

Important current contracts include:

- `repository-policy`
- `agent-runtime`
- `design-judge`
- `redesign-premium`
- `open-design-direction`
- `expert-hero-full-bleed`
- `google-reviews-verification`
- `autonomous-site-review`
- `outreach-proposta`
- `deploy-site`
- `contrato-servico`

Runtime adapters must point agents to these skills rather than copying them.

## Design judge portability

An external current `gpt-taste` skill remains the preferred critic when the active runtime actually has it.

Prospector no longer requires one vendor/runtime to provide it. Runtimes without external gpt-taste use the repository-owned:

```text
prospector-de-sites/skills/design-judge/SKILL.md
```

The deterministic autonomous-review launcher accepts either:

```text
real external gpt-taste + real path/hash
```

or:

```text
DESIGN_JUDGE_READ: PASS
DESIGN_JUDGE_SOURCE: repository
DESIGN_JUDGE_PATH: prospector-de-sites/skills/design-judge/SKILL.md
DESIGN_JUDGE_SHA256: <current sha256>
```

It never permits a runtime to fake `GPT_TASTE_READ: PASS` merely because the external skill is unavailable.

## Site creation flow

For schema v2+ first versions, the intended workflow is:

```text
Prospector factual research/evidence
→ runtime capability probe
→ OpenDesign direction pass when available
→ design critique/selection
→ Prospector-owned HTML/CSS/JS implementation
→ deterministic QA
→ browser/visual QA
→ deploy gates
→ human-reviewed proposal/outreach
```

OpenDesign is art direction only. It does not become a factual source, production renderer, or deploy authority.

## Expert hero rule

When `heroVisual.kind` is `expert` or `expert-placeholder`, the expert media must remain a full-width hero background/media plane on desktop and mobile.

OpenDesign or a runtime-specific design model cannot replace it with:

- a framed side portrait;
- a card/tile;
- an inset image panel;
- a split-column portrait.

The deterministic expert-hero gate and browser geometry QA remain runtime-independent.

## Google review evidence

Google review/rating publication is fail-closed.

Direct Maps evidence, per-entry provenance, traversal completeness, fingerprint integrity, and evidence-to-DOM binding are separate checks.

The runtime must never generate reviewer names, dates, patient/client status, quotes, review IDs, or other factual metadata to satisfy layout/schema requirements.

A valid hash over fabricated metadata is still fabricated metadata.

## Browser QA

Browser QA can be satisfied by any implementation that proves the required observations:

- native agent browser;
- Playwright MCP;
- another browser automation layer.

The tool brand is not canonical.

If no browser is available, the runtime cannot claim `BROWSER REVIEW: PASS` or full production readiness.

## Image generation

Image generation/editing is a runtime capability, not a Prospector vendor dependency.

Preferred order:

```text
verified real/user-provided assets
→ runtime-native image capability when available
→ canonical Prospector templates
→ explicit external provider only when configured/authorized
```

Prospector must never silently activate a paid image API.

Missing image capability is never permission to fabricate a real expert, facility, patient, result, or product.

## OpenDesign MCP

OpenDesign is runtime-neutral through MCP.

When available, Prospector uses it for:

```text
factual creative brief
→ two structurally distinct directions
→ DESIGN.md
→ independent design critique/selection
```

The MCP must be probed in the active runtime. A config file alone is not proof of availability.

Antigravity-specific OpenDesign bootstrap remains documented in its adapter, but OpenDesign can be consumed by any compatible MCP client.

The OpenDesign direction contract accepts either a real external gpt-taste review or the repository design-judge review. Agent portability does not reduce the selection quality bar.

## CRM

The CRM MCP runs over the same local `prospector.db` used by the dashboard:

```bash
python prospector-de-sites/prospector-mcp.py --pasta <workspace>
```

Local test:

```bash
python prospector-de-sites/prospector-mcp.py --teste
```

The CRM can therefore be used by any runtime capable of stdio MCP, or the underlying Python/database can be operated through repository code when MCP is unavailable.

## Dashboard and editor

The existing dashboard, editor, CMS, and publish bridge remain repository-owned and agent-neutral.

Editor generation:

```bash
python create_editor.py sites/<slug>/<slug>.html
```

Local editor/publish bridge:

```bash
python editor_server.py
```

Production publication still requires authentication, tenant isolation, HTTPS, server-side credentials, and the canonical publish gates.

## GitHub and Vercel

Prospector does not require one connector implementation.

A runtime may use:

- native GitHub/Vercel tools;
- CLI;
- authenticated API/MCP integration;
- repository Git commands.

The required evidence remains the same: correct repository/ref, gates PASS, deployment state verified, public URL checked.

If deploy credentials are absent, stop at local production-candidate status.

## Outreach

The messaging implementation may vary by runtime, but human approval does not.

Prospector must never send cold outreach merely because the active agent has Gmail, Evolution API, WhatsApp, or another messaging connector.

The canonical outreach skill remains authoritative.

## Adapters

Runtime setup lives under:

```text
prospector-de-sites/adapters/
```

Current examples:

```text
generic.md
antigravity.md
codex.md
claude-code.md
opencode.md
hermes.md
```

Use `generic` first for a new CLI. Add a dedicated adapter only when the runtime needs special setup/discovery.

## CI / self-test

Repository runtime bootstrap self-test:

```bash
python prospector.py self-test
```

The GitHub quality workflow runs this together with the existing evidence and autonomous-review regressions.

## Portability principle

Agent portability means:

```text
same evidence rules
same design invariants
same QA gates
same approval requirements
different capability providers
```

It does **not** mean reducing the quality bar for a CLI that lacks a required capability.

If a mandatory capability is unavailable, complete safe earlier stages, record the limitation accurately, and stop before the stage that requires it.
