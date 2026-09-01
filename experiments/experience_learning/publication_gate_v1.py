"""Global quality/resource publication gate for real-stream guard receipts.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Sequence

from .energy import read_energy_csv
from .plasticity_guard_assessment_v1 import PLAN_DIGEST


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def evaluate(results: Sequence[dict], energy_receipt: Path | None = None) -> dict:
    if len(results) < 2:
        raise ValueError("publication gate requires at least two stream receipts")
    datasets = [result.get("dataset") for result in results]
    if any(not isinstance(name, str) for name in datasets) or len(set(datasets)) != len(datasets):
        raise ValueError("publication gate datasets must be distinct")
    for result in results:
        if result.get("schema_version") != "oaklab.experience-learning.plasticity-guard-assessment.v1":
            raise ValueError("publication gate assessment schema mismatch")
        if result.get("plan_digest") != PLAN_DIGEST:
            raise ValueError("publication gate plan digest mismatch")
        expected_digest = result.get("result_digest")
        if expected_digest != _digest({key: value for key, value in result.items() if key != "result_digest"}):
            raise ValueError(f"publication gate input digest mismatch: {result.get('dataset')}")
        strict_gate = result.get("strict_gate")
        if not isinstance(strict_gate, dict) or strict_gate.get("status") not in {"candidate", "no_candidate"}:
            raise ValueError(f"publication gate input strict-gate status invalid: {result.get('dataset')}")
        if strict_gate["status"] == "candidate" and not all(
            strict_gate.get(key) is True for key in ("lower_loss", "paired_p_le_alpha", "power_target_met", "resource_non_inferiority")
        ):
            raise ValueError(f"publication gate input candidate has failed requirement: {result.get('dataset')}")
    candidate_streams = [
        result["dataset"] for result in results
        if result.get("strict_gate", {}).get("status") == "candidate"
    ]
    energy = None
    if energy_receipt is not None:
        receipt = read_energy_csv(str(energy_receipt))
        energy = {"hardware": receipt.hardware, "events": receipt.events,
                  "joules_per_event": receipt.joules_per_event,
                  "source_sha256": receipt.source_sha256}
    requirements = {
        "at_least_two_candidate_streams": len(candidate_streams) >= 2,
        "measured_hardware_energy": energy is not None,
        "all_stream_receipts_valid": True,
    }
    passed = all(requirements.values())
    return {
        "schema_version": "oaklab.experience-learning.publication-gate.v1",
        "state_slice": STATE_SLICE,
        "plan_digest": PLAN_DIGEST,
        "stream_receipt_digests": [result["result_digest"] for result in results],
        "candidate_streams": candidate_streams,
        "requirements": requirements,
        "energy": energy,
        "status": "candidate" if passed else "no_candidate",
        "claim_ceiling": "LocalDevelopmentOakLabExperienceLearningBenchmarkV2" if not passed else "PublicationCandidatePendingIndependentReview",
    }


def read_results(paths: Sequence[Path]) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]
