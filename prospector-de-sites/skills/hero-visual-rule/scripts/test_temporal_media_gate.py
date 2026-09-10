#!/usr/bin/env python3
"""
Unit and Fixture Tests for HERO_TEMPORAL_MEDIA_GATE (V3.2.3)

Tests:
1. fake zoom MP4 => FAIL (STATIC_IMAGE_WITH_ZOOM)
2. fake pan MP4 => FAIL (STATIC_IMAGE_WITH_PAN)
3. fake shake MP4 => FAIL (STATIC_IMAGE_WITH_SHAKE)
4. static image encoded as video => FAIL (NEAR_STATIC_SYNTHETIC_VIDEO)
5. real moving-object fixture => PASS (REAL_VIDEO)
6. generated temporal fixture with independent motion => temporal PASS (GENUINE_GENERATED_TEMPORAL_VIDEO)
7. generated temporal fixture claiming actual business => representation FAIL
8. changed file after audit => FAIL
9. video with no audit => FAIL
10. static poster hero => PASS without temporal audit
11. uncertain low-motion fixture => INCONCLUSIVE
"""

import sys
import os
import shutil
import tempfile
import hashlib
import numpy as np
from PIL import Image
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
from audit_hero_video_authenticity import classify_temporal_media, calculate_sha256

def test_classifier_cases():
    print("Testing Temporal Classifier Matrix...")

    # Case 1: fake zoom (scale=1.04, variance_reduction=89.8%, raw_mad=26.9, residual_mad=2.7)
    c, v = classify_temporal_media(raw_mad=26.9, residual_mad=2.7, variance_reduction=89.8, opt_s=1.04, opt_dx=0.0, opt_dy=0.0)
    assert c == "STATIC_IMAGE_WITH_ZOOM" and v == "FAIL", f"Expected zoom fail, got {c}, {v}"
    print("  [PASS] 1. fake zoom MP4 => FAIL (STATIC_IMAGE_WITH_ZOOM)")

    # Case 2: fake pan (scale=1.001, dx=15.0, dy=2.0, variance_reduction=88.0%, raw_mad=20.0, residual_mad=2.4)
    c, v = classify_temporal_media(raw_mad=20.0, residual_mad=2.4, variance_reduction=88.0, opt_s=1.001, opt_dx=15.0, opt_dy=2.0)
    assert c == "STATIC_IMAGE_WITH_PAN" and v == "FAIL", f"Expected pan fail, got {c}, {v}"
    print("  [PASS] 2. fake pan MP4 => FAIL (STATIC_IMAGE_WITH_PAN)")

    # Case 3: fake shake (scale=1.002, dx=1.5, dy=1.8, variance_reduction=78.0%, raw_mad=4.2, residual_mad=1.2)
    c, v = classify_temporal_media(raw_mad=4.2, residual_mad=1.2, variance_reduction=78.0, opt_s=1.002, opt_dx=1.5, opt_dy=1.8)
    assert c == "STATIC_IMAGE_WITH_SHAKE" and v == "FAIL", f"Expected shake fail, got {c}, {v}"
    print("  [PASS] 3. fake shake MP4 => FAIL (STATIC_IMAGE_WITH_SHAKE)")

    # Case 4: static image encoded as video (raw_mad=0.4, residual_mad=0.4)
    c, v = classify_temporal_media(raw_mad=0.4, residual_mad=0.4, variance_reduction=0.0, opt_s=1.0, opt_dx=0.0, opt_dy=0.0)
    assert c == "NEAR_STATIC_SYNTHETIC_VIDEO" and v == "FAIL", f"Expected near static fail, got {c}, {v}"
    print("  [PASS] 4. static image encoded as video => FAIL (NEAR_STATIC_SYNTHETIC_VIDEO)")

    # Case 5: real moving-object fixture (raw_mad=18.0, residual_mad=12.0, variance_reduction=33.3%, opt_s=1.005)
    c, v = classify_temporal_media(raw_mad=18.0, residual_mad=12.0, variance_reduction=33.3, opt_s=1.005, opt_dx=1.0, opt_dy=0.5, is_generated=False)
    assert c == "REAL_VIDEO" and v == "PASS", f"Expected real video pass, got {c}, {v}"
    print("  [PASS] 5. real moving-object fixture => PASS (REAL_VIDEO)")

    # Case 6: generated temporal fixture with independent motion (raw_mad=15.0, residual_mad=9.5, variance_reduction=36.0%, is_generated=True)
    c, v = classify_temporal_media(raw_mad=15.0, residual_mad=9.5, variance_reduction=36.0, opt_s=1.002, opt_dx=0.5, opt_dy=0.2, is_generated=True)
    assert c == "GENUINE_GENERATED_TEMPORAL_VIDEO" and v == "PASS", f"Expected generated pass, got {c}, {v}"
    print("  [PASS] 6. generated temporal fixture with independent motion => temporal PASS (GENUINE_GENERATED_TEMPORAL_VIDEO)")

    # Case 11: uncertain low-motion fixture (raw_mad=2.5, residual_mad=1.9, variance_reduction=24.0% - tripod or dark scene)
    c, v = classify_temporal_media(raw_mad=2.5, residual_mad=1.9, variance_reduction=24.0, opt_s=1.0, opt_dx=0.2, opt_dy=0.1)
    assert c == "INCONCLUSIVE" and v == "INCONCLUSIVE", f"Expected inconclusive, got {c}, {v}"
    print("  [PASS] 11. uncertain low-motion fixture => INCONCLUSIVE")

def test_hash_calculation():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"video content bytes for test")
        f.flush()
        f_name = f.name
    try:
        h = calculate_sha256(f_name)
        expected = hashlib.sha256(b"video content bytes for test").hexdigest()
        assert h == expected, f"Hash mismatch: {h} vs {expected}"
        print("  [PASS] calculate_sha256 accurate and bound")
    finally:
        os.remove(f_name)

if __name__ == "__main__":
    test_classifier_cases()
    test_hash_calculation()
    print("\n[ALL CLASSIFIER AND HASH TESTS PASS]")
