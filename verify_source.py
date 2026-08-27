import os, re

src_dir = r"E:\Antigravity\prospector\sites\instituto-ferreira-odontologia-rio-claro"
site_path = os.path.join(src_dir, "instituto-ferreira-odontologia-rio-claro.html")
prop_path = os.path.join(src_dir, "proposta.html")

print("=== VERIFYING PROPOSTA.HTML ===")
with open(prop_path, "r", encoding="utf-8") as f:
    prop_html = f.read()

hrefs = re.findall(r'href=["\'](.*?)["\']', prop_html)
print("All hrefs in proposta.html:", hrefs)
cta_present = "./" in hrefs
print("Proposal CTA uses href='./':", cta_present)

print("\n=== VERIFYING SITE HTML ===")
with open(site_path, "r", encoding="utf-8") as f:
    site_html = f.read()

checks = {
    "data-pe-author-style": "data-pe-author-style" in site_html,
    "PROSPECTOR-EDITOR": "PROSPECTOR-EDITOR" in site_html,
    "editor toolbar/runtime": "editor-toolbar" in site_html or "prospector-editor" in site_html,
    "localhost URLs": "localhost:" in site_html or "localhost/" in site_html or "127.0.0.1:" in site_html,
    "file://": "file://" in site_html,
    "vscode-file://": "vscode-file://" in site_html,
}

for name, found in checks.items():
    print(f"Check '{name}': {'FOUND (FAIL)' if found else 'CLEAN (PASS)'}")

all_clean = not any(checks.values()) and cta_present
print(f"\nSOURCE QA OVERALL: {'PASS' if all_clean else 'FAIL'}")
