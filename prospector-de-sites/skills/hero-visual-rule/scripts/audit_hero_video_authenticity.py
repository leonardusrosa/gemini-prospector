#!/usr/bin/env python3
"""
HERO_TEMPORAL_MEDIA_GATE (V3.2.3 Final Hardening)

Answers: "Is this genuinely temporal media?"
It does NOT answer: "Is this real footage of this business?"
Representation reality is governed separately by: MEDIA_REPRESENTATION_PROVENANCE.

Classifications:
PASS:
- REAL_VIDEO
- GENUINE_GENERATED_TEMPORAL_VIDEO

FAIL:
- STATIC_IMAGE_WITH_ZOOM
- STATIC_IMAGE_WITH_SHAKE
- STATIC_IMAGE_WITH_PAN
- NEAR_STATIC_SYNTHETIC_VIDEO

INCONCLUSIVE:
- subtle physical movement
- low-light footage
- mostly static tripod footage
- strong compression
- global camera movement with uncertain residual motion

INCONCLUSIVE => do not auto-approve video.
Fallback: STATIC_POSTER.
"""

import sys
import os
import json
import argparse
import subprocess
import hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import zoom, shift
from scipy.optimize import minimize

AUDIT_VERSION = "3.2.3"

def calculate_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def run_ffprobe(video_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_format", "-show_streams",
        "-print_format", "json", video_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)

def extract_frames(video_path, duration, fps, out_dir):
    """
    Sample temporal frames at:
    0%, 20%, 40%, 60%, 80%, last_decodable_frame.
    Avoid 100% timestamp outside final frame.
    """
    os.makedirs(out_dir, exist_ok=True)
    pcts = [0.0, 0.20, 0.40, 0.60, 0.80]
    frame_paths = []

    for pct in pcts:
        t = duration * pct
        out_f = os.path.join(out_dir, f"sample_{int(pct*100):02d}pct.png")
        cmd = [
            "ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", video_path,
            "-vframes", "1", "-q:v", "2", out_f
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        frame_paths.append((pct, out_f))

    # last_decodable_frame: avoid literal duration endpoint
    t_last = max(0.0, duration - max(0.08, 1.5 / max(1.0, fps)))
    out_last = os.path.join(out_dir, "sample_last_decodable_frame.png")
    cmd_last = [
        "ffmpeg", "-y", "-ss", f"{t_last:.3f}", "-i", video_path,
        "-vframes", "1", "-q:v", "2", out_last
    ]
    subprocess.run(cmd_last, capture_output=True, check=True)
    frame_paths.append((1.0, out_last))

    return frame_paths

def classify_temporal_media(raw_mad, residual_mad, variance_reduction, opt_s, opt_dx, opt_dy, is_generated=False, brightness_std=50.0):
    scale_diff = abs(opt_s - 1.0)
    translation_mag = (opt_dx**2 + opt_dy**2)**0.5

    # 1. Near static synthetic video: virtually zero frame difference
    if raw_mad < 1.8:
        return "NEAR_STATIC_SYNTHETIC_VIDEO", "FAIL"

    # 2. Fake zoom: global affine scale explains > 70% of variance, scale_diff > 1.5%
    if scale_diff > 0.015 and variance_reduction > 70.0:
        return "STATIC_IMAGE_WITH_ZOOM", "FAIL"

    # 3. Fake pan: global translation explains > 70% of variance, translation > 5px, scale near 1.0
    if translation_mag > 5.0 and scale_diff <= 0.015 and variance_reduction > 70.0:
        return "STATIC_IMAGE_WITH_PAN", "FAIL"

    # 4. Fake shake / jitter: raw MAD is noticeable, but global translation/scale explains > 75% with small scale, jittery motion
    if raw_mad > 2.5 and variance_reduction > 75.0 and scale_diff < 0.01 and residual_mad < 2.5:
        return "STATIC_IMAGE_WITH_SHAKE", "FAIL"

    # 5. INCONCLUSIVE cases:
    # - Low-light footage: brightness std dev is low (< 18)
    # - Mostly static tripod footage: raw_mad < 3.8 and residual_mad < 2.8
    # - Global camera movement with uncertain residual motion: variance_reduction between 50% and 75%, residual_mad < 3.2
    if brightness_std < 18.0 or (raw_mad < 3.8 and residual_mad < 2.8) or (50.0 <= variance_reduction <= 75.0 and residual_mad < 3.2):
        return "INCONCLUSIVE", "INCONCLUSIVE"

    # 6. PASS: Clear independent scene motion
    if variance_reduction < 60.0 or residual_mad >= 4.0:
        classification = "GENUINE_GENERATED_TEMPORAL_VIDEO" if is_generated else "REAL_VIDEO"
        return classification, "PASS"

    return "INCONCLUSIVE", "INCONCLUSIVE"

def analyze_temporal_media(video_path, poster_path=None, is_generated=False, work_dir="/tmp/temporal_gate_audit"):
    asset_hash = calculate_sha256(video_path)
    probe = run_ffprobe(video_path)
    video_stream = next((s for s in probe["streams"] if s.get("codec_type") == "video"), None)
    if not video_stream:
        raise ValueError("No video stream found in file")

    duration = float(probe["format"].get("duration", video_stream.get("duration", 0)))
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    fps_eval = video_stream.get("avg_frame_rate", "25/1")
    fps = eval(fps_eval) if "/" in fps_eval else float(fps_eval)
    nb_frames = int(video_stream.get("nb_frames") or round(duration * fps))

    frames = extract_frames(video_path, duration, fps, work_dir)
    arr_frames = [np.array(Image.open(f).convert("L"), dtype=np.float32) for _, f in frames]
    h, w = arr_frames[0].shape

    brightness_std = float(np.std(arr_frames[0]))
    raw_mad_end = float(np.mean(np.abs(arr_frames[-1] - arr_frames[0])))

    # Optimize global 2D transform (scale, dx, dy)
    scale_factor = 0.25
    f0_small = np.array(Image.fromarray(arr_frames[0].astype(np.uint8)).resize((int(w * scale_factor), int(h * scale_factor))), dtype=np.float32)
    f_end_small = np.array(Image.fromarray(arr_frames[-1].astype(np.uint8)).resize((int(w * scale_factor), int(h * scale_factor))), dtype=np.float32)
    sh, sw = f0_small.shape

    def loss(params):
        s, dx, dy = params
        scaled = f0_small if abs(s - 1.0) < 1e-4 else zoom(f0_small, s, order=1)
        zh, zw = scaled.shape
        if zh >= sh:
            cropped = scaled[(zh - sh)//2 : (zh - sh)//2 + sh, (zw - sw)//2 : (zw - sw)//2 + sw]
        else:
            pad_y = (sh - zh) // 2
            pad_x = (sw - zw) // 2
            cropped = np.pad(scaled, ((pad_y, sh - zh - pad_y), (pad_x, sw - zw - pad_x)), mode='edge')
        shifted = shift(cropped, (dy, dx), order=1, mode='nearest')
        return float(np.mean(np.abs(shifted - f_end_small)))

    res = minimize(loss, [1.0, 0.0, 0.0], method='Nelder-Mead', options={'maxiter': 100, 'xatol': 0.001, 'fatol': 0.05})
    opt_s, opt_dx_small, opt_dy_small = res.x
    opt_dx = opt_dx_small / scale_factor
    opt_dy = opt_dy_small / scale_factor

    # Evaluate at full resolution
    scaled_full = zoom(arr_frames[0], opt_s, order=1)
    zh, zw = scaled_full.shape
    if zh >= h:
        cropped_full = scaled_full[(zh - h)//2 : (zh - h)//2 + h, (zw - w)//2 : (zw - w)//2 + w]
    else:
        pad_y = (h - zh) // 2
        pad_x = (w - zw) // 2
        cropped_full = np.pad(scaled_full, ((pad_y, h - zh - pad_y), (pad_x, w - zw - pad_x)), mode='edge')

    shifted_full = shift(cropped_full, (opt_dy, opt_dx), order=1, mode='nearest')
    residual_mad = float(np.mean(np.abs(shifted_full - arr_frames[-1])))
    variance_reduction = ((raw_mad_end - residual_mad) / raw_mad_end * 100.0) if raw_mad_end > 0 else 0.0

    classification, verdict = classify_temporal_media(
        raw_mad_end, residual_mad, variance_reduction, opt_s, opt_dx, opt_dy,
        is_generated=is_generated, brightness_std=brightness_std
    )

    temporal_audit = {
        "classification": classification,
        "verdict": verdict,
        "duration": round(duration, 2),
        "fps": round(fps, 1),
        "frameCount": nb_frames,
        "globalTransformDominance": round(variance_reduction / 100.0, 4),
        "residualVariance": round(residual_mad, 2),
        "independentMotion": bool(verdict == "PASS"),
        "auditVersion": AUDIT_VERSION,
        "auditedAssetHash": f"sha256:{asset_hash}"
    }

    return temporal_audit, {
        "raw_mad": raw_mad_end,
        "opt_s": opt_s,
        "opt_dx": opt_dx,
        "opt_dy": opt_dy,
        "residual_mad": residual_mad,
        "variance_reduction": variance_reduction,
        "width": width,
        "height": height,
        "brightness_std": brightness_std
    }

def print_report(temporal_audit, metrics):
    print("==========================================")
    print("HERO_TEMPORAL_MEDIA_GATE REPORT")
    print("Question: 'Is this genuinely temporal media?'")
    print("Disclaimer: Does NOT verify business representation truth.")
    print("==========================================")
    print(f"DURATION: {temporal_audit['duration']} s")
    print(f"RESOLUTION: {metrics['width']}x{metrics['height']}")
    print(f"FPS: {temporal_audit['fps']}")
    print(f"FRAME_COUNT: {temporal_audit['frameCount']}")
    print(f"RAW_MAD: {metrics['raw_mad']:.2f}")
    print(f"GLOBAL_TRANSFORM: scale={metrics['opt_s']:.4f}, dx={metrics['opt_dx']:.1f}px, dy={metrics['opt_dy']:.1f}px")
    print(f"RESIDUAL_MAD: {metrics['residual_mad']:.2f}")
    print(f"VARIANCE_REDUCTION: {metrics['variance_reduction']:.1f}%")
    print(f"TEMPORAL_CLASSIFICATION: {temporal_audit['classification']}")
    print(f"INDEPENDENT_OBJECT_MOTION: {'YES' if temporal_audit['independentMotion'] else 'NO'}")
    print(f"ASSET_SHA256: {temporal_audit['auditedAssetHash']}")
    print(f"GATE_VERDICT: {temporal_audit['verdict']}")
    if temporal_audit["verdict"] == "PASS":
        print("ACTION: ACCEPT_TEMPORAL_MEDIA (Requires separate MEDIA_REPRESENTATION_PROVENANCE check)")
    elif temporal_audit["verdict"] == "INCONCLUSIVE":
        print("ACTION: USE_STATIC_POSTER (Inconclusive motion does not auto-approve; fallback to static poster)")
    else:
        print("ACTION: USE_STATIC_POSTER (Static premium image is preferred over fake cinematic motion)")
    print("==========================================")

def main():
    parser = argparse.ArgumentParser(description="Hero Temporal Media Gate (V3.2.3)")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--poster", help="Optional path to poster image")
    parser.add_argument("--generated", action="store_true", help="Media is known to be synthetic/generated")
    parser.add_argument("--json", action="store_true", help="Print audit JSON payload for manifest")
    args = parser.parse_args()

    temporal_audit, metrics = analyze_temporal_media(
        args.video, args.poster, is_generated=args.generated
    )

    if args.json:
        print(json.dumps(temporal_audit, indent=2))
    else:
        print_report(temporal_audit, metrics)

    sys.exit(0 if temporal_audit["verdict"] == "PASS" else 1)

if __name__ == "__main__":
    main()
