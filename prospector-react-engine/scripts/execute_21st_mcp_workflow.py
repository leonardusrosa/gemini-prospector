import os
import json
import urllib.request
import urllib.error
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Read key
mcp_config_path = r"e:\Antigravity\prospector\.agents\plugins\prospector-de-sites\mcp_config.json"
with open(mcp_config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

api_key = cfg["mcpServers"]["21st"]["headers"]["x-api-key"]
url = "https://21st.dev/api/mcp"

OUT_DIR = r"e:\Antigravity\prospector\prospector-react-engine\scripts\mcp_results"
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

def mcp_search(query, search_type="component", limit=10, author=None):
    args = {"query": query, "type": search_type, "limit": limit}
    if author:
        args["author"] = author
    res = call_mcp("tools/call", {"name": "search", "arguments": args})
    
    # Parse result
    content_list = res.get("result", {}).get("content", [])
    if content_list and "text" in content_list[0]:
        try:
            return json.loads(content_list[0]["text"])
        except Exception:
            return content_list[0]["text"]
    return res

def mcp_get_component(demo_id):
    res = call_mcp("tools/call", {"name": "get_component", "arguments": {"id": demo_id}})
    content_list = res.get("result", {}).get("content", [])
    if content_list and "text" in content_list[0]:
        try:
            return json.loads(content_list[0]["text"])
        except Exception:
            return content_list[0]["text"]
    return res

print("=== 1. Re-running Searches for 6 Categories via MCP ===")
categories = ["hero", "services", "image comparison", "reviews", "navigation", "closing"]
category_results = {}

for cat in categories:
    print(f"Searching: '{cat}'...")
    data = mcp_search(cat, search_type="component", limit=10)
    category_results[cat] = data
    with open(os.path.join(OUT_DIR, f"search_{cat.replace(' ', '_')}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    count = len(data) if isinstance(data, list) else 0
    print(f"  -> Found {count} items for '{cat}'")
    if isinstance(data, list) and count > 0:
        for i, it in enumerate(data[:3]):
            author = it.get("author", {}).get("username") if isinstance(it.get("author"), dict) else it.get("author")
            print(f"     {i+1}. {it.get('name')} by @{author} (id: {it.get('id')})")

print("\n=== 2. Resolving Adapted Components via MCP ===")
adapted_targets = [
    {"role": "Signature", "query": "image comparison slider", "author": "minhxthanh", "target": "image-comparison-slider"},
    {"role": "Hero", "query": "hero-05", "author": "felipemenezes098", "target": "hero-05"},
    {"role": "Services", "query": "vertical accordion", "author": "TomIsLoading", "target": "vertical-accordion"},
    {"role": "Reviews", "query": "animated testimonials", "author": "bankkroll", "target": "animated-testimonials"},
    {"role": "Navigation", "query": "floating nav", "author": "ruixen.ui", "target": "floating-nav"},
    {"role": "Closing", "query": "lets work section", "author": "jatin-yadav05", "target": "lets-work-section"}
]

resolved_components = []

for item in adapted_targets:
    print(f"\nSearching for adapted component: {item['target']} by @{item['author']} (Role: {item['role']})")
    search_data = mcp_search(item["query"], limit=10)
    
    found = None
    if isinstance(search_data, list):
        for candidate in search_data:
            c_name = candidate.get("name", "").lower()
            c_slug = candidate.get("component_name", "").lower()
            author = (candidate.get("author", {}).get("username") or "").lower()
            if item["target"].lower() in c_name or item["target"].lower() in c_slug or item["author"].lower() in author:
                found = candidate
                break
        if not found and len(search_data) > 0:
            found = search_data[0] # closest match
    
    if found:
        demo_id = found.get("id")
        author = found.get("author", {}).get("username") if isinstance(found.get("author"), dict) else found.get("author")
        print(f"  Found match: '{found.get('name')}' by @{author} with Demo ID: {demo_id}")
        
        # Now fetch with get_component
        print(f"  Fetching code for Demo ID: {demo_id}...")
        code_data = mcp_get_component(demo_id)
        
        code_record_path = os.path.join(OUT_DIR, f"code_{item['target']}.json")
        with open(code_record_path, "w", encoding="utf-8") as f:
            json.dump(code_data, f, indent=2)
            
        resolved_components.append({
            "target": item["target"],
            "role": item["role"],
            "author": author,
            "demo_id": demo_id,
            "metadata": found,
            "code_data": code_data
        })
    else:
        print(f"  Could not find match for {item['target']}")

# Save complete summary
with open(os.path.join(OUT_DIR, "mcp_resolution_summary.json"), "w", encoding="utf-8") as f:
    json.dump({
        "searches": {k: len(v) if isinstance(v, list) else 0 for k, v in category_results.items()},
        "resolved_components": [
            {
                "target": r["target"],
                "role": r["role"],
                "author": r["author"],
                "demo_id": r["demo_id"],
                "has_code": bool(r.get("code_data"))
            } for r in resolved_components
        ]
    }, f, indent=2)

print("\n=== MCP Resolution Pipeline Completed Successfully ===")
