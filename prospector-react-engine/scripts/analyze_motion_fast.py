import os
import numpy as np
from PIL import Image
from scipy.ndimage import zoom, shift
from scipy.optimize import minimize

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

print(f"\nFull Frame Dimensions: {w}x{h}")
for i in range(1, len(frames)):
    raw_diff = np.mean(np.abs(arr_frames[i] - arr_frames[0]))
    print(f"Frame {i*20}% vs Frame 00% raw MAD: {raw_diff:.2f}")

# 3. Fast Optimization for Global Transformation (Scale + Translation)
# Downsample to 344x192 for rapid optimization
scale_factor = 0.25
f0_small = np.array(Image.fromarray(arr_frames[0].astype(np.uint8)).resize((int(w * scale_factor), int(h * scale_factor))), dtype=np.float32)
f_end_small = np.array(Image.fromarray(arr_frames[-1].astype(np.uint8)).resize((int(w * scale_factor), int(h * scale_factor))), dtype=np.float32)
sh, sw = f0_small.shape

def loss(params):
    s, dx, dy = params
    # zoom f0_small
    if abs(s - 1.0) < 1e-4:
        scaled = f0_small
    else:
        scaled = zoom(f0_small, s, order=1)
    
    zh, zw = scaled.shape
    # center crop or pad
    if zh >= sh:
        y0 = (zh - sh) // 2
        x0 = (zw - sw) // 2
        cropped = scaled[y0:y0+sh, x0:x0+sw]
    else:
        pad_y = (sh - zh) // 2
        pad_x = (sw - zw) // 2
        cropped = np.pad(scaled, ((pad_y, sh - zh - pad_y), (pad_x, sw - zw - pad_x)), mode='edge')
    
    # apply shift
    shifted = shift(cropped, (dy, dx), order=1, mode='nearest')
    return float(np.mean(np.abs(shifted - f_end_small)))

# Run optimization from (1.0, 0, 0)
res = minimize(loss, [1.0, 0.0, 0.0], method='Nelder-Mead', options={'maxiter': 100, 'xatol': 0.001, 'fatol': 0.05})

opt_s, opt_dx_small, opt_dy_small = res.x
opt_dx = opt_dx_small / scale_factor
opt_dy = opt_dy_small / scale_factor

# Evaluate at full resolution
scaled_full = zoom(arr_frames[0], opt_s, order=1)
zh, zw = scaled_full.shape
if zh >= h:
    y0 = (zh - h) // 2
    x0 = (zw - w) // 2
    cropped_full = scaled_full[y0:y0+h, x0:x0+w]
else:
    pad_y = (h - zh) // 2
    pad_x = (w - zw) // 2
    cropped_full = np.pad(scaled_full, ((pad_y, h - zh - pad_y), (pad_x, w - zw - pad_x)), mode='edge')

shifted_full = shift(cropped_full, (opt_dy, opt_dx), order=1, mode='nearest')
residual_mad = float(np.mean(np.abs(shifted_full - arr_frames[-1])))
raw_mad_end = float(np.mean(np.abs(arr_frames[-1] - arr_frames[0])))
variance_reduction = ((raw_mad_end - residual_mad) / raw_mad_end) * 100.0

print("\n=== STABILIZATION TEST RESULTS ===")
print(f"Raw MAD (Frame 00% vs Frame 100%): {raw_mad_end:.2f}")
print(f"Optimal Global Transform: Scale={opt_s:.4f}, dx={opt_dx:.1f}px, dy={opt_dy:.1f}px")
print(f"Residual MAD after Global Transform: {residual_mad:.2f}")
print(f"Variance Reduction: {variance_reduction:.1f}%")

# Generate Difference Maps
diff_raw = np.clip(np.abs(arr_frames[-1] - arr_frames[0]) * 3.0, 0, 255).astype(np.uint8)
diff_stabilized = np.clip(np.abs(shifted_full - arr_frames[-1]) * 3.0, 0, 255).astype(np.uint8)

Image.fromarray(diff_raw).save(os.path.join(DIR, "diff_raw_amplified.png"))
Image.fromarray(diff_stabilized).save(os.path.join(DIR, "diff_stabilized_amplified.png"))
print(f"Saved difference maps to {DIR}")

# Check local motion variance in interior detail regions
# (e.g. check if high residual error is concentrated on moving elements or uniform noise)
std_residual = float(np.std(np.abs(shifted_full - arr_frames[-1])))
print(f"Residual Standard Deviation: {std_residual:.2f}")

if residual_mad < 3.5 or variance_reduction > 70.0:
    print("\nRESULT CLASSIFICATION: SYNTHETIC_STILL_MOTION (Ken Burns / Pan / Zoom on static 2D image)")
elif raw_mad_end < 2.0:
    print("\nRESULT CLASSIFICATION: NEAR_STATIC")
else:
    print("\nRESULT CLASSIFICATION: REAL_SCENE_MOTION")
