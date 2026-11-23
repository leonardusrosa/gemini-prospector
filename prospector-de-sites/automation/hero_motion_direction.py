"""Concrete shot direction for Flow: prompts are compiled from the shot plan."""
import math
import re

FILLER = re.compile(r"\b(?:cinematic|premium|stunning|breathtaking|gorgeous|masterpiece|high[- ]end|epic|beautiful|tasteful|dramatic reveal|dynamic movement|subtle push[- ]in)\b", re.I)

def concrete(text, label):
    if not isinstance(text, str) or len(text.strip()) < 16:
        raise ValueError("Missing concrete shot instruction: " + label)
    if FILLER.search(text):
        raise ValueError("Generic prompt wording: " + label)
    return text.strip()

def compile_video_prompt(variant):
    d = variant.get("motionDirection")
    if not isinstance(d, dict) or d.get("version") != 1:
        raise ValueError("Structured motion direction required")
    duration = variant["targetSeconds"]
    keys = ("cameraSetup", "startComposition", "endComposition",
            "continuity", "protectedTextArea", "forbiddenEffects")
    values = {k: concrete(d.get(k), k) for k in keys}
    beats = d.get("beats")
    if not isinstance(beats, list) or len(beats) < 3:
        raise ValueError("At least three timed shot beats required")
    lines = []
    previous = 0
    for i, beat in enumerate(beats):
        start, end = beat.get("start"), beat.get("end")
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in (start,end)):
            raise ValueError("Invalid shot timing")
        if start != previous or not start < end <= duration:
            raise ValueError("Shot beats must cover the duration without gaps")
        camera = concrete(beat.get("camera"), "camera path")
        action = concrete(beat.get("action"), "physical action")
        phase = beat.get("phase")
        if phase not in {"motion", "settle"}:
            raise ValueError("Shot phase must be motion or settle")
        if phase == "settle" and (i != len(beats)-1 or start < duration - 1):
            raise ValueError("Settling only in the final second")
        lines.append(f"{start:g}-{end:g}s: Camera: {camera} Action: {action}")
        previous = end
    if previous != duration:
        raise ValueError("Shot beats must cover the full duration")
    return "\n".join([
        f"One continuous {duration:g}-second {variant['aspectRatio']} shot. Use supplied first and last frames.",
        "Camera setup: " + values["cameraSetup"],
        "First frame: " + values["startComposition"],
        *lines,
        "Last frame: " + values["endComposition"],
        "Continuity: " + values["continuity"],
        "Text-safe area: " + values["protectedTextArea"],
        "Exclude: " + values["forbiddenEffects"],
        "No generated text or logos. No cuts. No audio.",
    ])

def validate_direction(variant):
    for k in ("startFramePrompt", "endFramePrompt"):
        concrete(variant.get(k), k)
    if variant.get("videoPrompt") != compile_video_prompt(variant):
        raise ValueError("Video prompt must match the compiled shot direction")
