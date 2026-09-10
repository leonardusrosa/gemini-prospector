import re
import json
import urllib.request
import urllib.error

# 1. Read the newly added key
source_file = r"e:\Antigravity\prospector\.agents\plugins\prospector-de-sites\mcp_config.json"
with open(source_file, "r", encoding="utf-8") as f:
    content = f.read()

# Match the key safely
match = re.search(r'"x-api-key"\s*:\s*"([^"]+)"', content)
if not match:
    # Try finding any api-key
    match = re.search(r'api[-_]?key["\']?\s*[:=]\s*["\']?([^"\'\s,\}\]]+)', content, re.IGNORECASE)

if not match:
    print("ERROR: Could not extract API key from mcp_config.json")
    exit(1)

new_key = match.group(1).strip()
print(f"Successfully extracted new API key (length: {len(new_key)})")

# 2. Fix the JSON syntax in e:\Antigravity\prospector\.agents\plugins\prospector-de-sites\mcp_config.json
fixed_config = {
    "mcpServers": {
        "prospector-crm": {
            "command": "python",
            "args": [
                "C:/Users/leo_b/.gemini/config/plugins/prospector-de-sites/prospector-mcp.py",
                "--pasta",
                "e:/Antigravity/prospector"
            ]
        },
        "playwright": {
            "command": "npx",
            "args": [
                "-y",
                "@playwright/mcp@latest"
            ]
        },
        "21st": {
            "url": "https://21st.dev/api/mcp",
            "headers": {
                "x-api-key": new_key
            }
        }
    }
}

with open(source_file, "w", encoding="utf-8") as f:
    json.dump(fixed_config, f, indent=2)
print(f"Fixed JSON syntax in {source_file}")

# Also update 21st-magic in C:\Users\leo_b\.gemini\antigravity-ide\mcp_config.json
ide_config_file = r"C:\Users\leo_b\.gemini\antigravity-ide\mcp_config.json"
try:
    with open(ide_config_file, "r", encoding="utf-8") as f:
        ide_cfg = json.load(f)
    if "21st-magic" in ide_cfg.get("mcpServers", {}):
        ide_cfg["mcpServers"]["21st-magic"]["args"] = ["-y", "@21st-dev/magic@latest", f"API_KEY={new_key}"]
    ide_cfg["mcpServers"]["21st"] = {
        "url": "https://21st.dev/api/mcp",
        "headers": {
            "x-api-key": new_key
        }
    }
    with open(ide_config_file, "w", encoding="utf-8") as f:
        json.dump(ide_cfg, f, indent=2)
    print(f"Updated {ide_config_file}")
except Exception as e:
    print(f"Could not update {ide_config_file}: {e}")

# 3. Test connecting to https://21st.dev/api/mcp
url = "https://21st.dev/api/mcp"

def send_mcp_request(method, params=None, req_id=1, headers_dict=None):
    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method
    }
    if params is not None:
        payload["params"] = params
    
    data = json.dumps(payload).encode("utf-8")
    req_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "MCP-Client/1.0",
        "x-api-key": new_key
    }
    if headers_dict:
        req_headers.update(headers_dict)
        
    req = urllib.request.Request(url, data=data, headers=req_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, body

print("\n=== Connecting to https://21st.dev/api/mcp ===")
try:
    status, init_resp = send_mcp_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "prospector-antigravity", "version": "1.0.0"}
    })
    print(f"Initialize status: {status}")
    parsed_init = json.loads(init_resp)
    print("Initialize result keys:", list(parsed_init.get("result", {}).keys()))
    print("Server info:", parsed_init.get("result", {}).get("serverInfo", {}))
except urllib.error.HTTPError as e:
    print(f"Initialize HTTPError {e.code}: {e.read().decode('utf-8', errors='replace')}")
    exit(1)
except Exception as e:
    print(f"Initialize Exception: {e}")
    exit(1)

# 4. List tools
print("\n=== Listing available MCP tools ===")
try:
    status, tools_resp = send_mcp_request("tools/list", req_id=2)
    parsed_tools = json.loads(tools_resp)
    tools = parsed_tools.get("result", {}).get("tools", [])
    print(f"Tools count: {len(tools)}")
    for t in tools:
        print(f"  - {t.get('name')}: {t.get('description', '')[:100]}")
except Exception as e:
    print(f"Tools list exception: {e}")

# 5. Search "image comparison"
print("\n=== Searching 'image comparison' via MCP ===")
try:
    status, search_resp = send_mcp_request("tools/call", {
        "name": "search",
        "arguments": {"query": "image comparison"}
    }, req_id=3)
    parsed_search = json.loads(search_resp)
    print("Search result status:", status)
    content = parsed_search.get("result", {}).get("content", [])
    print("Content items:", len(content))
    for c in content:
        text = c.get("text", "")
        print("Text snippet:", text[:500])
        # Save full result for inspection
        with open(r"e:\Antigravity\prospector\prospector-react-engine\scripts\search_image_comparison.json", "w", encoding="utf-8") as out_f:
            out_f.write(text)
except Exception as e:
    print(f"Search exception: {e}")
