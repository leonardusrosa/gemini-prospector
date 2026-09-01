#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORE = ROOT / "prospector-de-sites"
RUNTIME_DIR = ROOT / ".prospector"
KNOWN_ADAPTERS = {"generic", "antigravity", "codex", "claude-code", "opencode", "hermes"}


def which(name: str) -> str | None:
    return shutil.which(name)


def normalize_agent(value: str | None) -> str:
    value = (value or "generic").strip().lower()
    return value or "generic"


def adapter_path(agent: str) -> Path:
    candidate = CORE / "adapters" / f"{agent}.md"
    return candidate if candidate.is_file() else CORE / "adapters" / "generic.md"


def command_version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=4,
            check=False,
        )
    except Exception:
        return None
    lines = (result.stdout or "").strip().splitlines()
    return lines[0][:200] if lines else None


def static_capabilities() -> dict:
    crm = CORE / "prospector-mcp.py"
    skills = CORE / "skills"
    open_design_candidate = None

    od = which("od")
    if od:
        open_design_candidate = od
    elif os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            candidate = Path(local) / "Programs" / "Open Design release-stable-win" / "Open Design.exe"
            if candidate.exists():
                open_design_candidate = str(candidate)

    return {
        "platform": platform.platform(),
        "repoRoot": str(ROOT),
        "python": {
            "available": True,
            "path": sys.executable,
            "version": platform.python_version(),
        },
        "node": {
            "available": bool(which("node")),
            "path": which("node"),
            "version": command_version(["node", "--version"]) if which("node") else None,
        },
        "npx": {"available": bool(which("npx")), "path": which("npx")},
        "git": {
            "available": bool(which("git")),
            "path": which("git"),
            "version": command_version(["git", "--version"]) if which("git") else None,
        },
        "prospectorCrmMcp": {
            "available": crm.is_file(),
            "path": str(crm),
            "transport": "stdio",
        },
        "skills": {"available": skills.is_dir(), "path": str(skills)},
        "openDesign": {
            "installedCandidate": bool(open_design_candidate),
            "path": open_design_candidate,
            "runtimeProbeRequired": True,
        },
        "browser": {
            "playwrightMcpLaunchable": bool(which("npx")),
            "runtimeProbeRequired": True,
        },
        "imageGeneration": {
            "runtimeProbeRequired": True,
            "note": "Agent-specific capability. Verified assets/canonical hero templates are the fallback.",
        },
        "github": {"runtimeProbeRequired": True},
        "vercel": {"runtimeProbeRequired": True},
    }


def core_ok(caps: dict) -> bool:
    return bool(
        caps["python"]["available"]
        and caps["prospectorCrmMcp"]["available"]
        and caps["skills"]["available"]
    )


def mcp_config(workspace: Path) -> dict:
    return {
        "mcpServers": {
            "prospector-crm": {
                "command": sys.executable,
                "args": [str(CORE / "prospector-mcp.py"), "--pasta", str(workspace)],
            },
            "playwright": {
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest"],
                "optional": True,
            },
        }
    }


def write_runtime(agent: str, workspace: Path) -> tuple[Path, Path]:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    runtime = {
        "agent": agent,
        "knownAdapter": agent in KNOWN_ADAPTERS,
        "workspace": str(workspace),
        "repoRoot": str(ROOT),
        "canonicalInstructions": str(ROOT / "AGENTS.md"),
        "adapter": str(adapter_path(agent)),
        "capabilities": static_capabilities(),
    }
    runtime_path = RUNTIME_DIR / "runtime.json"
    mcp_path = RUNTIME_DIR / "mcp.generated.json"
    runtime_path.write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mcp_path.write_text(json.dumps(mcp_config(workspace), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return runtime_path, mcp_path


def print_human_doctor(agent: str, caps: dict) -> None:
    print(f"Prospector runtime doctor — agent={agent}")
    print(f"Adapter: {adapter_path(agent)}")
    print(f"Repository: {caps['repoRoot']}")
    rows = [
        ("Python", caps["python"]["available"], caps["python"]["version"]),
        ("Node", caps["node"]["available"], caps["node"]["version"]),
        ("npx", caps["npx"]["available"], caps["npx"]["path"]),
        ("Git", caps["git"]["available"], caps["git"]["version"]),
        ("Prospector CRM MCP", caps["prospectorCrmMcp"]["available"], caps["prospectorCrmMcp"]["path"]),
        ("Canonical skills", caps["skills"]["available"], caps["skills"]["path"]),
        ("OpenDesign installed candidate", caps["openDesign"]["installedCandidate"], caps["openDesign"]["path"]),
        ("Playwright MCP launchable", caps["browser"]["playwrightMcpLaunchable"], "runtime probe required"),
    ]
    for label, ok, detail in rows:
        print(f"{label:30} {'PASS' if ok else 'MISSING':8} {detail or ''}")
    print()
    print("Runtime-only capabilities still require live probes: MCP connectivity, browser, OpenDesign,")
    print("image generation, GitHub/Vercel authentication, and other connected services.")
    print(f"Core status: {'PASS' if core_ok(caps) else 'FAIL'}")


def cmd_doctor(args: argparse.Namespace) -> int:
    agent = normalize_agent(args.agent)
    caps = static_capabilities()
    payload = {
        "agent": agent,
        "adapter": str(adapter_path(agent)),
        "knownAdapter": agent in KNOWN_ADAPTERS,
        "corePass": core_ok(caps),
        "capabilities": caps,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human_doctor(agent, caps)
    return 0 if payload["corePass"] else 1


def cmd_setup(args: argparse.Namespace) -> int:
    agent = normalize_agent(args.agent)
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else ROOT
    runtime_path, mcp_path = write_runtime(agent, workspace)
    print(f"Generated runtime descriptor: {runtime_path}")
    print(f"Generated portable MCP config: {mcp_path}")
    if agent not in KNOWN_ADAPTERS:
        print(f"No dedicated adapter for '{agent}'; using generic adapter.")
    print("Next: make the agent read AGENTS.md, import the generated MCP config using its native")
    print("configuration mechanism, probe live capabilities, and obey canonical repository gates.")
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else ROOT
    print(json.dumps(mcp_config(workspace), ensure_ascii=False, indent=2))
    return 0


def cmd_instructions(args: argparse.Namespace) -> int:
    agent = normalize_agent(args.agent)
    print(ROOT / "AGENTS.md")
    print(adapter_path(agent))
    return 0


def cmd_self_test(_: argparse.Namespace) -> int:
    required = [
        ROOT / "AGENTS.md",
        CORE / "prospector-mcp.py",
        CORE / "skills" / "repository-policy" / "SKILL.md",
        CORE / "skills" / "agent-runtime" / "SKILL.md",
        CORE / "skills" / "design-judge" / "SKILL.md",
        CORE / "skills" / "autonomous-site-review" / "SKILL.md",
        CORE / "adapters" / "generic.md",
        CORE / "mcp_config.example.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print(json.dumps({"pass": False, "missing": missing}, indent=2))
        return 1

    config = mcp_config(ROOT)
    crm_args = config["mcpServers"]["prospector-crm"]["args"]
    if not Path(crm_args[0]).is_file():
        print(json.dumps({"pass": False, "missingCrmTarget": crm_args[0]}, indent=2))
        return 1

    unknown_adapter = adapter_path("some-future-cli")
    if unknown_adapter.name != "generic.md":
        print(json.dumps({"pass": False, "genericFallback": str(unknown_adapter)}, indent=2))
        return 1

    print(json.dumps({"pass": True, "requiredFiles": len(required), "genericFallback": True}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prospector",
        description="Agent-agnostic bootstrap and capability doctor for Prospector.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Inspect static capabilities without claiming runtime connectivity.")
    doctor.add_argument("--agent", default="generic", help="Runtime label. Unknown labels automatically use generic adapter.")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=cmd_doctor)

    setup = sub.add_parser("setup", help="Generate agent-neutral runtime and MCP handoff files.")
    setup.add_argument("--agent", default="generic", help="Runtime label. Unknown labels automatically use generic adapter.")
    setup.add_argument("--workspace", default=None)
    setup.set_defaults(func=cmd_setup)

    mcp = sub.add_parser("mcp-config", help="Print portable MCP server definitions with absolute local paths.")
    mcp.add_argument("--workspace", default=None)
    mcp.set_defaults(func=cmd_mcp)

    instructions = sub.add_parser("instructions", help="Print canonical instruction and selected adapter paths.")
    instructions.add_argument("--agent", default="generic")
    instructions.set_defaults(func=cmd_instructions)

    test = sub.add_parser("self-test", help="Verify the agent-agnostic bootstrap contract.")
    test.set_defaults(func=cmd_self_test)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
