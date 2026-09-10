import os
import numpy as np
from PIL import Image
from scipy.ndimage import zoom, shift

DIR = r"e:\Antigravity\prospector\prospector-react-engine\scripts\video_audit"
POSTER = r"e:\Antigravity\prospector\prospector-react-engine\public\assets\hero-poster.webp"

frames = [
    os.path.join(DIR, f"frame_{pct}pct.png")
    for pct in ["00", "20", "40", "60", "80", "100"]
]

print("=== TEMPORAL MOTION AUDIT ===")

# 1. Compare frame 0 with hero-poster.webp
im_poster = Image.open(POSTER).convert("RGB")
im_f0 = Image.open(frames[0]).convert("RGB")

arr_poster = np.array(im_poster, dtype=np.float32)
arr_f0 = np.array(im_f0, dtype=np.float32)

poster_diff = np.mean(np.abs(arr_poster - arr_f0))
print(f"Poster vs Frame 0 Mean Absolute Diff: {poster_diff:.2f} / 255.0")

# 2. Compare frames over time
arr_frames = [np.array(Image.open(f).convert("L"), dtype=np.float32) for f in frames]
h, w = arr_frames[0].shape

print(f"\nFrame Dimensions: {w}x{h}")
for i in range(1, len(frames)):
    raw_diff = np.mean(np.abs(arr_frames[i] - arr_frames[0]))
    print(f"Frame {i*20}% vs Frame 00% raw MAD: {raw_diff:.2f}")

# 3. Test global transformation between Frame 0 and Frame 100%
# Test if Frame 100% is simply a scaled or translated version of Frame 0
# We search over scale (0.95 to 1.10) and translation (dx, dy)
f0 = arr_frames[0]
f_end = arr_frames[-1]

best_error = float("inf")
best_params = (1.0, 0, 0)

# Multi-scale grid search
for s in np.linspace(0.98, 1.08, 21):
    # Rescale f0
    if s == 1.0:
        scaled = f0
    else:
        scaled = zoom(f0, s, order=1)
    
    # Crop or pad to original size
    sh, sw = scaled.shape
    if s >= 1.0:
        y_start = (sh - h) // 2
        x_start = (sw - w) // 2
        cropped = scaled[y_start:y_start+h, x_start:x_start+w]
    else:
        pad_y = (h - sh) // 2
        pad_x = (w - sw) // 2
        cropped = np.pad(scaled, ((pad_y, h - sh - pad_y), (pad_x, w - sw - pad_x)), mode='edge')
    
    # Check translations
    for dy in range(-15, 16, 3):
        for dx in range(-25, 26, 5):
            shifted = shift(cropped, (dy, dx), order=1, mode='nearest')
            err = np.mean(np.abs(shifted - f_end))
            if err < best_error:
                best_error = err
                best_params = (s, dx, dy)

s_best, dx_best, dy_best = best_params
raw_err_end = np.mean(np.abs(f_end - f0))

print("\n=== STABILIZATION TEST RESULTS ===")
print(f"Raw MAD between Frame 00% and Frame 100%: {raw_err_end:.2f}")
print(f"Best global affine fit: scale={s_best:.4f}, dx={dx_best}px, dy={dy_best}px")
print(f"Residual MAD after global stabilization: {best_error:.2f}")
variance_reduction = ((raw_err_end - best_error) / raw_err_end) * 100
print(f"Variance reduction from pure global transform: {variance_reduction:.1f}%")

if best_error < 4.0 or variance_reduction > 75.0:
    print("\nCLASSIFICATION: SYNTHETIC_STILL_MOTION (Ken Burns / Zoom / Pan on static 2D image)")
else:
    print("\nCLASSIFICATION: REAL_SCENE_MOTION")
