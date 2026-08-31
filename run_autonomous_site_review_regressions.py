#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical runner for the autonomous site-review regression module.

The historical fixture predates fixed-control exclusivity and contains both an
assistant launcher and a floating WhatsApp launcher. Production policy now
forbids that state. This runner normalizes the positive baseline without
weakening any negative regression, then executes every test_* function.

Keep this runner until the legacy fixture module is fully refactored.
"""

from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
MODULE_PATH = ROOT / "test_autonomous_site_review_regression.py"
SPEC = importlib.util.spec_from_file_location("autonomous_regressions", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["autonomous_regressions"] = mod
SPEC.loader.exec_module(mod)

FLOATING_WA = '<a href="https://wa.me/5511999999999" data-role="floating-whatsapp">WhatsApp</a>\n'

# Canonical positive baseline: assistant present => no persistent floating WA.
mod.BASE_MANIFEST["motion"]["floatingCtaSyncRequired"] = False
mod.BASE_MANIFEST["whatsapp"]["floatingRequired"] = False
mod.PASS_HTML = mod.PASS_HTML.replace(FLOATING_WA, "")

_original_run_case = mod.run_case


def run_case(html=None, design_transform=None, manifest=None, custom_setup=None):
    """Preserve the normalized baseline when a test does not supply HTML."""
    if html is None:
        html = mod.PASS_HTML
    return _original_run_case(
        html=html,
        design_transform=design_transform,
        manifest=manifest,
        custom_setup=custom_setup,
    )


mod.run_case = run_case


def test_missing_floating_whatsapp_is_blocked():
    """No assistant + verified WhatsApp still requires the floating launcher."""
    manifest = copy.deepcopy(mod.BASE_MANIFEST)
    manifest["assistant"] = {"present": False, "collisionCheckRequired": False}
    manifest["whatsapp"]["floatingRequired"] = True
    manifest["motion"]["floatingCtaSyncRequired"] = True
    html = mod.PASS_HTML.replace('<button data-role="assistant-launcher">Assistente</button>\n', "")
    code, payload = mod.run_case(html=html, manifest=manifest)
    assert code == 1
    assert "floating_whatsapp_hook" in mod.failed_keys(payload)


mod.test_missing_floating_whatsapp_is_blocked = test_missing_floating_whatsapp_is_blocked


def main() -> int:
    tests = sorted(name for name in vars(mod) if name.startswith("test_"))
    for name in tests:
        getattr(mod, name)()
        print(f"[PASS] {name}")
    print(f"\n{len(tests)}/{len(tests)} autonomous site-review regression cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
