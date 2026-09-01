# Hermes Runtime Adapter

Hermes uses the same Prospector Core and deterministic gates as every other runtime.

Bootstrap:

```bash
python prospector.py doctor --agent hermes
python prospector.py setup --agent hermes --workspace .
```

Use `.prospector/mcp.generated.json` with the active Hermes MCP configuration mechanism if available. When a capability is missing, follow the canonical fail-closed fallback instead of changing site/review/design rules.

Do not copy canonical Prospector policies into Hermes-specific prompts.
