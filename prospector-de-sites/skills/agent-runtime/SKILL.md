---
name: agent-runtime
instruction_language: en
description: Canonical runtime portability and capability-negotiation rules for operating Prospector from any agent CLI/IDE. Keeps vendor-specific setup in thin adapters while preserving one shared Prospector Core.
---

# Agent Runtime Portability

Prospector Core is agent-agnostic. No canonical rule may require one specific agent vendor when the underlying capability can be expressed generically.

Read this skill after `repository-policy` and before relying on runtime-specific tools.

## 1. Capability model

Treat runtime support as capabilities rather than product names.

Canonical capability names:

```text
filesystem
shell
python
node
git
mcp
browser
image_generation
open_design
github
vercel
mail
calendar
```

A task may require only a subset.

Do not infer capability availability from the runtime brand. Probe it.

## 2. Bootstrap

From the repository root, run:

```bash
python prospector.py doctor --agent <agent>
```

For local MCP handoff:

```bash
python prospector.py setup --agent <agent> --workspace <workspace>
```

The generated `.prospector/` files are local runtime artifacts and must remain uncommitted.

## 3. Static discovery vs live proof

The bootstrap doctor may discover:

- executables;
- repository scripts;
- likely local installations;
- paths.

That is not proof of live service connectivity.

Examples requiring an independent live probe:

- an MCP server exists in config but cannot start;
- OpenDesign is installed but its daemon is unreachable;
- Git exists but push credentials are unavailable;
- Vercel CLI/tool exists but the account/project is unauthorized;
- Playwright is installed but the browser cannot launch;
- an image provider is configured but generation is unavailable.

Never convert static discovery into a false runtime PASS.

## 4. Thin adapter rule

Runtime-specific knowledge belongs under:

```text
prospector-de-sites/adapters/
```

Adapters may describe setup/discovery only.

They must not fork, duplicate, weaken, or reinterpret:

- repository policy;
- factual evidence rules;
- review provenance;
- OpenDesign design contract;
- hero invariants;
- conversion rules;
- outreach approvals;
- autonomous QA;
- deployment gates.

If an adapter conflicts with Core, Core wins.

## 5. Runtime-neutral tool selection

When multiple implementations can satisfy one capability, choose by this order:

1. already connected/native capability in the active runtime;
2. local MCP/server already configured;
3. repository-owned deterministic script;
4. explicit external provider only when configured/authorized.

Do not silently activate paid APIs or require a vendor key when a local/native path exists.

## 6. Browser capability

Browser QA may be satisfied by:

- a native agent browser;
- Playwright MCP;
- another browser automation layer that can prove the same required observations.

The QA contract matters more than the tool brand.

No browser capability means no `BROWSER REVIEW: PASS`.

## 7. Image capability

Image generation/editing is optional runtime infrastructure.

If available, it must still obey asset provenance and expert-identity rules.

If unavailable:

- use real/user-provided assets when available;
- use canonical hero templates when applicable;
- use honest contextual imagery only under existing rules;
- never invent a real expert/facility/patient to compensate for missing tooling.

## 8. OpenDesign capability

OpenDesign is MCP-based and therefore runtime-neutral when the active CLI supports MCP.

Probe its tools dynamically. Do not assume one static tool list.

If unavailable, record the canonical unavailable state rather than pretending another design model was OpenDesign.

## 9. Design judge portability

The final creative critique is a capability, not an agent vendor feature.

When the external current `gpt-taste` skill is installed and readable, use it as the preferred critic and record the actual path/hash when required by current gates.

When it is absent in another runtime, do not fabricate its presence. Use only the repository-documented fallback state until the deterministic design-judge contract is satisfied.

Agent portability may not be achieved by weakening design QA.

## 10. GitHub and deploy capability

GitHub/Vercel operations may be performed through connectors, CLI tools, APIs, or native runtime integrations.

Canonical deployment evidence remains the same:

- correct repository/ref;
- deterministic gates pass;
- deployment reaches expected state;
- production/preview URL is verified.

No authenticated deploy capability means stop at a local candidate.

## 11. Outreach capability

Changing runtimes never changes human-approval semantics.

A runtime with Gmail, WhatsApp/Evolution, or other messaging capability must still obey the canonical outreach skill and explicit approval requirements.

## 12. Fail-closed portability

If a runtime cannot satisfy a mandatory capability for the requested stage:

1. complete all safe earlier stages;
2. record the missing capability accurately;
3. stop before the stage requiring it;
4. do not downgrade a hard gate merely to support that runtime.

Portability means alternate capability providers and explicit fallbacks, not lower quality bars.
