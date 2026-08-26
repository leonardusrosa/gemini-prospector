#!/usr/bin/env python3
"""Workspace convenience wrapper for the Prospector editor publish server."""

from pathlib import Path
import runpy

SCRIPT = Path(__file__).resolve().parent / "prospector-de-sites" / "editor_publish_server.py"
if not SCRIPT.exists():
    raise SystemExit(f"Editor publish server not found: {SCRIPT}")

runpy.run_path(str(SCRIPT), run_name="__main__")
