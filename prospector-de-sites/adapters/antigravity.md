# Antigravity Runtime Adapter

Antigravity is one supported runtime, not the canonical Prospector architecture.

Read `../../AGENTS.md`, `../skills/repository-policy/SKILL.md`, and `../skills/agent-runtime/SKILL.md` first.

## Bootstrap

From the repository/workspace root:

```powershell
python prospector.py doctor --agent antigravity
python prospector.py setup --agent antigravity --workspace .
```

The generated portable MCP handoff is:

```text
.prospector/mcp.generated.json
```

Antigravity may also load a copied plugin from its own plugin directories, but that is a convenience adapter only. Canonical Prospector rules stay in the repository.

## OpenDesign

The existing local OpenDesign MCP can be registered in Antigravity using the OpenDesign installer/wrapper documented by `skills/open-design-direction/SKILL.md`.

Probe the MCP in the active Agent session after installation/reload. A config entry alone is not proof of connectivity.

## Image generation

Prefer any image generation/editing capability already available in the active Antigravity session, subject to Prospector provenance and identity rules. If unavailable, use canonical templates/other documented fallbacks rather than requiring a paid external API.

## Google Maps discovery

A native Google Maps Platform integration may be used when available, but it is not required by Prospector Core. Browser/direct Maps collection and the canonical evidence gates remain authoritative where required.
