"""Post-approval hero HTML embed contract; synthetic assets, no provider calls."""
from __future__ import annotations
import sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"prospector-de-sites"/"automation"))
import hero_motion
import hero_site_gate as site

HTML='''<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>.hero{min-height:100svh}.hero-video{object-fit:cover}
.hero-video-desktop{display:block}.hero-video-mobile{display:none}
@media(max-width:700px){.hero-video-desktop{display:none}.hero-video-mobile{display:block}}
@media(prefers-reduced-motion:reduce){.hero-video{display:none}}
</style></head><body>
<section class="hero" data-hero-video="approved">
<video class="hero-video hero-video-desktop" data-hero-variant="desktop"
  data-ending="seamless_loop" muted autoplay playsinline preload="none"
  poster="assets/desktop-end.png"><source src="assets/desktop.mp4" type="video/mp4"></video>
<video class="hero-video hero-video-mobile" data-hero-variant="mobile"
  data-ending="freeze_on_end" muted autoplay playsinline preload="none"
  poster="assets/mobile-end.png"><source src="assets/mobile.mp4" type="video/mp4"></video>
<div class="hero-overlay"><h1>Test video hero</h1>
<p class="hero-subtitle">Real text, not baked into video</p>
<a class="hero-cta" href="#menu">See Menu</a></div></section>
<section id="menu"><h2>Menu</h2></section>
</body></html>'''

class VideoImplementationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        a=self.root/"assets"
        a.mkdir()
        self.delivery={"frames":{},"videos":{}}
        for variant in ("desktop","mobile"):
            png=a/(variant+"-end.png")
            png.write_bytes(("synthetic poster "+variant).encode())
            video=a/(variant+".mp4")
            video.write_bytes(("synthetic approved video "+variant).encode())
            self.delivery["frames"][variant+"_end"]={"sha256":hero_motion.sha_file(png)}
            self.delivery["videos"][variant]={
                "sha256":hero_motion.sha_file(video),
                "posterFrame":variant+"_end",
                "ending":"seamless_loop" if variant=="desktop" else "freeze_on_end",
            }
        self.page=self.root/"index.html"
        self.page.write_text(HTML,encoding="utf-8")

    def audit(self):
        return site.audit_site(self.page,self.delivery)

    def test_full_screen_desktop_mobile_approved_video_embeds(self):
        o=self.audit()
        self.assertEqual(o["result"],"APPROVED_HERO_EMBEDDED")
        self.assertFalse(o["productionReleaseAuthorized"])

    def test_rejects_only_static_poster(self):
        self.page.write_text(HTML.replace('data-hero-video="approved"','data-hero-video="pending"'))
        with self.assertRaisesRegex(ValueError,"actual approved"):
            self.audit()

    def test_rejects_single_video_desktop_cropped_to_mobile(self):
        self.page.write_text(HTML.replace('data-hero-variant="mobile"','data-hero-variant="desktop"'))
        with self.assertRaisesRegex(ValueError,"Duplicated"):
            self.audit()

    def test_rejects_missing_real_html_cta(self):
        self.page.write_text(HTML.replace('class="hero-cta"','class="link"'))
        with self.assertRaisesRegex(ValueError,"headline, subtitle and CTA"):
            self.audit()

    def test_rejects_missing_muted_autoplay(self):
        self.page.write_text(HTML.replace('muted autoplay playsinline','playsinline'))
        with self.assertRaisesRegex(ValueError,"muted"):
            self.audit()

    def test_rejects_wrong_video_file_hash(self):
        (self.root/"assets"/"desktop.mp4").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"approved asset SHA"):
            self.audit()

    def test_rejects_missing_poster(self):
        (self.root/"assets"/"mobile-end.png").unlink()
        with self.assertRaisesRegex(ValueError,"approved asset SHA"):
            self.audit()

    def test_rejects_missing_reduced_motion(self):
        self.page.write_text(HTML.replace("@media(prefers-reduced-motion:reduce)","@media(screen)"))
        with self.assertRaisesRegex(ValueError,"Reduced-motion"):
            self.audit()

    def test_rejects_external_unversioned_video(self):
        self.page.write_text(HTML.replace('src="assets/desktop.mp4"','src="https://random.example/video.mp4"'))
        with self.assertRaisesRegex(ValueError,"locally versioned"):
            self.audit()

    def test_rejects_unsafe_video_source_traversal(self):
        self.page.write_text(HTML.replace('src="assets/desktop.mp4"','src="../secret.mp4"'))
        with self.assertRaisesRegex(ValueError,"traversal"):
            self.audit()

if __name__=="__main__":
    unittest.main(verbosity=2)
