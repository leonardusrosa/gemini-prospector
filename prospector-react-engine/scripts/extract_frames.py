import os
import subprocess
from PIL import Image

OUT_DIR = r"e:\Antigravity\prospector\prospector-react-engine\scripts\video_audit"
os.makedirs(OUT_DIR, exist_ok=True)

VIDEO_PATH = r"e:\Antigravity\prospector\prospector-react-engine\public\assets\hero-video.mp4"

# Timestamps for 0%, 20%, 40%, 60%, 80%, 100%
timestamps = [
    ("00", "0.0"),
    ("20", "1.2"),
    ("40", "2.4"),
    ("60", "3.6"),
    ("80", "4.8"),
    ("100", "5.96")
]

extracted_images = []

for pct, t in timestamps:
    out_file = os.path.join(OUT_DIR, f"frame_{pct}pct.png")
    cmd = [
        "ffmpeg", "-y", "-ss", t, "-i", VIDEO_PATH,
        "-vframes", "1", "-q:v", "2", out_file
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Extracted frame at {pct}% ({t}s) -> {out_file}")
    extracted_images.append(out_file)

# Create contact sheet (2 rows of 3 columns)
cols = 3
rows = 2
w, h = 1376, 768
thumb_w = w // 2 # 688
thumb_h = h // 2 # 384

contact_sheet = Image.new("RGB", (thumb_w * cols, thumb_h * rows), (10, 10, 10))

for idx, img_path in enumerate(extracted_images):
    im = Image.open(img_path)
    im_thumb = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    c = idx % cols
    r = idx // cols
    contact_sheet.paste(im_thumb, (c * thumb_w, r * thumb_h))

contact_sheet_path = os.path.join(OUT_DIR, "contact_sheet.jpg")
contact_sheet.save(contact_sheet_path, quality=92)
print(f"Saved contact sheet to {contact_sheet_path}")
