from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

in_dir = Path("e:/Antigravity/prospector/sites/dallas-detailing-and-buffing/research/downloaded_maps_photos")
thumb_w, thumb_h = 320, 240
cols, rows = 4, 4

sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), color=(20, 20, 20))
draw = ImageDraw.Draw(sheet)

for idx in range(16):
    file_path = in_dir / f"maps_photo_{idx+1:02d}.jpg"
    if not file_path.exists():
        continue
    try:
        with Image.open(file_path) as im:
            im.thumbnail((thumb_w - 10, thumb_h - 30))
            col = idx % cols
            row = idx // cols
            x = col * thumb_w + (thumb_w - im.width) // 2
            y = row * thumb_h + 25 + (thumb_h - 30 - im.height) // 2
            sheet.paste(im, (x, y))
            draw.text((col * thumb_w + 10, row * thumb_h + 5), f"[{idx+1:02d}] {file_path.name}", fill=(255, 215, 0))
    except Exception as e:
        print(f"Error {idx+1}: {e}")

out_path = Path("e:/Antigravity/prospector/prospector-react-engine/maps_photos_contact_sheet.jpg")
sheet.save(out_path, quality=85)
print("Saved contact sheet to", out_path)

# Also copy to artifacts
import shutil
shutil.copyfile(str(out_path), "C:/Users/leo_b/.gemini/antigravity-ide/brain/e9e77699-be15-4e73-a267-218d256e1de1/maps_photos_contact_sheet.jpg")
