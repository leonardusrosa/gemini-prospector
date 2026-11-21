"""Actual HTML integration QA for previously approved Flow hero videos.

Ensures the approved desktop/mobile videos are present as separate local
static assets in a full-screen hero, alongside posters and real HTML text.
This is not a visual/browser QA substitute: Chromium must still test
autoplay, reduced motion, text readability, and loop/freeze timing.
"""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import re
import hero_motion

class HeroElements(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hero=None
        self.depth=0
        self.current_video=None
        self.videos={}
        self.headline_count=0
        self.cta_count=0
        self.subtitle_count=0

    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="section" and a.get("data-hero-video")=="approved":
            if self.hero is not None:
                raise ValueError("Multiple hero video sections")
            self.hero=a
            self.depth=1
            return
        if self.depth<=0:
            return
        if tag=="video" and a.get("data-hero-variant"):
            name=a["data-hero-variant"]
            if name in self.videos:
                raise ValueError("Duplicated video variant")
            self.current_video=name
            self.videos[name]={"attrs":a,"sources":[]}
        if tag=="source" and self.current_video:
            self.videos[self.current_video]["sources"].append(a)
        if tag=="h1":
            self.headline_count+=1
        if tag=="p" and "hero-subtitle" in a.get("class","").split():
            self.subtitle_count+=1
        if tag=="a" and "hero-cta" in a.get("class","").split():
            self.cta_count+=1
        if tag not in ("source","img","meta","input","br","link","hr"):
            self.depth+=1

    def handle_endtag(self,tag):
        if self.depth<=0:
            return
        if tag=="video":
            self.current_video=None
        self.depth-=1
        if self.depth<0:
            raise ValueError("Unexpected hero closing tag")

def audit_site(html_file:Path,delivery:dict)->dict:
    path=Path(html_file)
    if not path.is_file():
        raise ValueError("Rendered HTML source missing")
    html=path.read_text(encoding="utf-8")
    parsed=HeroElements()
    parsed.feed(html)
    if parsed.hero is None or set(parsed.videos)!={"desktop","mobile"}:
        raise ValueError("Hero must contain actual approved desktop/mobile video tags")
    if parsed.headline_count<1 or parsed.subtitle_count<1 or parsed.cta_count<1:
        raise ValueError("Hero headline, subtitle and CTA must be real accessible HTML")
    if not re.search(r"(?i)100(?:s|d|l)?vh",html):
        raise ValueError("Hero must occupy full viewport")
    if "prefers-reduced-motion" not in html or "object-fit:cover" not in html.replace(" ",""):
        raise ValueError("Reduced-motion poster and cover CSS contract missing")
    for name,media in parsed.videos.items():
        attrs=media["attrs"]
        for boolean in ("muted","autoplay","playsinline"):
            if boolean not in attrs:
                raise ValueError("Missing video attribute "+name+" "+boolean)
        if attrs.get("data-ending")!=delivery["videos"][name]["ending"]:
            raise ValueError("Video ending behavior differs from approved media")
        srcs=media["sources"]
        if len(srcs)!=1 or not isinstance(srcs[0].get("src"),str):
            raise ValueError("One independent source required per viewport")
        video_ref=srcs[0]["src"]
        poster_ref=attrs.get("poster")
        if not video_ref or not poster_ref:
            raise ValueError("Hero source and poster required")
        for reference,expected in (
            (video_ref,delivery["videos"][name]["sha256"]),
            (poster_ref,delivery["frames"][delivery["videos"][name]["posterFrame"]]["sha256"]),
        ):
            if reference.startswith(("http:","https:","//","/")):
                raise ValueError("Video/poster should be a locally versioned relative asset")
            target=(path.parent/reference).resolve()
            if path.parent.resolve() not in target.parents:
                raise ValueError("Video/poster source path traversal blocked")
            if not target.is_file() or hero_motion.sha_file(target)!=expected:
                raise ValueError("Generated hero source is missing or differs from approved asset SHA")
        if name=="mobile" and "hero-video-mobile" not in attrs.get("class",""):
            raise ValueError("Mobile class required for responsive variant switch")
        if name=="desktop" and "hero-video-desktop" not in attrs.get("class",""):
            raise ValueError("Desktop class required for responsive variant switch")
    return {"result":"APPROVED_HERO_EMBEDDED",
            "variants":2,"originalMediaHashesVerified":True,
            "visualBrowserQAStillRequired":True,"productionReleaseAuthorized":False}
