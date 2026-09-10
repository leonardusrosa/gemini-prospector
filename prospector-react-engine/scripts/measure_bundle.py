import os, re, gzip

out_dir = r"e:\Antigravity\prospector\prospector-react-engine\out"
index_path = os.path.join(out_dir, "index.html")

with open(index_path, "r", encoding="utf-8") as f:
    html = f.read()

scripts = re.findall(r'src="([^"]+\.js)"', html)
print(f"Scripts in index.html: {len(scripts)}")
total_raw = 0
total_gzip = 0
for s in scripts:
    s_clean = s.lstrip("/").replace("/", os.sep)
    p = os.path.join(out_dir, s_clean)
    if os.path.exists(p):
        raw = os.path.getsize(p)
        with open(p, "rb") as fp:
            gz = len(gzip.compress(fp.read()))
        total_raw += raw
        total_gzip += gz
        print(f"  {s_clean}: {raw/1024:.1f} KB raw, {gz/1024:.1f} KB gzip")
    else:
        print(f"  {s_clean}: NOT FOUND")

print(f"Total Page JS: raw={total_raw/1024:.1f} KB, gzip={total_gzip/1024:.1f} KB")

# Also measure CSS
styles = re.findall(r'href="([^"]+\.css)"', html)
total_css_raw = 0
total_css_gzip = 0
for st in styles:
    st_clean = st.lstrip("/").replace("/", os.sep)
    p = os.path.join(out_dir, st_clean)
    if os.path.exists(p):
        raw = os.path.getsize(p)
        with open(p, "rb") as fp:
            gz = len(gzip.compress(fp.read()))
        total_css_raw += raw
        total_css_gzip += gz
        print(f"  CSS: {st_clean}: {raw/1024:.1f} KB raw, {gz/1024:.1f} KB gzip")

print(f"Total Page CSS: raw={total_css_raw/1024:.1f} KB, gzip={total_css_gzip/1024:.1f} KB")
print(f"HTML size: raw={len(html.encode('utf-8'))/1024:.1f} KB, gzip={len(gzip.compress(html.encode('utf-8')))/1024:.1f} KB")
