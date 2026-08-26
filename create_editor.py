#!/usr/bin/env python3
"""Workspace convenience wrapper for the plugin-bundled visual editor generator."""

from pathlib import Path
import runpy

SCRIPT = Path(__file__).resolve().parent / "prospector-de-sites" / "create_editor.py"
if not SCRIPT.exists():
    raise SystemExit(f"Editor generator not found: {SCRIPT}")

runpy.run_path(str(SCRIPT), run_name="__main__")
