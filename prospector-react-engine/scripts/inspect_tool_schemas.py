import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Read key
with open(r"e:\Antigravity\prospector\.agents\plugins\prospector-de-sites\mcp_config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

api_key = cfg["mcpServers"]["21st"]["headers"]["x-api-key"]
url = "https://21st.dev/api/mcp"

def call_mcp(method, params=None, req_id=1):
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        payload["params"] = params
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "x-api-key": api_key
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

tools_res = call_mcp("tools/list")
tools = tools_res.get("result", {}).get("tools", [])

for t in tools:
    if t["name"] in ["search", "get_component", "get_inspiration"]:
        print(f"=== Tool: {t['name']} ===")
        print(f"Description: {t.get('description')}")
        print("Parameters Schema:", json.dumps(t.get("inputSchema", {}), indent=2))
        print()
