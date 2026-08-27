import os, shutil

src_root = r"E:\Antigravity\prospector\sites\instituto-ferreira-odontologia-rio-claro"
dest_root = r"E:\Antigravity\prospector-sites\clientes\instituto-ferreira-odontologia-rio-claro"

os.makedirs(dest_root, exist_ok=True)
dest_assets = os.path.join(dest_root, "assets")
os.makedirs(dest_assets, exist_ok=True)

# 1. Copy main site -> index.html
src_site = os.path.join(src_root, "instituto-ferreira-odontologia-rio-claro.html")
dest_index = os.path.join(dest_root, "index.html")
shutil.copy2(src_site, dest_index)
print(f"Copied {src_site} -> {dest_index}")

# 2. Copy proposta.html -> proposta.html
src_prop = os.path.join(src_root, "proposta.html")
dest_prop = os.path.join(dest_root, "proposta.html")
shutil.copy2(src_prop, dest_prop)
print(f"Copied {src_prop} -> {dest_prop}")

# 3. Copy assets
src_assets = os.path.join(src_root, "assets")
asset_count = 0
for item in os.listdir(src_assets):
    s = os.path.join(src_assets, item)
    d = os.path.join(dest_assets, item)
    if os.path.isfile(s):
        shutil.copy2(s, d)
        asset_count += 1

print(f"Copied {asset_count} assets to {dest_assets}")

# Verify destination contents
all_dest_files = []
for root, dirs, files in os.walk(dest_root):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), dest_root)
        all_dest_files.append(rel)

print(f"\nTotal copied files: {len(all_dest_files)}")
print(f"Copied asset count: {asset_count}")
print("Destination structure:", all_dest_files)
