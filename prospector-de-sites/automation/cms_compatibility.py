"""Structural compatibility gate for the existing AutoCORA Client CMS.

Canonical implementation: prospector-dashboard docs/client-cms-framework.md,
lib/editor-layer.ts, lib/cms-store.ts and client-admin-template.html.
This verifies *static HTML editability*, not live provisioning or visual
editor correctness. A separately authenticated CMS E2E is mandatory before
final client handoff; this script cannot provide or fake that verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class SiteProbe(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: dict[str, int] = {}
        self.lang = None
        self.title_text = ""
        self.in_title = False
        self.meta_viewport = False
        self.head = False
        self.body = False
        self.charset = False
        self.no_edit_headers = 0
        self.editor_injected = False
        self.images = 0
        self.actions = 0
        self.text_elements = 0
        self.css_bg_editable = 0
        self.script_sources: list[str] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.forms = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "head":
            self.head = True
        if tag == "body":
            self.body = True
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            if attrs.get("name", "").lower() == "viewport":
                self.meta_viewport = "width=device-width" in attrs.get("content", "").lower()
            if attrs.get("charset"):
                self.charset = True
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "figcaption"}:
            self.text_elements += 1
        if tag == "img":
            self.images += 1
        if tag in {"a", "button"}:
            self.actions += 1
        if tag == "form":
            self.forms += 1
        if attrs.get("data-pe-bg-src"):
            self.css_bg_editable += 1
        if attrs.get("id"):
            if attrs["id"] in self.ids:
                self.duplicate_ids.add(attrs["id"])
            self.ids.add(attrs["id"])
        if tag == "script" and attrs.get("src"):
            self.script_sources.append(attrs["src"])
        if attrs.get("data-pe-ui") is not None or attrs.get("id") in {"pe-script", "pe-style"}:
            self.editor_injected = True
        if tag in {"h1", "h2"} and attrs.get("data-pe-no-edit") is not None:
            self.no_edit_headers += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data.strip()


def audit_html_file(html_path: Path, expected_slug: str | None = None) -> dict:
    html_path = Path(html_path)
    if not html_path.is_file() or html_path.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("CMS requires a real HTML file")
    html_bytes = html_path.read_bytes()
    if len(html_bytes) > 5_000_000:
        raise ValueError("Large HTML files need independent editor-limit benchmarking")
    html = html_bytes.decode("utf-8-sig", errors="strict")
    parser = SiteProbe()
    parser.feed(html)
    failures: list[str] = []
    warnings: list[str] = []

    if not re.search(r"(?i)<!doctype\s+html>", html):
        failures.append("Missing HTML5 doctype")
    if not (parser.head and parser.body and parser.lang):
        failures.append("Missing html[lang], head or body document structure")
    if not (parser.charset and parser.meta_viewport):
        failures.append("Missing UTF-8 charset or responsive viewport metadata")
    if not parser.title_text:
        failures.append("Missing page title")
    if parser.tags.get("h1", 0) < 1 or parser.text_elements < 3:
        failures.append("Not enough semantic inline-editable text")
    if parser.actions < 1:
        failures.append("No inline-editable action/link target")
    if parser.images < 1 and parser.css_bg_editable < 1:
        warnings.append("No directly editable image or marked CSS background")
    if parser.editor_injected or "PROSPECTOR-EDITOR-START" in html:
        failures.append("Generated site must not persist injected CMS editor/chrome")
    if re.search(r"(?i)\bcontenteditable\s*=", html):
        failures.append("Generated site must not persist contenteditable state")
    if parser.duplicate_ids:
        failures.append("Duplicate element ids risk corrupting editor properties")
    if re.search(r"(?i)(?:id=[\\\"']__next[\\\"']|__NEXT_DATA__|/_next/static/)", html):
        failures.append("Hydrated Next.js runtime cannot be assumed safe for HTML-roundtrip CMS")
    if re.search(r"(?i)\b(?:document\.write|outerHTML\s*=)", html):
        warnings.append("Dynamic DOM replacement requires a dedicated CMS E2E")
    if expected_slug:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", expected_slug):
            raise ValueError("Invalid expected site slug")
        if expected_slug not in str(html_path).replace("\\\\", "/"):
            warnings.append("Site path is not under the canonical client's slug directory")

    return {
        "schemaVersion": 1, "validator": "autocora-cms-html-structural-v1",
        "result": "STRUCTURE_PASS" if not failures else "BLOCK",
        "htmlSha256": hashlib.sha256(html_bytes).hexdigest(),
        "requirements": {
            "siteRuntime": "static HTML, JS/CSS allowed if compatible with roundtrip edits",
            "adminUrlPattern": "/clientes/{slug}/admin/",
            "publishedCmsRoutePattern": "/clientes/{slug}/site/",
            "clientEditable": ["text", "images", "CTA and social links", "contact details"],
            "operatorProvisioningNeeded": True,
            "tenantLocaleMustEqualLeadLocale": True,
            "clientAdminRuntimeE2EStillRequired": True,
            "cmsChromeOnlyInAuthenticatedAdminShell": True,
            "protectedPreviewDoesNotAuthorizePublicPublication": True,
        },
        "observed": {
            "htmlLanguage": parser.lang, "h1Count": parser.tags.get("h1", 0),
            "semanticTextNodes": parser.text_elements,
            "imageElements": parser.images,
            "editableBackgroundCandidates": parser.css_bg_editable,
            "actionElements": parser.actions, "formElements": parser.forms,
            "externalScriptReferences": len(parser.script_sources),
        },
        "failures": failures, "warnings": warnings,
        "tenantProvisioned": False, "runtimeCmsSmokePassed": False,
        "publicReleaseAuthorized": False,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description="Read-only CMS HTML compatibility audit")
    cli.add_argument("--html", type=Path, required=True)
    cli.add_argument("--slug")
    options = cli.parse_args()
    audit = audit_html_file(options.html, options.slug)
    print(json.dumps(audit, sort_keys=True))
    return 0 if audit["result"] == "STRUCTURE_PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"result": "BLOCK", "reason": type(exc).__name__,
                          "detail": str(exc)[:170], "publicReleaseAuthorized": False}))
        raise SystemExit(2)
