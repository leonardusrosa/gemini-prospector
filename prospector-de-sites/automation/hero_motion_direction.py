"""Validate internal shot direction and compile the versioned Flow execution prompt."""
import math
import re

FILLER = re.compile(r"\b(?:cinematic|premium|stunning|breathtaking|gorgeous|masterpiece|high[- ]end|epic|beautiful|tasteful|dramatic reveal|dynamic movement|subtle push[- ]in)\b", re.I)
MAX_V2_WORDS = 180

def concrete(text, label):
    if not isinstance(text, str) or len(text.strip()) < 16:
        raise ValueError("Missing concrete shot instruction: " + label)
    if FILLER.search(text):
        raise ValueError("Generic prompt wording: " + label)
    return text.strip()

def timed_lines(beats, duration):
    if not isinstance(beats, list) or len(beats) < 3:
        raise ValueError("At least three timed shot beats required")
    lines = []
    previous = 0
    for i, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise ValueError("Invalid shot beat")
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
    return lines

def compile_video_prompt(variant):
    d = variant.get("motionDirection")
    if not isinstance(d, dict) or type(d.get("version")) is not int or d["version"] not in (1,2):
        raise ValueError("Structured motion direction required")
    duration = variant["targetSeconds"]
    if type(duration) not in (int,float) or not math.isfinite(duration) or not 5 <= duration <= 10:
        raise ValueError("Hero clip must last 5-10 seconds")
    keys = ("cameraSetup", "startComposition", "endComposition",
            "protectedTextArea", "forbiddenEffects")
    values = {k: concrete(d.get(k), k) for k in keys}
    opening = f"One continuous {duration:g}-second {variant['aspectRatio']} shot. Use supplied first and last frames."
    if d["version"] == 1:
        continuity = concrete(d.get("continuity"), "continuity")
        lines = timed_lines(d.get("beats"), duration)
        return "\n".join([
            opening,
            "Camera setup: " + values["cameraSetup"],
            "First frame: " + values["startComposition"],
            *lines,
            "Last frame: " + values["endComposition"],
            "Continuity: " + continuity,
            "Text-safe area: " + values["protectedTextArea"],
            "Exclude: " + values["forbiddenEffects"],
            "No generated text or logos. No cuts. No audio.",
        ])
    if "beats" in d or "continuity" in d:
        raise ValueError("V2 uses temporal_sequence and physical_continuity, not legacy aliases")
    fields = {k: concrete(d.get(k), k) for k in (
        "product_lock", "physical_continuity", "camera_choreography", "end_state")}
    lines = timed_lines(d.get("temporal_sequence"), duration)
    # Frame descriptions and camera setup remain in the internal brief. The
    # generation prompt concerns motion and invariants, not restyling the images.
    prompt = "\n".join([
        opening,
        "Camera: " + fields["camera_choreography"],
        "Product lock: " + fields["product_lock"],
        "Physical continuity: " + fields["physical_continuity"],
        *lines,
        "End state: " + fields["end_state"],
        "Text-safe area: " + values["protectedTextArea"],
        "Exclude: " + values["forbiddenEffects"],
        "No generated text or logos. No cuts. No audio.",
    ])
    if len(prompt.split()) > MAX_V2_WORDS:
        raise ValueError("V2 Flow motion prompt exceeds 180 words; condense motion instructions")
    return prompt

def validate_direction(variant):
    for k in ("startFramePrompt", "endFramePrompt"):
        concrete(variant.get(k), k)
    if variant.get("videoPrompt") != compile_video_prompt(variant):
        raise ValueError("Video prompt must match the compiled shot direction")
