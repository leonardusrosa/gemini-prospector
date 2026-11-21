"""Engine C -> AutoCORA Client CMS collection-markup handoff.

Conservatively annotates *existing* generated static HTML cards using IDs from
a separately source-reviewed research manifest. Never invents a menu item,
doctor, price, service, photograph, link, or business fact.

This structural tool cannot establish the truth of source information,
copyright rights, authenticated CMS tenant provisioning or public-release
permission. It performs no network calls, site generation, DB writes, or
outreach. Output is written to a new file and never overwrites source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from site_research import https_url

KINDS = {"menu", "gallery", "services", "team", "pricing"}
PRIORITY_NICHES = {"restaurant", "pizzeria", "cafe", "dentistry", "clinic"}
FOOD = {"restaurant", "pizzeria", "cafe"}
CLINICAL = {"dentistry", "clinic"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_:-]{0,119}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}
SAFE_LIST_TAGS = {"div", "ul", "ol", "section"}
SAFE_ITEM_TAGS = {"article", "li", "figure", "div"}
MAX_COLLECTION_ITEMS = 40


def sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass
class Element:
    tag: str
    attrs: dict[str, str | None]
    start: int
    raw: str
    parent: "Element | None" = None
    children: list["Element"] = field(default_factory=list)


class StartTagLocations(HTMLParser):
    """Record original source offsets without serializing/reformatting HTML."""

    def __init__(self, html: str):
        super().__init__(convert_charrefs=True)
        self.source = html
        self.line_starts = [0]
        for line in html.splitlines(keepends=True):
            self.line_starts.append(self.line_starts[-1] + len(line))
        self.stack: list[Element] = []
        self.elements: list[Element] = []
        self.by_id: dict[str, list[Element]] = {}
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line, column = self.getpos()
        raw = self.get_starttag_text()
        attributes = dict(attrs)
        node = Element(
            tag=tag, attrs=attributes,
            start=self.line_starts[line - 1] + column,
            raw=raw, parent=self.stack[-1] if self.stack else None,
        )
        if node.parent:
            node.parent.children.append(node)
        self.elements.append(node)
        if attributes.get("id"):
            self.by_id.setdefault(attributes["id"], []).append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        # Recover only a previously-opened matching tag. A malformed source
        # remains a matter for the canonical CMS HTML structural audit.
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def unique(self, ident: str) -> Element:
        matches = self.by_id.get(ident, [])
        if len(matches) != 1:
            raise ValueError(f"HTML ID {ident!r} must exist exactly once")
        return matches[0]


def _collections(manifest: dict) -> list[dict]:
    if manifest.get("noOutbound") is not True:
        raise ValueError("Research manifest must explicitly forbid outbound actions")
    assessment = manifest.get("assessment")
    if not isinstance(assessment, dict):
        raise ValueError("Missing country/niche assessment")
    if assessment.get("scope") != "ALLOW":
        raise ValueError("Only in-scope prospects can be annotated")
    niche = assessment.get("priorityNiche")
    if niche in CLINICAL and not assessment.get("regulatedClinicalClaimsReview"):
        raise ValueError("Clinical lead lacks regulated claims review flag")
    entries = manifest.get("cmsCollections")
    if entries is None:
        entries = []
    if not isinstance(entries, list):
        raise ValueError("cmsCollections must be a list")
    if niche in PRIORITY_NICHES and not entries:
        raise ValueError("Priority niche needs a source-reviewed CMS collection plan")
    if len(entries) > 12:
        raise ValueError("More than 12 sections requires editorial review")
    containers: set[str] = set()
    card_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") not in KINDS:
            raise ValueError("Unknown or malformed CMS collection kind")
        container = entry.get("containerId")
        items = entry.get("itemIds")
        if not isinstance(container, str) or not ID.fullmatch(container):
            raise ValueError("CMS collection needs a valid container ID")
        if container in containers:
            raise ValueError("Duplicate CMS collection container ID")
        containers.add(container)
        if not isinstance(items, list) or not 1 <= len(items) <= MAX_COLLECTION_ITEMS:
            raise ValueError("CMS collection requires 1 to 40 verified existing card IDs")
        if any(not isinstance(x, str) or not ID.fullmatch(x) for x in items):
            raise ValueError("Invalid CMS card ID")
        if len(items) != len(set(items)) or any(x in card_ids for x in items):
            raise ValueError("Duplicate CMS item ID in source plan")
        card_ids.update(items)
        if not https_url(entry.get("sourcePage")):
            raise ValueError("Source-backed CMS collection needs an HTTPS source page")
        evidence = entry.get("sourceEvidence")
        if not isinstance(evidence, dict):
            raise ValueError("Missing independent browser/source review evidence file")
        path = evidence.get("path")
        expected_sha = evidence.get("sha256")
        if (not isinstance(path, str) or not Path(path).is_file()
                or not isinstance(expected_sha, str) or not SHA.fullmatch(expected_sha)
                or sha_file(Path(path)) != expected_sha):
            raise ValueError("CMS collection factual evidence file missing or stale")
        if niche in CLINICAL and entry.get("clinicalClaimsReviewed") is not True:
            raise ValueError("Clinical collections need independent claims review")
    if niche in FOOD and entries and not any(e["kind"] in {"menu", "services"} for e in entries):
        raise ValueError("Food service site must include a verified menu/services collection")
    if niche in CLINICAL and entries and not any(e["kind"] == "services" for e in entries):
        raise ValueError("Clinical site must include a verified services collection")
    return entries


def _validate_source(html: str, manifest: dict) -> tuple[StartTagLocations, list[dict]]:
    if manifest.get("schemaVersion") != 1:
        raise ValueError("Unsupported research manifest schema")
    slug = manifest.get("leadSlug")
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        raise ValueError("Invalid lead slug")
    entries = _collections(manifest)
    parser = StartTagLocations(html)
    used: set[int] = set()
    for entry in entries:
        kind = entry["kind"]
        container = parser.unique(entry["containerId"])
        if container.tag not in SAFE_LIST_TAGS:
            raise ValueError("Collection container is not a static list/grid tag")
        old_kind = container.attrs.get("data-pe-collection")
        if old_kind is not None and old_kind != kind:
            raise ValueError("Conflicting collection marker")
        if len(container.children) < 1:
            raise ValueError("CMS collection contains no items")
        planned_ids = set(entry["itemIds"])
        live_items = []
        for child in container.children:
            if child.tag not in SAFE_ITEM_TAGS:
                raise ValueError("Collection container has non-card direct child")
            card_id = child.attrs.get("id")
            if not card_id or card_id not in planned_ids:
                raise ValueError("Unplanned direct child in CMS collection")
            if card_id in live_items:
                raise ValueError("Duplicate card ID inside CMS collection")
            live_items.append(card_id)
            if child.attrs.get("data-pe-item") not in (None, ""):
                raise ValueError("Unexpected CMS card marker value")
            if child.attrs.get("contenteditable") is not None:
                raise ValueError("Public HTML must not persist editor contenteditable")
            for inner in parser.elements:
                if inner is child or _descends_from(inner, child):
                    if inner.attrs.get("data-pe-field") is not None:
                        raise ValueError("Item-specific content must not inherit global CMS sync keys")
            used.add(id(child))
        if len(live_items) != len(planned_ids) or set(live_items) != planned_ids:
            raise ValueError("Verified card IDs differ from actual generated site")
        used.add(id(container))
    # No additional unreviewed collections or card markers are silently accepted.
    for el in parser.elements:
        if ("data-pe-collection" in el.attrs or "data-pe-item" in el.attrs) and id(el) not in used:
            raise ValueError("Unreviewed CMS collection/card marker present")
    return parser, entries


def _descends_from(node: Element, parent: Element) -> bool:
    current = node.parent
    while current:
        if current is parent:
            return True
        current = current.parent
    return False


def audit_html(html: str, manifest: dict) -> dict:
    parser, entries = _validate_source(html, manifest)
    missing = []
    for entry in entries:
        container = parser.unique(entry["containerId"])
        if container.attrs.get("data-pe-collection") != entry["kind"]:
            missing.append(entry["containerId"])
        for item in entry["itemIds"]:
            if "data-pe-item" not in parser.unique(item).attrs:
                missing.append(item)
    return {
        "result": "STRUCTURE_PASS" if not missing else "NEEDS_MARKUP",
        "niche": manifest["assessment"].get("priorityNiche"),
        "plannedCollections": len(entries),
        "plannedItems": sum(len(entry["itemIds"]) for entry in entries),
        "missingMarkers": missing,
        "independentFactVerificationStillRequired": True,
        "cmsTenantProvisioned": False,
        "clientHandoffAuthorized": False, "productionReleaseAuthorized": False,
    }


def annotate_html(html: str, manifest: dict) -> str:
    parser, entries = _validate_source(html, manifest)
    edits: list[tuple[int, str]] = []
    for entry in entries:
        targets = [(parser.unique(entry["containerId"]), "data-pe-collection",
                    entry["kind"])]
        targets.extend((parser.unique(item), "data-pe-item", "")
                       for item in entry["itemIds"])
        for node, attribute, value in targets:
            if attribute in node.attrs:
                continue
            raw = node.raw
            closing = re.search(r"\s*/?>$", raw)
            if not closing or raw.endswith("/>"):
                raise ValueError("Cannot annotate a self-closing collection element")
            # Insert immediately before the final > (and do not normalize HTML).
            position = node.start + len(raw) - 1
            if html[position] != ">":
                raise ValueError("CMS annotation source offset mismatch")
            injection = f' {attribute}="{value}"' if value else f" {attribute}"
            edits.append((position, injection))
    result = html
    for position, injection in sorted(edits, reverse=True):
        result = result[:position] + injection + result[position:]
    if audit_html(result, manifest)["result"] != "STRUCTURE_PASS":
        raise ValueError("CMS collection annotation output failed revalidation")
    return result


def annotate_file(source: Path, manifest_file: Path, output: Path) -> dict:
    source, manifest_file, output = map(Path, (source, manifest_file, output))
    if not source.is_file() or source.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("Source site must be an existing static HTML file")
    if output.exists() or source.resolve() == output.resolve():
        raise FileExistsError("Output must be new; never overwrite original site")
    if not output.parent.is_dir() or output.suffix.lower() != ".html":
        raise ValueError("Output must be a new HTML file in an existing folder")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Research manifest must be a JSON object")
    html = source.read_text(encoding="utf-8")
    original_sha = sha_file(source)
    expected = manifest.get("cmsSourceHtmlSha256")
    if not isinstance(expected, str) or expected != original_sha:
        raise ValueError("Generated HTML SHA must match the research-to-site handoff")
    updated = annotate_html(html, manifest)
    output.write_text(updated, encoding="utf-8", newline="")
    report = audit_html(updated, manifest)
    report.update({
        "originalSha256": original_sha,
        "annotatedSha256": sha_file(output),
        "bytesChanged": updated != html,
    })
    return report


def main() -> int:
    cli = argparse.ArgumentParser(description="Safe Engine C CMS collection annotator")
    cli.add_argument("--html", type=Path, required=True)
    cli.add_argument("--research", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    options = cli.parse_args()
    print(json.dumps(annotate_file(options.html, options.research, options.output),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({
            "result": "BLOCK", "reason": type(exc).__name__,
            "detail": str(exc)[:240], "productionReleaseAuthorized": False,
        }))
        raise SystemExit(2)
