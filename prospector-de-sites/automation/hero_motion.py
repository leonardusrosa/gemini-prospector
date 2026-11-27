"""Engine C v1 hero-motion planning and delivered-media QA for Google Flow.

One full-viewport hero video per viewport: 16:9 desktop, 9:16 mobile.
Exactly four start/end frames + two verified clips. User approval is
authenticated/out-of-band and must bind to the exact delivered assets.
This module never calls Flow, generates media, reads Google cookies or
spends credits. Source assets are optional; facts/identities stay verified.
"""
from __future__ import annotations

from hero_motion_direction import validate_direction

import hashlib
import hmac
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Any

KINDS = {"restaurant", "pizzeria", "cafe", "dentistry", "clinic"}
VARIANTS = {"desktop": "16:9", "mobile": "9:16"}
FRAMES = {"desktop_start", "desktop_end", "mobile_start", "mobile_end"}
MOTION_ENDINGS = {"seamless_loop", "freeze_on_end"}
ACCOUNT_ALIASES = {"flow-a", "flow-b"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_RETRIES = 2
MAX_TOTAL_GENERATIONS = 8  # four frames + two videos + two targeted retries
DEFAULT_MONTHLY_ACCOUNT_CREDITS = 1000  # claimed capacity; verify in Flow UI
QA_FIELDS = (
    "brandConsistency", "premiumTaste", "noObjectWarping",
    "textSafeThroughMotion", "noStrobe", "ctaReadable",
    "posterAvailable", "prefersReducedMotionPoster",
    "videoPlaybackConfirmed", "mobileAndDesktopSeparatelyComposed", "directedMotionVerified",
    "noUnplannedEffects", "noPrematureMotionStop",
)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Hero artifact must be a JSON object")
    return data


def _file_ref(value: dict, extensions: set[str]) -> Path:
    if not isinstance(value, dict):
        raise ValueError("Missing referenced media artifact")
    name, digest = value.get("path"), value.get("sha256")
    if not isinstance(name, str) or not name or not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ValueError("Media path and exact SHA-256 are mandatory")
    path = Path(name)
    if not path.is_file() or path.suffix.lower() not in extensions:
        raise ValueError("Referenced media artifact missing or unsupported")
    if sha_file(path) != digest:
        raise ValueError("Media artifact changed after generation")
    return path


def _box(value: object, label: str) -> tuple[float, float, float, float]:
    if not isinstance(value, dict):
        raise ValueError("Missing text/subject safe zone: " + label)
    try:
        x, y, w, h = [value[k] for k in ("x", "y", "width", "height")]
    except KeyError as exc:
        raise ValueError("Missing zone dimension") from exc
    if any(isinstance(a, bool) or not isinstance(a, (int, float)) for a in (x, y, w, h)):
        raise ValueError("Zones must have normalized numeric dimensions")
    if not (0 <= x <= 1 and 0 <= y <= 1 and .05 <= w <= 1 and .04 <= h <= 1 and x+w <= 1.0001 and y+h <= 1.0001):
        raise ValueError("Text/subject zone outside video frame")
    return float(x),float(y),float(w),float(h)


def _overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax,ay,aw,ah=a
    bx,by,bw,bh=b
    area=max(0,min(ax+aw,bx+bw)-max(ax,bx))*max(0,min(ay+ah,by+bh)-max(ay,by))
    return area / min(aw*ah, bw*bh)


def validate_plan(plan: dict, research: dict | None = None) -> dict:
    if plan.get("schemaVersion") != 1 or plan.get("provider") != "google-flow":
        raise ValueError("Unsupported hero plan schema/provider")
    slug=plan.get("leadSlug")
    if not isinstance(slug,str) or not SLUG.fullmatch(slug):
        raise ValueError("Hero plan needs a stable lead slug")
    if plan.get("noOutbound") is not True:
        raise ValueError("Hero generation cannot authorize messaging, calls or publishing")
    if not isinstance(plan.get("selectedDesignDirectionSha256"),str) or not SHA256.fullmatch(plan["selectedDesignDirectionSha256"]):
        raise ValueError("Hero plan must bind to selected design direction")
    if plan.get("placement") != "AFTER_DESIGN_BEFORE_IMPLEMENTATION":
        raise ValueError("Hero must follow design direction and precede implementation")
    if plan.get("appliesToAllNiches") is not True:
        raise ValueError("All niches require the hero motion gate")
    if plan.get("manualApprovalRequired") is not True:
        raise ValueError("Human approval is mandatory; auto-selection is not yet enabled")
    if plan.get("publicReleaseAuthorized") is not False:
        raise ValueError("Hero asset generation does not authorize site publication")
    if plan.get("durationRangeSeconds") != [5,10]:
        raise ValueError("User-approved hero duration must be 5-10 seconds")
    subject=plan.get("subject")
    if (not isinstance(subject,dict) or
        subject.get("sourceStrategy") not in {"optional_lead_asset","verified_brand_grounded","abstract_brand_motion"} or
        not isinstance(subject.get("creativeRationale"),str) or len(subject["creativeRationale"].strip()) < 25 or
        not isinstance(subject.get("brandConsistencyRules"),list) or not subject["brandConsistencyRules"]):
        raise ValueError("Motion subject must include a justified tasteful creative direction")
    if subject.get("basedOnLeadPhoto") is True and not subject.get("assetProvenanceSha256"):
        raise ValueError("Lead-photo-based hero needs first-party asset provenance")
    budgets=plan.get("budget")
    if (not isinstance(budgets,dict) or budgets.get("tier") != "standard" or
        budgets.get("plannedFrames") != 4 or budgets.get("plannedVideos") != 2 or
        budgets.get("maxRetries") != MAX_RETRIES or budgets.get("maxGenerations") != MAX_TOTAL_GENERATIONS or
        budgets.get("creditsAreUIVerified") is not False):
        raise ValueError("Standard budget contract: 4 frames, 2 clips, 2 retries; check account balance in UI")
    routing=plan.get("accountRouting")
    if (not isinstance(routing,dict) or routing.get("mode") != "authenticated_desktop_profiles" or
        sorted(routing.get("aliases",[])) != sorted(ACCOUNT_ALIASES) or
        routing.get("noStoredPasswords") is not True or routing.get("checkCreditsAndCostsBeforeEachJob") is not True):
        raise ValueError("Only authorized user-signed-in Flow profiles, no credentials or hidden spend")
    variants=plan.get("variants")
    if not isinstance(variants,dict) or set(variants)!=set(VARIANTS):
        raise ValueError("Separate original desktop and mobile hero directions are required")
    for name,aspect in VARIANTS.items():
        v=variants[name]
        if not isinstance(v,dict) or v.get("aspectRatio")!=aspect:
            raise ValueError("Hero variant must have dedicated "+aspect+" composition")
        duration=v.get("targetSeconds")
        if isinstance(duration,bool) or not isinstance(duration,(int,float)) or not 5<=duration<=10:
            raise ValueError("Hero clip must last 5-10 seconds")
        if v.get("loopMode") not in {"engine_choice","seamless_loop","freeze_on_end"}:
            raise ValueError("Loop strategy missing")
        if not all(isinstance(v.get(k),str) and len(v[k].strip())>=40 for k in
                   ("startFramePrompt","endFramePrompt","videoPrompt","motionReason")):
            raise ValueError("Both frames, motion and rationale must have concrete prompts")
        validate_direction(v)
        if v.get("firstAndLastFrameRequired") is not True or v.get("fullViewport") is not True:
            raise ValueError("Hero must use two frames and fill viewport")
        safe=v.get("safeZones")
        if not isinstance(safe,dict) or set(safe)!={"title","subtitle","cta","subject"}:
            raise ValueError("Title, subtitle, CTA and subject safe zones required")
        subject_box=_box(safe["subject"],"subject")
        for zone in ("title","subtitle","cta"):
            text_box=_box(safe[zone],zone)
            if _overlap(text_box,subject_box) > .08:
                raise ValueError("Hero subject overlaps text/CTA zone: "+name+" "+zone)
        if name=="mobile" and v.get("independentMobileComposition") is not True:
            raise ValueError("Mobile may not simply crop desktop")
    if research is not None:
        if research.get("leadSlug")!=slug:
            raise ValueError("Hero plan lead identity mismatch")
        if research.get("noOutbound") is not True:
            raise ValueError("Research does not prohibit outbound")
        if subject.get("basedOnLeadPhoto"):
            hashes={asset.get("sha256") for asset in research.get("assets",[]) if isinstance(asset,dict)}
            if subject["assetProvenanceSha256"] not in hashes:
                raise ValueError("Lead photo reference not in immutable research assets")
    return {"result":"PLAN_VALID","variants":2,"framesPlanned":4,
            "videosPlanned":2,"maxExtraGenerations":MAX_RETRIES,
            "manualApprovalRequired":True,"publicReleaseAuthorized":False}


def _video_metadata(path:Path) -> dict:
    # This is a measured media probe, not a JSON claim written by the generator.
    try:
        proc=subprocess.run([
            "ffprobe","-v","error","-show_entries",
            "format=duration:stream=codec_type,codec_name,width,height,duration",
            "-of","json",str(path)],
            text=True,capture_output=True,timeout=25,check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError('ffprobe unavailable or cannot verify video bytes') from exc
    if proc.returncode:
        raise ValueError("ffprobe cannot verify video bytes")
    data=json.loads(proc.stdout)
    stream=next((s for s in data.get("streams",[]) if s.get("codec_type")=="video"),None)
    if not stream:
        raise ValueError("Video has no valid video stream")
    return {"durationSeconds":float(data.get("format",{}).get("duration") or stream["duration"]),
            "width":int(stream.get("width") or 0),"height":int(stream.get("height") or 0)}


def validate_delivery(plan:dict,delivery:dict,qa:dict,
                      probe:Callable[[Path],dict]=_video_metadata) -> dict:
    validate_plan(plan)
    if delivery.get("schemaVersion")!=1 or delivery.get("leadSlug")!=plan["leadSlug"]:
        raise ValueError("Hero delivery source/schema mismatch")
    if delivery.get("planSha256")!=plan.get("_fileSha256"):
        raise ValueError("Delivery must bind the exact plan file hash")
    frames=delivery.get("frames")
    if not isinstance(frames,dict) or set(frames)!=FRAMES:
        raise ValueError("Four exact frame artifacts required")
    for frame in frames.values():
        _file_ref(frame,{".png",".jpeg",".jpg",".webp"})
    videos=delivery.get("videos")
    if not isinstance(videos,dict) or set(videos)!=set(VARIANTS):
        raise ValueError("Two distinct video artifacts required")
    video_hashes=[]
    for name,ratio in VARIANTS.items():
        item=videos[name]
        path=_file_ref(item,{".mp4",".webm"})
        video_hashes.append(item["sha256"])
        metadata=probe(path)
        dur=metadata["durationSeconds"]
        width,height=metadata["width"],metadata["height"]
        if not 5<=dur<=10.5 or width<600 or height<360:
            raise ValueError("Hero video duration/resolution outside accepted bounds")
        detected_ratio=width/height
        if name=="desktop" and not 1.7<=detected_ratio<=1.85:
            raise ValueError("Desktop hero must be actual 16:9 video")
        if name=="mobile" and not .53<=detected_ratio<=.59:
            raise ValueError("Mobile hero must be actual 9:16 video")
        if item.get("ending") not in MOTION_ENDINGS:
            raise ValueError("Every clip must choose verified loop or freeze ending")
        if item.get("posterFrame") not in {name+"_start",name+"_end"}:
            raise ValueError("Separate hero poster must be chosen")
    if len(set(video_hashes))!=2:
        raise ValueError("Desktop and mobile must not reuse identical video bytes")
    credits=delivery.get("creditLedger")
    if not isinstance(credits,list) or not 6<=len(credits)<=MAX_TOTAL_GENERATIONS:
        raise ValueError("Six base generations and at most two retries must be accounted for")
    if len(credits)-6>MAX_RETRIES:
        raise ValueError("Hero retry budget exceeded")
    for entry in credits:
        if not isinstance(entry,dict) or entry.get("accountAlias") not in ACCOUNT_ALIASES:
            raise ValueError("Credit log must identify one signed-in authorized account")
        if not isinstance(entry.get("model"),str) or not entry["model"]:
            raise ValueError("Generation model/cost audit missing")
        spent=entry.get("creditsSpent")
        if isinstance(spent,bool) or not isinstance(spent,(int,float)) or spent<0:
            raise ValueError("Credit charge must be individually verified")
        if entry.get("uiCostChecked") is not True:
            raise ValueError("Flow UI cost must be checked before generation")
    for name, variant in plan["variants"].items():
        if variant["motionDirection"]["version"] not in (4,5):
            continue
        for suffix in ("start", "end", "video"):
            step = name + "_" + suffix
            latest = next((e for e in reversed(credits) if e.get("step") == step), None)
            expected = videos[name] if suffix == "video" else frames[step]
            if (not latest or latest.get("outcome") != "downloaded" or
                not isinstance(latest.get("artifact"), dict) or
                latest["artifact"].get("sha256") != expected["sha256"]):
                raise ValueError("V4 delivery must bind each Flow ledger download: " + step)
    if qa.get("schemaVersion")!=1 or qa.get("planSha256")!=delivery["planSha256"]:
        raise ValueError("Hero QA must bind the approved plan hash")
    if qa.get("deliverySha256")!=delivery.get("_fileSha256"):
        raise ValueError("Hero QA must bind actual delivered media manifest")
    observations=qa.get("variants")
    if not isinstance(observations,dict) or set(observations)!=set(VARIANTS):
        raise ValueError("Independent hero video QA must cover desktop and mobile")
    for name,item in observations.items():
        if not isinstance(item,dict) or item.get("reviewer") in (None,delivery.get("generatorId")):
            raise ValueError("Hero QA requires a distinct reviewer")
        if not all(item.get(k) is True for k in QA_FIELDS):
            raise ValueError("Hero motion QA failed: "+name)
        if plan["variants"][name]["motionDirection"]["version"] in (4,5):
            for field in ("flowPairReferenceVerified", "standaloneFramesVerified",
                          "meaningfulMotionPayoffVerified", "scenePopulationVerified"):
                if item.get(field) is not True:
                    raise ValueError("V4 independent QA missing: " + field)
        if plan["variants"][name]["motionDirection"]["version"] == 5:
            for field in ("openingHookVerified", "signatureEventVerified",
                          "intentionalRhythmVerified", "advertisingGradeMotionVerified"):
                if item.get(field) is not True:
                    raise ValueError("V5 creative QA missing: " + field)
        end=videos[name]["ending"]
        if end=="seamless_loop" and item.get("loopSeamAcceptable") is not True:
            raise ValueError("Loop seam rejected for "+name)
        if end=="freeze_on_end" and item.get("endFrameStable") is not True:
            raise ValueError("Freeze end-frame rejected for "+name)
        if item.get("browserVideoScreenshot") is None:
            raise ValueError("Actual rendered browser screenshot required")
        _file_ref(item["browserVideoScreenshot"],{".png"})
    return {"result":"VIDEO_QA_READY_FOR_HUMAN_APPROVAL",
            "variantsValidated":["desktop","mobile"],"manualApprovalRequired":True,
            "publicReleaseAuthorized":False}


def _approval_payload(approval:dict) -> bytes:
    return "|".join((approval["deliverySha256"],approval["planSha256"],
                     approval["approverId"],approval["decision"])).encode("utf-8")


def approve_with_human_receipt(plan:dict,delivery:dict,qa:dict,approval:dict,
                               key:str | None=None,
                               probe:Callable[[Path],dict]=_video_metadata) -> dict:
    validate_delivery(plan,delivery,qa,probe=probe)
    if approval.get("schemaVersion")!=1 or approval.get("decision")!="APPROVED":
        raise ValueError("Only explicit human approval can advance")
    if approval.get("channel")!="authenticated_admin_review":
        raise ValueError("Approval must be from authenticated human admin review")
    if approval.get("autoSelected") is not False or approval.get("actorType")!="human":
        raise ValueError("Automatic approval is not available in v1")
    if approval.get("planSha256")!=delivery["planSha256"] or approval.get("deliverySha256")!=delivery["_fileSha256"]:
        raise ValueError("Human approval is stale or does not bind exact video bytes")
    identity=approval.get("approverId")
    if not isinstance(identity,str) or not re.fullmatch(r"[A-Za-z0-9_@.-]{3,80}",identity):
        raise ValueError("Human approver identity missing")
    if identity==delivery.get("generatorId"):
        raise ValueError("Video generator may not approve its own output")
    key = key if key is not None else os.environ.get("ENGINE_C_HERO_APPROVAL_KEY")
    if not isinstance(key,str) or len(key)<32:
        raise ValueError("Human approval verification key not configured")
    mac=hmac.new(key.encode(),_approval_payload(approval),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(str(approval.get("signature") or ""),mac):
        raise ValueError("Unsigned or forged human approval receipt")
    return {"result":"HERO_MOTION_MANUALLY_APPROVED",
            "desktopVideoSha256":delivery["videos"]["desktop"]["sha256"],
            "mobileVideoSha256":delivery["videos"]["mobile"]["sha256"],
            "approvalActor":identity,
            "productionReleaseAuthorized":False,
            "readyForSiteImplementation":True}


def validate_stage_artifact(artifact:dict,source_manifest:dict,
                            file_hash:Callable[[Path],str]=sha_file) -> dict:
    """Fail-closed controller gate. Cannot self-approve by editing a JSON value."""
    file_references={
        name:artifact.get(name) for name in
        ("heroPlanFile","heroDeliveryFile","heroQaFile","heroHumanApprovalFile")
    }
    if not all(isinstance(v,str) and Path(v).is_file() for v in file_references.values()):
        raise ValueError("Four stage files mandatory: plan, delivered media, QA and human approval")
    plan_hash=artifact.get("heroPlanSha256")
    delivery_hash=artifact.get("heroDeliverySha256")
    qa_hash=artifact.get("heroQaSha256")
    approval_hash=artifact.get("heroHumanApprovalSha256")
    for label,value,digest in zip(file_references,file_references.values(),
                                  (plan_hash,delivery_hash,qa_hash,approval_hash)):
        if not isinstance(digest,str) or not SHA256.fullmatch(digest) or file_hash(Path(value))!=digest:
            raise ValueError("Hero "+label+" file changed since review")
    plan=read_json(Path(file_references["heroPlanFile"]))
    if plan.get("sourceManifestSha256")!=artifact.get("sourceManifestSha256"):
        raise ValueError("Hero plan research hash mismatch")
    validate_plan(plan,source_manifest)
    plan["_fileSha256"]=plan_hash
    delivery=read_json(Path(file_references["heroDeliveryFile"]))
    delivery["_fileSha256"]=delivery_hash
    qa=read_json(Path(file_references["heroQaFile"]))
    approval=read_json(Path(file_references["heroHumanApprovalFile"]))
    return approve_with_human_receipt(plan,delivery,qa,approval)
