import json
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

with open(r"e:\Antigravity\prospector\prospector-react-engine\scripts\search_image_comparison.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("Type:", type(data))
if isinstance(data, list):
    print(f"Items count: {len(data)}")
    for i, item in enumerate(data[:10]):
        author_info = item.get("author") or {}
        username = author_info.get("username") if isinstance(author_info, dict) else str(author_info)
        print(f"\n[{i+1}] {item.get('name')} by @{username}")
        print(f"    ID: {item.get('id')}")
        print(f"    Component Name: {item.get('component_name')}")
        print(f"    Description: {str(item.get('description', ''))[:120]}")
elif isinstance(data, dict):
    print("Keys in dict:", list(data.keys()))
    for k, v in data.items():
        if isinstance(v, list):
            print(f"Key '{k}' has {len(v)} items")
            for i, item in enumerate(v[:5]):
                if isinstance(item, dict):
                    print(f"  - {item.get('name')} | id: {item.get('id')}")
