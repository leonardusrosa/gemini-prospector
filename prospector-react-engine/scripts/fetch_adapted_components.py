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

OUT_DIR = r"e:\Antigravity\prospector\prospector-react-engine\scripts\mcp_results"

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

def mcp_search(query, author=None):
    args = {"query": query, "type": "component", "limit": 10}
    if author:
        args["author"] = author
    res = call_mcp("tools/call", {"name": "search", "arguments": args})
    content_list = res.get("result", {}).get("content", [])
    if content_list and "text" in content_list[0]:
        return content_list[0]["text"]
    return ""

def mcp_get_component(demo_id):
    res = call_mcp("tools/call", {"name": "get_component", "arguments": {"id": int(demo_id)}})
    content_list = res.get("result", {}).get("content", [])
    if content_list and "text" in content_list[0]:
        return content_list[0]["text"]
    return json.dumps(res)

adapted_specs = [
    {"name": "image-comparison-slider", "author": "minhxthanh", "role": "Signature", "known_id": 7763},
    {"name": "hero-05", "author": "felipemenezes098", "role": "Hero"},
    {"name": "vertical-accordion", "author": "TomIsLoading", "role": "Services"},
    {"name": "animated-testimonials", "author": "bankkroll", "role": "Reviews"},
    {"name": "floating-nav", "author": "ruixen.ui", "role": "Navigation"},
    {"name": "lets-work-section", "author": "jatin-yadav05", "role": "Closing"}
]

print("=== Fetching Code for Adapted Components via MCP ===")

results = []

for spec in adapted_specs:
    print(f"\nProcessing {spec['name']} by @{spec['author']} ({spec['role']})...")
    demo_id = spec.get("known_id")
    
    if not demo_id:
        # Search by query
        search_text = mcp_search(spec["name"])
        # Find id in text
        m = re.search(r"\[id:\s*(\d+)\]", search_text)
        if not m and spec.get("author"):
            # Try searching by author
            search_text_author = mcp_search(spec["name"], author=spec["author"])
            m = re.search(r"\[id:\s*(\d+)\]", search_text_author)
            if m:
                search_text = search_text_author
        
        if m:
            demo_id = int(m.group(1))
            print(f"  Found Demo ID via search: {demo_id}")
        else:
            print(f"  Could not locate Demo ID for {spec['name']} by search")
    else:
        print(f"  Using known Demo ID: {demo_id}")
    
    code_text = None
    if demo_id:
        print(f"  Calling get_component(id={demo_id})...")
        code_text = mcp_get_component(demo_id)
        # Save raw code
        file_name = f"mcp_code_{spec['name'].replace('-', '_')}_{demo_id}.txt"
        with open(os.path.join(OUT_DIR, file_name), "w", encoding="utf-8") as f:
            f.write(code_text)
        print(f"  Saved code to {file_name} (length: {len(code_text)} bytes)")
    
    results.append({
        "name": spec["name"],
        "author": spec["author"],
        "role": spec["role"],
        "demo_id": demo_id,
        "code_snippet": code_text[:300] if code_text else None
    })

print("\n=== Finished Fetching Adapted Components ===")
