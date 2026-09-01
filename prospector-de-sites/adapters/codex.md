# Codex CLI Runtime Adapter

Use the canonical repository `AGENTS.md` as the primary project instruction file.

Bootstrap:

```bash
python prospector.py doctor --agent codex
python prospector.py setup --agent codex --workspace .
```

Import `.prospector/mcp.generated.json` through the active Codex environment's supported MCP configuration mechanism when MCP is available.

Do not duplicate Prospector skills into Codex-specific prompts. Use repository scripts/gates directly through shell execution. If browser, image, GitHub, or Vercel capabilities are not connected, report those capabilities unavailable rather than weakening QA.
