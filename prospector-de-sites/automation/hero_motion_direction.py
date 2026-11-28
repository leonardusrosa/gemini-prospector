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
    if not isinstance(d, dict) or type(d.get("version")) is not int or d["version"] not in (1,2,3,4,5,6):
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
    population = []
    if d["version"] in (3,4,5,6):
        payoff = d.get("motion_payoff")
        if not isinstance(payoff, dict) or payoff.get("kind") not in {
            "viewpoint_change", "physical_action", "assembly", "environment_progression",
            "time_progression", "controlled_effect", "scale_only_fallback",
        }:
            raise ValueError("V3 requires a defined visual payoff")
        concrete(payoff.get("description"), "visual payoff")
        if payoff["kind"] == "scale_only_fallback":
            concrete(payoff.get("fallbackReason"), "scale-only fallback rationale")
        scene = d.get("scene_population", "human_free")
        if scene == "human_free":
            if d.get("human_exception"):
                raise ValueError("Human-free direction cannot include a human exception")
            population = ["Scene remains unoccupied: no people, hands, limbs, silhouettes or reflections of people."]
        elif scene == "human_exception":
            exception = d.get("human_exception")
            if not isinstance(exception, dict):
                raise ValueError("Human exception requires specific justification")
            concrete(exception.get("reason"), "human exception rationale")
            role = concrete(exception.get("role"), "specific human role and action")
            population = ["Only this necessary human action: " + role + " No other people."]
        else:
            raise ValueError("Unsupported scene population")
    rhythm = []
    if d["version"] in (5,6):
        creative = d.get("attention_direction")
        if not isinstance(creative, dict):
            raise ValueError("V5 requires attention direction")
        hook = concrete(creative.get("opening_hook"), "opening hook")
        event = concrete(creative.get("signature_event"), "signature visual event")
        timing = concrete(creative.get("rhythm"), "intentional rhythm")
        concrete(creative.get("niche_fit"), "niche fit")
        style = creative.get("technique")
        if not isinstance(style, str) or not style.strip():
            raise ValueError("V5 requires a named motion technique")
        if style.strip().lower() in {"zoom", "pan", "steady pan", "steady orbit", "slow push-in", "handheld", "scale_only"} or payoff["kind"] == "scale_only_fallback":
            raise ValueError("Routine camera motion alone is insufficient for V5")
        rhythm = ["Opening hook: " + hook, "Signature event: " + event,
                  "Rhythm: " + timing, "Stabilized camera, no handheld shake."]
    if d["version"] == 6:
        intensity = d.get("intensity_direction")
        if not isinstance(intensity, dict):
            raise ValueError("V6 requires assembly-equivalent visual intensity")
        if intensity.get("event_kind") not in {
            "substantial_assembly", "substantial_transformation",
            "substantial_environmental_transition", "substantial_spatial_reveal",
            "substantial_brand_specific_event"
        }:
            raise ValueError("V6 decorative motion alone is insufficient")
        for field in ("initial_state", "intermediate_event", "final_state",
                      "assembly_equivalent_rationale"):
            concrete(intensity.get(field), field)
    # Frame descriptions and camera setup remain in the internal brief. The
    # generation prompt concerns motion and invariants, not restyling the images.
    prompt = "\n".join([
        opening,
        "Camera: " + fields["camera_choreography"],
        *rhythm,
        "Product lock: " + fields["product_lock"],
        "Physical continuity: " + fields["physical_continuity"],
        *lines,
        "End state: " + fields["end_state"],
        "Text-safe area: " + values["protectedTextArea"],
        "Exclude: " + values["forbiddenEffects"],
        *population,
        "No generated text or logos. No cuts. No audio.",
    ])
    if len(prompt.split()) > MAX_V2_WORDS:
        raise ValueError("Structured Flow motion prompt exceeds 180 words; condense motion instructions")
    return prompt

def validate_direction(variant):
    d = variant.get("motionDirection")
    if isinstance(d, dict) and d.get("version") in (4,5,6):
        route = variant.get("frameRouting")
        if route != {"provider": "google-flow", "mode": "reference_linked_pair",
                     "endUsesStartReference": True, "standaloneFramesRequired": True}:
            raise ValueError("V4 matched frames must be generated in Flow with start reference")
    for k in ("startFramePrompt", "endFramePrompt"):
        concrete(variant.get(k), k)
    if variant.get("videoPrompt") != compile_video_prompt(variant):
        raise ValueError("Video prompt must match the compiled shot direction")
