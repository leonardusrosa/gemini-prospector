import os
import http.server
import socketserver
import threading
import time
from playwright.sync_api import sync_playwright

PORT = 4022
DIRECTORY = r"e:\Antigravity\prospector\prospector-react-engine\out"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run_server():
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        httpd.serve_forever()

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(0.5)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    print("\n=== HERO MEDIA POLISH QA ===")

    viewports = [
        ("desktop_1440", 1440, 900),
        ("tablet_768", 768, 1024),
        ("mobile_390", 390, 844),
    ]

    for name, w, h in viewports:
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(f"http://127.0.0.1:{PORT}/", wait_until="networkidle")

        hero = page.locator('[data-role="hero"]')
        poster = hero.locator("img.hero-poster-fallback")
        video = hero.locator("video.hero-video-bg")

        poster_count = poster.count()
        video_count = video.count()

        # Check transform / scale
        poster_transform = poster.evaluate("el => window.getComputedStyle(el).transform")
        video_transform = video.evaluate("el => window.getComputedStyle(el).transform") if video_count > 0 else "none"

        poster_obj_pos = poster.evaluate("el => window.getComputedStyle(el).objectPosition")
        video_obj_pos = video.evaluate("el => window.getComputedStyle(el).objectPosition") if video_count > 0 else "none"

        print(f"[{name}] Viewport {w}x{h}:")
        print(f"  Poster: count={poster_count}, transform={poster_transform}, objPos={poster_obj_pos}")
        print(f"  Video:  count={video_count}, transform={video_transform}, objPos={video_obj_pos}")

        # Ensure no artificial scaling/rotation
        assert "matrix" not in poster_transform or poster_transform == "none" or "1, 0, 0, 1, 0, 0" in poster_transform, f"Artificial transform on poster: {poster_transform}"

        # Capture screenshot of hero
        hero.screenshot(path=f"public/hero_b3_2_{name}.png")
        print(f"  Captured hero screenshot: public/hero_b3_2_{name}.png")

        page.close()

    # Test reduced motion
    print("\n[Reduced Motion Test]")
    rm_page = browser.new_page(
        viewport={"width": 1440, "height": 900},
        extra_http_headers={},
    )
    rm_page.emulate_media(reduced_motion="reduce")
    rm_page.goto(f"http://127.0.0.1:{PORT}/", wait_until="networkidle")

    rm_hero = rm_page.locator('[data-role="hero"]')
    rm_poster = rm_hero.locator("img.hero-poster-fallback")
    rm_video = rm_hero.locator("video.hero-video-bg")

    poster_visible = rm_poster.is_visible()
    video_count = rm_video.count()
    video_visible = rm_video.is_visible() if video_count > 0 else False

    print(f"  Reduced Motion: Poster visible={poster_visible}, Video in DOM={video_count}, Video visible={video_visible}")
    assert poster_visible, "Poster must remain visible under reduced motion"
    assert not video_visible, "Video must not be visible under reduced motion"

    rm_hero.screenshot(path="public/hero_b3_2_reduced_motion.png")
    print("  Captured reduced motion screenshot: public/hero_b3_2_reduced_motion.png")
    rm_page.close()

    browser.close()
    print("\nALL HERO MEDIA QA CHECKS PASSED!")
