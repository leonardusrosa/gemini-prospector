#!/usr/bin/env python3
"""Workspace convenience wrapper for the plugin-bundled visual editor generator."""

from pathlib import Path
import importlib.util
import runpy
import sys

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "prospector-de-sites" / "create_editor.py"
PATCHER = ROOT / "prospector-de-sites" / "editor_brand_media_patch.py"

if not SCRIPT.exists():
    raise SystemExit(f"Editor generator not found: {SCRIPT}")

# Resolve the editor output before running the canonical generator so we can apply
# post-generation compatibility fixes without changing the public source HTML.
args = sys.argv[1:]
source = Path(args[0]) if args else None
output = None
if source:
    for i, arg in enumerate(args[1:], start=1):
        if arg in {"--output", "-o"} and i + 1 < len(args):
            output = Path(args[i + 1])
            break
    if output is None:
        output = source if source.stem.endswith("-editor") else source.with_name(source.stem + "-editor" + source.suffix)

runpy.run_path(str(SCRIPT), run_name="__main__")

if output and output.exists() and PATCHER.exists():
    spec = importlib.util.spec_from_file_location("prospector_editor_brand_patch", PATCHER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load editor brand-media patcher: {PATCHER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.patch_editor(output)
    print(f"Logo/brand media editing enabled in: {output}")
