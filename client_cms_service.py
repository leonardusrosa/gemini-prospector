#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector Client CMS — Core Operations Service Module.
Executes tenant publishing, drafting, rollback, and media uploads
with strict path containment, Git staging isolation, and audit logging.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
from typing import Any, Dict, Optional, Tuple

from client_cms_audit import log_audit_event

MAX_HTML_BYTES = 25 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/svg+xml", "image/gif"}
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_slug(slug: str) -> str:
    """Validates slug format and rejects path traversal."""
    s = (slug or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s or not SLUG_RE.fullmatch(s):
        raise ValueError(f"Identificador de site inválido: '{slug}'")
    return s


def sanitize_html(html: str) -> str:
    """Removes darkreader proxies, editor-only base tag, and temporary runtime styles before saving/publishing."""
    html = re.sub(r'<base\b[^>]*\bdata-pe-ui="true"[^>]*>\s*', "", html, flags=re.IGNORECASE)
    html = re.sub(r'<base\b[^>]*\bdata-pe-ui=\'[^\']*\'[^>]*>\s*', "", html, flags=re.IGNORECASE)
    html = re.sub(r'\s+data-darkreader-[a-zA-Z0-9\-_]+(="[^"]*"|=\'[^\']*\'|=[^\s>]+)?', "", html)
    html = re.sub(r'\s+data-darkreader-proxy-injected="true"', "", html)
    html = re.sub(r'\s+data-pe-author-style="[^"]*"', "", html)
    html = re.sub(r'(<header\b[^>]*)\bclass="([^"]*)\bscrolled\b([^"]*)"', lambda m: m.group(1) + (f' class="{(m.group(2) + " " + m.group(3)).strip()}"' if (m.group(2) + m.group(3)).strip() else ''), html)
    html = re.sub(r'(<a\b[^>]*\bid="floatingWhatsapp"[^>]*)\bclass="([^"]*)\bvisible\b([^"]*)"', lambda m: m.group(1) + (f' class="{(m.group(2) + " " + m.group(3)).strip()}"' if (m.group(2) + m.group(3)).strip() else ''), html)
    html = re.sub(r'\s+class=""', "", html)
    return html


def validate_html(html: str) -> None:
    """Validates that candidate HTML is complete and free of editor UI artifacts."""
    if not isinstance(html, str) or not html.strip():
        raise ValueError("O HTML enviado está vazio.")
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        raise ValueError("O HTML excede o limite máximo permitido de 25 MB.")
    low = html.lower()
    if "</body>" not in low or "</html>" not in low:
        raise ValueError("O HTML está incompleto ou corrompido.")
    forbidden = [
        "prospector-editor-start",
        "data-pe-ui",
        'id="pe-script"',
        "id='pe-script'",
        'id="pe-publish-script"',
        "id='pe-publish-script'",
    ]
    if any(mark in low for mark in forbidden):
        raise ValueError("Artefatos de runtime do editor não podem ser publicados.")


def atomic_write(path: pathlib.Path, text: str) -> None:
    """Writes content atomically with explicit LF newlines."""
    text = sanitize_html(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_file = path.parent / f"{path.name}.{os.getpid()}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        temp_file.replace(path)
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


def backup_version(root_dir: pathlib.Path, slug: str, source_path: pathlib.Path) -> Optional[pathlib.Path]:
    """Creates a local timestamped backup of the current site HTML."""
    if not source_path.exists():
        return None
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    backup_file = root_dir / ".prospector-editor" / "backups" / slug / f"{stamp}.html"
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, backup_file)
    return backup_file


def run_git(repo: pathlib.Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Runs a git command inside the specified repository."""
    git_bin = shutil.which("git") or "git"
    env = dict(os.environ)
    if "HOME" not in env or not env["HOME"]:
        env["HOME"] = "/home/ubuntu" if os.path.exists("/home/ubuntu") else str(pathlib.Path.home())
    return subprocess.run(
        [git_bin, "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
        env=env,
    )


class ClientCmsService:
    def __init__(self, root_dir: pathlib.Path, deploy_repo: Optional[pathlib.Path] = None, base_path: str = "clientes"):
        self.root_dir = root_dir.resolve()
        self.deploy_repo = deploy_repo.resolve() if deploy_repo else None
        self.base_path = base_path.strip("/\\")

    def get_live_file(self, slug: str) -> pathlib.Path:
        v_slug = validate_slug(slug)
        if self.deploy_repo and self.deploy_repo.exists():
            rel = pathlib.PurePosixPath(self.base_path) / v_slug / "index.html"
            return (self.deploy_repo / pathlib.Path(*rel.parts)).resolve()
        return (self.root_dir / "sites" / v_slug / f"{v_slug}.html").resolve()

    def get_live_content(self, slug: str) -> Optional[str]:
        f = self.get_live_file(slug)
        return f.read_text(encoding="utf-8") if f.exists() else None

    def get_live_hash(self, slug: str) -> str:
        content = self.get_live_content(slug)
        return hashlib.sha256(content.encode("utf-8")).hexdigest() if content else ""

    def get_live_commit(self) -> str:
        if self.deploy_repo and self.deploy_repo.exists():
            return run_git(self.deploy_repo, ["rev-parse", "HEAD"], check=False).stdout.strip()
        return ""

    def get_draft_meta_file(self, slug: str) -> pathlib.Path:
        v_slug = validate_slug(slug)
        return self.root_dir / ".prospector-editor" / "drafts" / v_slug / "meta.json"

    def get_draft_file(self, slug: str) -> pathlib.Path:
        v_slug = validate_slug(slug)
        return self.root_dir / ".prospector-editor" / "drafts" / v_slug / f"{v_slug}.html"

    def get_draft_info(self, slug: str) -> Dict[str, Any]:
        v_slug = validate_slug(slug)
        d_file = self.get_draft_file(v_slug)
        m_file = self.get_draft_meta_file(v_slug)
        if not d_file.exists():
            return {"hasDraft": False, "draftState": "none"}
        meta: Dict[str, Any] = {}
        if m_file.exists():
            try:
                meta = json.loads(m_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        live_hash = self.get_live_hash(v_slug)
        base_hash = meta.get("baseContentHash")
        draft_state = "current" if base_hash and base_hash == live_hash else "stale"
        return {
            "hasDraft": True,
            "draftState": draft_state,
            "savedAt": meta.get("savedAt"),
            "actor": meta.get("actor"),
            "baseCommit": meta.get("baseCommit"),
            "baseContentHash": base_hash,
            "draftContentHash": meta.get("draftContentHash"),
        }

    def save_draft(self, slug: str, html_content: str, actor: str, base_content_hash: Optional[str] = None) -> Dict[str, Any]:
        """Saves an isolated draft for a tenant with version metadata."""
        v_slug = validate_slug(slug)
        html_content = sanitize_html(html_content)
        validate_html(html_content)

        draft_file = self.get_draft_file(v_slug)
        atomic_write(draft_file, html_content)

        draft_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
        base_hash = base_content_hash or self.get_live_hash(v_slug)
        meta = {
            "slug": v_slug,
            "savedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "actor": actor,
            "baseCommit": self.get_live_commit(),
            "baseContentHash": base_hash,
            "draftContentHash": draft_hash,
        }
        meta_file = self.get_draft_meta_file(v_slug)
        atomic_write(meta_file, json.dumps(meta, indent=2))
        log_audit_event(self.root_dir, v_slug, actor, "draft", status="success", details={"draftHash": draft_hash, "baseHash": base_hash})

        return {
            "success": True,
            "status": "draft_saved",
            "slug": v_slug,
            "savedAt": meta["savedAt"],
            "baseContentHash": base_hash,
            "draftContentHash": draft_hash,
        }

    def get_draft(self, slug: str) -> Optional[str]:
        """Retrieves an active draft for a tenant if present."""
        v_slug = validate_slug(slug)
        draft_file = self.get_draft_file(v_slug)
        if draft_file.exists():
            return draft_file.read_text(encoding="utf-8")
        return None

    def discard_draft(self, slug: str, actor: str, reason: str = "user_discard") -> bool:
        """Discards an active draft and its metadata."""
        v_slug = validate_slug(slug)
        draft_dir = self.root_dir / ".prospector-editor" / "drafts" / v_slug
        if draft_dir.exists():
            shutil.rmtree(draft_dir, ignore_errors=True)
            log_audit_event(self.root_dir, v_slug, actor, "draft_discard", status="success", details={"reason": reason})
            return True
        return False

    def publish_content(
        self,
        slug: str,
        html_content: str,
        actor: str,
        remote: str = "origin",
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Publishes validated HTML to the deploy repository, commits, and pushes to remote."""
        v_slug = validate_slug(slug)
        html_content = sanitize_html(html_content)
        validate_html(html_content)

        if not self.deploy_repo or not self.deploy_repo.exists():
            raise RuntimeError("Repositório de deploy Git não configurado ou inacessível.")

        rel_path = pathlib.PurePosixPath(self.base_path) / v_slug / "index.html"
        target_path = (self.deploy_repo / pathlib.Path(*rel_path.parts)).resolve()

        if self.deploy_repo not in target_path.parents:
            raise ValueError("Tentativa de escape do diretório do repositório de deploy.")

        # Git preflight 1: verify active branch
        curr_branch = run_git(self.deploy_repo, ["rev-parse", "--abbrev-ref", "HEAD"], check=False).stdout.strip()
        if curr_branch and curr_branch != branch:
            raise RuntimeError(f"Repositório de deploy no branch incorreto: '{curr_branch}' (esperado '{branch}').")

        # Git preflight 2: reset any leftover staging in deploy repo before atomic publish
        run_git(self.deploy_repo, ["reset", "HEAD"], check=False)

        # Backup current file before overwrite
        backup_path = backup_version(self.root_dir, v_slug, target_path)

        # Write sanitized HTML atomically
        atomic_write(target_path, html_content)

        # Stage only this tenant's index.html
        add_res = run_git(self.deploy_repo, ["add", "--", rel_path.as_posix()], check=False)
        if add_res.returncode != 0:
            err_msg = (add_res.stderr or add_res.stdout or "Falha ao preparar arquivos no Git").strip()
            log_audit_event(self.root_dir, v_slug, actor, "publish", status="stage_failed", details={"error": err_msg})
            return {
                "success": False,
                "status": "stage_failed",
                "error": err_msg,
            }

        # Check if diff exists
        diff_check = run_git(self.deploy_repo, ["diff", "--cached", "--quiet", "--", rel_path.as_posix()], check=False)
        if diff_check.returncode == 0:
            log_audit_event(self.root_dir, v_slug, actor, "publish", status="no_changes")
            return {
                "success": True,
                "status": "no_changes",
                "slug": v_slug,
                "message": "Nenhuma alteração detectada para publicação.",
            }

        # Commit
        commit_msg = f"Client publish: {v_slug}"
        commit_res = run_git(self.deploy_repo, ["commit", "-m", commit_msg], check=False)
        if commit_res.returncode != 0:
            err_msg = (commit_res.stderr or commit_res.stdout or "Falha ao criar commit Git").strip()
            log_audit_event(self.root_dir, v_slug, actor, "publish", status="commit_failed", details={"error": err_msg})
            return {
                "success": False,
                "status": "commit_failed",
                "error": err_msg,
            }
        commit_sha = run_git(self.deploy_repo, ["rev-parse", "HEAD"]).stdout.strip()

        # Push
        push_res = run_git(self.deploy_repo, ["push", remote, branch], check=False)
        if push_res.returncode != 0:
            err_msg = (push_res.stderr or push_res.stdout or "Falha ao enviar commit para GitHub").strip()
            log_audit_event(self.root_dir, v_slug, actor, "publish", commit_sha=commit_sha, status="push_failed", details={"error": err_msg})
            return {
                "success": False,
                "status": "push_failed",
                "commit": commit_sha,
                "error": err_msg,
            }

        # Clean up draft after successful publish
        self.discard_draft(v_slug, actor, reason="published")

        log_audit_event(self.root_dir, v_slug, actor, "publish", commit_sha=commit_sha, status="published")

        return {
            "success": True,
            "status": "published_git",
            "slug": v_slug,
            "commit": commit_sha,
            "backup": str(backup_path.relative_to(self.root_dir)) if backup_path else None,
            "publishedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        }

    def rollback_content(
        self,
        slug: str,
        actor: str,
        remote: str = "origin",
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Rolls back the tenant index.html to the most recent backup."""
        v_slug = validate_slug(slug)
        backups_dir = self.root_dir / ".prospector-editor" / "backups" / v_slug
        if not backups_dir.exists():
            raise FileNotFoundError(f"Nenhum backup disponível para o site '{v_slug}'.")

        backup_files = sorted(backups_dir.glob("*.html"))
        if not backup_files:
            raise FileNotFoundError(f"Nenhum arquivo de backup encontrado para '{v_slug}'.")

        latest_backup = backup_files[-1]
        restored_html = latest_backup.read_text(encoding="utf-8")

        res = self.publish_content(
            slug=v_slug,
            html_content=restored_html,
            actor=f"{actor}:rollback",
            remote=remote,
            branch=branch,
        )
        if res.get("success"):
            self.discard_draft(v_slug, actor, reason="rollback")
            log_audit_event(self.root_dir, v_slug, actor, "rollback", commit_sha=res.get("commit"), status="rolled_back", details={"restoredFrom": latest_backup.name})
            res["status"] = "rolled_back"
            res["restoredBackup"] = latest_backup.name
            try:
                latest_backup.unlink(missing_ok=True)
            except Exception:
                pass

        return res
