#!/usr/bin/env python3
"""Prospector visual-editor publish server.

Local mode (default):
    python editor_publish_server.py
    open http://127.0.0.1:8787/sites/<slug>/<slug>-editor.html

`Publicar alterações` atomically replaces only the canonical public HTML for the
same slug. It never publishes on each keystroke.

Git mode is intended for an authenticated/protected deployment backend. It writes
only `<basePath>/<slug>/index.html` inside the configured deploy checkout, stages
that exact path, commits, and pushes. Git/Vercel credentials remain server-side.

This is deliberately a narrow content-publish bridge, not a general file-write
API. Never expose it publicly without per-client authorization and HTTPS.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

try:
    from client_cms_auth import TenantAuthStore
    from client_cms_audit import get_audit_history, log_audit_event
    from client_cms_service import ClientCmsService
    from create_editor import EDITOR_LAYER, strip_existing_editor, tag_author_styles
except ImportError:
    from .client_cms_auth import TenantAuthStore
    from .client_cms_audit import get_audit_history, log_audit_event
    from .client_cms_service import ClientCmsService
    from .create_editor import EDITOR_LAYER, strip_existing_editor, tag_author_styles

SCRIPT = pathlib.Path(__file__).resolve()
if (SCRIPT.parent / "prospector-config.json").exists() or (SCRIPT.parent / "sites").exists():
    DEFAULT_ROOT = SCRIPT.parent
elif (SCRIPT.parent.parent / "prospector-config.json").exists() or (SCRIPT.parent.parent / "sites").exists():
    DEFAULT_ROOT = SCRIPT.parent.parent
else:
    DEFAULT_ROOT = SCRIPT.parent

DEFAULT_PORT = 8787
MAX_HTML_BYTES = 25 * 1024 * 1024
TARGET_RE = re.compile(r"^sites/([A-Za-z0-9][A-Za-z0-9._-]*)/\1\.html$")


def _load_json(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _find_config(root: pathlib.Path) -> dict:
    candidates = [
        root / "prospector-config.json",
        root / "prospector-de-sites" / "dashboard" / "prospector-config.json",
        root / "prospector-de-sites" / "prospector-config.json",
    ]
    for path in candidates:
        if path.exists():
            return _load_json(path)
    return {}


def _parse_clients(raw: str) -> dict[str, set[str]]:
    """Parse token->allowed-slug(s) mapping from JSON env.

    Accepted examples:
      {"token-a":"cliente-a"}
      {"token-a":["cliente-a","cliente-b"]}
    """
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
    except Exception as exc:
        raise SystemExit(f"PROSPECTOR_EDITOR_CLIENTS must be valid JSON: {exc}")
    if not isinstance(obj, dict):
        raise SystemExit("PROSPECTOR_EDITOR_CLIENTS must be a JSON object")
    out: dict[str, set[str]] = {}
    for token, slugs in obj.items():
        if not isinstance(token, str) or not token:
            continue
        if isinstance(slugs, str):
            vals = {slugs}
        elif isinstance(slugs, list):
            vals = {str(x) for x in slugs if str(x)}
        else:
            continue
        out[token] = vals
    return out


def _canonical_target(target: str) -> tuple[str, str]:
    target = (target or "").replace("\\", "/").lstrip("/")
    if ".." in pathlib.PurePosixPath(target).parts:
        raise ValueError("Path traversal is not allowed")
    m = TARGET_RE.fullmatch(target)
    if not m:
        raise ValueError("Publish target must be sites/<slug>/<slug>.html")
    return target, m.group(1)


def _validate_html(html: str) -> None:
    if not isinstance(html, str) or not html.strip():
        raise ValueError("HTML is empty")
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        raise ValueError("HTML exceeds the 25 MB editor publish limit")
    low = html.lower()
    if "</body>" not in low or "</html>" not in low:
        raise ValueError("Candidate HTML is incomplete")
    forbidden = [
        "prospector-editor-start",
        "data-pe-ui",
        'id="pe-script"',
        "id='pe-script'",
        'id="pe-publish-script"',
        "id='pe-publish-script'",
    ]
    if any(mark in low for mark in forbidden):
        raise ValueError("Editor runtime/UI must not be published")


def _sanitize_html(html: str) -> str:
    html = re.sub(r'\s+data-darkreader-[a-zA-Z0-9\-_]+(="[^"]*"|=\'[^\']*\'|=[^\s>]+)?', "", html)
    html = re.sub(r'\s+data-darkreader-proxy-injected="true"', "", html)
    html = re.sub(r'\s+data-pe-author-style="[^"]*"', "", html)
    html = re.sub(r'(<header\b[^>]*)\bclass="([^"]*)\bscrolled\b([^"]*)"', lambda m: m.group(1) + (f' class="{(m.group(2) + " " + m.group(3)).strip()}"' if (m.group(2) + m.group(3)).strip() else ''), html)
    html = re.sub(r'(<a\b[^>]*\bid="floatingWhatsapp"[^>]*)\bclass="([^"]*)\bvisible\b([^"]*)"', lambda m: m.group(1) + (f' class="{(m.group(2) + " " + m.group(3)).strip()}"' if (m.group(2) + m.group(3)).strip() else ''), html)
    html = re.sub(r'\s+class=""', "", html)
    return html


def _atomic_write(path: pathlib.Path, text: str) -> None:
    text = _sanitize_html(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def _backup(root: pathlib.Path, slug: str, source: pathlib.Path) -> pathlib.Path | None:
    if not source.exists():
        return None
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    dest = root / ".prospector-editor" / "backups" / slug / f"{stamp}.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest


def _run_git(repo: pathlib.Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    git_bin = shutil.which("git") or "git"
    return subprocess.run(
        [git_bin, "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=check,
    )


class PublishConfig:
    def __init__(self, args: argparse.Namespace):
        self.root = pathlib.Path(args.root).expanduser().resolve()
        cfg = _find_config(self.root)
        deploy = cfg.get("deploy", {}) if isinstance(cfg.get("deploy"), dict) else {}

        self.host = args.host
        self.port = args.port
        self.mode = (args.mode or os.environ.get("PROSPECTOR_EDITOR_PUBLISH_MODE") or "local").strip().lower()
        if self.mode not in {"local", "git"}:
            raise SystemExit("Editor publish mode must be 'local' or 'git'")

        env_repo = os.environ.get("PROSPECTOR_EDITOR_DEPLOY_REPO", "")
        repo_raw = str(args.deploy_repo or env_repo or deploy.get("repoPath") or "").strip()
        self.deploy_repo = pathlib.Path(repo_raw).expanduser().resolve() if repo_raw else None
        self.base_path = (args.base_path or os.environ.get("PROSPECTOR_EDITOR_DEPLOY_BASE_PATH") or deploy.get("basePath") or "clientes").strip("/\\")
        self.branch = args.branch or os.environ.get("PROSPECTOR_EDITOR_DEPLOY_BRANCH") or deploy.get("branch") or "main"
        self.remote = args.remote or os.environ.get("PROSPECTOR_EDITOR_DEPLOY_REMOTE") or "origin"
        self.domain = str(deploy.get("domain") or "").strip().rstrip("/")

        if self.mode == "git":
            if self.deploy_repo is None or not self.deploy_repo.exists():
                raise SystemExit("Git publish mode requires a valid deploy repo path")
            try:
                inside = _run_git(self.deploy_repo, ["rev-parse", "--is-inside-work-tree"]).stdout.strip()
            except Exception as exc:
                raise SystemExit(f"Deploy path is not a usable Git checkout: {exc}")
            if inside != "true":
                raise SystemExit("Deploy path is not inside a Git work tree")

        self.data_dir = pathlib.Path(os.environ.get("PROSPECTOR_CMS_DATA_DIR") or self.root).expanduser().resolve()
        self.auth_store = TenantAuthStore(self.data_dir)
        self.cms_service = ClientCmsService(
            root_dir=self.data_dir,
            deploy_repo=self.deploy_repo,
            base_path=self.base_path,
        )

        self.clients = _parse_clients(os.environ.get("PROSPECTOR_EDITOR_CLIENTS", ""))
        loopback = self.host in {"127.0.0.1", "localhost", "::1"}
        if (self.mode == "git" or not loopback) and not self.clients and not self.auth_store:
            raise SystemExit(
                "Refusing protected/non-local editor publishing without authentication store or PROSPECTOR_EDITOR_CLIENTS."
            )

    def authorize(self, headers, slug: str) -> bool:
        auth = headers.get("Authorization", "")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else headers.get("X-Prospector-Editor-Token", "").strip()

        # Check tenant auth store first
        if token:
            ok, payload, _ = self.auth_store.authorize_request(token, slug)
            if ok:
                return True

        if self.mode == "local" and self.host in {"127.0.0.1", "localhost", "::1"} and not self.clients:
            return True

        allowed = self.clients.get(token, set())
        return slug in allowed or "*" in allowed

    def public_url(self, slug: str) -> str:
        if self.mode == "local":
            return f"http://{self.host}:{self.port}/sites/{slug}/{slug}.html"
        if self.domain:
            domain = self.domain if self.domain.startswith("http") else "https://" + self.domain
            return f"{domain}/{self.base_path}/{slug}/"
        return ""


class PublishApp(SimpleHTTPRequestHandler):
    server_version = "ProspectorEditor/1.0"

    def __init__(self, *args, config: PublishConfig, **kwargs):
        self.config = config
        super().__init__(*args, directory=str(config.root), **kwargs)

    def _client_ip(self) -> str:
        x_forwarded = self.headers.get("X-Forwarded-For", "").strip()
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return self.client_address[0] if self.client_address else "127.0.0.1"

    def _send_security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")

    def _json(self, code: int, obj: dict) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_security_headers()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _html(self, code: int, html_str: str) -> None:
        data = html_str.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._send_security_headers()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_HTML_BYTES + 1024 * 1024:
            raise ValueError("Invalid request size")
        raw = self.rfile.read(n).decode("utf-8")
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            raise ValueError("JSON object required")
        return obj

    def _request_target(self, body: dict) -> tuple[str, str]:
        return _canonical_target(str(body.get("target") or ""))

    def _get_bearer_token(self) -> str:
        auth = self.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        return self.headers.get("X-Prospector-Editor-Token", "").strip()

    def _require_auth(self, slug: str) -> bool:
        if self.config.authorize(self.headers, slug):
            return True
        self._json(401, {"success": False, "error": "Editor authorization required for this site", "requiresToken": True})
        return False

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Prospector-Editor-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Route 1: Client Admin SPA UI (/clientes/<slug>/admin/ or /sites/<slug>/admin)
        admin_match = re.match(r"^/(?:clientes|sites)/([A-Za-z0-9._-]+)/admin(?:/|/index\.html)?$", path)
        if admin_match:
            slug = admin_match.group(1)
            tpl_candidates = [
                self.config.root / "prospector-de-sites" / "client_admin_template.html",
                SCRIPT.parent / "client_admin_template.html",
                self.config.root / "client_admin_template.html",
            ]
            tpl_content = None
            for p in tpl_candidates:
                if p.exists():
                    tpl_content = p.read_text(encoding="utf-8")
                    break
            if tpl_content:
                return self._html(200, tpl_content)
            return self._json(404, {"error": "Admin template not found"})

        # Route 1.5: Client Editor Frame endpoint (dynamic visual editor for tenant)
        if path == "/api/client-cms/editor-frame":
            slug = parse_qs(parsed.query).get("slug", [""])[0]
            token = self._get_bearer_token() or parse_qs(parsed.query).get("token", [""])[0]
            
            # Authorize request for slug
            ok, payload, err = self.config.auth_store.authorize_request(token, slug)
            if not ok:
                return self._json(401, {"success": False, "error": err})

            # Check draft first, then deploy repo HTML, then local sites HTML
            draft_html = self.config.cms_service.get_draft(slug)
            raw_html = None
            if draft_html:
                raw_html = draft_html
            elif self.config.deploy_repo:
                target = self.config.deploy_repo / self.config.base_path / slug / "index.html"
                if target.exists():
                    raw_html = target.read_text(encoding="utf-8")
            if not raw_html:
                local_site = self.config.root / "sites" / slug / f"{slug}.html"
                if local_site.exists():
                    raw_html = local_site.read_text(encoding="utf-8")

            if not raw_html:
                return self._json(404, {"error": f"Página do site para '{slug}' não encontrada."})

            # Inject editor layer dynamically
            clean_html = strip_existing_editor(raw_html)
            clean_html = tag_author_styles(clean_html)
            idx = clean_html.lower().rfind("</body>")
            if idx != -1:
                editor_page = clean_html[:idx] + EDITOR_LAYER + "\n" + clean_html[idx:]
            else:
                editor_page = clean_html + "\n" + EDITOR_LAYER

            return self._html(200, editor_page)

        # Route 2: Client CMS Status API
        if path == "/api/client-cms/status":
            slug = parse_qs(parsed.query).get("slug", [""])[0]
            token = self._get_bearer_token()
            ok, payload, err = self.config.auth_store.authorize_request(token, slug)
            if not ok:
                return self._json(401, {"success": False, "authorized": False, "error": err})
            return self._json(200, {
                "success": True,
                "authorized": True,
                "slug": slug,
                "actor": payload.get("actor"),
                "displayName": slug.replace("-", " ").title(),
            })

        # Route 2.5: Client CMS Draft API (Load Draft)
        if path == "/api/client-cms/draft":
            slug = parse_qs(parsed.query).get("slug", [""])[0]
            token = self._get_bearer_token()
            ok, payload, err = self.config.auth_store.authorize_request(token, slug)
            if not ok:
                return self._json(401, {"success": False, "error": err})
            draft_html = self.config.cms_service.get_draft(slug)
            return self._json(200, {"success": True, "slug": slug, "hasDraft": draft_html is not None, "html": draft_html})

        # Route 3: Client CMS Audit API
        if path == "/api/client-cms/audit":
            slug = parse_qs(parsed.query).get("slug", [""])[0]
            token = self._get_bearer_token()
            ok, payload, err = self.config.auth_store.authorize_request(token, slug)
            if not ok:
                return self._json(401, {"success": False, "error": err})
            history = get_audit_history(self.config.data_dir, slug)
            return self._json(200, {"success": True, "slug": slug, "history": history})

        # Route 4: Legacy editor status
        if path == "/api/editor/status":
            try:
                target, slug = _canonical_target(parse_qs(parsed.query).get("target", [""])[0])
            except ValueError as exc:
                return self._json(400, {"success": False, "error": str(exc)})
            return self._json(200, {
                "success": True,
                "mode": self.config.mode,
                "target": target,
                "slug": slug,
                "requiresToken": bool(self.config.clients),
                "publicUrl": self.config.public_url(slug),
            })

        return super().do_GET()

    def do_POST(self):
        route = urlparse(self.path).path

        # Route A: Client CMS Authentication Login
        if route == "/api/client-cms/auth":
            try:
                body = self._body()
                slug = str(body.get("slug") or "").strip()
                user = str(body.get("username") or "").strip()
                pwd = str(body.get("password") or "")
                client_ip = self._client_ip()
                ok, token_or_err, err_code = self.config.auth_store.authenticate(slug, user, pwd, client_ip=client_ip)
                if ok:
                    return self._json(200, {"success": True, "token": token_or_err, "slug": slug})
                code = 429 if err_code == "RATE_LIMITED" else 401
                return self._json(code, {"success": False, "error": token_or_err, "code": err_code})
            except Exception as exc:
                return self._json(400, {"success": False, "error": str(exc)})

        # Route B: Client CMS Draft Save
        if route == "/api/client-cms/draft":
            try:
                body = self._body()
                slug = str(body.get("slug") or "").strip()
                html = str(body.get("html") or "")
                token = self._get_bearer_token()
                ok, payload, err = self.config.auth_store.authorize_request(token, slug)
                if not ok:
                    return self._json(401, {"success": False, "error": err})
                res = self.config.cms_service.save_draft(slug, html, actor=payload.get("actor", "tenant"))
                return self._json(200, res)
            except Exception as exc:
                return self._json(400, {"success": False, "error": str(exc)})

        # Route C: Client CMS Publish
        if route == "/api/client-cms/publish":
            try:
                body = self._body()
                slug = str(body.get("slug") or "").strip()
                html = str(body.get("html") or "")
                token = self._get_bearer_token()
                ok, payload, err = self.config.auth_store.authorize_request(token, slug)
                if not ok:
                    return self._json(401, {"success": False, "error": err})
                confirmed = bool(body.get("confirmed"))
                if not confirmed:
                    return self._json(400, {"success": False, "error": "Confirmação explícita é obrigatória."})
                res = self.config.cms_service.publish_content(
                    slug=slug,
                    html_content=html,
                    actor=payload.get("actor", "tenant"),
                    remote=self.config.remote,
                    branch=self.config.branch,
                )
                code = 200 if res.get("success") else 502
                return self._json(code, res)
            except Exception as exc:
                return self._json(500, {"success": False, "error": str(exc)})

        # Route D: Client CMS Rollback
        if route == "/api/client-cms/rollback":
            try:
                body = self._body()
                slug = str(body.get("slug") or "").strip()
                token = self._get_bearer_token()
                ok, payload, err = self.config.auth_store.authorize_request(token, slug)
                if not ok:
                    return self._json(401, {"success": False, "error": err})
                confirmed = bool(body.get("confirmed"))
                if not confirmed:
                    return self._json(400, {"success": False, "error": "Confirmação explícita é obrigatória."})
                res = self.config.cms_service.rollback_content(
                    slug=slug,
                    actor=payload.get("actor", "tenant"),
                    remote=self.config.remote,
                    branch=self.config.branch,
                )
                code = 200 if res.get("success") else 502
                return self._json(code, res)
            except Exception as exc:
                return self._json(500, {"success": False, "error": str(exc)})

        # Legacy routes: /api/editor/draft and /api/editor/publish
        if route not in {"/api/editor/draft", "/api/editor/publish"}:
            return self._json(404, {"success": False, "error": "Unknown route"})
        try:
            body = self._body()
            target, slug = self._request_target(body)
            if not self._require_auth(slug):
                return
            html = body.get("html")
            _validate_html(html)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            return self._json(400, {"success": False, "error": str(exc)})

        if route == "/api/editor/draft":
            draft = self.config.root / ".prospector-editor" / "drafts" / slug / f"{slug}.html"
            _atomic_write(draft, html)
            return self._json(200, {
                "success": True,
                "status": "draft_saved",
                "mode": self.config.mode,
                "target": target,
            })

        if not bool(body.get("confirmed")):
            return self._json(400, {"success": False, "error": "Explicit publish confirmation is required"})

        try:
            if self.config.mode == "local":
                dest = (self.config.root / target).resolve()
                sites_root = (self.config.root / "sites").resolve()
                if sites_root not in dest.parents:
                    raise ValueError("Target escaped sites directory")
                backup = _backup(self.config.root, slug, dest)
                _atomic_write(dest, html)
                draft = self.config.root / ".prospector-editor" / "drafts" / slug / f"{slug}.html"
                try:
                    draft.unlink()
                except FileNotFoundError:
                    pass
                return self._json(200, {
                    "success": True,
                    "status": "published_local",
                    "mode": "local",
                    "target": target,
                    "backup": str(backup.relative_to(self.config.root)) if backup else None,
                    "publicUrl": self.config.public_url(slug),
                })

            # Protected git-backed publishing. Never stages arbitrary repository paths.
            repo = self.config.deploy_repo
            assert repo is not None
            rel = pathlib.PurePosixPath(self.config.base_path) / slug / "index.html"
            dest = (repo / pathlib.Path(*rel.parts)).resolve()
            if repo not in dest.parents:
                raise ValueError("Deploy target escaped deploy repository")

            staged_before = _run_git(repo, ["diff", "--cached", "--name-only"]).stdout.strip()
            if staged_before:
                raise RuntimeError("Deploy repository already has staged changes; refusing mixed client publish")

            backup = _backup(self.config.root, slug, dest)
            _atomic_write(dest, html)
            _run_git(repo, ["add", "--", rel.as_posix()])
            diff_check = _run_git(repo, ["diff", "--cached", "--quiet", "--", rel.as_posix()], check=False)
            if diff_check.returncode == 0:
                return self._json(200, {
                    "success": True,
                    "status": "no_changes",
                    "mode": "git",
                    "publicUrl": self.config.public_url(slug),
                })
            if diff_check.returncode not in {0, 1}:
                raise RuntimeError("Could not inspect staged client change")

            _run_git(repo, ["commit", "-m", f"Client publish: {slug}", "--", rel.as_posix()])
            commit = _run_git(repo, ["rev-parse", "HEAD"]).stdout.strip()
            push = _run_git(repo, ["push", self.config.remote, self.config.branch], check=False)
            if push.returncode != 0:
                return self._json(502, {
                    "success": False,
                    "status": "committed_push_failed",
                    "mode": "git",
                    "commit": commit,
                    "error": (push.stderr or push.stdout or "git push failed").strip(),
                })

            draft = self.config.root / ".prospector-editor" / "drafts" / slug / f"{slug}.html"
            try:
                draft.unlink()
            except FileNotFoundError:
                pass
            return self._json(200, {
                "success": True,
                "status": "published_git",
                "mode": "git",
                "commit": commit,
                "backup": str(backup) if backup else None,
                "publicUrl": self.config.public_url(slug),
            })
        except Exception as exc:
            return self._json(500, {"success": False, "error": str(exc), "mode": self.config.mode})

    def log_message(self, fmt, *args):
        # Keep useful local logs without leaking Authorization headers/body.
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Serve Prospector sites/editors with explicit draft/publish actions")
    p.add_argument("--root", default=str(DEFAULT_ROOT), help="Prospector workspace root")
    p.add_argument("--host", default="127.0.0.1", help="Bind host; non-loopback requires client token mapping")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--mode", choices=["local", "git"], help="Override PROSPECTOR_EDITOR_PUBLISH_MODE")
    p.add_argument("--deploy-repo", help="Git-mode deploy checkout; defaults to env/config deploy.repoPath")
    p.add_argument("--base-path", help="Git-mode client base path; defaults to config deploy.basePath")
    p.add_argument("--branch", help="Git-mode production branch")
    p.add_argument("--remote", default="origin", help="Git remote name")
    return p


def main() -> None:
    args = build_parser().parse_args()
    config = PublishConfig(args)

    def handler(*h_args, **h_kwargs):
        return PublishApp(*h_args, config=config, **h_kwargs)

    print(f"Prospector editor server: http://{config.host}:{config.port}")
    print(f"Mode: {config.mode}")
    print("Publish is explicit only; edits are never auto-published.")
    if config.mode == "local":
        print("Open the *-editor.html through this server, then click 'Publicar alterações'.")
    else:
        print(f"Deploy repo: {config.deploy_repo} | {config.remote}/{config.branch} | basePath={config.base_path}")
    try:
        ThreadingHTTPServer((config.host, config.port), handler).serve_forever()
    except KeyboardInterrupt:
        print("\nEditor server stopped.")


if __name__ == "__main__":
    main()
