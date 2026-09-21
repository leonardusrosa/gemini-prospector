"""Regression gate for the Dallas nested static export.

The site is served below /clientes/dallas-detailing-and-buffing/, so this
test exercises the same URL shape that the prospector-sites host exposes.
It intentionally checks both hydrated and JavaScript-disabled rendering.
"""

from __future__ import annotations

import functools
import http.server
import shutil
import socketserver
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
SITE_PREFIX = "/clientes/dallas-detailing-and-buffing"
PORT = 4057


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


def start_server(directory: Path) -> socketserver.TCPServer:
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def local_asset_urls(page: Page) -> list[str]:
    return page.evaluate(
        """() => [...document.querySelectorAll('img[src],link[href],script[src]')]
          .map((node) => node.src || node.href)
          .filter((url) => url.startsWith(location.origin))"""
    )


def assert_core_content(page: Page, label: str) -> None:
    selectors = {
        "hero": '[data-role="hero"]',
        "services": "#services",
        "comparison": "#comparison",
        "reviews": "#reviews",
        "gallery": "#gallery",
        "studio": "#studio",
        "footer": "footer",
    }
    for name, selector in selectors.items():
        element = page.locator(selector).first
        assert element.count() == 1, f"{label}: missing {name} ({selector})"
        box = element.bounding_box()
        assert box and box["width"] > 0 and box["height"] > 0, f"{label}: empty {name}"
        opacity = float(element.evaluate("node => getComputedStyle(node).opacity"))
        assert opacity > 0, f"{label}: {name} is transparent"

    body_text = page.locator("body").inner_text().upper()
    for text in ("TECHNICAL DETAILING SERVICES", "PUBLIC REVIEW", "VEHICLE PHOTO ARCHIVE", "16284 MIDWAY RD"):
        assert text in body_text, f"{label}: missing text {text!r}"


def assert_local_assets(page: Page, label: str) -> None:
    urls = sorted(set(local_asset_urls(page)))
    assert urls, f"{label}: no local assets discovered"
    for url in urls:
        response = page.request.get(url)
        assert response.status == 200, f"{label}: asset {url} returned {response.status}"
        pathname = url.split("/", 3)[-1]
        if "/_next/" in url or "/assets/" in url:
            assert SITE_PREFIX in url, f"{label}: unscoped asset URL {url}"


def main() -> None:
    assert OUT.is_dir(), f"missing build output: {OUT}"
    assert (OUT / "index.html").is_file(), "missing out/index.html"

    with tempfile.TemporaryDirectory(prefix="dallas-nested-export-") as temp:
        root = Path(temp)
        nested = root / SITE_PREFIX.lstrip("/")
        nested.mkdir(parents=True)
        for name in ("index.html", "404.html"):
            shutil.copy2(OUT / name, nested / name)
        for directory in ("assets", "_next"):
            shutil.copytree(OUT / directory, nested / directory)

        server = start_server(root)
        url = f"http://127.0.0.1:{PORT}{SITE_PREFIX}/"
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                for name, viewport in (("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})):
                    page = browser.new_page(viewport=viewport)
                    failures: list[str] = []
                    page.on("response", lambda response: failures.append(f"{response.status} {response.url}") if response.status >= 400 else None)
                    page.goto(url, wait_until="networkidle")
                    assert_core_content(page, f"{name}/js")
                    assert_local_assets(page, f"{name}/js")
                    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), f"{name}: horizontal overflow"
                    assert not failures, f"{name}: network failures: {failures}"
                    page.close()

                no_js = browser.new_page(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
                no_js.goto(url, wait_until="load")
                assert_core_content(no_js, "desktop/no-js")
                no_js.close()
                browser.close()
        finally:
            server.shutdown()
            server.server_close()

    print("NESTED_EXPORT: PASS")
    print("FULL_PAGE_VISIBILITY: PASS")
    print("NO_JS_CORE_CONTENT: PASS")
    print("NETWORK_404: 0")
    print("DESKTOP: PASS")
    print("MOBILE: PASS")


if __name__ == "__main__":
    main()
