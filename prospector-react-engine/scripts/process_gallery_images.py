import json
from PIL import Image
from pathlib import Path

raw_dir = Path("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/downloaded_maps_photos")
out_dir = Path("e:/Antigravity/prospector/prospector-react-engine/public/assets/gallery")
out_dir.mkdir(parents=True, exist_ok=True)

with open("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/maps_photos_catalog.json") as f:
    catalog = {item["id"]: item for item in json.load(f)}

selected = [
    {
        "id": "gallery-01",
        "rawId": "maps_photo_08",
        "slug": "studio-porsche-cayenne",
        "alt": "Porsche Cayenne inside Addison detailing studio on checkered floor under ceiling LED light bars",
        "aspect": "16/10",
        "category": "Studio Environment"
    },
    {
        "id": "gallery-02",
        "rawId": "maps_photo_05",
        "slug": "rolls-royce-gloss-finish",
        "alt": "Deep black Rolls Royce clearcoat finished to high gloss reflection",
        "aspect": "1/1",
        "category": "High Gloss Finish"
    },
    {
        "id": "gallery-03",
        "rawId": "maps_photo_09",
        "slug": "gmc-sierra-heavy-duty",
        "alt": "White GMC Sierra truck with detailed paint and mirror-polished chrome",
        "aspect": "16/10",
        "category": "Exterior Detail"
    },
    {
        "id": "gallery-04",
        "rawId": "maps_photo_12",
        "slug": "acura-mdx-exterior-service",
        "alt": "White Acura MDX detailed outside the shop with detailing equipment",
        "aspect": "16/10",
        "category": "Vehicle Delivery"
    },
    {
        "id": "gallery-05",
        "rawId": "maps_photo_02",
        "slug": "interior-cockpit-restoration",
        "alt": "Restored driver cockpit, dashboard, and clean floor mats",
        "aspect": "4/5",
        "category": "Interior Cockpit"
    },
    {
        "id": "gallery-06",
        "rawId": "maps_photo_06",
        "slug": "red-metallic-paint-reflection",
        "alt": "Red metallic paint panel polished to clean optical reflection",
        "aspect": "16/10",
        "category": "Surface Correction"
    },
    {
        "id": "gallery-07",
        "rawId": "maps_photo_07",
        "slug": "leather-interior-reconditioning",
        "alt": "Cleaned and conditioned light gray leather rear vehicle seating",
        "aspect": "4/5",
        "category": "Leather Care"
    },
    {
        "id": "gallery-08",
        "rawId": "maps_photo_13",
        "slug": "instrument-cluster-precision",
        "alt": "Dust-free vehicle instrument gauges and dash cluster detail",
        "aspect": "16/10",
        "category": "Precision Detail"
    }
]

manifest = []

for item in selected:
    raw_info = catalog[item["rawId"]]
    raw_file = Path(raw_info["localFile"])
    dest_filename = f"{item['id']}-{item['slug']}.webp"
    dest_path = out_dir / dest_filename

    with Image.open(raw_file) as im:
        # Resize to max 1600px width/height while maintaining aspect
        im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        im.save(dest_path, "WEBP", quality=84, method=6)
        w, h = im.size

    record = {
        "imageId": item["id"],
        "sourceUrl": raw_info["originalUrl"],
        "sourceSurface": "Google Maps Place Profile (0x864c20bdf8a4cd63:0x9e31a704cb899cc4)",
        "sourceType": "GOOGLE_MAPS_BUSINESS_MEDIA",
        "representsActualBusiness": True,
        "businessMatch": "Dallas Detailing And Buffing (16284 Midway Rd, Addison TX)",
        "contentDescription": item["alt"],
        "localPath": f"/assets/gallery/{dest_filename}",
        "width": w,
        "height": h,
        "aspect": item["aspect"],
        "category": item["category"]
    }
    manifest.append(record)
    print(f"Processed {item['id']}: {dest_filename} ({w}x{h}, {dest_path.stat().st_size // 1024} KB)")

manifest_path = Path("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/gallery_manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"\nSaved {len(manifest)} gallery images and manifest successfully.")
