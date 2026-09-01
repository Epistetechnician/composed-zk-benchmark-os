"""Strict publication gate for the full Oak Lab real-stream campaign.

State slice: ``oaklab-experience-learning-benchmark-v2``.

Publication is a quality/adaptation/resource/energy claim, not a digest
claim. At least two stream families must show the same algorithm beating
fixed SGD on every declared dimension, with paired significance and powered
assessment cohorts. A valid energy receipt is mandatory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from .benchmark import ALGORITHM_IDS
from .backends import validate_backend_result
from .energy import campaign_binding_digest, read_energy_csv


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"
MIN_STREAMS = 2
MIN_ASSESSMENT_COHORTS = 32


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _validate_matrix(matrix: dict) -> None:
    if matrix.get("state_slice") != STATE_SLICE or not isinstance(matrix.get("datasets"), dict):
        raise ValueError("publication input matrix state or datasets invalid")
    expected = matrix.get("result_digest")
    if expected != _digest({key: value for key, value in matrix.items() if key != "result_digest"}):
        raise ValueError("publication input matrix digest mismatch")
    for name, result in matrix["datasets"].items():
        if set(result.get("algorithms", {})) != set(ALGORITHM_IDS):
            raise ValueError(f"{name}: all-baseline coverage missing")
        count = result.get("assessment_cohort_count")
        if not isinstance(count, int) or count < MIN_ASSESSMENT_COHORTS:
            raise ValueError(f"{name}: powered assessment missing")
        controls = result.get("controls", {})
        if not isinstance(controls, dict) or controls.get("noise_floor", {}).get("status") != "executed" or controls.get("fit_only_topk_feature_sgd_b1", {}).get("status") != "executed":
            raise ValueError(f"{name}: required noise-floor or feature control missing")
        for algorithm, arm in result["algorithms"].items():
            if arm.get("status") == "executed":
                if len(arm.get("assessment_cohorts", [])) != count:
                    raise ValueError(f"{name}/{algorithm}: assessment cohort payload incomplete")


def _candidate_records(matrices: Sequence[dict]) -> dict[str, list[str]]:
    wins: dict[str, list[str]] = {algorithm: [] for algorithm in ALGORITHM_IDS if algorithm != "sgd_b1"}
    for matrix in matrices:
        for stream, result in matrix["datasets"].items():
            records = result.get("publish_records", {})
            reference = records.get("sgd_b1")
            if not reference:
                continue
            for algorithm, record in records.items():
                if algorithm == "sgd_b1" or algorithm not in wins:
                    continue
                required = ("mean_loss", "adaptation_lag", "updates", "active_synaptic_ops",
                            "state_bytes", "replay_storage_bytes")
                if not all(key in record for key in required):
                    continue
                lower = all(record[key] <= reference[key] for key in required)
                strict_resource_reduction = any(record[key] < reference[key] for key in required[1:])
                strict_quality = record["mean_loss"] < reference["mean_loss"]
                p_value = record.get("paired_p_value")
                if lower and strict_resource_reduction and strict_quality and isinstance(p_value, (int, float)) and p_value <= 0.05:
                    wins[algorithm].append(stream)
    return wins


def evaluate(matrices: Sequence[dict], guard_results: Sequence[dict], energy_receipt: Path | None = None,
             backend_results: Sequence[dict] | None = None) -> dict:
    if not matrices:
        raise ValueError("publication gate requires at least one real matrix")
    for matrix in matrices:
        _validate_matrix(matrix)
    if len({stream for matrix in matrices for stream in matrix["datasets"]}) < MIN_STREAMS:
        raise ValueError("publication gate requires at least two stream families")
    for result in guard_results:
        if result.get("state_slice") != STATE_SLICE or result.get("strict_gate", {}).get("status") not in {"candidate", "no_candidate"}:
            raise ValueError("invalid powered guard result")
        if result.get("assessment_cohort_count", 0) < MIN_ASSESSMENT_COHORTS or result.get("power", {}).get("target_met") is not True:
            raise ValueError(f"powered guard result is below the sealed power target: {result.get('dataset')}")
        if result.get("result_digest") != _digest({key: value for key, value in result.items() if key != "result_digest"}):
            raise ValueError(f"guard digest mismatch: {result.get('dataset')}")
    wins = _candidate_records(matrices)
    qualifying = {algorithm: sorted(set(streams)) for algorithm, streams in wins.items()
                  if len(set(streams)) >= MIN_STREAMS}
    energy = None
    if energy_receipt is not None:
        if not backend_results:
            raise ValueError("campaign-bound energy requires backend parity receipts")
        for backend_result in backend_results:
            validate_backend_result(backend_result)
        expected_matrix_digests = tuple(matrix["result_digest"] for matrix in matrices)
        expected_guard_digests = tuple(result["result_digest"] for result in guard_results)
        expected_backend_digests = tuple(result["result_digest"] for result in backend_results)
        receipt = read_energy_csv(str(energy_receipt), require_campaign_binding=True)
        if receipt.matrix_digests != expected_matrix_digests:
            raise ValueError("energy receipt matrix campaign binding mismatch")
        if receipt.guard_result_digests != expected_guard_digests:
            raise ValueError("energy receipt guard campaign binding mismatch")
        if receipt.backend_result_digests != expected_backend_digests:
            raise ValueError("energy receipt backend campaign binding mismatch")
        expected_campaign = campaign_binding_digest(expected_matrix_digests, expected_guard_digests, expected_backend_digests)
        if receipt.campaign_manifest_sha256 != expected_campaign:
            raise ValueError("energy receipt campaign manifest does not match gate inputs")
        energy = {"hardware": receipt.hardware, "events": receipt.events,
                  "joules": receipt.joules, "joules_per_event": receipt.joules_per_event,
                  "source_sha256": receipt.source_sha256,
                  "campaign_manifest_sha256": receipt.campaign_manifest_sha256,
                  "matrix_digests": list(receipt.matrix_digests),
                  "guard_result_digests": list(receipt.guard_result_digests),
                  "backend_result_digests": list(receipt.backend_result_digests)}
    requirements = {
        "at_least_two_stream_families": len({stream for matrix in matrices for stream in matrix["datasets"]}) >= MIN_STREAMS,
        "all_baselines_and_controls_validated": True,
        "powered_assessments": all(result.get("assessment_cohort_count", 0) >= MIN_ASSESSMENT_COHORTS
                                    for matrix in matrices for result in matrix["datasets"].values()),
        "candidate_beats_fixed_sgd_on_quality_adaptation_resources": bool(qualifying),
        "measured_hardware_energy": energy is not None,
    }
    passed = all(requirements.values())
    return {
        "schema_version": "oaklab.experience-learning.publication-gate.v2",
        "state_slice": STATE_SLICE,
        "matrix_digests": [matrix["result_digest"] for matrix in matrices],
        "guard_result_digests": [result["result_digest"] for result in guard_results],
        "candidate_algorithms": qualifying,
        "requirements": requirements,
        "energy": energy,
        "status": "candidate" if passed else "no_candidate",
        "claim_ceiling": "PublicationCandidatePendingIndependentReview" if passed else "LocalDevelopmentOakLabExperienceLearningBenchmarkV2",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, action="append", required=True)
    parser.add_argument("--guard", type=Path, action="append", required=True)
    parser.add_argument("--energy", type=Path)
    parser.add_argument("--backend", type=Path, action="append")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    matrices = [json.loads(path.read_text(encoding="utf-8")) for path in args.matrix]
    guards = [json.loads(path.read_text(encoding="utf-8")) for path in args.guard]
    backends = None if args.backend is None else [json.loads(path.read_text(encoding="utf-8")) for path in args.backend]
    result = evaluate(matrices, guards, args.energy, backends)
    result["result_digest"] = _digest(result)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(result["result_digest"])


if __name__ == "__main__":
    main()
