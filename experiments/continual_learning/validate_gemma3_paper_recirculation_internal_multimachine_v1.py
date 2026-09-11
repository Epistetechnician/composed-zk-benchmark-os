#!/usr/bin/env python3
"""Fail-closed validator for the internal multi-instance lane.

State slice: continual-learning-gemma3-paper-recirculation-internal-multimachine-v1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-gemma3-paper-recirculation-internal-multimachine-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3InternalMultiInstanceReplication"
INSTANCE_SCHEMA = "gemma3-paper-recirculation-internal-multimachine-v1-instance"
REPLICA_COUNT = 3
PARITY_TOLERANCE = 1e-5
IMPLEMENTATION_MANIFEST_PATH = REPO_ROOT / "docs/research/continual-learning/298-gemma3-paper-recirculation-internal-multimachine-v1-implementation-manifest.json"


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_result(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing result: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != INSTANCE_SCHEMA:
        raise ValueError("instance result schema mismatch")
    result_sha = value.get("result_sha256")
    body = {key: item for key, item in value.items() if key != "result_sha256"}
    if not isinstance(result_sha, str) or digest(body) != result_sha:
        raise ValueError("instance result digest mismatch")
    return value


def validate_implementation_manifest() -> str:
    if not IMPLEMENTATION_MANIFEST_PATH.is_file() or IMPLEMENTATION_MANIFEST_PATH.is_symlink():
        raise ValueError("implementation manifest is missing")
    value = json.loads(IMPLEMENTATION_MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != "gemma3-paper-recirculation-internal-multimachine-v1-implementation":
        raise ValueError("implementation manifest schema mismatch")
    if value.get("state_slice") != STATE_SLICE:
        raise ValueError("implementation manifest state slice mismatch")
    stored = value.get("manifest_sha256")
    body = {key: item for key, item in value.items() if key != "manifest_sha256"}
    if not isinstance(stored, str) or digest(body) != stored:
        raise ValueError("implementation manifest digest mismatch")
    entries = value.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("implementation manifest file list missing")
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
            raise ValueError("invalid implementation manifest entry")
        path = (REPO_ROOT / entry["path"]).resolve()
        if REPO_ROOT not in path.parents or path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"implementation digest mismatch: {entry.get('path')}")
    return stored


def validate_instance(path: Path) -> dict[str, Any]:
    value = read_result(path)
    required = ("state_slice", "claim_ceiling", "instance_id", "machine_id", "selected_pair", "candidate_pairs", "fit_window_count", "assessment_window_count", "window_limit", "execution_mode", "assessment_deltas", "assessment_mean_delta", "assessment_bootstrap_upper_95", "zero_alpha_parity", "deterministic_repeat_max_abs_delta", "temperature_control", "evaluation_alpha", "evaluation_beta", "network_access", "training", "weights_frozen", "model_manifest_sha256", "corpus_manifest_sha256", "runner_sha256", "protocol_sha256", "implementation_manifest_sha256")
    if any(key not in value for key in required):
        raise ValueError("instance result is incomplete")
    if value["state_slice"] != STATE_SLICE or value["claim_ceiling"] != CLAIM_CEILING:
        raise ValueError("instance identity mismatch")
    if not isinstance(value["instance_id"], str) or not value["instance_id"]:
        raise ValueError("instance id missing")
    if value["selected_pair"] not in ([7, 2], [9, 3], [11, 4], [12, 5]):
        raise ValueError("selected pair is outside fixed candidates")
    if value["candidate_pairs"] != [[7, 2], [9, 3], [11, 4], [12, 5]]:
        raise ValueError("candidate set mismatch")
    if value["window_limit"] not in (4, 16) or value["fit_window_count"] != value["window_limit"] or value["assessment_window_count"] != value["window_limit"]:
        raise ValueError("window count contract mismatch")
    expected_mode = "replication" if value["window_limit"] == 16 else "engineering-smoke"
    if value["execution_mode"] != expected_mode:
        raise ValueError("execution mode mismatch")
    deltas = value["assessment_deltas"]
    if len(deltas) != value["window_limit"] or not all(type(item) in (int, float) and math.isfinite(item) for item in deltas):
        raise ValueError("assessment deltas are invalid")
    if type(value["assessment_mean_delta"]) not in (int, float) or not math.isfinite(value["assessment_mean_delta"]):
        raise ValueError("assessment mean delta is invalid")
    if not math.isclose(value["assessment_mean_delta"], sum(deltas) / len(deltas), rel_tol=0, abs_tol=1e-12):
        raise ValueError("assessment mean delta mismatch")
    if type(value["assessment_bootstrap_upper_95"]) not in (int, float) or not math.isfinite(value["assessment_bootstrap_upper_95"]):
        raise ValueError("bootstrap bound invalid")
    parity = value["zero_alpha_parity"]
    if not isinstance(parity, dict) or parity.get("passed") is not True or parity.get("max_abs_logit_delta", float("inf")) > PARITY_TOLERANCE:
        raise ValueError("zero-alpha parity failed")
    if type(value["deterministic_repeat_max_abs_delta"]) not in (int, float) or not math.isfinite(value["deterministic_repeat_max_abs_delta"]) or value["deterministic_repeat_max_abs_delta"] > PARITY_TOLERANCE:
        raise ValueError("deterministic repeat failed")
    if value["evaluation_alpha"] != 0.15 or value["evaluation_beta"] != 0.85:
        raise ValueError("evaluation mixture mismatch")
    temperature = value["temperature_control"]
    if not isinstance(temperature, dict) or temperature.get("temperature") != 1.2 or type(temperature.get("baseline_mean_nll")) not in (int, float) or not math.isfinite(temperature["baseline_mean_nll"]):
        raise ValueError("temperature control failed")
    if value["network_access"] is not False or value["training"] is not False or value["weights_frozen"] is not True:
        raise ValueError("offline/frozen controls failed")
    return value


def aggregate(paths: list[Path]) -> dict[str, Any]:
    if len(paths) != REPLICA_COUNT:
        raise ValueError(f"exactly {REPLICA_COUNT} instance results are required")
    implementation_manifest_sha256 = validate_implementation_manifest()
    results = [validate_instance(path) for path in paths]
    if any(item["window_limit"] != 16 for item in results):
        raise ValueError("engineering smoke results cannot be aggregated as replication")
    ids = [item["instance_id"] for item in results]
    if len(set(ids)) != len(ids):
        raise ValueError("instance identities are not unique")
    bound_fields = ("model_manifest_sha256", "corpus_manifest_sha256", "runner_sha256", "protocol_sha256", "implementation_manifest_sha256")
    for field in bound_fields:
        if len({item[field] for item in results}) != 1:
            raise ValueError(f"cross-instance {field} mismatch")
    if results[0]["implementation_manifest_sha256"] != implementation_manifest_sha256:
        raise ValueError("implementation manifest binding mismatch")
    pairs = {tuple(item["selected_pair"]) for item in results}
    if len(pairs) != 1:
        decision = "NoCandidate"
    else:
        all_deltas = [delta for item in results for delta in item["assessment_deltas"]]
        mean_delta = sum(all_deltas) / len(all_deltas)
        upper = max(item["assessment_bootstrap_upper_95"] for item in results)
        every_instance_passed = all(
            item["assessment_mean_delta"] < 0 and item["assessment_bootstrap_upper_95"] < 0
            for item in results
        )
        decision = "InternalReplicatedEffect" if every_instance_passed and mean_delta < 0 and upper < 0 else "NoCandidate"
    machines = {item["machine_id"] for item in results}
    disposition = "MultiMachineInternalReplication" if len(machines) >= 2 else "SingleMachineMultiInstanceOnly"
    output = {
        "schema": "gemma3-paper-recirculation-internal-multimachine-v1-aggregate",
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "instance_count": len(results),
        "instance_ids": ids,
        "machine_count": len(machines),
        "selected_pairs": [item["selected_pair"] for item in results],
        "bound_digests": {field: results[0][field] for field in bound_fields},
        "decision": decision,
        "disposition": disposition,
        "independent_review": False,
        "scientific_claim_authorized": False,
        "result_sha256": digest({
            "instance_count": len(results),
            "instance_ids": ids,
            "machine_count": len(machines),
            "selected_pairs": [item["selected_pair"] for item in results],
            "bound_digests": {field: results[0][field] for field in bound_fields},
            "decision": decision,
            "disposition": disposition,
            "independent_review": False,
            "scientific_claim_authorized": False,
        }),
    }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-result", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = aggregate(args.instance_result)
    if args.output:
        if args.output.exists() or REPO_ROOT in args.output.resolve().parents:
            raise ValueError("output must be new and external")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
