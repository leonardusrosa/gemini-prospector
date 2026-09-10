import json
import urllib.request
from PIL import Image
from pathlib import Path

urls_file = Path("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/dallas_maps_photos_final.json")
with open(urls_file, "r") as f:
    urls = json.load(f)

out_dir = Path("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/downloaded_maps_photos")
out_dir.mkdir(parents=True, exist_ok=True)

catalog = []

for idx, url in enumerate(urls):
    # append =s1600 to get high-res original
    download_url = f"{url}=s1600"
    file_name = f"maps_photo_{idx+1:02d}.jpg"
    target_path = out_dir / file_name

    try:
        req = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            target_path.write_bytes(data)

        with Image.open(target_path) as im:
            w, h = im.size
            aspect = round(w / h, 2)
            catalog.append({
                "id": f"maps_photo_{idx+1:02d}",
                "originalUrl": url,
                "downloadUrl": download_url,
                "localFile": str(target_path),
                "width": w,
                "height": h,
                "aspect": aspect,
                "bytes": len(data),
                "format": im.format
            })
            print(f"[{idx+1:02d}] {file_name}: {w}x{h} ({aspect} aspect) - {len(data)//1024} KB")
    except Exception as e:
        print(f"[{idx+1:02d}] Failed: {e}")

catalog_file = Path("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/maps_photos_catalog.json")
with open(catalog_file, "w") as f:
    json.dump(catalog, f, indent=2)

print(f"\nSuccessfully downloaded and cataloged {len(catalog)} photos.")
