# OpenCode Runtime Adapter

Use Prospector through the repository contract rather than a forked OpenCode-specific implementation.

Bootstrap:

```bash
python prospector.py doctor --agent opencode
python prospector.py setup --agent opencode --workspace .
```

Import `.prospector/mcp.generated.json` through OpenCode's active MCP configuration mechanism when supported. Probe each server before use.

Shell-accessible deterministic gates remain canonical. Do not mark browser/design/deploy capabilities PASS unless the active OpenCode runtime actually exposes and successfully probes them.
