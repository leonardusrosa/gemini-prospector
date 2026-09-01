# Claude Code Runtime Adapter

Prospector Core does not require Claude-specific plugin packaging. The repository `AGENTS.md` and canonical skills remain authoritative.

Bootstrap:

```bash
python prospector.py doctor --agent claude-code
python prospector.py setup --agent claude-code --workspace .
```

If the active Claude Code environment supports MCP, import `.prospector/mcp.generated.json` using its native MCP configuration path. Otherwise run Prospector Python/Node gates directly.

Do not create a separate Claude copy of canonical rules. Runtime-specific instructions may only map Claude tools to Prospector capabilities such as browser, image generation, GitHub, and deploy.
