import os
import re
import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding="utf-8")

mcp_config_path = r"e:\Antigravity\prospector\.agents\plugins\prospector-de-sites\mcp_config.json"
with open(mcp_config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

api_key = cfg["mcpServers"]["21st"]["headers"]["x-api-key"]
url = "https://21st.dev/api/mcp"

OUT_DIR = r"e:\Antigravity\prospector\prospector-react-engine\scripts\mcp_inspiration"
os.makedirs(OUT_DIR, exist_ok=True)

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
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

design_context = {
    "business": "Dallas automotive detailing studio",
    "direction": "architectural editorial cinematic high-negative-space low-UI-density high-end-automotive minimal-chrome non-SaaS non-card-grid non-bento non-glass",
    "palette": "obsidian liquid carbon",
    "constraints": ["no generic card grids", "no bento grids", "no SaaS marketing templates", "no glassmorphism", "no vendor review branding"]
}

sections = [
    {"role": "hero", "query": "luxury automotive hero full bleed editorial typography"},
    {"role": "services", "query": "editorial service index numbered service list"},
    {"role": "signature", "query": "cinematic before after full bleed image comparison"},
    {"role": "reviews", "query": "editorial testimonial spotlight pull quote"},
    {"role": "navigation", "query": "architectural navbar minimal navigation hairline header"},
    {"role": "closing", "query": "architectural closing section editorial contact studio monolith"}
]

print("=== Calling get_inspiration for 6 Sections ===")
inspiration_results = {}

for s in sections:
    role = s["role"]
    query = s["query"]
    print(f"Requesting get_inspiration for [{role.upper()}]: '{query}'...")
    try:
        res = call_mcp("tools/call", {
            "name": "get_inspiration",
            "arguments": {
                "query": query,
                "context": design_context,
                "limit": 6,
                "diversity": True
            }
        })
        content_list = res.get("result", {}).get("content", [])
        text = content_list[0]["text"] if content_list else ""
        inspiration_results[role] = text
        with open(os.path.join(OUT_DIR, f"inspiration_{role}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  -> Saved inspiration_{role}.txt ({len(text)} bytes)")
    except Exception as e:
        print(f"  -> get_inspiration error for {role}: {e}")

print("\n=== Calling targeted search with design intent ===")
targeted_searches = [
    {"role": "hero", "query": "editorial hero"},
    {"role": "services", "query": "editorial service index"},
    {"role": "services_numbered", "query": "numbered service list"},
    {"role": "signature", "query": "cinematic before after"},
    {"role": "signature_compare", "query": "full bleed image comparison"},
    {"role": "reviews", "query": "editorial testimonial spotlight"},
    {"role": "navigation", "query": "architectural navbar"},
    {"role": "closing", "query": "editorial contact section"}
]

targeted_results = {}
for ts in targeted_searches:
    role = ts["role"]
    query = ts["query"]
    print(f"Searching: '{query}'...")
    try:
        res = call_mcp("tools/call", {
            "name": "search",
            "arguments": {
                "query": query,
                "type": "component",
                "limit": 8
            }
        })
        content_list = res.get("result", {}).get("content", [])
        text = content_list[0]["text"] if content_list else ""
        targeted_results[role] = text
        with open(os.path.join(OUT_DIR, f"search_{role}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  -> Saved search_{role}.txt ({len(text)} bytes)")
    except Exception as e:
        print(f"  -> search error for {query}: {e}")

print("\n=== Phase 1 & 2 Execution Complete ===")
