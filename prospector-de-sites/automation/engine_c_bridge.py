"""Verify Engine C's actual three-mock, blind-evaluation selection contract.

Read-only: calculates the deterministic weighted winner, validates the
selected candidate against all hard gates, binds evaluations to mock bytes,
and demands separate generator/evaluator contexts for *new* runs.

A valid contract does not itself prove the evaluator visually inspected the
candidate; independent vision/browser review remains mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

HASH_RE = re.compile(r"^[a-f0-9]{64}$")
CANDIDATES = ("A", "B", "C")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path: Path) -> dict:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Expected JSON object")
    return obj


def score(config: dict, evaluation: dict) -> dict:
    gates = config["hard_gates"]
    weights = config["scoring"]["criteria"]
    if not isinstance(weights, dict) or sum(weights.values()) != 100:
        raise ValueError("Engine C score weights must sum to 100")
    failing = [gate for gate in gates if evaluation.get("hard_gates", {}).get(gate) is not True]
    scores = evaluation.get("scores", {})
    total = 0.0
    for key, weight in weights.items():
        value = scores.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 10:
            raise ValueError("Engine C score value invalid for criterion " + key)
        total += (value / 10.0) * weight
    return {
        "candidate": evaluation.get("candidate_id"),
        "score": round(total, 2),
        "hardGatesPass": not failing,
        "failedGates": failing,
        "scores": scores,
    }


def _tie_key(candidate: dict, config: dict):
    tie_breakers = config["scoring"]["tie_breakers"]
    return tuple(
        candidate["scores"].get(key, -1) if key != "candidate_id"
        else -ord(candidate["candidate"][0])
        for key in tie_breakers
    )


def audit_experiment(path: Path) -> dict:
    path = Path(path).resolve()
    config = load(path / "engine-c.config.json")
    selection = load(path / "selection.json")
    if config.get("candidate_ids") != list(CANDIDATES) or config.get("candidate_count") != 3:
        raise ValueError("Expected exactly three configured Engine C candidates")
    if not isinstance(config.get("hard_gates"), list) or not config["hard_gates"]:
        raise ValueError("Engine C hard gates missing")
    results = []
    blockers = []
    for candidate in CANDIDATES:
        visual = path / "mocks" / f"candidate-{candidate.lower()}.png"
        if not visual.is_file():
            raise ValueError("Engine C original mock screenshot missing")
        evaluation = load(path / "evaluations" / f"candidate-{candidate.lower()}.json")
        if evaluation.get("candidate_id") != candidate:
            raise ValueError("Evaluation candidate ID doesn't match expected image")
        current = score(config, evaluation)
        provenance = evaluation.get("provenance")
        if not isinstance(provenance, dict):
            blockers.append(f"{candidate}: independent evaluation provenance missing")
        else:
            generation = provenance.get("generatorId")
            evaluator = provenance.get("evaluatorId")
            contexts = [provenance.get("generationContextSha256"),
                        provenance.get("evaluationContextSha256")]
            if not generation or not evaluator or generation == evaluator:
                blockers.append(f"{candidate}: generator and evaluator identities not separated")
            if not all(isinstance(v, str) and HASH_RE.fullmatch(v) for v in contexts):
                blockers.append(f"{candidate}: generation/evaluation context SHAs missing")
            elif contexts[0] == contexts[1]:
                blockers.append(f"{candidate}: evaluator context is not fresh")
            if provenance.get("mockSha256") != sha(visual):
                blockers.append(f"{candidate}: evaluation bound to wrong/stale mock image")
        results.append(current)

    min_score = config["scoring"]["min_total"]
    eligible = [r for r in results if r["hardGatesPass"] and r["score"] >= min_score]
    order = config["scoring"]["tie_breakers"]

    def sort_key(result: dict):
        vals = [-result["score"]]
        for key in order:
            if key == "candidate_id":
                vals.append(result["candidate"])
            else:
                vals.append(-result["scores"].get(key, -1))
        vals.append(result["candidate"])
        return tuple(vals)

    eligible.sort(key=sort_key)
    expected_action = "CONTINUE" if eligible else "REGENERATE"
    expected_winner = eligible[0]["candidate"] if eligible else None
    if selection.get("action") != expected_action or selection.get("winner") != expected_winner:
        blockers.append("Stored Engine C selection differs from independent deterministic recomputation")
    prior = selection.get("results", [])
    if not isinstance(prior, list) or len(prior) != 3:
        blockers.append("Stored Engine C results lack the exact three evaluation records")
    else:
        for computed in results:
            previous = next((v for v in prior if isinstance(v, dict)
                             and v.get("candidate_id") == computed["candidate"]), None)
            if not previous or not math.isclose(
                float(previous.get("total", -1)), computed["score"], abs_tol=0.01
            ) or previous.get("hard_gate_pass") != computed["hardGatesPass"]:
                blockers.append(f"{computed['candidate']}: stored score/hard gate mismatch")

    return {
        "status": "BLOCKED" if blockers else "CONTRACT_VERIFIED",
        "selectorAction": expected_action,
        "recomputedWinner": expected_winner,
        "candidateScores": [
            {"id": r["candidate"], "score": r["score"],
             "hardGatesPass": r["hardGatesPass"]} for r in results
        ],
        "sourceHashes": {
            "configSha256": sha(path / "engine-c.config.json"),
            "selectionSha256": sha(path / "selection.json"),
            "candidateImageSha256": {
                c: sha(path / "mocks" / f"candidate-{c.lower()}.png")
                for c in CANDIDATES
            },
        },
        "blockers": blockers,
        "independentVisionReviewStillRequired": True,
        "readyForHumanPreview": False,
        "productionReleaseAuthorized": False, "outreachAuthorized": False,
        "callbackAuthorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, required=True)
    args = parser.parse_args()
    result = audit_experiment(args.experiment)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "CONTRACT_VERIFIED" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": type(exc).__name__,
                          "detail": str(exc)[:200], "readyForHumanPreview": False}))
        raise SystemExit(2)
