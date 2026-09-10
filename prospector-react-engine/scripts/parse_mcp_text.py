import os
import re
import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = r"e:\Antigravity\prospector\prospector-react-engine\scripts\mcp_results"

def parse_mcp_text(raw_text):
    # Parse items matching pattern
    # ### [component] Name [id: 123]
    pattern = re.compile(
        r"###\s*\[(?P<type>[^\]]+)\]\s*(?P<name>[^\n\[]+)\[id:\s*(?P<id>\d+)\]\s*\n"
        r"by\s*(?P<author>[^\n]+)\s*\n"
        r"(?P<description>.*?)"
        r"(?:preview:\s*(?P<preview>[^\n]+)\s*\n)?"
        r"(?:install:\s*(?P<install>[^\n]+)\s*\n)?"
        r"(?:.*?get_component\(\{\s*id:\s*(?P<get_id>\d+)\s*\}\))?",
        re.DOTALL
    )

    items = []
    # Split by ### [
    blocks = raw_text.split("### [")
    for block in blocks[1:]:
        full_block = "### [" + block
        m = pattern.search(full_block)
        if m:
            desc = m.group("description").strip()
            # Clean up desc if preview was matched or inside
            if "preview:" in desc:
                desc = desc.split("preview:")[0].strip()
            items.append({
                "type": m.group("type").strip(),
                "name": m.group("name").strip(),
                "id": int(m.group("id")),
                "author": m.group("author").strip(),
                "description": desc,
                "preview": (m.group("preview") or "").strip(),
                "install": (m.group("install") or "").strip()
            })
        else:
            # Fallback simple extraction
            id_match = re.search(r"\[id:\s*(\d+)\]", full_block)
            by_match = re.search(r"\nby\s+([^\n]+)", full_block)
            name_match = re.search(r"###\s*\[[^\]]+\]\s*([^\[\n]+)", full_block)
            if id_match and name_match:
                items.append({
                    "name": name_match.group(1).strip(),
                    "id": int(id_match.group(1)),
                    "author": by_match.group(1).strip() if by_match else "unknown",
                    "description": "",
                    "preview": "",
                    "install": ""
                })
    return items

categories = ["hero", "services", "image comparison", "reviews", "navigation", "closing"]
all_parsed = {}

for cat in categories:
    file_path = os.path.join(OUT_DIR, f"search_{cat.replace(' ', '_')}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        items = parse_mcp_text(raw)
        all_parsed[cat] = items
        print(f"\n================================")
        print(f"Category: '{cat.upper()}' (Total Found: {len(items)})")
        print(f"================================")
        for i, item in enumerate(items[:5]):
            print(f"[{i+1}] {item['name']} [id: {item['id']}] by @{item['author']}")
            if item['description']:
                print(f"    Desc: {item['description'][:90]}...")
            if item['install']:
                print(f"    Install: {item['install']}")

with open(os.path.join(OUT_DIR, "all_parsed_categories.json"), "w", encoding="utf-8") as f:
    json.dump(all_parsed, f, indent=2)
print("\nSaved parsed categories to all_parsed_categories.json")
