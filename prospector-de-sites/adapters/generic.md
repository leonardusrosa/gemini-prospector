# Generic Agent CLI Adapter

Use this adapter for any CLI/IDE agent that is not covered by a more specific adapter.

This adapter contains no canonical business/site rules. Read `../../AGENTS.md` and the canonical Prospector skills first.

## Minimum runtime

Required:

- repository filesystem read/write
- shell command execution
- Python 3

Recommended for the full workflow:

- Node.js / npx
- Git
- MCP client support
- browser automation or Playwright
- GitHub credentials/tooling
- Vercel credentials/tooling

## Bootstrap

From the repository root:

```bash
python prospector.py doctor --agent generic
python prospector.py setup --agent generic --workspace .
```

Then import:

```text
.prospector/mcp.generated.json
```

using the CLI's native MCP configuration mechanism.

If the CLI has no MCP support, the agent may still run repository scripts directly. It must not claim MCP-derived capabilities or browser QA that it cannot perform.

## Runtime capability mapping

Map the CLI's native features into these abstract Prospector capabilities:

```text
filesystem
shell
mcp
browser
image_generation
open_design
github
vercel
mail/calendar/other connectors
```

Only mark a capability available after a real probe.

## Browser

If no native browser exists but Node/npx are available, the generated MCP handoff includes the Playwright MCP launch definition as an optional server.

If neither native browser nor Playwright is available:

```text
BROWSER REVIEW: UNAVAILABLE
```

Do not promote a site to full production PASS.

## OpenDesign

OpenDesign is accessed through MCP. Probe the server dynamically; do not assume tool names from old documentation.

If unavailable, follow `skills/open-design-direction/SKILL.md` and record the truthful fallback state.

## Image generation

Image generation is runtime-specific and optional. Prefer, in order:

1. verified real/user-provided assets;
2. runtime-native generation/editing when available and allowed;
3. canonical Prospector hero templates;
4. explicit external provider only when configured/authorized.

Never use capability absence as a reason to fabricate a real expert, facility, patient, product, or testimonial.

## GitHub / Vercel

Use any authenticated mechanism the runtime exposes. The repository does not require a specific connector implementation.

If credentials are absent, stop at local production candidate status.

## New CLI rule

Do not add a dedicated adapter until generic mode has been tried. A dedicated adapter should contain setup/discovery details only, never copies of canonical Prospector policy.
