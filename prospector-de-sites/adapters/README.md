# Prospector Runtime Adapters

Adapters make Prospector usable from different agent CLIs/IDEs without duplicating canonical rules.

The default is `generic.md`. A dedicated adapter exists only when a runtime needs special installation/discovery instructions.

Canonical policy remains in:

```text
../../AGENTS.md
../skills/repository-policy/SKILL.md
../skills/agent-runtime/SKILL.md
```

## Supported labels

The bootstrap CLI currently recognizes:

```text
generic
antigravity
codex
claude-code
opencode
hermes
```

The labels are capability/setup hints, not separate Prospector implementations.

If a dedicated `<agent>.md` file is absent, `prospector.py` automatically points to `generic.md`.

## Adding another runtime

A new adapter may document only:

- where that runtime reads project instructions;
- where/how it imports MCP definitions;
- browser/tool discovery;
- image-generation discovery;
- authentication/tooling handoff.

Do not copy factual, design, review, outreach, hero, QA, CMS, or deployment policy into adapters.
