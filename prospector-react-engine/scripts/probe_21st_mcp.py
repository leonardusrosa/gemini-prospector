import json
import urllib.request
import urllib.error

# Read local secret safely without printing it
mcp_config_path = r"C:\Users\leo_b\.gemini\antigravity-ide\mcp_config.json"
with open(mcp_config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

arg = cfg["mcpServers"]["21st-magic"]["args"][2]
api_key = arg.split("API_KEY=")[1].strip()

url = "https://21st.dev/api/mcp"

# Test 1: GET request
print("=== Testing GET ===")
for header_name in ["Authorization", "x-api-key"]:
    val = f"Bearer {api_key}" if header_name == "Authorization" else api_key
    req = urllib.request.Request(url, headers={header_name: val, "User-Agent": "MCP-Client/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"GET with {header_name}: status {resp.status}, Content-Type: {resp.headers.get('Content-Type')}")
            body = resp.read(500).decode("utf-8", errors="replace")
            print("Response preview:", body[:200])
    except urllib.error.HTTPError as e:
        print(f"GET with {header_name}: HTTPError {e.code} - {e.reason}")
        err_body = e.read().decode("utf-8", errors="replace")
        print("Error preview:", err_body[:200])
    except Exception as e:
        print(f"GET with {header_name}: Exception: {e}")

# Test 2: POST JSON-RPC initialize
print("\n=== Testing POST JSON-RPC initialize ===")
init_payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "antigravity", "version": "1.0.0"}
    }
}).encode("utf-8")

for header_name in ["Authorization", "x-api-key"]:
    val = f"Bearer {api_key}" if header_name == "Authorization" else api_key
    req = urllib.request.Request(
        url,
        data=init_payload,
        headers={
            header_name: val,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "MCP-Client/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"POST with {header_name}: status {resp.status}, Content-Type: {resp.headers.get('Content-Type')}")
            body = resp.read(2000).decode("utf-8", errors="replace")
            print("Response body:", body[:500])
    except urllib.error.HTTPError as e:
        print(f"POST with {header_name}: HTTPError {e.code} - {e.reason}")
        err_body = e.read().decode("utf-8", errors="replace")
        print("Error preview:", err_body[:200])
    except Exception as e:
        print(f"POST with {header_name}: Exception: {e}")
