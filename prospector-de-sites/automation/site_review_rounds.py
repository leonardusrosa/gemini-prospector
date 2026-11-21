"""Offline Engine C review-round protocol.

Agents may produce artifacts and independent review reports; this protocol
controls evidence binding and retry budgets. No generation provider, browser,
CRM, deploy, outreach or scheduler is invoked by this module. A protocol PASS
does not prove a report is truthful: an independent browser/source reviewer
must actually inspect the evidence before submitting it.

Use from a local, ignored .prospector directory. Never store lead PII in git.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import struct
import tempfile
from pathlib import Path

import site_research
import engine_c_bridge
import cms_compatibility

STAGES = (
    "FACTS_AND_IDENTITIES",
    "MEDIA_RIGHTS_AND_RELEVANCE",
    "ENGINE_C_CANDIDATES",
    "INDEPENDENT_DESIGN_DIRECTION",
    "IMPLEMENTATION_AND_RESPONSIVE",
    "CLIENT_CMS_COMPATIBILITY",
    "BROWSER_VISUAL_AND_INTERACTIONS",
    "FACTUAL_AND_CONVERSION_RECHECK",
)
MAX_CORRECTIONS_PER_STAGE = 2
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HASH = re.compile(r"^[0-9a-f]{64}$")
VALID_RESULTS = {"PASS", "FAIL"}
ROLE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._@-]{2,79}$")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    """Check that PNG files have a real IHDR and usable pixel dimensions.

    This is structural validation, not image-content or browser proof.
    """
    with Path(path).open("rb") as fh:
        header = fh.read(24)
    if len(header) != 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Invalid screenshot/candidate PNG signature")
    if header[12:16] != b"IHDR":
        raise ValueError("PNG missing IHDR")
    width, height = struct.unpack(">II", header[16:24])
    if width < 1 or height < 1 or width > 10000 or height > 20000:
        raise ValueError("PNG pixel dimensions invalid")
    return width, height


def read_json(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected an object JSON document")
    return value


def atomic_write_json(path: Path, value: dict) -> None:
    path = Path(path)
    if not path.parent.is_dir():
        raise FileNotFoundError("Run directory must exist; refusing implicit directory creation")
    # This module accepts only files under a local ignored .prospector directory
    # for mutable run receipts. Source and report files may live elsewhere.
    if ".prospector" not in path.resolve().parts:
        raise ValueError("Run state must reside under the ignored .prospector directory")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".site-review-",
        suffix=".tmp", delete=False, newline="\n",
    ) as handle:
        temp = Path(handle.name)
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    try:
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


@contextlib.contextmanager
def exclusive_run_lock(path: Path):
    """Fail-closed local single writer. A stale lock requires manual diagnosis."""
    lock_file = Path(str(path) + ".lock")
    fd = None
    try:
        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, b"Prospector local site review lock; never remove while active.\n")
        yield
    finally:
        if fd is not None:
            os.close(fd)
            lock_file.unlink(missing_ok=True)


def verify_chain(run: dict) -> None:
    """Re-check every previously accepted artifact and reviewer witness."""
    original = Path(run["sourceManifest"])
    if file_hash(original) != run.get("sourceManifestSha256"):
        raise ValueError("Research manifest changed: previous stage evidence is stale")
    for stage in STAGES:
        entry = run["stageState"][stage]
        artifact_path = entry.get("artifact")
        if artifact_path:
            artifact = Path(artifact_path)
            if not artifact.is_file() or file_hash(artifact) != entry.get("artifactSha256"):
                raise ValueError("Stage artifact was modified after submission: " + stage)
            _stage_content_checks(stage, read_json(artifact), run)
        report_path = entry.get("report")
        if report_path:
            report_file = Path(report_path)
            if not report_file.is_file() or file_hash(report_file) != entry.get("reportSha256"):
                raise ValueError("Stage review report was modified after submission: " + stage)
            report = read_json(report_file)
            if report.get("artifactSha256") != entry["artifactSha256"]:
                raise ValueError("Stage review no longer binds to the artifact: " + stage)
            for observation in report.get("observations", []):
                path = Path(observation["evidencePath"])
                if not path.is_file() or file_hash(path) != observation["evidenceSha256"]:
                    raise ValueError("Independent reviewer witness changed: " + stage)


def new_run(manifest_path: Path) -> dict:
    manifest = read_json(manifest_path)
    slug = manifest.get("leadSlug")
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        raise ValueError("Invalid research lead slug")
    if manifest.get("schemaVersion") != 1 or manifest.get("noOutbound") is not True:
        raise ValueError("Research manifest must be v1 read-only/no-outbound")
    # A structured report from the research CLI is not sufficient to claim
    # source/media rights. Independent research review remains its own stage.
    site_research.audit_research_manifest(manifest)
    return {
        "schemaVersion": 2, "leadSlug": slug,
        "sourceManifest": str(Path(manifest_path).resolve()),
        "sourceManifestSha256": file_hash(manifest_path),
        "stages": list(STAGES),
        "currentStageIndex": 0,
        "stageState": {
            stage: {
                "status": "AWAITING_ARTIFACT",
                "correctionCount": 0,
                "artifact": None, "artifactSha256": None,
                "authorId": None, "report": None,
                "reportSha256": None, "reviewerId": None,
            } for stage in STAGES
        },
        "events": [{"stage": STAGES[0], "event": "RUN_STARTED"}],
        "state": "IN_PROGRESS",
        "readyForHumanPreview": False,
        "productionReleaseAuthorized": False,
        "outreachAuthorized": False,
        "callbackAuthorized": False,
        "providerCalls": 0,
    }


def current_stage(run: dict) -> str | None:
    index = run["currentStageIndex"]
    return run["stages"][index] if index < len(run["stages"]) else None


def _assert_current(run: dict, stage: str) -> dict:
    if stage != current_stage(run):
        raise ValueError("Stage is not current; stale/future stage updates are prohibited")
    if run.get("state") != "IN_PROGRESS":
        raise ValueError("Run is blocked or already ready for human Preview")
    return run["stageState"][stage]


def _stage_content_checks(stage: str, artifact: dict, current: dict) -> None:
    if artifact.get("schemaVersion") != 1 or artifact.get("stage") != stage:
        raise ValueError("Artifact stage/schema mismatch")
    if artifact.get("sourceManifestSha256") != current["sourceManifestSha256"]:
        raise ValueError("Artifact must bind to exact initial source manifest SHA")
    if stage == "ENGINE_C_CANDIDATES":
        candidates = artifact.get("candidates")
        if not isinstance(candidates, list) or len(candidates) != 3:
            raise ValueError("Engine C requires exactly three independent candidates")
        ids = [x.get("id") for x in candidates if isinstance(x, dict)]
        if sorted(ids) != ["A", "B", "C"]:
            raise ValueError("Engine C candidate ids must be A/B/C exactly")
        digests = []
        for candidate in candidates:
            image_file = candidate.get("imageFile")
            if not isinstance(image_file, str) or not image_file:
                raise ValueError("Engine C candidate missing image file")
            path = Path(image_file)
            if not path.is_file() or not path.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg"}:
                raise ValueError("Engine C candidate image missing or unsupported")
            if path.suffix.lower() == ".png":
                png_dimensions(path)
            digest = file_hash(path)
            if digest != candidate.get("imageSha256"):
                raise ValueError("Engine C candidate image has changed since provenance was recorded")
            if not ROLE_ID.fullmatch(str(candidate.get("generatorId") or "")):
                raise ValueError("Candidate generator identity must be present")
            digests.append(digest)
        if len(set(digests)) != 3:
            raise ValueError("Engine C candidates must not share the same image bytes")
    elif stage == "INDEPENDENT_DESIGN_DIRECTION":
        experiment_dir = artifact.get("engineCExperimentDirectory")
        if not isinstance(experiment_dir, str):
            raise ValueError("Engine C source experiment directory required")
        # Recompute all hard gates/scores, bind all three original mock hashes,
        # and reject legacy evaluations without independent context metadata.
        bridge_result = engine_c_bridge.audit_experiment(Path(experiment_dir))
        if bridge_result["status"] != "CONTRACT_VERIFIED":
            raise ValueError("Engine C source evaluation provenance is not verified")
        if artifact.get("selectorAction") != "CONTINUE" or (
                artifact.get("winner") != bridge_result["recomputedWinner"]):
            raise ValueError("Engine C selected winner must match independent recomputation")
        if artifact.get("selectionSha256") != (
                bridge_result["sourceHashes"]["selectionSha256"]):
            raise ValueError("Engine C selector artifact changed; stale selection hash")
    elif stage == "CLIENT_CMS_COMPATIBILITY":
        html_file = artifact.get("htmlFile")
        if not isinstance(html_file, str) or not Path(html_file).is_file():
            raise ValueError("Client CMS requires the actual generated static HTML file")
        if file_hash(Path(html_file)) != artifact.get("htmlSha256"):
            raise ValueError("Client CMS source HTML file has changed since review")
        # Structural compatibility is independent of tenant provisioning and
        # authenticated end-to-end CMS/editor smoke tests.
        compatibility = cms_compatibility.audit_html_file(
            Path(html_file), current["leadSlug"]
        )
        if compatibility["result"] != "STRUCTURE_PASS":
            raise ValueError("Generated HTML is not compatible with existing AutoCORA Client CMS")
    elif stage == "BROWSER_VISUAL_AND_INTERACTIONS":
        source_manifest = read_json(Path(current["sourceManifest"]))
        preview_media = any(
            isinstance(item, dict) and item.get("useInProtectedOwnerPreview") is True
            for item in source_manifest.get("assets") or []
        )
        if preview_media:
            probe = artifact.get("independentPreviewAccessProbe") or {}
            decision = site_research.audit_protected_owner_preview(
                source_manifest, access_evidence=probe
            )
            if decision["result"] != "STRUCTURE_READY_FOR_PRIVATE_PREVIEW":
                raise ValueError("Access-protected owner preview lacks independently verified privacy controls")
        screenshots = artifact.get("screenshots")
        if not isinstance(screenshots, dict):
            raise ValueError("Live browser screenshots required")
        for viewport in ("desktop", "mobile"):
            item = screenshots.get(viewport)
            if not isinstance(item, dict):
                raise ValueError("Desktop and mobile screenshot witnesses required")
            path = Path(str(item.get("path") or ""))
            if not path.is_file() or path.suffix.lower() not in {".png", ".webp"}:
                raise ValueError("Screenshot witness missing")
            if file_hash(path) != item.get("sha256"):
                raise ValueError("Screenshot witness changed since capture")
            width, height = png_dimensions(path) if path.suffix.lower() == ".png" else (0, 0)
            if path.suffix.lower() != ".png":
                raise ValueError("Browser screenshots must be real PNG captures")
            if viewport == "desktop" and not (1000 <= width <= 3200 and height >= 600):
                raise ValueError("Desktop screenshot dimensions invalid")
            if viewport == "mobile" and not (320 <= width <= 600 and height >= 500):
                raise ValueError("Mobile screenshot dimensions invalid")
        for check in ("pageErrorsZero", "noHorizontalOverflow",
                      "primaryCtaVisible", "navigationWorks"):
            if artifact.get("checks", {}).get(check) is not True:
                raise ValueError("Browser evidence lacks required observed check: " + check)
    elif stage == "FACTUAL_AND_CONVERSION_RECHECK":
        if artifact.get("deterministicGateExit") != 0:
            raise ValueError("Canonical deterministic site-review gate must pass")
        log_path = artifact.get("deterministicGateLogPath")
        if not isinstance(log_path, str) or not Path(log_path).is_file():
            raise ValueError("Canonical site-review gate log file must exist")
        if artifact.get("deterministicGateLogSha256") != file_hash(Path(log_path)):
            raise ValueError("Canonical site-review log SHA mismatch")
        if artifact.get("sourceFactsIndependentlyRechecked") is not True:
            raise ValueError("Public factual claims require independent source re-check")


def submit_artifact(run: dict, stage: str, path: Path, author: str) -> dict:
    entry = _assert_current(run, stage)
    if not ROLE_ID.fullmatch(author):
        raise ValueError("Author identity is missing/invalid")
    if entry["status"] not in {"AWAITING_ARTIFACT", "NEEDS_CORRECTION"}:
        raise ValueError("Stage already has an artifact awaiting review")
    if not Path(path).is_file():
        raise FileNotFoundError("Stage artifact does not exist")
    artifact = read_json(path)
    _stage_content_checks(stage, artifact, run)
    digest = file_hash(path)
    if entry["status"] == "NEEDS_CORRECTION":
        if digest == entry["artifactSha256"]:
            raise ValueError("Correction must change artifact content")
        if entry["correctionCount"] >= MAX_CORRECTIONS_PER_STAGE:
            raise ValueError("Correction budget exhausted")
        entry["correctionCount"] += 1
    entry.update({"status": "AWAITING_REVIEW", "artifact": str(Path(path).resolve()),
                  "artifactSha256": digest, "authorId": author,
                  "report": None, "reportSha256": None, "reviewerId": None})
    run["events"].append({"stage": stage, "event": "ARTIFACT_SUBMITTED",
                          "artifactSha256": digest, "round": entry["correctionCount"]})
    return run


def independent_review(run: dict, report_path: Path) -> dict:
    stage = current_stage(run)
    if stage is None:
        raise ValueError("No active stage")
    entry = _assert_current(run, stage)
    if entry["status"] != "AWAITING_REVIEW":
        raise ValueError("Stage is not awaiting an independent review")
    if file_hash(Path(entry["artifact"])) != entry["artifactSha256"]:
        raise ValueError("Artifact changed after submission; old review invalid")
    artifact = read_json(Path(entry["artifact"]))
    _stage_content_checks(stage, artifact, run)
    report = read_json(report_path)
    if report.get("schemaVersion") != 1 or report.get("stage") != stage:
        raise ValueError("Review report stage/schema mismatch")
    if report.get("artifactSha256") != entry["artifactSha256"]:
        raise ValueError("Stale review: exact artifact SHA binding required")
    reviewer = report.get("reviewerId")
    if not isinstance(reviewer, str) or not ROLE_ID.fullmatch(reviewer):
        raise ValueError("Independent reviewer identity missing")
    if reviewer == entry["authorId"]:
        raise ValueError("Self-reviewed artifact cannot pass or fail a stage")
    verdict = report.get("verdict")
    if verdict not in VALID_RESULTS:
        raise ValueError("Invalid review verdict")
    observations = report.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("Reviewer must attach concrete observations")
    for obs in observations:
        if not isinstance(obs, dict):
            raise ValueError("Invalid observation shape")
        evidence = obs.get("evidencePath")
        digest = obs.get("evidenceSha256")
        if not isinstance(evidence, str) or not Path(evidence).is_file():
            raise ValueError("Reviewer evidence file must exist")
        if digest != file_hash(Path(evidence)):
            raise ValueError("Review evidence file hash mismatch")
    # A source + media rights audit is always performed on its own stage.
    if verdict == "PASS" and stage in {"FACTS_AND_IDENTITIES",
                                       "MEDIA_RIGHTS_AND_RELEVANCE"}:
        source_manifest = read_json(Path(run["sourceManifest"]))
        structural = site_research.audit_research_manifest(source_manifest)
        if structural["result"] == "BLOCK":
            raise ValueError("Source/media provenance has structural blockers")
        if (stage == "MEDIA_RIGHTS_AND_RELEVANCE" and
                structural["result"] != "STRUCTURE_PASS"):
            # A private owner-facing design preview may use verifiable,
            # brand-linked source media WITHOUT requiring reuse permission
            # at this design stage. It never grants public deployment.
            preview = site_research.audit_protected_owner_preview(source_manifest)
            if (preview["result"] == "BLOCK" or
                    preview["brandAssetsUsableInInternalPreview"] < 1):
                raise ValueError("Media rights unresolved and no valid protected owner-preview path")
    entry.update({"report": str(Path(report_path).resolve()),
                  "reportSha256": file_hash(report_path),
                  "reviewerId": reviewer})
    run["events"].append({"stage": stage, "event": "INDEPENDENT_REVIEW",
                          "verdict": verdict, "round": entry["correctionCount"],
                          "artifactSha256": entry["artifactSha256"],
                          "evidenceCount": len(observations)})
    if verdict == "PASS":
        entry["status"] = "PASS_REVIEWED"
        run["currentStageIndex"] += 1
        if current_stage(run) is None:
            run["state"] = "AWAITING_HUMAN_PREVIEW"
            run["readyForHumanPreview"] = True
        else:
            run["events"].append({"stage": current_stage(run),
                                  "event": "STAGE_AVAILABLE"})
    elif entry["correctionCount"] >= MAX_CORRECTIONS_PER_STAGE:
        entry["status"] = "BLOCKED"
        run["state"] = "BLOCKED"
    else:
        entry["status"] = "NEEDS_CORRECTION"
    return run


def status(run: dict) -> dict:
    stage = current_stage(run)
    entry = run["stageState"].get(stage) if stage else None
    return {
        "leadSlug": run["leadSlug"],
        "state": run["state"],
        "stage": stage,
        "stageStatus": entry["status"] if entry else "COMPLETE",
        "correctionRound": entry["correctionCount"] if entry else 0,
        "maxCorrections": MAX_CORRECTIONS_PER_STAGE,
        "readyForHumanPreview": run["readyForHumanPreview"],
        "productionReleaseAuthorized": False,
        "outreachAuthorized": False, "callbackAuthorized": False,
        "cmsTenantProvisioned": False,
        "cmsAuthenticatedEditPublishRestoreSmokePassed": False,
        "readyForClientHandoff": False,
        "nextAction": (
            "SUBMIT_STAGE_ARTIFACT" if entry and entry["status"] == "AWAITING_ARTIFACT"
            else "INDEPENDENT_REVIEW" if entry and entry["status"] == "AWAITING_REVIEW"
            else "CORRECT_AND_RESUBMIT" if entry and entry["status"] == "NEEDS_CORRECTION"
            else "HUMAN_PREVIEW_DECISION" if stage is None
            else "HUMAN_ESCALATION"
        ),
    }


def main() -> int:
    cli = argparse.ArgumentParser(description="Local site build QA protocol; no provider calls")
    actions = cli.add_subparsers(dest="action", required=True)
    init = actions.add_parser("init")
    init.add_argument("--research", type=Path, required=True)
    init.add_argument("--run", type=Path, required=True)
    for action in ("submit", "review", "status"):
        sub = actions.add_parser(action)
        sub.add_argument("--run", type=Path, required=True)
        if action == "submit":
            sub.add_argument("--stage", required=True, choices=STAGES)
            sub.add_argument("--artifact", required=True, type=Path)
            sub.add_argument("--author", required=True)
        if action == "review":
            sub.add_argument("--report", required=True, type=Path)
    args = cli.parse_args()
    with exclusive_run_lock(args.run):
        if args.action == "init":
            if args.run.exists():
                raise ValueError("Cannot overwrite existing run")
            result = new_run(args.research)
        else:
            result = read_json(args.run)
            if result.get("schemaVersion") != 2 or result.get("stages") != list(STAGES):
                raise ValueError("Old review protocol; start a new isolated v2 run")
            verify_chain(result)
            if args.action == "submit":
                submit_artifact(result, args.stage, args.artifact, args.author)
            elif args.action == "review":
                independent_review(result, args.report)
        if args.action != "status":
            atomic_write_json(args.run, result)
        print(json.dumps(status(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)[:200],
                          "productionReleaseAuthorized": False,
                          "outreachAuthorized": False, "callbackAuthorized": False}))
        raise SystemExit(2)
